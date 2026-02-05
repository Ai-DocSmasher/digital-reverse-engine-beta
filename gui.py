import sys
import soundfile as sf
import numpy as np
import librosa

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QComboBox, QTextEdit, QGridLayout
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from core.hybrid.pipeline import process_audio


# -----------------------------
# Tempo Detection Helper
# -----------------------------
def detect_tempo(audio, sr):
    """Lightweight tempo detection using onset envelope + autocorrelation."""
    try:
        if audio.ndim > 1:
            audio = librosa.to_mono(audio.T)

        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)
        return float(tempo[0])
    except Exception:
        return None


# -----------------------------
# GUI Application
# -----------------------------
class ReverseGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Reverse Engine™ — GUI v1.1 Beta")
        self.setWindowIcon(QIcon("assets/icon.ico"))
        self.setMinimumWidth(650)

        layout = QGridLayout()

        # Input file
        self.input_label = QLabel("Input File:")
        self.input_path = QLineEdit()
        self.input_browse = QPushButton("Browse")
        self.input_browse.clicked.connect(self.load_input_file)
        self.input_label.setToolTip("Select a WAV or MP3 file to reverse.")

        layout.addWidget(self.input_label, 0, 0)
        layout.addWidget(self.input_path, 0, 1)
        layout.addWidget(self.input_browse, 0, 2)

        # Mode selector
        self.mode_label = QLabel("Mode:")
        self.mode_dropdown = QComboBox()
        self.mode_dropdown.addItems([
            "TRUE_REVERSE",
            "HQ_REVERSE",
            "QBEAT_REVERSE",
            "TATUM_REVERSE",
            "STUDIO_REVERSE"
        ])
        self.mode_label.setToolTip("Choose the reverse mode.\nHQ_REVERSE is recommended for most users.")

        layout.addWidget(self.mode_label, 1, 0)
        layout.addWidget(self.mode_dropdown, 1, 1)

        # Tempo
        self.tempo_label = QLabel("Tempo (BPM):")
        self.tempo_field = QLineEdit("")
        self.tempo_label.setToolTip("Leave blank to auto-detect tempo.\nOr enter a BPM manually for deterministic slicing.")

        layout.addWidget(self.tempo_label, 2, 0)
        layout.addWidget(self.tempo_field, 2, 1)

        # Beats per bar
        self.bpb_label = QLabel("Beats per Bar:")
        self.bpb_field = QLineEdit("")
        self.bpb_label.setToolTip("Optional. Default = 4.\nUsed for STUDIO_REVERSE and HQ_REVERSE.")

        layout.addWidget(self.bpb_label, 3, 0)
        layout.addWidget(self.bpb_field, 3, 1)

        # Bars per slice
        self.bars_label = QLabel("Bars per Slice (Studio):")
        self.bars_field = QLineEdit("")
        self.bars_label.setToolTip("Optional. Default = 1.\nUsed only for STUDIO_REVERSE.")

        layout.addWidget(self.bars_label, 4, 0)
        layout.addWidget(self.bars_field, 4, 1)

        # Tatum fraction
        self.tatum_label = QLabel("Tatum Fraction:")
        self.tatum_field = QLineEdit("")
        self.tatum_label.setToolTip("Optional. Default = 0.25.\nUsed only for TATUM_REVERSE.")

        layout.addWidget(self.tatum_label, 5, 0)
        layout.addWidget(self.tatum_field, 5, 1)

        # Output file
        self.output_label = QLabel("Output File:")
        self.output_path = QLineEdit()
        self.output_browse = QPushButton("Browse")
        self.output_browse.clicked.connect(self.choose_output_file)
        self.output_label.setToolTip("Choose where to save the reversed audio.")

        layout.addWidget(self.output_label, 6, 0)
        layout.addWidget(self.output_path, 6, 1)
        layout.addWidget(self.output_browse, 6, 2)

        # Process button
        self.process_button = QPushButton("Process Audio")
        self.process_button.clicked.connect(self.process_audio_clicked)
        layout.addWidget(self.process_button, 7, 1)

        # Log window
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setToolTip("Processing log and auto-filled defaults will appear here.")
        layout.addWidget(self.log, 8, 0, 1, 3)

        self.setLayout(layout)

    # -----------------------------
    # File loading
    # -----------------------------
    def load_input_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Audio File", "", "Audio Files (*.wav *.mp3)")
        if file:
            self.input_path.setText(file)
            self.log.append(f"Loaded input file: {file}")

    def choose_output_file(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Output File", "", "WAV Files (*.wav)")
        if file:
            self.output_path.setText(file)
            self.log.append(f"Output will be saved to: {file}")

    # -----------------------------
    # DSP Processing
    # -----------------------------
    def process_audio_clicked(self):
        try:
            input_file = self.input_path.text()
            output_file = self.output_path.text()

            if not input_file or not output_file:
                self.log.append("❌ Please select input and output files.")
                return

            # Load audio
            audio, sr = sf.read(input_file)
            audio = audio.astype(np.float32)

            # Tempo handling
            tempo_text = self.tempo_field.text().strip()

            if tempo_text == "":
                detected = detect_tempo(audio, sr)
                if detected:
                    tempo = detected
                    self.tempo_field.setText(str(round(tempo, 2)))
                    self.log.append(f"Auto-detected tempo: {tempo:.2f} BPM")
                else:
                    tempo = 120.0
                    self.log.append("Tempo detection failed. Using default 120 BPM.")
            else:
                tempo = float(tempo_text)

            # Safe defaults
            def safe_int(value, default):
                try:
                    return int(value)
                except:
                    return default

            def safe_float(value, default):
                try:
                    return float(value)
                except:
                    return default

            beats_per_bar = safe_int(self.bpb_field.text(), 4)
            bars_per_slice = safe_int(self.bars_field.text(), 1)
            tatum_fraction = safe_float(self.tatum_field.text(), 0.25)

            self.log.append(
                f"Using parameters → tempo={tempo}, beats_per_bar={beats_per_bar}, "
                f"bars_per_slice={bars_per_slice}, tatum_fraction={tatum_fraction}"
            )

            mode = self.mode_dropdown.currentText()
            self.log.append(f"Processing with mode: {mode}")

            # DSP call
            processed = process_audio(
                audio,
                sample_rate=sr,
                mode=mode,
                tempo=tempo,
                beats_per_bar=beats_per_bar,
                bars_per_slice=bars_per_slice,
                tatum_fraction=tatum_fraction
            )

            # Save output
            sf.write(output_file, processed, sr)
            self.log.append("✅ Processing complete!")
            self.log.append(f"Saved to: {output_file}")

        except Exception as e:
            self.log.append(f"❌ Error: {str(e)}")


# -----------------------------
# App Entry Point
# -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ReverseGUI()
    window.show()
    sys.exit(app.exec())
