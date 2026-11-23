# DSP recipe notes

## Custom code loop

Load audio as floating-point arrays with an explicit sample rate and channel axis. Check shape, finite values, clipping, and headroom. Write small functions with explicit units (dB, Hz, milliseconds, samples). Render a short passage, measure it, listen, adjust one or two linked parameters, then render the full-length copy. Keep the exact parameter recipe beside each output.

## Effect order is a musical decision

Common starting order: cleanup/filter → corrective EQ → dynamics → tone/saturation/amp → tonal EQ → time effects → automation → output safety. Move stages when the sound calls for it. Use parallel paths for distortion, ambience, or transient enhancement when preserving the dry attack matters. Use gain staging between stages; nonlinear processors change timbre with input level.

## Pitch and tempo

For a time-preserving pitch shift, use a phase-vocoder or high-quality library (for example `librosa.effects.pitch_shift`) and preserve exact output length with a controlled trim/pad. For tempo change that preserves pitch, use time stretch. Check transients, sibilants, vibrato, and stereo coherence. Large shifts and dense polyphonic mixes create artifacts; process isolated vocal/instrument stems when possible. Phrase-level or note-level correction needs reliable F0 tracking, voiced/unvoiced detection, note targets, transition smoothing, and listening; do not call a single global semitone shift autotune.

## Guitar amp and cabinet

An educational amp-color chain can oversample, apply pre-EQ, asymmetric or multistage waveshaping, sag/dynamic response, post-EQ, and convolution with a licensed cabinet impulse response, then downsample with anti-alias filtering. Compare level-matched. Oversampling reduces aliasing but does not make a waveshaper a circuit model. Do not bundle or redistribute IRs without compatible terms.

## Slap-like bass enhancement

On an isolated bass track, detect/enhance note onsets, add a short controlled transient, create upper harmonics with gentle nonlinear shaping or parallel distortion, and blend with the clean fundamental. Preserve timing and level; high-pass the parallel layer to avoid doubling sub energy. This changes timbre, not the performed articulation or missing notes.

## Reverb and delay

Prefer an impulse response convolution when a suitable licensed IR is available. Otherwise a Schroeder-style network (parallel comb delays followed by serial all-pass stages) gives an adjustable algorithmic room. Include predelay, damping, stereo decorrelation, wet/dry, and a tail check. Delay time may be derived from BPM, but ask before quantizing expressive throws.

## Distortion families and scratch

Choose distortion by harmonic character and level-match it: soft tube-like saturation, harder clipping, asymmetric harmonics, fuzz, foldback, or bit reduction. Oversample nonlinear stages when practical, then low-pass appropriately; oversampling reduces aliasing but cannot guarantee none. A custom scratch gesture can map output time to a variable signed playback-rate curve and interpolate source samples. This is an offline effect, useful for a scratch phrase or transition; real turntable/DVS performance needs a live low-latency audio engine and controller input. Preserve the clean source and audition gesture shape, speed reversals, pitch drops, and boundaries.

## Meter and compare

Measure before/after with the same method. For A/B audition, apply a common loudness-match gain to preview copies only; do not silently change the requested render gain. Compare peaks separately and prevent preview clipping. Analyze frequency-band energy as a locator, not proof of a mix problem. Never claim a render was auditioned if playback was unavailable.
