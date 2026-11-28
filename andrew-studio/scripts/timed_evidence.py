"""Local timestamped acoustic evidence and optional user-provided lyric cues.

Measurements are not judgments of artistic intention or speech recognition.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import numpy as np
import soundfile as sf


def dbfs(value):
    return 20 * math.log10(value) if value > 0 else None


def validate_cues(cues):
    if not isinstance(cues, list) or len(cues) > 100000:
        raise ValueError("Expected a bounded list of lyric cues")
    out = []
    for cue in cues:
        if not isinstance(cue, dict):
            raise ValueError("Invalid cue")
        start, end, text = (cue.get(k) for k in ("start_seconds", "end_seconds", "text"))
        if (type(start) not in (int, float) or type(end) not in (int, float)
                or not math.isfinite(start) or not math.isfinite(end)
                or not 0 <= start < end or not isinstance(text, str) or not text.strip()):
            raise ValueError("Invalid lyric cue interval or text")
        out.append({"start_seconds": start, "end_seconds": end, "text": text})
    return sorted(out, key=lambda c: c["start_seconds"])


def analyze(path, window_seconds=1.0, cues=None):
    """Stream non-overlapping blocks; keep timestamp and cue attribution explicit."""
    if (type(window_seconds) not in (int, float) or not math.isfinite(window_seconds)
            or not .1 <= window_seconds <= 10):
        raise ValueError("Window must be 0.1–10 seconds")
    cues = validate_cues([] if cues is None else cues)
    rows, active = [], []
    cue_index, offset = 0, 0
    with sf.SoundFile(path) as audio:
        sr, channels = audio.samplerate, audio.channels
        if not 1 <= sr <= 384000 or not 1 <= channels <= 32 or audio.frames <= 0:
            raise ValueError("Unsupported or empty audio")
        window = max(1, round(window_seconds * sr))
        if window * channels > 8_000_000 or math.ceil(audio.frames / window) > 100000:
            raise ValueError("Analysis exceeds block or report size limit")
        for block in audio.blocks(blocksize=window, dtype="float64", always_2d=True):
            if not np.isfinite(block).all():
                raise ValueError("Non-finite audio")
            start, end = offset / sr, (offset + len(block)) / sr
            peak = float(np.abs(block).max())
            rms = float(np.sqrt(np.mean(block * block)))
            # Channel-wise power, not mono sum, to avoid phase cancellation.
            spectrum = np.abs(np.fft.rfft(block * np.hanning(len(block))[:, None], axis=0)) ** 2
            power = spectrum.sum(axis=1)
            freq = np.fft.rfftfreq(len(block), 1 / sr)
            total = float(power.sum())
            centroid = float(np.dot(freq, power) / total) if total > 0 else None
            while cue_index < len(cues) and cues[cue_index]["start_seconds"] < end:
                active.append(cues[cue_index])
                cue_index += 1
            active = [c for c in active if c["end_seconds"] > start]
            rows.append({
                "start_seconds": start, "end_seconds": end,
                "sample_peak_dbfs": dbfs(peak), "rms_dbfs": dbfs(rms),
                "crest_db": 20 * math.log10(peak / rms) if rms > 0 else None,
                "spectral_centroid_hz": centroid,
                "clipped_samples": int(np.count_nonzero(np.abs(block) >= 1)),
                "lyric_cues": [dict(c) for c in active],
            })
            offset += len(block)
    return {"source": str(Path(path).name), "sample_rate_hz": sr, "channels": channels,
            "duration_seconds": offset / sr, "window_seconds_requested": window_seconds,
            "evidence_type": "measured_acoustic_features_with_user_supplied_cues",
            "limitations": "Not speech recognition, source separation, certified true peak, or artistic-intent inference.",
            "segments": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio")
    parser.add_argument("--window-seconds", type=float, default=1)
    parser.add_argument("--lyrics-json")
    args = parser.parse_args()
    cues = None
    if args.lyrics_json:
        with open(args.lyrics_json, "rb") as handle:
            raw = handle.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError("Lyric cue file too large")
        cues = json.loads(raw)
    print(json.dumps(analyze(args.audio, args.window_seconds, cues), ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
