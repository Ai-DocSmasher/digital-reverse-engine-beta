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


TRUE\_REVERSE
Classic tape‑style reverse (waveform flipped).
Pure sample‑level reversal.



HQ\_REVERSE (Recommended for first‑time users)
Beat‑level structural reverse.

One slice per beat

Perfectly clean and musical

Requires correct tempo for best results

Halving the tempo produces creative stretched reversals

This mode is the flagship for predictable, DAW‑accurate reverse effects.



QBEAT\_REVERSE
Quarter‑beat slicing for rhythmic, glitch‑style reversals.
Great for electronic, trap, and experimental textures.

TATUM\_REVERSE
Sub‑beat micro‑slicing.

1/4 beat

triplet

1/2 beat

custom fractions

Produces granular‑style reversals without the harsh artifacts of granular engines.



STUDIO\_REVERSE
Multi‑bar phrase‑level reverse.

Slices audio into N‑bar chunks

Reverses the order of phrases

Works best on longer audio (30s–2min)

Highly expressive when adjusting tempo, beats‑per‑bar, or bar size

Setting beats\_per\_bar = 1 makes it behave like a macro HQ\_REVERSE

This mode is ideal for arrangement‑style transformations and cinematic reversals.



🎧 Recommended Workflow

1. Start with HQ\_REVERSE
   Attach the correct tempo for perfect, glitch‑free results.
2. Experiment with tempo
   Halving or doubling the tempo produces creative structural variations.
3. Explore STUDIO\_REVERSE on long tracks
   Phrase‑level slicing becomes expressive on full songs or long loops.
4. Adjust beats‑per‑bar
   Setting beats\_per\_bar = 1 turns STUDIO\_REVERSE into a beat‑level slicer.
5. Use TATUM\_REVERSE for micro‑textures
   Great for sound design and glitch effects.



🚀 Usage



python dre.py input.wav --mode HQ\_REVERSE --tempo 128 --output out.wav
Examples:



python dre.py track.wav --mode STUDIO\_REVERSE --tempo 179 --output bars.wav
python dre.py loop.wav --mode QBEAT\_REVERSE --tempo 140 --output qbeat.wav
python dre.py pad.wav --mode TATUM\_REVERSE --tempo 120 --tatum-fraction 0.25 --output micro.wav
python dre.py fx.wav --mode TRUE\_REVERSE --output classic.wav



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



📦 Running the Desktop App (GUI)



After building with PyInstaller, the standalone executable will appear in:



dist/gui.exe

You can launch the Digital Reverse Engine™ GUI by double‑clicking the file.

No command‑line usage is required for the GUI.



🖥 Running from CLI (Optional)

The engine can still be used directly from the command line:





python dre.py input.wav --mode HQ\_REVERSE --tempo 128 --output out.wav



Both the GUI and CLI use the same deterministic DSP engine.

