v1.1.0 — Tempo‑Aware GUI Upgrade

This release introduces major improvements to the Digital Reverse Engine GUI.



New Features

Automatic Tempo Detection  

When the tempo field is left blank, the GUI analyzes the audio and fills in a detected BPM.

Falls back to 120 BPM if detection fails.



Smart Defaults for Optional Fields  

Blank fields now auto‑fill with stable defaults:



Beats per bar → 4



Bars per slice → 1



Tatum fraction → 0.25



Improved User Experience



Hover tooltips added to every field



Clear logging of auto‑detected values and defaults



Cleaner layout and more intuitive workflow



Stability Improvements

Fixed crashes caused by empty fields



Improved error handling and logging



Ensured GUI always launches cleanly



Removed stray metadata that could break PyInstaller builds

