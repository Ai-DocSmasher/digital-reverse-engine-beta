Digital Reverse Engine™
A fully offline, deterministic, tempo‑aware structural reverse processor for WAV/MP3 audio.
Designed for clarity, musicality, and modern DSP workflows.

Unlike traditional reverse effects that flip the waveform sample‑by‑sample, this engine performs structural reversal:

slicing audio into musically meaningful segments

reversing the order of those segments

preserving forward playback inside each slice

using a mathematically perfect timing grid (no beat detection, no drift)

producing clean, glitch‑free, DAW‑grade results

The outcome is a reverse effect that feels musical, intentional, and artifact‑free — often cleaner than real‑time plugins like Gross Beat.

✨ Reverse Modes
TRUE_REVERSE
Classic tape‑style reverse (waveform flipped).
Pure sample‑level reversal.

HQ_REVERSE (Recommended for first‑time users)
Beat‑level structural reverse.

One slice per beat

Perfectly clean and musical

Requires correct tempo for best results

Halving the tempo produces creative stretched reversals

This mode is the flagship for predictable, DAW‑accurate reverse effects.

QBEAT_REVERSE
Quarter‑beat slicing for rhythmic, glitch‑style reversals.
Great for electronic, trap, and experimental textures.

TATUM_REVERSE
Sub‑beat micro‑slicing.

1/4 beat

triplet

1/2 beat

custom fractions

Produces granular‑style reversals without the harsh artifacts of granular engines.

STUDIO_REVERSE
Multi‑bar phrase‑level reverse.

Slices audio into N‑bar chunks

Reverses the order of phrases

Works best on longer audio (30s–2min)

Highly expressive when adjusting tempo, beats‑per‑bar, or bar size

Setting beats_per_bar = 1 makes it behave like a macro HQ_REVERSE

This mode is ideal for arrangement‑style transformations and cinematic reversals.

🎧 Recommended Workflow
1. Start with HQ_REVERSE
Attach the correct tempo for perfect, glitch‑free results.

2. Experiment with tempo
Halving or doubling the tempo produces creative structural variations.

3. Explore STUDIO_REVERSE on long tracks
Phrase‑level slicing becomes expressive on full songs or long loops.

4. Adjust beats‑per‑bar
Setting beats_per_bar = 1 turns STUDIO_REVERSE into a beat‑level slicer.

5. Use TATUM_REVERSE for micro‑textures
Great for sound design and glitch effects.

🚀 Usage


python dre.py input.wav --mode HQ_REVERSE --tempo 128 --output out.wav
Examples:


python dre.py track.wav --mode STUDIO_REVERSE --tempo 179 --output bars.wav
python dre.py loop.wav --mode QBEAT_REVERSE --tempo 140 --output qbeat.wav
python dre.py pad.wav --mode TATUM_REVERSE --tempo 120 --tatum-fraction 0.25 --output micro.wav
python dre.py fx.wav --mode TRUE_REVERSE --output classic.wav

📦 Installation

pip install -r requirements.txt
Dependencies:

numpy

soundfile

librosa (loader only; timing grid is fully deterministic)

🧠 How It Works
The engine uses a deterministic TimingGrid:

No beat detection

No onset detection

No spectral analysis

No drift or jitter

100% offline, sample‑accurate slicing

Every slice is computed from:

tempo

beats per bar

subdivisions

bar count

This produces DAW‑grade structural reversals with zero artifacts.