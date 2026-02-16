# Digital Reverse Engine — Virtual Studio v3.2  
A modern, tempo‑aware, deterministic audio reversal workstation.

The Digital Reverse Engine (DRE) is a hybrid DSP + GUI system designed for
structural audio reversal using deterministic timing grids.  
This release introduces a fully redesigned Cyber‑Studio interface with zoomable
waveforms, time markers, metronome, and real‑time playback visualization.



✨ Features (v3.2 GUI Edition)

🎛️ Cyber‑Studio Interface
- Modern dark‑themed UI with neon accents  
- Sweep Indicator synced to BPM  
- NeonWaveform visualizer with:
  - Zoom‑in / zoom‑reset  
  - Drag‑pan navigation  
  - Adaptive time markers  
  - Cyber hint overlay  
  - Real‑time playhead tracking  

🎚️ Structural Reverse Modes
All DSP modes use deterministic TimingGrid slicing (no Librosa beat detection):
- TRUE_REVERSE — classic waveform reverse  
- HQ_REVERSE — high‑fidelity structural reverse  
- TATUM_REVERSE — micro‑grid slicing (tatum‑based)  
- STUDIO_MODE — bar‑level shuffle reverse (GUI alias for STUDIO_REVERSE)  

🎵 Transport & Playback
- Real‑time playback with sample‑accurate playhead  
- Click‑to‑jump navigation  
- Sweep auto‑start/stop synced to playback  
- Metronome with BPM‑accurate click timing  

📁 File Support
- Import: WAV, MP3, FLAC  
- Export: WAV, MP3, FLAC  
- Stereo + mono compatible  

⚙️ DSP Engine
- Deterministic TimingGrid  
- No jitter, no drift  
- Sample‑accurate slicing  
- Hybrid pipeline (DSP + cost engine) supported  


🚀 Installation

1. Create and activate a virtual environment

powershell

python -m venv dre-env
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\dre-env\Scripts\activate

2. Install dependencies

powershell
pip install -r requirements.txt

3. Run the GUI

powershell
python gui_player.py

🏗️ Building the Executable (Windows)

Install PyInstaller

powershell
pip install pyinstaller

Build using the spec file

powershell
pyinstaller dre_player.spec

The executable will appear in:

dist/dre_player/
📦 Project Structure

digital-reverse-engine/

├── gui_player.py

├── dre_player.spec

├── dre.py

├── core/

│   ├── dsp/

│   ├── hybrid/

│   └── economic/

└── assets/


🧪 Status
This is a beta‑stage GUI with a stable DSP engine.
Feedback, issues, and feature requests are welcome.
