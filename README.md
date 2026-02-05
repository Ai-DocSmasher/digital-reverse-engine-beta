Digital Reverse Engine™ — v1.1.0

A deterministic, tempo‑aware structural reverse processor for WAV/MP3 audio.

Designed for AI‑music creators, producers, remixers, and sound designers who want clean, glitch‑free, DAW‑grade reverse effects without beat detection drift or artifacts.



This engine uses a mathematical timing grid (patent pending) to reverse audio with perfect consistency.



✨ What’s New in v1.1.0

Auto‑Tempo Detection

Leave the tempo field blank in the GUI and the engine will analyze the audio and fill in a detected BPM automatically.

If detection fails, it safely falls back to 120 BPM.



Smart Defaults for Optional Fields

If any optional field is left empty, the GUI fills in stable defaults:



Beats per bar → 4



Bars per slice → 1



Tatum fraction → 0.25



Improved User Experience

Hover tooltips explain every field



Clear logging of auto‑detected values and defaults



Cleaner layout and more intuitive workflow



No crashes from empty fields



🎛 Standalone GUI (Windows)

A fully offline PyQt6 desktop app is included.



How to Run

Download gui.zip from the Releases page



Extract the ZIP



Double‑click gui.exe



Load audio → choose mode → process



No Python required.

No installation.

No dependencies.



SmartScreen Notice

Windows may warn about running an unsigned executable.

Click More Info → Run Anyway to launch the GUI.



🖥 CLI Usage (Optional)

For power users:



python dre.py input.wav --mode HQ\_REVERSE --tempo 128 --output out.wav

All modes are supported:



TRUE\_REVERSE



HQ\_REVERSE



QBEAT\_REVERSE



TATUM\_REVERSE



STUDIO\_REVERSE



🎧 Perfect For

AI music creators (Suno, Udio, Stable Audio, etc.)



Producers \& remixers



DJs \& sound designers



Anyone who wants clean, musical reverse effects



🧠 Patent Pending

The deterministic structural reversal method implemented in this engine is patent pending.



📣 Feedback Welcome

This is an active public beta.

Share your reversed audio, ideas, and issues in the GitHub Discussions or Issues tab.

