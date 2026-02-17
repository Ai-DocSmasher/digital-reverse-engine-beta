⭐ INSTRUCTIONS.md — Digital Reverse Engine™ (Build 3.2)
First‑Time User Guide & High‑Fidelity Workflow

🎛️ 1. Introduction
Welcome to the Digital Reverse Engine™, a tempo‑aware, reversible audio engine designed for musicians, producers, sound designers, and AI audio researchers.

This guide walks first‑time users through the correct workflow to achieve perfect, DAW‑grade reversals, especially using the newly renamed High Fidelity mode.

Note: In earlier builds, this mode was called HQ_Preset.
It has been renamed to High Fidelity for clarity and consistency.



🎚️ 2. Recommended First‑Time Workflow

Step 1 — Import Your Audio
Click Import Audio and load any WAV/MP3/FLAC file.
The engine will:

Display the waveform

Detect the BPM (approximate)

Load album art (if available)

Prepare the buffer for processing


Step 2 — Enter the Tempo Manually (Critical for Accuracy)
For the highest‑quality reverse, manually enter the exact BPM of the track.

Automatic BPM detection is included, but manual entry is always more accurate for:

DJ mixes

Live recordings

Tracks with swing/groove

Songs with soft or ambiguous transients

Humanized timing

Why this matters:  
High Fidelity mode uses tempo‑aligned slicing.
Correct BPM = perfect structural reverse.


Step 3 — Select “High Fidelity” Mode
Click High Fidelity to generate the cleanest, most musically accurate reverse.

This mode:

Preserves bar structure

Maintains beat alignment

Avoids transient smearing

Prevents phase tearing

Produces a studio‑grade reverse

This is the recommended starting point for all new users.


Step 4 — Preview the Result
Use:

Initialize Playback

Cease Playback

Waveform click‑to‑jump

Sweep indicator for tempo visualization

The engine updates the playhead in real time.


Step 5 — Export the Master
Click Export Master to save the processed audio.

The engine writes a clean WAV/MP3 file with no clipping or artifacts.



🎨 3. Exploring Creative Modes (Optional)
Once users understand High Fidelity mode, they can explore:

Studio Shuffle
Bar‑level rearrangements for rhythmic experimentation.

Tatum Logic
Micro‑grid slicing for glitch, IDM, and granular‑style effects.

Standard Reverse
Raw waveform reversal — classic, simple, and fast.



🧠 4. Tips for Best Results 

✔ Always enter BPM manually for High Fidelity
This is the single most important step for clean, phase‑accurate reversal.
Manual BPM ensures perfect bar alignment and prevents micro‑drift.

✔ Use integer BPM values for most EDM/Pop
Most commercial tracks are exactly 120, 128, 130, 140, etc.
Rounding to the nearest whole BPM gives the most stable results.

✔ For live recordings, round to the nearest whole BPM
High Fidelity mode tolerates ±0.5 BPM drift without introducing artifacts.
If the tempo fluctuates, choose the closest stable BPM.

✔ Use Studio Shuffle for rhythmic creativity
This mode is designed for pattern‑level experimentation, DJ‑style rearrangements,
and non‑destructive rhythmic play.

✔ Use Tatum Logic for micro‑slicing
Ideal for glitch, IDM, sound design, and granular‑style transformations.
It excels at micro‑timing and sub‑beat slicing.

⭐ NB Notes (Important)
— Large audio files require more processing time
Tracks longer than 30 seconds may trigger a noticeable delay during processing.
The engine will display:


[ENGINE] Processing large audio buffer… please wait.
This is normal — High Fidelity and Studio modes analyze the full waveform
to maintain timing accuracy.

— “Clear Buffer” also deletes temporary files
When you press Clear Buffer, the engine:

resets the active audio buffer

clears waveform visualization

deletes all temporary files created during processing

resets playback and metronome state

This prevents disk clutter and ensures each session starts clean.

📝 5. Changelog Note (Build 3.2)
HQ_Preset → High Fidelity  
Renamed for clarity and consistency across UI/UX.
No DSP changes — only naming improvements.

Improved UI layout stability

Enhanced waveform rendering

Updated tempo visualization

Better album art scaling

Cleaner logging and navigation



🆘 6. Troubleshooting
BPM feels wrong
Enter the BPM manually — do not rely on auto‑detection for complex tracks.

Reverse sounds “off‑grid”
Double‑check:

BPM

Bars

Beats

Tatum settings

Buttons resize or UI shifts
Restart the app — layout fixes are applied in Build 3.2.

Audio not playing
Ensure no other app is locking the audio device.


🎉 7. You’re Ready
This guide gives first‑time users a guaranteed success path:

Import → Enter BPM → High Fidelity → Preview → Export

From here, they can explore the creative modes and push the engine into new territory.
