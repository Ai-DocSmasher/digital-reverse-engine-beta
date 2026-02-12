Digital Reverse Engine™ (DRE) — Master Edition [v1.3.0]

The definitive deterministic structural audio reversal workstation.

Digital Reverse Engine™ isn’t just a "reverse" effect; it is a structural audio processor designed to flip audio while maintaining musical phrasing, grid alignment, and rhythmic integrity. Perfect for AI music creators, sound designers, and professional producers.

 🚀 Why v1.3.0 "Master Edition"?

The v1.3.0 update marks the transition from a CLI-first utility to a fully-fledged professional GUI workstation.

 Structural Integrity: Unlike standard DAW "reverse" functions that just flip the sample, DRE uses patent-pending structural logic to keep your audio musically coherent.
 Pro-Visual Engine: High-resolution waveform ruler with 0:00 to End time markers and "Glider-Zoom" inspection.
 Intelligent Analysis: Integrated Librosa beat-tracking automatically detects track BPM for instant grid alignment.
 Live Monitoring: Integrated sounddevice playback engine with a synchronized visual metronome.

 🎛 Reverse Modes
                             
-TRUE REVERSE--Standard FX--Classic sample-flipping for traditional reverse sounds. 


-HQ REVERSE--Vocals / Leads--High-fidelity structural reversal with optimized transients. 


-TATUM REVERSE--Percussion--Micro-structural flips based on the smallest rhythmic units. 


-STUDIO MODE--Full Tracks--The ultimate structural engine for flipping entire 4-bar or 8-bar phrases. 


 📦 Installation & Quick Start

 For Producers (No Python Required)

1. Download the latest `DRE_Master.zip` from [Releases].
2. Extract and run `DRE_Master.exe`.
3. Load your audio, let the engine detect the BPM, and hit Start Engine.

 For Developers (Python Environment)

bash

git clone https://github.com/your-repo/digital-reverse-engine.git

pip install -r requirements.txt

python gui_player.py



 🛠 Tech Stack

 Audio Core: Librosa, NumPy, SoundFile.
 
 I/O Engine: SoundDevice (Low-latency callback stream).
 
 Interface: PyQt6 (High-DPI vector-based GUI).

