# ——————————————————————————————————————————————————————————————
# Digital Reverse Engine — Player Edition (Final, SoundDevice Click)
# Tempo-calibrated Reverse Engine with Visual + Audio Metronome
# ——————————————————————————————————————————————————————————————
import sys
import os
import time
import logging
import shutil
import tempfile
import numpy as np
import soundfile as sf
import sounddevice as sd
import librosa

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout, QMessageBox,
    QTextEdit, QToolTip
)
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygon, QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint

# Fallback for processing core
try:
    from core.hybrid.pipeline import process_audio
except ImportError:
    def process_audio(**kwargs):
        logging.warning("Core pipeline missing. Returning original audio.")
        return kwargs.get("audio")

# ============================================================
# BACKGROUND WORKERS
# ============================================================
class TempoWorker(QThread):
    tempo_ready = pyqtSignal(float)

    def __init__(self, audio, sr, parent=None):
        super().__init__(parent)
        self.audio = audio
        self.sr = sr

    def run(self):
        try:
            y = self.audio
            if y.ndim > 1: y = y.mean(axis=1)
            y = y.astype(np.float32)
            tempo, _ = librosa.beat.beat_track(y=y, sr=self.sr)
            val = float(tempo[0] if isinstance(tempo, np.ndarray) else tempo)
            self.tempo_ready.emit(val if val > 0 else 120.0)
        except Exception:
            self.tempo_ready.emit(120.0)

class ReverseWorker(QThread):
    finished = pyqtSignal(np.ndarray, str)
    failed = pyqtSignal(str)

    def __init__(self, audio, sr, mode, tempo, parent=None):
        super().__init__(parent)
        self.params = {
            'audio': audio, 'sample_rate': sr, 'mode': mode,
            'tempo': tempo, 'beats_per_bar': 4,
            'tatum_fraction': 0.25, 'bars_per_slice': 1
        }

    def run(self):
        try:
            processed = process_audio(**self.params)
            self.finished.emit(processed, self.params['mode'])
        except Exception as e:
            self.failed.emit(str(e))

# ============================================================
# VISUALS: TEMPO SWEEP & WAVEFORM
# ============================================================
class TempoSweepIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_cells = 24
        self.bpm = 120.0
        self.phase = 0.0
        self.last_time = time.time()
        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.update_phase)
        self.setMinimumHeight(45)

    def start(self):
        self.last_time = time.time()
        if not self.timer.isActive(): self.timer.start()

    def stop(self):
        self.timer.stop(); self.phase = 0.0; self.update()

    def set_bpm(self, bpm): self.bpm = max(20.0, min(600.0, bpm))

    def update_phase(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        visual_scale = 1.0
        if self.bpm >= 90: visual_scale = 1.6
        if self.bpm >= 150: visual_scale = 2.4
        sweep_period = (60.0 / self.bpm) * visual_scale
        self.phase = (self.phase + dt / sweep_period) % 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(18, 18, 18))
        cell_w = self.width() / self.num_cells
        for i in range(self.num_cells):
            dist = abs(i - (self.phase * self.num_cells))
            bright = max(0.0, 1.0 - (dist / 5.0)) ** 1.6
            painter.fillRect(int(i * cell_w + 2), 5, int(cell_w - 4), int(self.height()*0.7), 
                             QColor(0, int(255 * bright), int(200 * bright)))

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.peaks = None
        self.total_samples = 0
        self.sr = 44100
        self.audio_len = 0
        self.playhead_sample = 0
        self.zoom_active = False
        self.sel_start = 0
        self.sel_end = 0
        self.axis_h = 25
        self.setMinimumHeight(180)
        self.setMouseTracking(True)

    def format_time(self, s): return f"{int(s//60)}:{int(s%60):02d}"

    def set_waveform(self, audio, sr):
        self.sr = sr
        self.audio_len = len(audio)
        pixels = max(100, self.width())
        samples_per_pixel = max(1, len(audio) // pixels)
        self.peaks = np.array([np.max(np.abs(audio[i:i+samples_per_pixel])) 
                               for i in range(0, len(audio), samples_per_pixel)])
        self.total_samples = len(self.peaks)
        self.update()

    def set_position_ms(self, ms):
        if self.total_samples == 0: return
        ratio = (ms / 1000.0) / (self.audio_len / self.sr)
        self.playhead_sample = int(ratio * self.total_samples)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.peaks is not None:
            self.zoom_active = True
            self.update_zoom(event.pos().x())

    def mouseMoveEvent(self, event):
        # Hint 1: Hover over Axis
        if event.pos().y() > self.height() - self.axis_h:
            QToolTip.showText(event.globalPosition().toPoint(), "HOLD LEFT BUTTON TO ZOOM IN", self)
        
        if self.zoom_active: self.update_zoom(event.pos().x())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.zoom_active = False; self.update()

    def update_zoom(self, x):
        center = int((x / self.width()) * self.total_samples)
        win = int(self.total_samples * 0.15)
        self.sel_start = max(0, center - win // 2)
        self.sel_end = min(self.total_samples, self.sel_start + win)
        self.update()

    def paintEvent(self, event):
        if self.peaks is None: return
        painter = QPainter(self)
        w, h = self.width(), self.height()
        wf_h = h - self.axis_h
        
        start = self.sel_start if self.zoom_active else 0
        end = self.sel_end if self.zoom_active else self.total_samples
        visible = self.peaks[start:end]
        
        # Waveform
        step = w / max(1, len(visible))
        painter.setPen(QPen(QColor(0, 255, 200, 150), 1))
        for i, p in enumerate(visible):
            x = int(i * step)
            amp = int(p * (wf_h / 2) * 0.8)
            painter.drawLine(x, wf_h//2 - amp, x, wf_h//2 + amp)

        # Time Axis
        painter.fillRect(0, wf_h, w, self.axis_h, QColor(30, 30, 30))
        painter.setPen(QColor(150, 150, 150))
        total_s = self.audio_len / self.sr
        painter.drawText(5, h-7, "0:00")
        painter.drawText(w-45, h-7, self.format_time(total_s))

# ============================================================
# MAIN ENGINE GUI
# ============================================================
class DigitalReverseEngine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Reverse Engine v3.0")
        self.setMinimumWidth(1050)
        self.original_audio = None
        self.current_audio = None
        self.sr = 44100
        self.stream = None
        self.click_enabled = False
        self.temp_dir = tempfile.mkdtemp(prefix="DRE_")
        
        self.play_timer = QTimer(); self.play_timer.timeout.connect(self.update_playhead)
        self.click_timer = QTimer(); self.click_timer.timeout.connect(self.play_click)
        
        # Pre-build click sound
        t = np.linspace(0, 0.03, int(44100 * 0.03))
        self.click_buffer = (np.sin(2 * np.pi * 1000 * t) * 0.4).astype(np.float32)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. File & Reset
        file_box = QHBoxLayout()
        self.load_btn = QPushButton("LOAD AUDIO"); self.load_btn.clicked.connect(self.load_file)
        self.reset_btn = QPushButton("RESET"); self.reset_btn.clicked.connect(self.reset_audio); self.reset_btn.setEnabled(False)
        self.clean_btn = QPushButton("CLEAN TEMP"); self.clean_btn.clicked.connect(self.manual_cleanup)
        self.file_info = QLineEdit("No file loaded"); self.file_info.setReadOnly(True)
        file_box.addWidget(self.load_btn); file_box.addWidget(self.reset_btn); file_box.addWidget(self.clean_btn); file_box.addWidget(self.file_info)
        layout.addLayout(file_box)

        # 2. Tempo Controls
        tempo_box = QHBoxLayout()
        self.tempo_field = QLineEdit("120.0")
        self.half_btn = QPushButton("HALF"); self.half_btn.clicked.connect(lambda: self.scale_tempo(0.5))
        self.double_btn = QPushButton("DOUBLE"); self.double_btn.clicked.connect(lambda: self.scale_tempo(2.0))
        self.click_btn = QPushButton("CLICK: OFF"); self.click_btn.clicked.connect(self.toggle_metronome)
        tempo_box.addWidget(QLabel("BPM:")); tempo_box.addWidget(self.tempo_field); tempo_box.addWidget(self.half_btn); tempo_box.addWidget(self.double_btn); tempo_box.addWidget(self.click_btn)
        layout.addLayout(tempo_box)

        self.sweep = TempoSweepIndicator(); layout.addWidget(self.sweep)
        self.waveform = WaveformWidget(); layout.addWidget(self.waveform)

        # 3. Processing Modes
        mode_box = QHBoxLayout()
        for m in ["TRUE_REVERSE", "HQ_REVERSE", "TATUM_REVERSE"]:
            btn = QPushButton(m.replace("_", " ")); btn.clicked.connect(lambda ch, mode=m: self.apply_reverse(mode))
            mode_box.addWidget(btn)
        layout.addLayout(mode_box)

        # 4. Playback & Save
        play_box = QHBoxLayout()
        self.play_btn = QPushButton("PLAY"); self.play_btn.clicked.connect(self.play_audio)
        self.stop_btn = QPushButton("STOP"); self.stop_btn.clicked.connect(self.stop_audio)
        self.save_btn = QPushButton("SAVE VERSION"); self.save_btn.clicked.connect(self.save_file)
        play_box.addWidget(self.play_btn); play_box.addWidget(self.stop_btn); play_box.addWidget(self.save_btn)
        layout.addLayout(play_box)

        self.log = QTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(80); layout.addWidget(self.log)

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget { background-color: #121212; color: #eee; font-family: 'Segoe UI'; }
            QPushButton { background-color: #222; border: 1px solid #444; padding: 8px; font-weight: bold; }
            QPushButton:hover { border-color: #00ffcc; background-color: #333; }
            QLineEdit { background-color: #000; border: 1px solid #333; color: #00ffcc; padding: 4px; }
        """)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Audio", "", "Audio Files (*.wav *.mp3 *.flac)")
        if path:
            y, sr = librosa.load(path, sr=None, mono=False)
            self.original_audio = y.T if y.ndim > 1 else y
            self.current_audio = self.original_audio.copy()
            self.sr = sr
            self.waveform.set_waveform(y.mean(axis=0) if y.ndim > 1 else y, sr)
            self.file_info.setText(os.path.basename(path)); self.reset_btn.setEnabled(True)
            self.log.append(f"Loaded {os.path.basename(path)}")
            # Detect Tempo
            self.tempo_worker = TempoWorker(y, sr)
            self.tempo_worker.tempo_ready.connect(lambda t: self.tempo_field.setText(f"{t:.2f}"))
            self.tempo_worker.start()

    def reset_audio(self):
        if self.original_audio is not None:
            self.current_audio = self.original_audio.copy()
            vis = self.current_audio.T.mean(axis=0) if self.current_audio.ndim > 1 else self.current_audio
            self.waveform.set_waveform(vis, self.sr)
            self.log.append("RELOADED ORIGINAL STATE.")

    def manual_cleanup(self):
        if QMessageBox.question(self, "Cleanup", "Delete temporary files beforehand?", QMessageBox.StandardButton.Yes) == QMessageBox.StandardButton.Yes:
            shutil.rmtree(self.temp_dir, ignore_errors=True); os.makedirs(self.temp_dir, exist_ok=True)
            self.log.append("Temp cache cleared.")

    def scale_tempo(self, factor):
        new_val = float(self.tempo_field.text()) * factor
        self.tempo_field.setText(f"{new_val:.2f}")

    def toggle_metronome(self):
        self.click_enabled = not self.click_enabled
        self.click_btn.setText(f"CLICK: {'ON' if self.click_enabled else 'OFF'}")
        if self.click_enabled: self.click_timer.start(int(60000 / float(self.tempo_field.text())))
        else: self.click_timer.stop()

    def play_click(self): sd.play(self.click_buffer, 44100)

    def play_audio(self):
        if self.current_audio is None: return
        self.stop_audio(); self.play_idx = 0
        chs = self.current_audio.shape[1] if self.current_audio.ndim > 1 else 1
        self.stream = sd.OutputStream(samplerate=self.sr, channels=chs, callback=self.audio_callback)
        self.stream.start(); self.play_timer.start(30); self.sweep.set_bpm(float(self.tempo_field.text())); self.sweep.start()

    def audio_callback(self, outdata, frames, time, status):
        chunk = self.current_audio[self.play_idx : self.play_idx + frames]
        if len(chunk) < frames:
            outdata[:len(chunk)] = chunk; outdata[len(chunk):].fill(0)
            self.play_idx = 0; raise sd.CallbackStop()
        else: outdata[:] = chunk; self.play_idx += frames

    def stop_audio(self):
        self.play_timer.stop(); self.sweep.stop()
        if self.stream: self.stream.stop(); self.stream.close(); self.stream = None
        self.waveform.set_position_ms(0)

    def update_playhead(self):
        if self.stream and self.stream.active: self.waveform.set_position_ms((self.play_idx / self.sr) * 1000)

    def apply_reverse(self, mode):
        if self.current_audio is None: return
        self.log.append(f"Processing {mode}...")
        self.worker = ReverseWorker(self.current_audio, self.sr, mode, float(self.tempo_field.text()))
        self.worker.finished.connect(self.on_process_done); self.worker.start()

    def on_process_done(self, audio, mode):
        self.current_audio = audio
        vis = audio.T.mean(axis=0) if audio.ndim > 1 else audio
        self.waveform.set_waveform(vis, self.sr); self.log.append(f"Finished {mode}")

    def save_file(self):
        if self.current_audio is None: return
        path, _ = QFileDialog.getSaveFileName(self, "Save Version", "", "WAV (*.wav)")
        if path: sf.write(path, self.current_audio, self.sr); self.log.append(f"Saved Version: {path}")

    def closeEvent(self, event): shutil.rmtree(self.temp_dir, ignore_errors=True); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); gui = DigitalReverseEngine(); gui.show(); sys.exit(app.exec())
