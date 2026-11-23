# Validation report

Validated locally in Codex on Windows using Python 3.13.14, NumPy 2.5.4, SciPy 1.18.1, and SoundFile 0.13.1. Results are for synthetic test signals, not a user's musical recording.

Checks performed:

- measurement reports handle stereo signals and report expected duration/peak shape;
- gain produces the expected amplitude factor;
- high-pass filter reduces low-frequency test energy and outputs finite samples;
- mono stereo-width operation remains safe;
- compressor, amp-color, distortion families, delay, reverb, chorus, transient, scratch, and slap-color operations preserve shape and finite output on test audio;
- stem mix aligns offset, creates stereo WAV, and preserves source bytes;
- render writes a report and new output while preserving the original; same-path overwrite is rejected.

Test command: `uv run --project <environment-with-numpy-scipy-soundfile> --with pytest pytest -q tests/test_studio_dsp.py`.

Not validated here: ChatGPT account installation, availability of the dependencies in a target runtime, perceptual quality on real songs, separation model weights, optional librosa pitch/time operations, commercial plugin compatibility, MIDI instruments, or live low-latency scratch.

## Local follow-up corrections (v0.1.1)

- Corrected feedback delay: mix=0 now returns an exact dry signal; wet echo feedback decays as requested.
- Corrected stem path resolution to be relative to the JSON recipe location.
- Prevented overwriting an existing output or report.
- Made reverb all-pass sections causal.
- Kept optional librosa requirements separate; adjusted ChatGPT skill installation steps; reinforced handling of lyrics and intentional scratch elements.
- Added regression tests for the above behaviors, executed locally on synthetic audio. Installation in the user account and actual song sound remain untested.
