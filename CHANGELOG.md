# Changelog — Digital Reverse Engine™ Player Edition

All notable changes to this project will be documented here.

---

## [1.2.0] — 2026-02-09
### Added
- New **sounddevice-based click metronome** (no external dependencies)
- **Train-car sweep indicator** for improved high-BPM readability
- **System Log panel** for debugging and user feedback
- Improved **Tap Tempo estimator** (multi-tap averaging)
- Restart now fully restores original audio buffer and UI state

### Improved
- Sweep indicator adaptive scaling for BPM > 90
- Cleaner GUI layout and dark theme consistency
- Playback engine stability and safe callback handling

### Fixed
- Removed redundant code blocks from earlier versions
- Eliminated simpleaudio dependency (Python 3.13 incompatible)
- Corrected indentation and structural issues in GUI class

---

## [1.1.0] — 2026-02-04
### Added
- First public GUI release
- Waveform viewer
- Reverse modes (True, HQ, Tatum, Studio)
- Tempo detection via librosa
- Tap Tempo (initial version)
- Playback engine with safe stop

---

## [1.0.0] — 2026-02-01
### Added
- Initial CLI-only release
