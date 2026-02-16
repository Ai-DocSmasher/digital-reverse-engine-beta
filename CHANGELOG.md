
---

# ⭐ **CHANGELOG.md (Draft for This Version)**  
*(Clear, structured, professional)*

```markdown
# Digital Reverse Engine — Changelog

---

## v3.2 — Cyber‑Studio GUI Upgrade (Current Release)

### 🔥 Major UI/UX Enhancements
- Added **NeonWaveform** visualizer with:
  - Zoom‑in / zoom‑reset
  - Drag‑pan navigation
  - Adaptive time markers
  - Cyber hint overlay
  - Real‑time playhead tracking
- Added **SweepIndicator** with BPM‑synced animation
- Sweep now **auto‑starts** on playback and **auto‑stops** on playback end
- Added **metronome** with BPM‑accurate click timing
- Added click‑to‑jump navigation on waveform
- Added improved transport controls and visual feedback

### 🎧 DSP Integration
- GUI now correctly maps `STUDIO_MODE` → `STUDIO_REVERSE`
- Updated ReverseWorker to pass deterministic grid parameters
- Improved error fallback handling

### 🎵 File Support
- Import: WAV, MP3, FLAC
- Export: WAV, MP3, FLAC
- Improved stereo/mono handling

### 🛠️ Internal Improvements
- Cleaned PLAYBACK block with proper indentation
- Added sweep sync inside `snap_to_ms`
- Added zoom‑aware playhead rendering
- Improved waveform sampling resolution (2000‑point peak map)
- Added hint fade‑out timer

---

## v3.1 — Deterministic TimingGrid Integration
- Replaced all beat detection with deterministic grid slicing
- Added HQ, TATUM, and STUDIO structural modes
- Added hybrid DSP + cost engine pipeline

---

## v3.0 — Initial GUI Prototype
- Basic waveform display
- Basic reverse modes
- Basic transport

---

## v2.x — CLI‑Only Engine
- TRUE_REVERSE
- WAV I/O
- Early DSP experiments

---

## v1.x — Early Experiments
- Prototype reverse logic
- No GUI
