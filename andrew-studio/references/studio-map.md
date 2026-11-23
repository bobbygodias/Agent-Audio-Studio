# Studio function map

This is a functional map, not a promise that named products or proprietary presets are installed.

| Studio need | Practical open route | Boundary to tell the user |
|---|---|---|
| Audio editing, fades, trims, batch conversion | Python + SoundFile/SciPy; FFmpeg when present; Audacity is an optional separate editor | Non-destructive renders are safer; an offline script is not a full DAW timeline UI |
| Mix bus, routing, automation, effect chains | NumPy/SciPy recipes; Pedalboard built-ins or an actually installed compatible plugin | Plugin hosting depends on the runtime OS, ABI, plugin binary, and license |
| EQ, filters, dynamics, saturation, delay, chorus, reverb | SciPy filters and explicit Python DSP; Pedalboard effects if importable | Parameters and topology affect sound; no single preset suits every source |
| Guitar amp/cab color | Oversampled nonlinear waveshaping + EQ + licensed/open impulse response convolution; Guitarix/LV2 or Neural Amp Modeler only where available | A basic waveshaper is not a Neural DSP/AmpliTube capture or analog circuit model |
| Vocal pitch and timing | librosa pitch shift/time stretch for broad changes; Rubber Band if installed; note-level correction requires pitch tracking and careful local edits | General pitch shift preserves duration approximately; it is not transparent polyphonic or melody-aware auto-tune |
| Source separation | [Demucs](https://github.com/adefossez/demucs) or another accessible model/runtime; check repository maintenance and model/license terms | Model weights may be large; separation leaves bleed and artifacts and may not fit the ChatGPT runtime |
| Drum programming/replacement | MIDI plus a present SFZ/SoundFont sampler/library; open sample packs with explicit license | Do not imply GetGood Drums or any commercial library is included |
| DJ transitions / Serato-like preparation | Analyze BPM/key/sections, create cue/transition plan, render crossfades/EQ/filter automation | This can prepare and render audio; it does not control Serato hardware or replicate its proprietary library/database |
| Master checks | LUFS meter where available, sample peak, oversampled peak estimate, channel correlation, spectrum, audition | Metering supports judgement; it cannot certify artistic readiness |

## GitHub starting points checked

- [Spotify Pedalboard](https://github.com/spotify/pedalboard): Python audio I/O/effects and optional VST3/AU hosting. A VST binary still has to be present and compatible; its GPL license matters when redistributing an application.
- [librosa](https://github.com/librosa/librosa): analysis, pitch shift and time stretch. Large changes can create artifacts; check API/dependency versions in the active runtime.
- [Demucs maintained fork](https://github.com/adefossez/demucs): open source separation code; weights, compute, dependency compatibility, and artifacts remain separate concerns.
- [Mixxx](https://github.com/mixxxdj/mixxx): DJ player architecture and scratch/rate-control reference. Its real-time turntable control depends on audio hardware and low-latency callbacks, which a rendered offline scratch gesture does not emulate.
- [Guitarix](https://github.com/brummer10/guitarix): Linux amp/effect ecosystem, LV2/VST3 modules and NAM support; direct use depends on OS/runtime/plugin host.
- [Neural Amp Modeler](https://github.com/sdatkinson/neural-amp-modeler) and [NeuralAmpModelerPlugin](https://github.com/sdatkinson/NeuralAmpModelerPlugin): train and play amp captures. The model file and runtime are required; the open project is not the same as a commercial Neural DSP Archetype preset or licensed capture.

Repository references were checked as implementation leads, not audited line-by-line or bundled. Re-check upstream status and licenses before integrating code or weights.

Use the closest route that exists in the current runtime. Python is the default for the supplied DSP implementation. Use JavaScript/TypeScript or another language only when its runtime and audio libraries materially help. Rust or Kotlin source by itself does not create an executable in a Python-only container.
