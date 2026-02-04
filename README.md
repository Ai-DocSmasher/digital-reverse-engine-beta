# Digital Reverse Engine™ (Beta)

A fully offline, tempo‑aware structural reverse processor for WAV audio.  
Designed for clarity, musicality, and modern DSP workflows.

This engine performs structural audio reversal by:
- analyzing tempo and rhythmic structure
- slicing audio into musically meaningful segments
- reversing the *order* of segments (not the waveforms)
- preserving forward playback inside each segment
- smoothing transitions with DSP‑grade windowing

The result is a clean, musical reverse effect that avoids the harsh artifacts
of traditional sample‑level reversal.

---

## ✨ Features

### 🎛️ Reverse Modes

**TRUE_REVERSE**  
Classic tape‑style reverse (waveform flipped).

**GRAIN_REVERSE**  
Granular reverse with Hann smoothing.

**TRANSIENTAWARE_REVERSE**  
Tatum‑like structural reverse using micro‑segments.

**HQ_REVERSE**  
Flagship mode.  
Tempo‑grid structural reverse with onset snapping for smooth, musical transitions.

**DJ_REVERSE**  
Aggressive 1/8‑beat slicing for rhythmic, performance‑style reverses.

**STUDIO_REVERSE**  
Bar‑level structural reverse for large‑scale musical rearrangements.

All modes run **100% offline**.

---

## 🚀 Usage

python dre.py  input.wav  --mode HQ_REVERSE --output output.wav
python dre.py  input.wav  --mode DJ_REVERSE --output dj.wav
python dre.py  input.wav  --mode STUDIO_REVERSE --output bars.wav