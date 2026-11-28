import sys
from pathlib import Path
import tempfile
import unittest
import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from timed_evidence import analyze, validate_cues


class TimedEvidenceTests(unittest.TestCase):
    def test_stereo_opposite_phase_and_partial_block(self):
        sr = 8000
        x = .5 * np.sin(2 * np.pi * 440 * np.arange(sr * 2 + 400) / sr)
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "test.wav"
            sf.write(p, np.column_stack((x, -x)), sr, subtype="FLOAT")
            result = analyze(p, 1, [{"start_seconds": .9, "end_seconds": 1.1, "text": "cue"}])
        rows = result["segments"]
        self.assertEqual(len(rows), 3)
        self.assertAlmostEqual(result["duration_seconds"], 2.05)
        self.assertAlmostEqual(rows[0]["spectral_centroid_hz"], 440, delta=1)
        self.assertAlmostEqual(rows[0]["rms_dbfs"], -9.03, delta=.05)
        self.assertEqual([len(r["lyric_cues"]) for r in rows], [1, 1, 0])

    def test_silence_has_no_db_or_centroid(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "silent.wav"
            sf.write(p, np.zeros(8000), 8000)
            r = analyze(p)["segments"][0]
        self.assertIsNone(r["rms_dbfs"])
        self.assertIsNone(r["spectral_centroid_hz"])
        self.assertEqual(r["clipped_samples"], 0)

    def test_clipped_samples_and_validation(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / "clip.wav"
            sf.write(p, np.array([1., -1., .5, 0]), 8000, subtype="FLOAT")
            self.assertEqual(analyze(p)["segments"][0]["clipped_samples"], 2)
            for value in (0, float("nan"), True, 11):
                with self.assertRaises(ValueError):
                    analyze(p, value)
        for cues in (None, [{"start_seconds": 2, "end_seconds": 1, "text": "a"}],
                     [{"start_seconds": True, "end_seconds": 2, "text": "a"}]):
            with self.assertRaises(ValueError):
                validate_cues(cues)


if __name__ == "__main__":
    unittest.main()
