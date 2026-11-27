import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import studio_dsp as dsp


class StudioDSPTests(unittest.TestCase):
    def setUp(self):
        self.sr = 24000
        t = np.arange(self.sr * 2) / self.sr
        mono = .25*np.sin(2*np.pi*220*t) + .08*np.sin(2*np.pi*1800*t)
        self.audio = np.column_stack((mono, mono*.8)).astype(np.float32)

    def test_measurement_shape_and_peak(self):
        report = dsp.inspect(self.audio, self.sr)
        self.assertEqual(report["channels"], 2)
        self.assertAlmostEqual(report["duration_seconds"], 2)
        self.assertLess(report["sample_peak_dbfs"], 0)

    def test_gain_and_filter_are_finite_and_useful(self):
        gained = dsp.apply_effect(self.audio, self.sr, {"effect":"gain", "parameters":{"db":6}})
        self.assertAlmostEqual(np.sqrt(np.mean(gained**2))/np.sqrt(np.mean(self.audio**2)), 10**(6/20), places=5)
        filtered = dsp.apply_effect(self.audio, self.sr, {"effect":"highpass", "parameters":{"hz":500}})
        self.assertTrue(np.isfinite(filtered).all())
        self.assertLess(np.sqrt(np.mean(filtered**2)), np.sqrt(np.mean(self.audio**2)))

    def test_mono_width_is_safe_and_effects_preserve_duration(self):
        mono = self.audio[:, :1]
        widened = dsp.apply_effect(mono, self.sr, {"effect":"stereo_width", "parameters":{"width":1.5}})
        self.assertEqual(widened.shape, mono.shape)
        for name, params in [("compressor", {}), ("guitar_amp", {}), ("delay", {}), ("reverb", {}), ("chorus", {}), ("slap_color", {}), ("transient", {})]:
            y = dsp.apply_effect(self.audio[:self.sr//2], self.sr, {"effect":name, "parameters":params})
            self.assertEqual(y.shape, self.audio[:self.sr//2].shape, name)
            self.assertTrue(np.isfinite(y).all(), name)

    def test_distortion_styles_and_scratch_gesture(self):
        for style in ("tube", "hard_clip", "fuzz", "asymmetric", "foldback", "bitcrush"):
            y = dsp.apply_effect(self.audio, self.sr, {"effect":"distortion", "parameters":{"style":style, "drive_db":15}})
            self.assertEqual(y.shape, self.audio.shape, style)
            self.assertTrue(np.isfinite(y).all(), style)
        curve = [[0, 1], [100, -1], [200, 1], [500, 1]]
        y = dsp.apply_effect(self.audio, self.sr, {"effect":"scratch", "parameters":{"rate_curve":curve, "start_seconds":.5}})
        self.assertEqual(y.shape, self.audio.shape)
        self.assertTrue(np.isfinite(y).all())

    def test_delay_dry_is_unchanged_and_feedback_has_correct_first_echo(self):
        src = np.zeros((self.sr, 1), dtype=np.float64)
        src[0, 0] = 0.5
        dry = dsp._delay(src, self.sr, time_ms=100, feedback=.5, mix=0)
        np.testing.assert_array_equal(dry, src)
        echo = dsp._delay(src, self.sr, time_ms=100, feedback=.5, mix=1)
        self.assertAlmostEqual(echo[2400, 0], 0.5, places=6)
        self.assertAlmostEqual(echo[4800, 0], 0.25, places=6)
        self.assertAlmostEqual(echo[7200, 0], 0.125, places=6)

    def test_relative_stem_paths_are_relative_to_recipe(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            assets = root / "assets"
            assets.mkdir()
            sf.write(assets / "vocal.wav", self.audio[:100], self.sr)
            (assets / "mix.json").write_text(json.dumps({
                "stems": [{"path":"vocal.wav", "name":"vocal"}]
            }), encoding="utf-8")
            output = root / "mix.wav"
            result = dsp.mix_stems(assets / "mix.json", output)
            self.assertEqual(result["stems"][0]["source"], "vocal.wav")
            self.assertTrue(output.is_file())

    def test_render_and_mix_never_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source, recipe, output = root/"in.wav", root/"recipe.json", root/"out.wav"
            sf.write(source, self.audio[:100], self.sr)
            sf.write(output, self.audio[:50], self.sr)
            bytes_before=output.read_bytes()
            recipe.write_text(json.dumps({"chain":[]}), encoding="utf-8")
            with self.assertRaises(FileExistsError):
                dsp.render(source, recipe, output)
            recipe.write_text(json.dumps({"stems":[{"path":str(source)}]}), encoding="utf-8")
            with self.assertRaises(FileExistsError):
                dsp.mix_stems(recipe, output)
            self.assertEqual(output.read_bytes(), bytes_before)

    def test_reverb_causal_impulse(self):
        src = np.zeros((self.sr, 1), dtype=np.float64)
        src[2000, 0] = 1
        out = dsp._reverb(src, self.sr, wet=1.0, predelay_ms=0)
        self.assertTrue(np.isfinite(out).all())
        self.assertTrue(np.all(out[:2000] == 0))

    def test_render_never_overwrites_source_and_writes_recipe_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, recipe, output = root/"input.wav", root/"chain.json", root/"output.wav"
            sf.write(source, self.audio, self.sr)
            before_hash = source.read_bytes()
            recipe.write_text(json.dumps({"chain":[{"effect":"gain", "parameters":{"db":-3}}]}), encoding="utf-8")
            report = dsp.render(source, recipe, output)
            self.assertEqual(source.read_bytes(), before_hash)
            self.assertTrue(output.is_file())
            self.assertTrue(output.with_suffix(".wav.report.json").is_file())
            self.assertEqual(report["source_preserved"], True)
            with self.assertRaises(ValueError):
                dsp.render(source, recipe, source)

    def test_mix_rejects_oversized_sources_before_reading_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, recipe, output = root/"stem.wav", root/"mix.json", root/"mix.wav"
            sf.write(source, self.audio[:100], self.sr)
            recipe.write_text(json.dumps({"stems": [{"path": str(source)}]}), encoding="utf-8")
            info = SimpleNamespace(frames=60_000_001, samplerate=self.sr, channels=1)
            with patch.object(dsp.sf, "info", return_value=info):
                with patch.object(dsp.sf, "read", side_effect=AssertionError("Too late: samples read")):
                    with self.assertRaisesRegex(ValueError, "limite de memória"):
                        dsp.mix_stems(recipe, output, target_sr=self.sr)
            self.assertFalse(output.exists())

    def test_mix_rejects_excessive_offsets_and_nonfinite_offsets_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, recipe, output = root/"stem.wav", root/"mix.json", root/"mix.wav"
            sf.write(source, self.audio[:100], self.sr)
            for offset, expected in [(3000, "limite de memória"), (float("inf"), "deve ser finito")]:
                recipe.write_text(json.dumps({"stems": [{"path": str(source), "start_seconds": offset}]}), encoding="utf-8")
                with patch.object(dsp.sf, "read", side_effect=AssertionError("Too late: samples read")):
                    with self.assertRaisesRegex(ValueError, expected):
                        dsp.mix_stems(recipe, output, target_sr=self.sr)
            self.assertFalse(output.exists())

    def test_stem_mix_aligns_offset_and_protects_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b, recipe_path, output = root/"vocal.wav", root/"guitar.wav", root/"mix.json", root/"mix.wav"
            sf.write(a, self.audio[:self.sr], self.sr)
            sf.write(b, self.audio[:self.sr//2, :1], self.sr)
            hashes = (a.read_bytes(), b.read_bytes())
            recipe_path.write_text(json.dumps({"sample_rate_hz":self.sr,"stems":[{"path":str(a),"name":"vocal"},{"path":str(b),"name":"guitar","start_seconds":.75,"pan":.5}]}), encoding="utf-8")
            report = dsp.mix_stems(recipe_path, output)
            self.assertEqual(sf.info(output).frames, self.sr*5//4)
            self.assertEqual((a.read_bytes(), b.read_bytes()), hashes)
            self.assertEqual(report["measurements"]["channels"], 2)


if __name__ == "__main__":
    unittest.main()
