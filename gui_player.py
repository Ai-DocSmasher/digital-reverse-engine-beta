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
import random
import numpy as np
import soundfile as sf
import sounddevice as sd
import librosa

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout, QMessageBox,
    QTextEdit, QToolTip, QSizePolicy
)
from PyQt6.QtGui import QPainter, QColor, QPen, QPolygon, QFont, QFontMetrics
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint

# ============================================================
# WORKERS
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
            # Fix for UserWarning: Ensure signal is long enough for FFT
            if len(y) < 2048:
                self.tempo_ready.emit(120.0)
                return
            
            tempo, _ = librosa.beat.beat_track(y=y.astype(np.float32), sr=self.sr)
            val = float(tempo[0] if isinstance(tempo, np.ndarray) else tempo)
            self.tempo_ready.emit(val if val > 0 else 120.0)
        except Exception:
            self.tempo_ready.emit(120.0)

class ReverseWorker(QThread):
    finished = pyqtSignal(np.ndarray, str)
    def __init__(self, audio, sr, mode, tempo, parent=None):
        super().__init__(parent)
        self.params = {'audio': audio, 'sample_rate': sr, 'mode': mode, 'tempo': tempo}

    def run(self):
        try:
            # Placeholder for your specific pipeline
            from core.hybrid.pipeline import process_audio
            processed = process_audio(**self.params)
            self.finished.emit(processed, self.params['mode'])
        except Exception:
            self.finished.emit(self.params['audio'], "BUFFER_ONLY")

# ============================================================
# VISUAL COMPONENTS
# ============================================================
class TempoSweepIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_cells = 40
        self.bpm = 120.0  # Default
        self.phase = 0.0
        self.last_time = time.time()
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_phase)
        self.setFixedHeight(55)
        self.color_palette = [QColor(0, 255, 255), QColor(255, 50, 50), QColor(255, 255, 0)]
        self.current_color = self.color_palette[0]

    # --- THE MISSING METHOD FIXED HERE ---
    def set_bpm(self, bpm):
        """Sets the visual sweep speed based on the track BPM."""
        try:
            self.bpm = float(bpm) if float(bpm) > 0 else 120.0
        except ValueError:
            self.bpm = 120.0

    def start(self):
        self.last_time = time.time()
        if not self.timer.isActive(): self.timer.start()

    def stop(self):
        self.timer.stop(); self.phase = 0.0; self.update()

    def update_phase(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        # Visual speed logic
        period = (60.0 / self.bpm) * 1.5
        new_phase = (self.phase + dt / period) % 1.0
        if new_phase < self.phase:
            self.current_color = random.choice(self.color_palette)
        self.phase = new_phase
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(10, 10, 10))
        cell_w = self.width() / self.num_cells
        for i in range(self.num_cells):
            dist = abs(i - (self.phase * self.num_cells))
            bright = max(0.0, 1.0 - (dist / 7.0)) ** 2.2
            c = QColor(self.current_color)
            c.setAlpha(int(255 * bright))
            p.fillRect(int(i * cell_w + 1), 5, int(cell_w - 2), self.height()-10, c)

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.peaks = None
        self.sr = 44100
        self.audio_len = 0
        self.playhead_sample = 0
        self.zoom_active = False
        self.sel_start = 0
        self.sel_end = 0
        self.axis_h = 35
        self.setMinimumHeight(220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def format_time(self, s):
        return f"{int(s//60)}:{int(s%60):02d}"

    def set_waveform(self, audio, sr):
        self.sr = sr
        self.audio_len = len(audio)
        pixels = 1200
        samples_per_pixel = max(1, len(audio) // pixels)
        self.peaks = np.array([np.max(np.abs(audio[i:i+samples_per_pixel])) for i in range(0, len(audio), samples_per_pixel)])
        self.total_samples = len(self.peaks)
        self.update()

    def set_position_ms(self, ms):
        if self.audio_len == 0: return
        ratio = (ms / 1000.0) / (self.audio_len / self.sr)
        self.playhead_sample = int(ratio * self.total_samples)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.peaks is not None:
            self.zoom_active = True
            self.update_zoom(event.pos().x())

    def mouseMoveEvent(self, event):
        if event.pos().y() > self.height() - self.axis_h:
            QToolTip.showText(event.globalPosition().toPoint(), "HOLD LEFT MOUSE TO ZOOM IN", self)
        if self.zoom_active: self.update_zoom(event.pos().x())
        self.update()

    def mouseReleaseEvent(self, event):
        self.zoom_active = False; self.update()

    def update_zoom(self, x):
        center = int((x / self.width()) * self.total_samples)
        win = int(self.total_samples * 0.12)
        self.sel_start = max(0, center - win // 2)
        self.sel_end = min(self.total_samples, self.sel_start + win)

    def paintEvent(self, event):
        if self.peaks is None: return
        painter = QPainter(self)
        w, h = self.width(), self.height()
        wf_h = h - self.axis_h
        
        start = self.sel_start if self.zoom_active else 0
        end = self.sel_end if self.zoom_active else self.total_samples
        visible = self.peaks[start:end]
        
        painter.fillRect(0, 0, w, wf_h, QColor(12, 12, 12))
        step = w / max(1, len(visible))
        painter.setPen(QPen(QColor(0, 255, 200, 160), 1))
        for i, p in enumerate(visible):
            x = int(i * step)
            amp = int(p * (wf_h / 2) * 0.9)
            painter.drawLine(x, wf_h//2 - amp, x, wf_h//2 + amp)

        painter.fillRect(0, wf_h, w, self.axis_h, QColor(25, 25, 25))
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        
        total_s = self.audio_len / self.sr
        painter.drawText(10, h - 12, "0:00")
        dur_str = self.format_time(total_s)
        end_w = QFontMetrics(painter.font()).horizontalAdvance(dur_str)
        painter.drawText(w - end_w - 10, h - 12, dur_str)
        
        if self.zoom_active:
            gx = int((self.sel_start / self.total_samples) * w)
            gw = int(((self.sel_end - self.sel_start) / self.total_samples) * w)
            painter.fillRect(gx, wf_h + 2, gw, self.axis_h - 4, QColor(255, 255, 0, 60))

# ============================================================
# MASTER ENGINE
# ============================================================
class DigitalReverseEngine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital Reverse Engine ™ | Pro Master Build")
        self.setMinimumSize(1150, 800)
        self.original_audio = None
        self.current_audio = None
        self.sr = 44100
        self.stream = None
        self.click_enabled = False
        self.temp_dir = tempfile.mkdtemp(prefix="DRE_PRO_")
        
        self.play_timer = QTimer(); self.play_timer.timeout.connect(self.update_playhead)
        self.click_timer = QTimer(); self.click_timer.timeout.connect(self.play_click)
        
        t = np.linspace(0, 0.03, int(44100 * 0.03))
        self.click_buffer = (np.sin(2 * np.pi * 1000 * t) * 0.5).astype(np.float32)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.load_btn = QPushButton("LOAD SOURCE")
        self.load_btn.clicked.connect(self.load_file)
        self.reset_btn = QPushButton("RESET TO ORIGIN"); self.reset_btn.clicked.connect(self.reset_audio); self.reset_btn.setEnabled(False)
        self.clean_btn = QPushButton("CLEAN CACHE"); self.clean_btn.clicked.connect(self.manual_cleanup)
        self.file_info = QLineEdit("System Ready."); self.file_info.setReadOnly(True)
        top.addWidget(self.load_btn); top.addWidget(self.reset_btn); top.addWidget(self.clean_btn); top.addWidget(self.file_info)
        layout.addLayout(top)

        tempo_box = QGridLayout()
        self.guessed_bpm = QLineEdit(""); self.guessed_bpm.setReadOnly(True)
        self.manual_bpm = QLineEdit("120.0")
        self.manual_bpm.textChanged.connect(self.log_tempo_change)
        
        tempo_box.addWidget(QLabel("AUTO-DETECTED:"), 0, 0); tempo_box.addWidget(self.guessed_bpm, 0, 1)
        tempo_box.addWidget(QLabel("MANUAL INPUT:"), 0, 2); tempo_box.addWidget(self.manual_bpm, 0, 3)
        
        ctrls = QHBoxLayout()
        for txt, f in [("½", 0.5), ("2x", 2.0)]:
            btn = QPushButton(txt); btn.clicked.connect(lambda ch, val=f: self.scale_bpm(val))
            ctrls.addWidget(btn)
        self.click_btn = QPushButton("METRONOME: OFF"); self.click_btn.clicked.connect(self.toggle_metronome)
        ctrls.addWidget(self.click_btn)
        tempo_box.addLayout(ctrls, 0, 4)
        layout.addLayout(tempo_box)

        self.sweep = TempoSweepIndicator(); layout.addWidget(self.sweep)
        self.waveform = WaveformWidget(); layout.addWidget(self.waveform)

        modes = QHBoxLayout()
        for m in ["TRUE_REVERSE", "HQ_REVERSE", "TATUM_REVERSE", "STUDIO_MODE"]:
            btn = QPushButton(m.replace("_", " ")); btn.clicked.connect(lambda ch, mode=m: self.apply_reverse(mode))
            modes.addWidget(btn)
        layout.addLayout(modes)

        playback = QHBoxLayout()
        self.play_btn = QPushButton("START ENGINE"); self.play_btn.clicked.connect(self.play_audio)
        self.stop_btn = QPushButton("STOP"); self.stop_btn.clicked.connect(self.stop_audio)
        self.save_btn = QPushButton("EXPORT MASTER"); self.save_btn.clicked.connect(self.save_file)
        playback.addWidget(self.play_btn); playback.addWidget(self.stop_btn); playback.addWidget(self.save_btn)
        layout.addLayout(playback)

        self.log = QTextEdit(); self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget { background-color: #0f0f0f; color: #eee; font-family: 'Segoe UI'; }
            QPushButton { background-color: #222; border: 1px solid #444; padding: 12px; font-weight: bold; }
            QLineEdit { background-color: #000; border: 1px solid #333; color: #00ffcc; padding: 6px; }
            QTextEdit { background-color: #050505; color: #00ff88; font-family: 'Consolas'; font-size: 11px; }
        """)

    def log_tempo_change(self):
        if self.manual_bpm.hasFocus():
            self.log.append(f"[USER] Manual tempo adjusted to: {self.manual_bpm.text()} BPM")

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Audio", "", "Audio Files (*.wav *.mp3 *.flac)")
        if path:
            self.log.append(f"[FILE] Loading: {os.path.basename(path)}")
            y, sr = librosa.load(path, sr=None, mono=False)
            self.original_audio = y.T if y.ndim > 1 else y
            self.current_audio = self.original_audio.copy()
            self.sr = sr
            self.waveform.set_waveform(y.mean(axis=0) if y.ndim > 1 else y, sr)
            self.file_info.setText(os.path.basename(path)); self.reset_btn.setEnabled(True)
            self.worker = TempoWorker(y, sr); self.worker.tempo_ready.connect(self.on_tempo_detected); self.worker.start()

    def on_tempo_detected(self, bpm):
        self.guessed_bpm.setText(f"{bpm:.2f}"); self.manual_bpm.setText(f"{bpm:.2f}")
        self.log.append(f"[ENGINE] Detected Tempo: {bpm:.2f} BPM")

    def reset_audio(self):
        if self.original_audio is not None:
            self.current_audio = self.original_audio.copy()
            vis = self.current_audio.T.mean(axis=0) if self.current_audio.ndim > 1 else self.current_audio
            self.waveform.set_waveform(vis, self.sr); self.log.append("[MIX] Reset to Original.")

    def manual_cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True); os.makedirs(self.temp_dir, exist_ok=True)
        self.log.append("[SYSTEM] Cache purged.")

    def scale_bpm(self, factor):
        try:
            val = float(self.manual_bpm.text()) * factor
            self.manual_bpm.setText(f"{val:.2f}")
        except: pass

    def toggle_metronome(self):
        self.click_enabled = not self.click_enabled
        self.click_btn.setText(f"METRONOME: {'ON' if self.click_enabled else 'OFF'}")
        if self.click_enabled: self.click_timer.start(int(60000 / float(self.manual_bpm.text())))
        else: self.click_timer.stop()

    def play_click(self): sd.play(self.click_buffer, 44100)

    def play_audio(self):
        if self.current_audio is None: return
        self.stop_audio(); self.play_idx = 0
        chs = self.current_audio.shape[1] if self.current_audio.ndim > 1 else 1
        self.stream = sd.OutputStream(samplerate=self.sr, channels=chs, callback=self.audio_callback)
        self.stream.start(); self.play_timer.start(25)
        # BUG FIX: set_bpm is now defined in TempoSweepIndicator
        self.sweep.set_bpm(self.manual_bpm.text())
        self.sweep.start()

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
        self.log.append(f"[PROCESS] Executing {mode}...")
        self.rev_worker = ReverseWorker(self.current_audio, self.sr, mode, float(self.manual_bpm.text()))
        self.rev_worker.finished.connect(self.on_rev_done); self.rev_worker.start()

    def on_rev_done(self, audio, mode):
        self.current_audio = audio
        vis = audio.T.mean(axis=0) if audio.ndim > 1 else audio
        self.waveform.set_waveform(vis, self.sr); self.log.append(f"[SUCCESS] {mode} complete.")

    def save_file(self):
        if self.current_audio is None: return
        path, _ = QFileDialog.getSaveFileName(self, "Export Master", "", "WAV (*.wav);;MP3 (*.mp3)")
        if path: sf.write(path, self.current_audio, self.sr); self.log.append(f"[EXPORT] Saved: {path}")

    def closeEvent(self, event): shutil.rmtree(self.temp_dir, ignore_errors=True); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); gui = DigitalReverseEngine(); gui.show(); sys.exit(app.exec())
