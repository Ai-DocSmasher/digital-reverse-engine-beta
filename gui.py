import sys
import soundfile as sf
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QComboBox, QTextEdit, QGridLayout
)
from PyQt6.QtCore import Qt

from core.hybrid.pipeline import process_audio

from PyQt6.QtGui import QIcon

class ReverseGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Reverse Engine™ — GUI Beta")
        self.setWindowIcon(QIcon("assets/icon.ico"))
        self.setMinimumWidth(600)


        layout = QGridLayout()

        # Input file
        self.input_label = QLabel("Input File:")
        self.input_path = QLineEdit()
        self.input_browse = QPushButton("Browse")
        self.input_browse.clicked.connect(self.load_input_file)

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

        layout.addWidget(self.mode_label, 1, 0)
        layout.addWidget(self.mode_dropdown, 1, 1)

        # Tempo
        self.tempo_label = QLabel("Tempo (BPM):")
        self.tempo_field = QLineEdit("120")

        layout.addWidget(self.tempo_label, 2, 0)
        layout.addWidget(self.tempo_field, 2, 1)

        # Beats per bar
        self.bpb_label = QLabel("Beats per Bar:")
        self.bpb_field = QLineEdit("4")

        layout.addWidget(self.bpb_label, 3, 0)
        layout.addWidget(self.bpb_field, 3, 1)

        # Bars per slice (Studio Reverse)
        self.bars_label = QLabel("Bars per Slice (Studio):")
        self.bars_field = QLineEdit("1")

        layout.addWidget(self.bars_label, 4, 0)
        layout.addWidget(self.bars_field, 4, 1)

        # Tatum fraction
        self.tatum_label = QLabel("Tatum Fraction:")
        self.tatum_field = QLineEdit("0.25")

        layout.addWidget(self.tatum_label, 5, 0)
        layout.addWidget(self.tatum_field, 5, 1)

        # Output file
        self.output_label = QLabel("Output File:")
        self.output_path = QLineEdit()
        self.output_browse = QPushButton("Browse")
        self.output_browse.clicked.connect(self.choose_output_file)

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
            if audio.ndim == 1:
                audio = audio.astype(np.float32)
            else:
                audio = audio.astype(np.float32)

            mode = self.mode_dropdown.currentText()
            tempo = float(self.tempo_field.text())
            beats_per_bar = int(self.bpb_field.text())
            bars_per_slice = int(self.bars_field.text())
            tatum_fraction = float(self.tatum_field.text())

            self.log.append(f"Processing with mode: {mode}")
            self.log.append(f"Tempo: {tempo} BPM")
            self.log.append(f"Beats per bar: {beats_per_bar}")

            # Call DSP engine
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
