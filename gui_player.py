# ——————————————————————————————————————————————————————————————
# Digital Reverse Engine — Player Edition (Final, SoundDevice Click)
# Tempo-calibrated Reverse Engine with Visual + Audio Metronome
# ——————————————————————————————————————————————————————————————

import sys
import os
import time
import logging
import tempfile
import shutil

import numpy as np
import soundfile as sf
import sounddevice as sd
import librosa

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout, QMessageBox,
    QTextEdit
)
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen, QPolygonF
from PyQt6.QtCore import Qt, QTimer, QSize, QPointF, QThread, pyqtSignal

from core.hybrid.pipeline import process_audio


# ============================================================
# LOGGING SETUP
# ============================================================
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "dre_player.log"),
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logging.info("=== Digital Reverse Engine Player launched ===")


# ============================================================
# BACKGROUND TEMPO DETECTION WORKER
# ============================================================
class TempoWorker(QThread):
    tempo_ready = pyqtSignal(float)

    def __init__(self, audio: np.ndarray, sr: int, parent=None):
        super().__init__(parent)
        self.audio = audio
        self.sr = sr

    def run(self):
        try:
            audio = self.audio
            if audio.ndim > 1:
                audio_mono = audio.mean(axis=1)
            else:
                audio_mono = audio
            audio_mono = audio_mono.astype(np.float32)
            tempo, _ = librosa.beat.beat_track(y=audio_mono, sr=self.sr)
            if tempo is None or tempo <= 0:
                tempo = 120.0
            tempo = float(tempo)
            logging.info(f"Background tempo detection finished: {tempo:.2f} BPM")
            self.tempo_ready.emit(tempo)
        except Exception as e:
            logging.warning(f"Background tempo detection failed: {e}")
            self.tempo_ready.emit(120.0)


# ============================================================
# TEMPO SWEEP INDICATOR WIDGET (adaptive visual metronome)
# ============================================================
class TempoSweepIndicator(QWidget):
    def __init__(self, parent=None, num_cells=24):
        super().__init__(parent)
        self.num_cells = num_cells
        self.bpm = 120.0
        self.phase = 0.0
        self.last_time = time.time()

        self.timer = QTimer(self)
        self.timer.setInterval(16)  # ~60 FPS
        self.timer.timeout.connect(self.update_phase)

        self.setMinimumHeight(40)

    def start(self):
        self.last_time = time.time()
        if not self.timer.isActive():
            self.timer.start()

    def stop(self):
        self.timer.stop()
        self.phase = 0.0
        self.update()

    def set_bpm(self, bpm: float):
        self.bpm = max(20.0, min(600.0, bpm))

    def update_phase(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        bpm = max(20.0, min(600.0, self.bpm))

        # Adaptive visual scaling: slower sweep as BPM increases
        if bpm < 90:
            visual_scale = 1.0
        elif bpm < 150:
            visual_scale = 1.8
        elif bpm < 240:
            visual_scale = 2.8
        else:
            visual_scale = 4.0

        sweep_period = (60.0 / bpm) * visual_scale  # seconds per full sweep
        self.phase = (self.phase + dt / sweep_period) % 1.0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        painter.fillRect(rect, QColor(20, 20, 20))

        if self.num_cells <= 0:
            return

        cell_w = w / self.num_cells

        # Determine sector (0–5)
        sector = int(self.bpm // 90)
        sector = max(0, min(5, sector))

        # Determine sub-band (0–3)
        sector_start = sector * 90
        delta = self.bpm - sector_start
        sub = int((4 * delta) / 90)
        sub = max(0, min(3, sub))

        # Base sector colors
        sector_colors = [
            QColor(255, 0, 0),      # Red
            QColor(255, 80, 0),     # Orange
            QColor(255, 160, 0),    # Amber
            QColor(255, 255, 0),    # Yellow
            QColor(255, 255, 160),  # Pale yellow
            QColor(255, 255, 255),  # White
        ]
        base_color = sector_colors[sector]

        # Train-like spaced blocks
        gap_ratio = 0.4  # portion of each cell left as gap
        block_w = cell_w * (1.0 - gap_ratio)
        offset = (cell_w - block_w) / 2.0

        # Draw LED cells as spaced "cars"
        for i in range(self.num_cells):
            x = i * cell_w + offset

            # Distance from sweep center
            pos = self.phase * self.num_cells
            d = abs(i - pos)

            # Brightness falloff
            brightness = max(0.0, 1.0 - d / 4.0)

            # Blend base color with white
            r = base_color.red()   + (255 - base_color.red())   * brightness
            g = base_color.green() + (255 - base_color.green()) * brightness
            b = base_color.blue()  + (255 - base_color.blue())  * brightness

            painter.fillRect(int(x), 0, int(block_w), int(h * 0.8), QColor(int(r), int(g), int(b)))

        # Draw sub-band bars at bottom
        bar_w = w / 4
        bar_h = h * 0.18
        for i in range(4):
            color = QColor(255, 255, 255) if i <= sub else QColor(80, 80, 80)
            painter.fillRect(int(i * bar_w), int(h - bar_h), int(bar_w - 2), int(bar_h), color)


# ============================================================
# WAVEFORM WIDGET (Precomputed solid-fill waveform)
# ============================================================
class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio = None
        self.sr = None
        self.duration_ms = 0
        self.position_ms = 0

        self.peaks = None  # precomputed |peak| values in [0,1]
        self.setMinimumHeight(140)
        pal = self.palette()
        pal.setColor(self.backgroundRole(), QColor(20, 20, 20))
        self.setPalette(pal)

    def sizeHint(self) -> QSize:
        return QSize(800, 160)

    def set_audio(self, audio: np.ndarray, sr: int):
        logging.info("WaveformWidget: setting audio data.")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        self.audio = audio
        self.sr = sr
        self.duration_ms = int(len(audio) * 1000 / sr)

        # Precompute low-res peaks (fast, freeze-proof)
        n_samples = len(audio)
        if n_samples == 0:
            self.peaks = None
        else:
            target_peaks = 200
            n_peaks = min(target_peaks, n_samples)
            window = max(1, n_samples // n_peaks)
            peaks = []
            for i in range(n_peaks):
                start = i * window
                end = min(n_samples, start + window)
                segment = audio[start:end]
                if segment.size == 0:
                    peaks.append(0.0)
                else:
                    peaks.append(float(np.max(np.abs(segment))))
            max_peak = max(peaks) if peaks else 1.0
            if max_peak == 0:
                max_peak = 1.0
            self.peaks = np.array(peaks, dtype=np.float32) / max_peak

        self.update()

    def set_position_ms(self, pos_ms: int):
        self.position_ms = pos_ms
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        painter.fillRect(rect, QColor(20, 20, 20))

        if self.peaks is None or self.audio is None:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Load audio to view waveform")
            return

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 220, 180))

        half_h = h / 2.0
        n_peaks = len(self.peaks)

        if n_peaks <= 1:
            return

        poly = QPolygonF()
        # top edge
        for i in range(n_peaks):
            x = rect.left() + (i / (n_peaks - 1)) * (w - 1)
            amp = self.peaks[i]
            y = half_h - amp * (half_h - 4)
            poly.append(QPointF(x, y))
        # bottom edge (reverse)
        for i in reversed(range(n_peaks)):
            x = rect.left() + (i / (n_peaks - 1)) * (w - 1)
            amp = self.peaks[i]
            y = half_h + amp * (half_h - 4)
            poly.append(QPointF(x, y))

        painter.drawPolygon(poly)

        # Playhead
        if self.duration_ms > 0:
            t = max(0, min(self.position_ms, self.duration_ms))
            x_pos = int((t / self.duration_ms) * w)
            pen_head = QPen(QColor(255, 80, 80))
            pen_head.setWidth(2)
            painter.setPen(pen_head)
            painter.drawLine(x_pos, 0, x_pos, h)

    def mousePressEvent(self, event):
        if self.audio is None:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            x = event.position().x()
            w = self.rect().width()
            ratio = max(0.0, min(1.0, x / max(1, w)))
            new_pos_ms = int(ratio * self.duration_ms)
            parent = self.parent()
            if hasattr(parent, "seek_from_waveform"):
                parent.seek_from_waveform(new_pos_ms)


# ============================================================
# MAIN GUI PLAYER
# ============================================================
class ReversePlayerGUI(QWidget):
    def __init__(self):
        super().__init__()
        logging.info("Initializing GUI...")

        self.setWindowTitle("Digital Reverse Engine™ — Player")
        self.setWindowIcon(QIcon("assets/icon.ico"))
        self.setMinimumWidth(900)

        self.audio = None
        self.sr = None
        self.current_file = None
        self.current_mode = "ORIGINAL"

        # Playback engine
        self.stream = None
        self.play_index = 0
        self.current_audio_buffer = None
        self.auto_stop_pending = False  # safe stop flag from audio callback

        self.play_timer = QTimer(self)
        self.play_timer.setInterval(20)
        self.play_timer.timeout.connect(self.update_playhead)

        # Tap tempo
        self.tap_times = []

        # State
        self.has_reversed = False
        self.tempo_worker = None

        # Temp dir only for reverse engine intermediates if needed
        self.temp_dir = tempfile.mkdtemp(prefix="dre_player_")

        # Click sound metronome (sounddevice)
        self.click_enabled = False
        self.click_timer = QTimer(self)
        self.click_timer.timeout.connect(self.play_click)

        # Generate a short click sound (1 kHz, 30 ms)
        self.click_sr = 44100
        duration_ms = 30
        t = np.linspace(0, duration_ms / 1000, int(self.click_sr * duration_ms / 1000), False)
        self.click_buffer = (0.5 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)

        # Layouts
        main_layout = QVBoxLayout()
        top_layout = QHBoxLayout()
        tempo_layout = QGridLayout()
        transport_layout = QHBoxLayout()
        reverse_layout = QHBoxLayout()
        info_layout = QGridLayout()
        advanced_layout = QGridLayout()

        # File controls
        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.load_input_file)

        self.save_button = QPushButton("Save As")
        self.save_button.clicked.connect(self.save_as)

        self.file_label = QLineEdit()
        self.file_label.setReadOnly(True)

        top_layout.addWidget(self.load_button)
        top_layout.addWidget(self.save_button)
        top_layout.addWidget(self.file_label)

        # Tempo controls
        self.guessed_label = QLabel("Guessed Tempo (BPM):")
        self.guessed_field = QLineEdit("")
        self.guessed_field.setReadOnly(True)
        self.guessed_field.setFixedWidth(80)

        self.tempo_label = QLabel("Input Tempo (BPM):")
        self.tempo_field = QLineEdit("")
        self.tempo_field.setFixedWidth(80)
        self.tempo_field.returnPressed.connect(self.on_manual_tempo_entered)

        self.half_button = QPushButton("Half")
        self.half_button.clicked.connect(self.half_tempo)
        self.half_button.setEnabled(False)

        self.double_button = QPushButton("Double")
        self.double_button.clicked.connect(self.double_tempo)
        self.double_button.setEnabled(False)

        self.tap_button = QPushButton("Tap Tempo")
        self.tap_button.clicked.connect(self.tap_tempo)

        self.click_checkbox = QPushButton("Click Sound: OFF")
        self.click_checkbox.setCheckable(True)
        self.click_checkbox.setChecked(False)
        self.click_checkbox.clicked.connect(self.toggle_click_sound)

        tempo_layout.addWidget(self.guessed_label, 0, 0)
        tempo_layout.addWidget(self.guessed_field, 0, 1)
        tempo_layout.addWidget(self.tempo_label, 1, 0)
        tempo_layout.addWidget(self.tempo_field, 1, 1)
        tempo_layout.addWidget(self.half_button, 0, 2)
        tempo_layout.addWidget(self.double_button, 0, 3)
        tempo_layout.addWidget(self.tap_button, 1, 2, 1, 2)
        tempo_layout.addWidget(self.click_checkbox, 2, 0, 1, 2)

        # Sweep indicator (visual metronome)
        self.sweep_indicator = TempoSweepIndicator(self)

        # Mode display
        self.mode_label = QLabel("Current Mode:")
        self.mode_field = QLineEdit("ORIGINAL")
        self.mode_field.setReadOnly(True)

        info_layout.addWidget(self.mode_label, 0, 0)
        info_layout.addWidget(self.mode_field, 0, 1)

        # Advanced reverse parameters
        self.beats_label = QLabel("Beats/Bar:")
        self.beats_field = QLineEdit("4")
        self.beats_field.setFixedWidth(50)

        self.bars_label = QLabel("Bars/Slice:")
        self.bars_field = QLineEdit("1")
        self.bars_field.setFixedWidth(50)

        self.tatum_label = QLabel("Tatum Fraction:")
        self.tatum_field = QLineEdit("0.25")
        self.tatum_field.setFixedWidth(60)

        advanced_layout.addWidget(self.beats_label, 0, 0)
        advanced_layout.addWidget(self.beats_field, 0, 1)
        advanced_layout.addWidget(self.bars_label, 0, 2)
        advanced_layout.addWidget(self.bars_field, 0, 3)
        advanced_layout.addWidget(self.tatum_label, 0, 4)
        advanced_layout.addWidget(self.tatum_field, 0, 5)

        # Waveform viewer
        self.waveform = WaveformWidget(self)

        # Transport controls
        self.play_button = QPushButton("Play")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.restart_button = QPushButton("Restart")

        self.play_button.clicked.connect(self.play_audio)
        self.pause_button.clicked.connect(self.pause_audio)
        self.stop_button.clicked.connect(self.stop_audio)
        self.restart_button.clicked.connect(self.restart_audio)

        transport_layout.addWidget(self.play_button)
        transport_layout.addWidget(self.pause_button)
        transport_layout.addWidget(self.stop_button)
        transport_layout.addWidget(self.restart_button)

        # Reverse mode buttons
        self.true_button = QPushButton("True Reverse")
        self.hq_button = QPushButton("HQ Reverse")
        self.tatum_button = QPushButton("Tatum Reverse")
        self.studio_button = QPushButton("Studio Reverse")

        self.true_button.clicked.connect(lambda: self.apply_reverse_mode("TRUE_REVERSE"))
        self.hq_button.clicked.connect(lambda: self.apply_reverse_mode("HQ_REVERSE"))
        self.tatum_button.clicked.connect(lambda: self.apply_reverse_mode("TATUM_REVERSE"))
        self.studio_button.clicked.connect(lambda: self.apply_reverse_mode("STUDIO_REVERSE"))

        reverse_layout.addWidget(self.true_button)
        reverse_layout.addWidget(self.hq_button)
        reverse_layout.addWidget(self.tatum_button)
        reverse_layout.addWidget(self.studio_button)

        # Log display (multi-line, scrollable)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(80)

        # Assemble
        main_layout.addLayout(top_layout)
        main_layout.addLayout(tempo_layout)
        main_layout.addWidget(self.sweep_indicator)
        main_layout.addLayout(info_layout)
        main_layout.addLayout(advanced_layout)
        main_layout.addWidget(self.waveform)
        main_layout.addLayout(transport_layout)
        main_layout.addLayout(reverse_layout)
        main_layout.addWidget(self.log)

        self.setLayout(main_layout)

        self.apply_dark_theme()

    # ============================================================
    # DARK THEME
    # ============================================================
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: Segoe UI, Arial;
                font-size: 10pt;
            }
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                padding: 2px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                padding: 4px;
            }
            QPushButton {
                background-color: #252525;
                border: 1px solid #3a3a3a;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            QPushButton:pressed {
                background-color: #444444;
            }
        """)

    # ============================================================
    # LOGGING TO UI
    # ============================================================
    def append_log(self, message: str):
        self.log.append(message)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
        logging.info(message)

    # ============================================================
    # FILE HANDLING
    # ============================================================
    def load_input_file(self):
        logging.info("User triggered file load.")
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", "Audio Files (*.wav *.mp3 *.flac)"
        )
        if not file:
            logging.warning("No file selected.")
            return

        # Stop any existing playback cleanly
        self.stop_audio()

        try:
            audio, sr = sf.read(file)
            audio = audio.astype(np.float32)
            self.audio = audio
            self.sr = sr
            self.current_file = file
            self.has_reversed = False
            self.half_button.setEnabled(False)
            self.double_button.setEnabled(False)

            logging.info(f"Loaded audio file: {file}, sr={sr}, shape={audio.shape}")
            self.file_label.setText(file)
            self.mode_field.setText("ORIGINAL")
            self.current_mode = "ORIGINAL"

            self.guessed_field.setText("")

            # Waveform + playback buffer
            self.waveform.set_audio(audio, sr)
            self.current_audio_buffer = audio.copy()
            self.play_index = 0

            # Background tempo detection
            self.append_log("Detecting tempo...")
            if self.tempo_worker is not None and self.tempo_worker.isRunning():
                self.tempo_worker.terminate()
            self.tempo_worker = TempoWorker(audio, sr, self)
            self.tempo_worker.tempo_ready.connect(self.on_tempo_detected)
            self.tempo_worker.start()

        except Exception as e:
            logging.exception("Error loading audio file:")
            self.append_log(f"Error loading file: {e}")

    def on_tempo_detected(self, tempo: float):
        self.guessed_field.setText(f"{tempo:.2f}")
        # Only overwrite input tempo if user hasn't typed anything
        if not self.tempo_field.text().strip():
            self.tempo_field.setText(f"{tempo:.2f}")
        self.sweep_indicator.set_bpm(tempo)
        self.sweep_indicator.start()
        if self.click_enabled:
            self.start_click_timer()
        self.append_log(f"Loaded file. Guessed tempo: {tempo:.2f} BPM.")

    def save_as(self):
        if self.current_audio_buffer is None or self.sr is None:
            QMessageBox.warning(self, "No audio", "No processed audio to save.")
            return

        file, _ = QFileDialog.getSaveFileName(
            self, "Save Processed Audio", "", "WAV Files (*.wav)"
        )
        if not file:
            return

        if os.path.exists(file):
            reply = QMessageBox.question(
                self,
                "Overwrite file?",
                f"File already exists:\n{file}\n\nOverwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        try:
            sf.write(file, self.current_audio_buffer, self.sr)
            self.append_log(f"Saved processed audio to: {file}")
        except Exception as e:
            logging.exception("Error saving file:")
            self.append_log(f"Error saving file: {e}")

    # ============================================================
    # TEMPO CONTROLS
    # ============================================================
    def get_tempo(self) -> float:
        try:
            if self.tempo_field.text():
                return float(self.tempo_field.text())
            if self.guessed_field.text():
                return float(self.guessed_field.text())
            return 120.0
        except ValueError:
            return 120.0

    def set_tempo(self, bpm: float, source: str = "Manual"):
        bpm = max(20.0, min(600.0, bpm))
        self.tempo_field.setText(f"{bpm:.2f}")
        self.sweep_indicator.set_bpm(bpm)
        self.sweep_indicator.start()
        if self.click_enabled:
            self.start_click_timer()
        self.append_log(f"Tempo changed to {bpm:.2f} BPM ({source}).")

    def on_manual_tempo_entered(self):
        text = self.tempo_field.text().strip()
        try:
            bpm = float(text)
            self.set_tempo(bpm, source="Manual entry")
        except ValueError:
            self.append_log(f"Invalid BPM entered: '{text}'")

    def half_tempo(self):
        if not self.has_reversed:
            self.append_log("Half tempo is available after applying a reverse mode.")
            return
        bpm = self.get_tempo() / 2.0
        self.set_tempo(bpm, source="Half")

    def double_tempo(self):
        if not self.has_reversed:
            self.append_log("Double tempo is available after applying a reverse mode.")
            return
        bpm = self.get_tempo() * 2.0
        self.set_tempo(bpm, source="Double")

    def tap_tempo(self):
        now = time.time()

        # Reset history if last tap was too long ago
        if self.tap_times and (now - self.tap_times[-1] > 3.0):
            self.tap_times = []

        self.tap_times.append(now)

        # Require at least 2 taps
        if len(self.tap_times) < 2:
            return

        intervals = np.diff(self.tap_times)

        # Reject outliers (too slow or too fast)
        intervals = [i for i in intervals if 0.1 < i < 2.0]
        if not intervals:
            return

        avg_interval = float(np.mean(intervals))
        bpm = 60.0 / avg_interval

        self.set_tempo(bpm, source="Tap tempo")

    # ============================================================
    # CLICK METRONOME (sounddevice)
    # ============================================================
    def toggle_click_sound(self):
        self.click_enabled = self.click_checkbox.isChecked()
        if self.click_enabled:
            self.click_checkbox.setText("Click Sound: ON")
            self.start_click_timer()
        else:
            self.click_checkbox.setText("Click Sound: OFF")
            self.click_timer.stop()

    def start_click_timer(self):
        bpm = self.get_tempo()
        interval_ms = int((60.0 / bpm) * 1000)
        self.click_timer.start(interval_ms)

    def play_click(self):
        if not self.click_enabled:
            return
        try:
            sd.play(self.click_buffer, self.click_sr, blocking=False)
        except Exception as e:
            logging.warning(f"Click playback error: {e}")

    # ============================================================
    # PLAYBACK ENGINE (sounddevice, safe callback)
    # ============================================================
    def play_audio(self):
        logging.info("Play pressed.")

        if self.current_audio_buffer is None or self.sr is None:
            self.append_log("Load an audio file first.")
            return

        # If a stream exists, stop it cleanly
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        buffer = self.current_audio_buffer
        self.play_index = max(0, min(self.play_index, len(buffer)))
        self.auto_stop_pending = False

        def callback(outdata, frames, time_info, status):
            if status:
                logging.warning(f"Sounddevice status: {status}")

            nonlocal buffer
            start = self.play_index
            end = start + frames

            if start >= len(buffer):
                outdata[:] = 0
                # signal main thread to stop on next timer tick
                self.auto_stop_pending = True
                return

            chunk = buffer[start:end]

            if chunk.ndim == 1:
                out_frames = min(frames, len(chunk))
                outdata[:out_frames, 0] = chunk[:out_frames]
                if out_frames < frames:
                    outdata[out_frames:] = 0
            else:
                out_frames = min(frames, chunk.shape[0])
                outdata[:out_frames, :chunk.shape[1]] = chunk[:out_frames]
                if out_frames < frames:
                    outdata[out_frames:] = 0

            self.play_index = end

        channels = 1 if self.current_audio_buffer.ndim == 1 else self.current_audio_buffer.shape[1]

        self.stream = sd.OutputStream(
            samplerate=self.sr,
            channels=channels,
            callback=callback,
            dtype='float32'
        )
        self.stream.start()
        self.play_timer.start()
        self.append_log("Playback started.")

    def pause_audio(self):
        logging.info("Pause pressed.")
        if self.stream:
            self.stream.stop()
        self.play_timer.stop()
        self.append_log("Playback paused.")

    def stop_audio(self):
        logging.info("Stop pressed.")
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.play_timer.stop()
        self.play_index = 0
        self.waveform.set_position_ms(0)
        self.auto_stop_pending = False

        self.append_log("Playback stopped.")

    def restart_audio(self):
        logging.info("Restart pressed.")

        # Restore original audio
        if self.audio is not None and self.sr is not None:
            self.current_audio_buffer = self.audio.copy()
            self.waveform.set_audio(self.audio, self.sr)
            self.mode_field.setText("ORIGINAL")
            self.current_mode = "ORIGINAL"
            self.has_reversed = False
            self.half_button.setEnabled(False)
            self.double_button.setEnabled(False)

        self.play_index = 0
        self.play_audio()

    def update_playhead(self):
        if self.sr is None:
            return

        # Handle auto-stop from callback safely on GUI thread
        if self.auto_stop_pending:
            self.auto_stop_pending = False
            self.stop_audio()
            return

        pos_ms = int((self.play_index / self.sr) * 1000)
        self.waveform.set_position_ms(pos_ms)

    def seek_from_waveform(self, pos_ms: int):
        logging.info(f"Seeking to {pos_ms} ms")
        if self.sr is None or self.current_audio_buffer is None:
            return
        self.play_index = int((pos_ms / 1000) * self.sr)
        self.waveform.set_position_ms(pos_ms)

    # ============================================================
    # REVERSE MODES
    # ============================================================
    def get_advanced_params(self):
        def parse_int(field, default):
            try:
                return int(field.text())
            except ValueError:
                return default

        def parse_float(field, default):
            try:
                return float(field.text())
            except ValueError:
                return default

        beats_per_bar = parse_int(self.beats_field, 4)
        bars_per_slice = parse_int(self.bars_field, 1)
        tatum_fraction = parse_float(self.tatum_field, 0.25)
        return beats_per_bar, bars_per_slice, tatum_fraction

    def apply_reverse_mode(self, mode: str):
        logging.info(f"Applying reverse mode: {mode}")

        if self.audio is None or self.sr is None:
            self.append_log("Load an audio file first.")
            return

        # Stop playback before processing
        self.stop_audio()

        try:
            tempo_val = self.get_tempo()
            beats_per_bar, bars_per_slice, tatum_fraction = self.get_advanced_params()

            processed = process_audio(
                self.audio,
                sample_rate=self.sr,
                mode=mode,
                tempo=tempo_val,
                beats_per_bar=beats_per_bar,
                bars_per_slice=bars_per_slice,
                tatum_fraction=tatum_fraction
            )

            self.current_mode = mode
            self.mode_field.setText(mode)
            self.waveform.set_audio(processed, self.sr)

            self.current_audio_buffer = processed.copy()
            self.play_index = 0
            self.has_reversed = True
            self.half_button.setEnabled(True)
            self.double_button.setEnabled(True)

            self.play_audio()

            self.append_log(
                f"Applied {mode} at {tempo_val:.2f} BPM "
                f"(beats/bar={beats_per_bar}, bars/slice={bars_per_slice}, tatum={tatum_fraction}) "
                f"and started playback."
            )

        except Exception as e:
            logging.exception("Reverse mode crashed:")
            self.append_log(f"Reverse mode error: {e}")

    # ============================================================
    # CLEANUP
    # ============================================================
    def closeEvent(self, event):
        logging.info("Closing application, cleaning up.")
        try:
            if self.tempo_worker is not None and self.tempo_worker.isRunning():
                self.tempo_worker.terminate()
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            logging.warning(f"Cleanup issue: {e}")
        event.accept()


# ============================================================
# APP ENTRY POINT
# ============================================================
if __name__ == "__main__":
    try:
        logging.info("Launching QApplication...")
        app = QApplication(sys.argv)
        window = ReversePlayerGUI()
        window.show()
        exit_code = app.exec()
        logging.info(f"Application exited with code {exit_code}")
        sys.exit(exit_code)
    except Exception:
        logging.exception("FATAL ERROR — Application crashed:")
        raise
