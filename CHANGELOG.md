Changelog — Digital Reverse Engine™ Player Edition
All notable changes to this project will be documented here.

[1.3.0] — 2026-02-11
Added
Master Time Ruler: Added high-visibility 0:00 and track duration markers to the waveform.

Dynamic UX Layout: Integrated Expanding policies for Waveform and Log windows; the UI now scales professionally to Fullscreen/Maximized states.

Enhanced Log Engine: Added detailed context-aware logging for user actions ([USER]), processing ([PROCESS]), and system status ([ENGINE]).

Export Versatility: Added support for both MP3 and WAV master exports.

Visual Metronome Lock: Sweep indicator height is now fixed for consistent UX across various window sizes.

Improved
Process Robustness: Added signal length validation to TempoWorker to prevent FFT errors on short audio buffers.

UI Responsiveness: Optimized Waveform pre-caching to 1200-pixel density for instant redraws during window resizing.

Fixed
BPM Sync Error: Resolved AttributeError: 'TempoSweepIndicator' object has no attribute 'set_bpm'.

Librosa Warning: Suppressed n_fft=2048 warning by adding input signal length verification.

Marker Color Palette: Swapped gray time markers for high-contrast white to ensure visibility on the dark studio theme.

[1.2.0] — 2026-02-09
Added
New sounddevice-based click metronome (no external dependencies)

Train-car sweep indicator for improved high-BPM readability

System Log panel for debugging and user feedback

Improved Tap Tempo estimator (multi-tap averaging)

Restart now fully restores original audio buffer and UI state

Improved
Sweep indicator adaptive scaling for BPM > 90

Cleaner GUI layout and dark theme consistency

Playback engine stability and safe callback handling

Fixed
Removed redundant code blocks from earlier versions

Eliminated simpleaudio dependency (Python 3.13 incompatible)

Corrected indentation and structural issues in GUI class

[1.1.0] — 2026-02-04
Added
First public GUI release

Waveform viewer

Reverse modes (True, HQ, Tatum, Studio)

Tempo detection via librosa

Tap Tempo (initial version)

Playback engine with safe stop

[1.0.0] — 2026-02-01
Added
Initial CLI-only release
