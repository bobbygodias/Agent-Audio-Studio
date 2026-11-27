#!/usr/bin/env python3
"""Small, transparent offline DSP rack for Andrew Studio.

Dependencies: numpy, scipy, soundfile. librosa is optional for pitch/time effects.
Audio arrays use shape (frames, channels), float32/float64, and a separate Hz rate.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import uniform_filter1d


def inspect(audio: np.ndarray, sr: int) -> dict:
    x = np.asarray(audio, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if not len(x) or not np.isfinite(x).all():
        raise ValueError("Áudio vazio ou com NaN/Inf.")
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x * x)))
    frequencies, power = signal.welch(x, fs=sr, nperseg=min(8192, len(x)), axis=0)
    power = power.sum(axis=1)
    band = lambda lo, hi: float(power[(frequencies >= lo) & (frequencies < hi)].sum())
    return {
        "duration_seconds": len(x) / sr,
        "sample_rate_hz": int(sr),
        "channels": int(x.shape[1]),
        "sample_peak_dbfs": 20 * math.log10(peak) if peak else None,
        "rms_dbfs": 20 * math.log10(rms) if rms else None,
        "samples_clipped": int(np.count_nonzero(np.abs(x) >= 1.0)),
        "band_energy_percent": {
            "sub_20_60_hz": 100 * band(20, 60) / max(float(power.sum()), 1e-30),
            "low_60_200_hz": 100 * band(60, 200) / max(float(power.sum()), 1e-30),
            "low_mid_200_500_hz": 100 * band(200, 500) / max(float(power.sum()), 1e-30),
            "mid_500_2k_hz": 100 * band(500, 2000) / max(float(power.sum()), 1e-30),
            "presence_2k_8k_hz": 100 * band(2000, 8000) / max(float(power.sum()), 1e-30),
            "air_8k_plus_hz": 100 * band(8000, sr / 2 + 1) / max(float(power.sum()), 1e-30),
        },
        "stereo_correlation": float(np.corrcoef(x.T)[0, 1]) if x.shape[1] == 2 and np.all(np.std(x, axis=0) > 1e-12) else None,
        "measurement_note": "Band energy locates energy only; it is not an automatic tonal diagnosis. Peak is sample peak, not certified true peak.",
    }


def _biquad(x, sr, kind, hz, q=0.707, gain_db=0.0):
    hz = float(np.clip(hz, 1.0, sr * 0.49))
    w0 = 2 * np.pi * hz / sr
    alpha = np.sin(w0) / (2 * max(q, 0.05))
    A = 10 ** (gain_db / 40)
    c, s = np.cos(w0), np.sin(w0)
    if kind == "peak":
        b = [1 + alpha * A, -2*c, 1 - alpha*A]
        a = [1 + alpha/A, -2*c, 1 - alpha/A]
    elif kind == "low_shelf":
        beta = 2*np.sqrt(A)*alpha
        b = [A*((A+1)-(A-1)*c+beta), 2*A*((A-1)-(A+1)*c), A*((A+1)-(A-1)*c-beta)]
        a = [(A+1)+(A-1)*c+beta, -2*((A-1)+(A+1)*c), (A+1)+(A-1)*c-beta]
    elif kind == "high_shelf":
        beta = 2*np.sqrt(A)*alpha
        b = [A*((A+1)+(A-1)*c+beta), -2*A*((A-1)+(A+1)*c), A*((A+1)+(A-1)*c-beta)]
        a = [(A+1)-(A-1)*c+beta, 2*((A-1)-(A+1)*c), (A+1)-(A-1)*c-beta]
    elif kind == "lowpass":
        b, a = signal.butter(2, hz, fs=sr, btype="lowpass")
    elif kind == "highpass":
        b, a = signal.butter(2, hz, fs=sr, btype="highpass")
    else:
        raise ValueError(f"Filtro desconhecido: {kind}")
    b, a = np.asarray(b) / a[0], np.asarray(a) / a[0]
    return signal.lfilter(b, a, x, axis=0)


def _compress(x, sr, threshold_db=-18, ratio=3, attack_ms=10, release_ms=100, makeup_db=0):
    threshold = 10 ** (threshold_db / 20)
    release = np.exp(-1 / max(sr * release_ms / 1000, 1))
    # Fast block-independent detector: short RMS window, then exponential release.
    win = max(1, round(sr * attack_ms / 1000))
    detector = np.sqrt(uniform_filter1d(x*x, size=win, axis=0, mode="nearest"))
    env = signal.lfilter([1-release], [1, -release], detector, axis=0)
    over = np.maximum(20*np.log10(np.maximum(env, 1e-12)) - threshold_db, 0)
    reduction_db = over * (1 - 1 / max(ratio, 1))
    return x * 10 ** (-reduction_db / 20) * 10 ** (makeup_db / 20)


def _delay(x, sr, time_ms=280, feedback=0.22, mix=0.2):
    """Causal feedback delay. A fully dry mix returns the original unchanged."""
    n = max(1, round(sr * time_ms / 1000))
    feedback = float(np.clip(feedback, 0, .85))
    mix = float(np.clip(mix, 0, 1))
    if mix == 0:
        return x.copy()
    line = np.zeros((n, x.shape[1]), dtype=x.dtype)
    out = np.empty_like(x)
    pos = 0
    for i in range(len(x)):
        delayed = line[pos].copy()
        line[pos] = x[i] + feedback * delayed
        out[i] = (1 - mix) * x[i] + mix * delayed
        pos = (pos + 1) % n
    return out


def _reverb(x, sr, room=0.65, damping_hz=6500, wet=0.18, predelay_ms=12):
    # Schroeder-style parallel combs + serial allpass stages, per channel.
    room, wet = np.clip(room, 0, .95), np.clip(wet, 0, 1)
    predelay = max(0, round(sr * predelay_ms / 1000))
    inp = np.pad(x, ((predelay, 0), (0, 0)))[:len(x)]
    comb_lengths = [round(sr*t) for t in (.0297, .0371, .0411, .0437)]
    wet_sig = np.zeros_like(inp)
    for n in comb_lengths:
        n = max(2, n)
        buf = np.zeros((n, x.shape[1]))
        pos = 0
        state = np.zeros(x.shape[1])
        damp = np.exp(-2*np.pi*np.clip(damping_hz, 100, sr*.45)/sr)
        for i in range(len(inp)):
            d = buf[pos].copy()
            state = (1-damp)*d + damp*state
            fb = room * state
            buf[pos] = inp[i] + fb
            wet_sig[i] += d
            pos = (pos + 1) % n
    wet_sig *= 1 / len(comb_lengths)
    # Causal Schroeder all-pass diffusion; no look-ahead/pre-echo.
    for delay_ms in (5.0, 1.7):
        n = max(1, round(sr * delay_ms / 1000))
        buf = np.zeros((n, x.shape[1]), dtype=wet_sig.dtype)
        pos = 0
        g = 0.55
        for i in range(len(wet_sig)):
            prev = buf[pos].copy()
            v = wet_sig[i] + g * prev
            wet_sig[i] = prev - g * v
            buf[pos] = v
            pos = (pos + 1) % n
    return x*(1-wet) + wet_sig*wet


def _chorus(x, sr, rate_hz=0.8, depth_ms=9, mix=0.18):
    t = np.arange(len(x)) / sr
    delay = (12 + depth_ms * (1 + np.sin(2*np.pi*rate_hz*t))) * sr / 1000
    idx = np.arange(len(x)) - delay
    out = np.empty_like(x)
    base = np.arange(len(x))
    for c in range(x.shape[1]):
        out[:, c] = np.interp(idx, base, x[:, c], left=0, right=0)
    return x*(1-mix) + out*mix


def _distortion(x, sr, style="tube", drive_db=12, mix=1.0, output_db=-3, oversample=2):
    """Several deliberately simple, named waveshaper families with optional oversampling."""
    drive = 10 ** (drive_db / 20)
    factor = int(np.clip(oversample, 1, 8))
    z = signal.resample_poly(x, factor, 1, axis=0) if factor > 1 else x
    v = z * drive
    if style == "tube":
        wet = np.tanh(v)
    elif style == "hard_clip":
        wet = np.clip(v, -1, 1)
    elif style == "fuzz":
        wet = np.tanh(v) + .16*np.tanh(3*v)
        wet /= 1.16
    elif style == "asymmetric":
        wet = np.where(v >= 0, np.tanh(v), .72*np.tanh(v*1.45))
    elif style == "foldback":
        wet = 1 - np.abs(np.mod(v + 1, 4) - 2)
    elif style == "bitcrush":
        bits = int(np.clip(16 - drive_db/3, 3, 16))
        levels = 2 ** (bits - 1)
        wet = np.round(np.clip(v, -1, 1)*levels)/levels
    else:
        raise ValueError("style: use tube, hard_clip, fuzz, asymmetric, foldback ou bitcrush")
    if factor > 1:
        wet = signal.resample_poly(wet, 1, factor, axis=0)[:len(x)]
    # Blend against dry and normalize the shaper's nominal peak; output gain remains explicit.
    wet = wet * 10 ** (output_db/20)
    return x*(1-mix) + wet*mix


def _scratch(x, sr, rate_curve, start_seconds=0.0, mix=1.0):
    """DJ-style scrub by variable-rate resampling; curve points are [time_ms, rate]."""
    if not isinstance(rate_curve, list) or len(rate_curve) < 2:
        raise ValueError("scratch precisa de ao menos dois pontos [time_ms, rate].")
    points = np.asarray(rate_curve, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 2 or np.any(np.diff(points[:, 0]) <= 0):
        raise ValueError("rate_curve deve ter tempos crescentes em ms e rate com sinal.")
    if np.any(np.abs(points[:, 1]) > 8):
        raise ValueError("Scratch rate deve ficar entre -8x e +8x.")
    out_times = np.arange(len(x), dtype=np.float64) / sr
    rates = np.interp(out_times*1000, points[:, 0], points[:, 1], left=points[0, 1], right=points[-1, 1])
    positions = round(start_seconds*sr) + np.concatenate(([0.0], np.cumsum((rates[:-1] + rates[1:])*.5)))
    base = np.arange(len(x), dtype=np.float64)
    scrubbed = np.column_stack([np.interp(positions, base, x[:, c], left=0.0, right=0.0) for c in range(x.shape[1])])
    mix = float(np.clip(mix, 0, 1))
    return x*(1-mix) + scrubbed*mix


def apply_effect(x: np.ndarray, sr: int, effect: dict) -> np.ndarray:
    name = effect.get("effect")
    p = effect.get("parameters", {})
    if effect.get("bypass", False):
        return x
    if name == "gain": return x * 10 ** (float(p.get("db", 0))/20)
    if name in ("lowpass", "highpass", "peak_eq", "low_shelf", "high_shelf"):
        return _biquad(x, sr, {"peak_eq":"peak"}.get(name, name), p.get("hz", 1000), p.get("q", .707), p.get("gain_db", 0))
    if name == "compressor": return _compress(x, sr, **p)
    if name == "saturator":
        drive = 10 ** (float(p.get("drive_db", 6))/20)
        return np.tanh(x*drive) / max(np.tanh(drive), 1e-8) * float(p.get("output", 1.0))
    if name == "distortion": return _distortion(x, sr, **p)
    if name == "guitar_amp":
        drive = 10 ** (float(p.get("drive_db", 15))/20)
        y = np.tanh(x*drive) * float(p.get("level", .8))
        y = _biquad(y, sr, "highpass", p.get("low_cut_hz", 80))
        return _biquad(y, sr, "lowpass", p.get("high_cut_hz", 8500))
    if name == "delay": return _delay(x, sr, **p)
    if name == "reverb": return _reverb(x, sr, **p)
    if name == "chorus": return _chorus(x, sr, **p)
    if name == "stereo_width":
        if x.shape[1] != 2: return x
        mid = (x[:, 0] + x[:, 1]) * .5
        side = (x[:, 0] - x[:, 1]) * .5 * float(p.get("width", 1.0))
        return np.column_stack((mid+side, mid-side))
    if name == "slap_color":
        # Harmonic parallel layer; cannot change performed articulation or notes.
        hp = _biquad(x, sr, "highpass", p.get("split_hz", 700))
        harmonics = np.tanh(hp * float(p.get("drive", 3.0)))
        return x + float(p.get("blend", .22))*harmonics
    if name == "transient":
        attack_ms = float(p.get("attack_ms", 12))
        win = max(2, round(sr*attack_ms/1000))
        smooth = signal.lfilter(np.ones(win)/win, [1], np.abs(x), axis=0)
        transient = x - np.sign(x)*smooth
        return x + float(p.get("amount", .35))*transient
    if name == "scratch": return _scratch(x, sr, **p)
    if name in ("pitch_shift", "time_stretch"):
        try:
            import librosa
        except ImportError as exc:
            raise RuntimeError(f"{name} requer librosa; biblioteca indisponível nesta execução.") from exc
        channels = []
        for ch in x.T:
            if name == "pitch_shift":
                y = librosa.effects.pitch_shift(ch.astype(np.float32), sr=sr, n_steps=float(p.get("semitones", 0)))
                y = librosa.util.fix_length(y, size=len(ch))
            else:
                y = librosa.effects.time_stretch(ch.astype(np.float32), rate=float(p.get("rate", 1)))
            channels.append(y)
        return np.column_stack(channels)
    raise ValueError(f"Efeito desconhecido: {name!r}")


def render(input_path: Path, recipe_path: Path, output_path: Path):
    source = input_path.resolve()
    output = output_path.resolve()
    if source == output:
        raise ValueError("A saída não pode sobrescrever o arquivo de origem.")
    if output.exists() or output.with_suffix(output.suffix + ".report.json").exists():
        raise FileExistsError("O arquivo de saída ou seu relatório já existe; escolha um novo nome/versionamento.")
    info = sf.info(source)
    if info.frames <= 0 or info.frames * info.channels > 100_000_000:
        raise ValueError("Arquivo vazio ou grande demais para este render em memória.")
    x, sr = sf.read(source, dtype="float32", always_2d=True)
    if not np.isfinite(x).all():
        raise ValueError("Áudio contém valores não finitos.")
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    chain = recipe.get("chain")
    if not isinstance(chain, list) or len(chain) > 32:
        raise ValueError("A receita precisa de uma lista chain com até 32 efeitos.")
    y = x.astype(np.float64)
    for item in chain:
        y = apply_effect(y, sr, item)
        if not np.isfinite(y).all():
            raise ValueError(f"{item.get('effect')} gerou valores não finitos; render cancelado.")
    output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output, y, sr, subtype="FLOAT", format="WAV")
    report = {"source": source.name, "output": str(output), "recipe": recipe, "before": inspect(x, sr), "after": inspect(y, sr), "output_subtype": "WAV float32", "source_preserved": True}
    output.with_suffix(output.suffix + ".report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def mix_stems(recipe_path: Path, output_path: Path, target_sr: int | None = None):
    """Align and sum named mono/stereo stems non-destructively from a JSON recipe."""
    recipe_path = recipe_path.resolve()
    recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
    stems = recipe.get("stems")
    if not isinstance(stems, list) or not stems:
        raise ValueError("A receita precisa conter stems: [ ... ].")
    output_path = output_path.resolve()
    # Stem paths are relative to the recipe location, not the shell working directory.
    paths = [(Path(item["path"]) if Path(item["path"]).is_absolute()
              else recipe_path.parent / item["path"]).resolve() for item in stems]
    if output_path in paths:
        raise ValueError("A saída não pode sobrescrever um stem.")
    if output_path.exists() or output_path.with_suffix(output_path.suffix + ".report.json").exists():
        raise FileExistsError("O arquivo de saída ou seu relatório já existe; escolha um novo nome/versionamento.")
    sr = int(target_sr or recipe.get("sample_rate_hz") or sf.info(paths[0]).samplerate)
    if sr < 8000 or sr > 192000:
        raise ValueError("sample_rate_hz deve ficar entre 8000 e 192000.")
    # Predict the mix allocation before loading any stem. Previously the limit
    # was checked only after sf.read/resample, when memory was already spent.
    preflight, projected_end, projected_loaded = [], 0, 0
    for item, path in zip(stems, paths):
        info = sf.info(path)
        if info.channels not in (1, 2) or info.frames < 1 or info.samplerate < 1:
            raise ValueError(f"{path.name}: stem vazio ou formato de canais inválido.")
        offset = float(item.get("start_seconds", 0))
        if not math.isfinite(offset):
            raise ValueError("Deslocamento do stem deve ser finito.")
        start = max(0, round(offset * sr))
        expected_frames = (int(info.frames) * sr + int(info.samplerate) - 1) // int(info.samplerate)
        projected_end = max(projected_end, start + expected_frames)
        projected_loaded += expected_frames * 2  # Mono is expanded to stereo.
        if projected_end * 2 > 120_000_000 or projected_loaded > 120_000_000:
            raise ValueError("Mix excede o limite de memória configurado.")
        preflight.append((item, path, start))

    loaded, end_frame = [], 0
    for item, path, start in preflight:
        audio, source_sr = sf.read(path, dtype="float32", always_2d=True)
        if audio.shape[1] > 2:
            raise ValueError(f"{path.name}: somente stems mono/estéreo são aceitos.")
        if not np.isfinite(audio).all():
            raise ValueError(f"{path.name}: áudio não finito.")
        if source_sr != sr:
            from math import gcd
            common = gcd(int(source_sr), sr)
            audio = signal.resample_poly(audio, sr//common, source_sr//common, axis=0)
        if audio.shape[1] == 1:
            audio = np.repeat(audio, 2, axis=1)
        chain = item.get("chain", [])
        for effect in chain:
            audio = apply_effect(audio.astype(np.float64), sr, effect)
        gain = 10 ** (float(item.get("gain_db", 0))/20)
        pan = float(np.clip(item.get("pan", 0), -1, 1))
        # Equal-power pan for mono/stereo-as-dual-mono; stereo balance otherwise.
        if np.allclose(audio[:, 0], audio[:, 1]):
            audio = audio * np.array([np.cos((pan+1)*np.pi/4), np.sin((pan+1)*np.pi/4)])
        elif pan < 0:
            audio[:, 1] *= 1+pan
        elif pan > 0:
            audio[:, 0] *= 1-pan
        if item.get("polarity_invert", False):
            audio *= -1
        audio *= gain
        end_frame = max(end_frame, start+len(audio))
        loaded.append((item.get("name", path.stem), audio, start, path))
    if end_frame * 2 > 120_000_000:
        raise ValueError("Mix excede o limite de memória configurado.")
    mix = np.zeros((end_frame, 2), dtype=np.float64)
    for _, audio, start, _ in loaded:
        mix[start:start+len(audio)] += audio
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, mix, sr, subtype="FLOAT", format="WAV")
    report = {"output": str(output_path), "sample_rate_hz": sr, "stems": [{"name": name, "source": path.name, "start_seconds": start/sr, "frames": len(audio)} for name, audio, start, path in loaded], "measurements": inspect(mix, sr), "output_subtype": "WAV float32", "source_preserved": True}
    output_path.with_suffix(output_path.suffix+".report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    pi = sub.add_parser("inspect"); pi.add_argument("input", type=Path)
    pr = sub.add_parser("render"); pr.add_argument("input", type=Path); pr.add_argument("recipe", type=Path); pr.add_argument("output", type=Path)
    pm = sub.add_parser("mix"); pm.add_argument("recipe", type=Path); pm.add_argument("output", type=Path); pm.add_argument("--sample-rate", type=int)
    args = ap.parse_args()
    if args.command == "inspect":
        x, sr = sf.read(args.input, dtype="float32", always_2d=True)
        print(json.dumps(inspect(x, sr), indent=2, ensure_ascii=False))
    elif args.command == "render":
        print(json.dumps(render(args.input, args.recipe, args.output), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(mix_stems(args.recipe, args.output, args.sample_rate), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
