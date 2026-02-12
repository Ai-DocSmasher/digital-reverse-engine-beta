"""
Digital Reverse Engine AGI-aiPilotGEM-build 3.2
aiCOPILOT Reverse Engine | BUILD 3.2
A tempo-aware, reversible audio engine with upgraded UX, logging, and visual feedback.
"""

import sys
import os
import time
import shutil
import tempfile
import random
import numpy as np
import soundfile as sf
import sounddevice as sd
import librosa

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout,
    QTextEdit, QSizePolicy
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# ============================================================
# STYLED CONTROLS (aiCOPILOT AESTHETIC)
# ============================================================
class StyledButton(QPushButton):
    def __init__(self, text, accent="#00ffc8", parent=None):
        super().__init__(text, parent)
        self.accent = accent
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #141414;
                color: {accent};
                border-radius: 4px;
                border: 1px solid #333;
                padding: 8px 14px;
                font-family: 'Segoe UI Semibold';
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                border-color: {accent};
                background-color: #1f1f1f;
            }}
            QPushButton:pressed {{
                background-color: #0b0b0b;
            }}
            QPushButton:disabled {{
                color: #555;
                border-color: #222;
                background-color: #101010;
            }}
        """)

class AccentLabel(QLabel):
    def __init__(self, text, color="#9fa4b8", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"color: {color}; font-family: 'Segoe UI'; font-size: 10pt;")

# ============================================================
# WORKERS (UNCHANGED CORE BEHAVIOR, SAFETY-PATCHED)
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
            if y.ndim > 1:
                y = y.mean(axis=1)
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
        self.params = {
            "audio": audio,
            "sample_rate": sr,
            "mode": mode,
            "tempo": tempo
        }

    def run(self):
        try:
            # External pipeline hook (same contract as your build)
            from core.hybrid.pipeline import process_audio
            processed = process_audio(**self.params)
            self.finished.emit(processed, self.params["mode"])
        except Exception:
            # Fallback for standalone testing or missing pipeline
            self.finished.emit(self.params["audio"], "ERROR_FALLBACK")

# ============================================================
# VISUAL COMPONENTS (TIME RULER + UPGRADED SWEEP)
# ============================================================
class TempoSweepIndicator(QWidget):
    """
    aiCOPILOT variant:
    - Slightly softer palette
    - BPM-sensitive sweep speed
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_cells = 40
        self.bpm = 120.0
        self.phase = 0.0
        self.last_time = time.time()
        self.timer = QTimer(self)
        self.timer.setInterval(20)
        self.timer.timeout.connect(self.update_phase)
        self.setFixedHeight(52)
        self.color_palette = [
            QColor(0, 255, 200),
            QColor(0, 180, 255),
            QColor(255, 120, 80)
        ]
        self.current_color = self.color_palette[0]

    def set_bpm(self, bpm_str):
        try:
            val = float(bpm_str)
            self.bpm = val if val > 0 else 120.0
        except Exception:
            self.bpm = 120.0

    def start(self):
        self.last_time = time.time()
        if not self.timer.isActive():
            self.timer.start()

    def stop(self):
        self.timer.stop()
        self.phase = 0.0
        self.update()

    def update_phase(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        # Slightly faster at higher BPM, slower at low BPM
        period = (60.0 / max(self.bpm, 1.0)) * 1.3
        self.phase = (self.phase + dt / period) % 1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(8, 8, 10))
        cell_w = self.width() / self.num_cells
        center_idx = self.phase * self.num_cells

        for i in range(self.num_cells):
            dist = abs(i - center_idx)
            bright = max(0.0, 1.0 - (dist / 7.0)) ** 2.2
            c = QColor(self.current_color)
            c.setAlpha(int(255 * bright))
            p.fillRect(
                int(i * cell_w + 1),
                6,
                int(cell_w - 2),
                self.height() - 12,
                c
            )


class WaveformWidget(QWidget):
    """
    Precision build:
    - Peak-based waveform
    - High-accuracy sub-second Time axis
    - Playhead
    - Simple zoom window on hover/drag
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.peaks = None
        self.sr = 44100
        self.audio_len = 0
        self.playhead_sample = 0
        self.zoom_active = False
        self.sel_start = 0
        self.sel_end = 0
        self.axis_h = 45
        self.setMinimumHeight(220)
        self.setMouseTracking(True)

    def set_waveform(self, audio, sr):
        self.sr = sr
        self.audio_len = len(audio)
        pixels = max(600, self.width() or 1200)
        step = max(1, len(audio) // pixels)
        self.peaks = np.array([
            np.max(np.abs(audio[i:i + step]))
            for i in range(0, len(audio), step)
        ])
        self.total_samples = len(self.peaks)
        self.update()

    def set_position_ms(self, ms):
        if self.audio_len == 0:
            return
        ratio = (ms / 1000.0) / (self.audio_len / self.sr)
        self.playhead_sample = int(ratio * self.total_samples)
        self.update()

    def update_zoom(self, x):
        center = int((x / max(self.width(), 1)) * self.total_samples)
        win = int(self.total_samples * 0.12)
        self.sel_start = max(0, center - win // 2)
        self.sel_end = min(self.total_samples, self.sel_start + win)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.peaks is not None:
            self.zoom_active = True
            self.update_zoom(event.pos().x())

    def mouseMoveEvent(self, event):
        if self.zoom_active:
            self.update_zoom(event.pos().x())
        self.update()

    def mouseReleaseEvent(self, event):
        self.zoom_active = False
        self.update()

    def paintEvent(self, event):
        if self.peaks is None:
            return

        p = QPainter(self)
        w, h = self.width(), self.height()
        wf_h = h - self.axis_h

        start = self.sel_start if self.zoom_active else 0
        end = self.sel_end if self.zoom_active else self.total_samples
        visible = self.peaks[start:end]

        # Waveform background
        p.fillRect(0, 0, w, wf_h, QColor(10, 10, 12))

        if len(visible) > 0:
            step = w / len(visible)
            p.setPen(QPen(QColor(0, 255, 200, 170), 1))
            for i, amp in enumerate(visible):
                x = int(i * step)
                line_h = int(amp * (wf_h / 2) * 0.9)
                p.drawLine(x, wf_h // 2 - line_h, x, wf_h // 2 + line_h)

        # Axis strip
        p.fillRect(0, wf_h, w, self.axis_h, QColor(20, 20, 24))
        p.setPen(QColor(230, 230, 230))
        p.setFont(QFont("Consolas", 8))

        # --- HIGH ACCURACY TIME CALCULATIONS ---
        total_duration = self.audio_len / self.sr if self.sr > 0 else 0
        start_time = (start / self.total_samples) * total_duration
        end_time = (end / self.total_samples) * total_duration
        visible_duration = end_time - start_time

        # Draw ticks every 1 second or 0.1 second depending on zoom
        tick_step = 1.0 if visible_duration > 5 else 0.1
        current_tick = np.ceil(start_time / tick_step) * tick_step
        
        while current_tick <= end_time:
            rel_pos = (current_tick - start_time) / (visible_duration if visible_duration > 0 else 1)
            tx = int(rel_pos * w)
            p.setPen(QPen(QColor(0, 255, 200, 80), 1))
            p.drawLine(tx, wf_h, tx, h - 20)
            
            # Label every major second or if zoomed in enough
            if current_tick % 1.0 == 0 or visible_duration < 2:
                p.setPen(QColor(200, 200, 200))
                p.drawText(tx + 2, h - 8, f"{current_tick:.0f}")
            
            current_tick += tick_step

        # Playhead
        if start <= self.playhead_sample < end and end > start:
            rel_x = (self.playhead_sample - start) / (end - start)
            x = int(rel_x * w)
            p.setPen(QPen(Qt.GlobalColor.white, 2))
            p.drawLine(x, 0, x, wf_h)

# ============================================================
# MASTER ENGINE (AGI-aiPilotGEM-build 3.2)
# ============================================================
class AiCopilotReverseEngine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AGI-aiPilotGEM-build 3.2 | Reverse Engine")
        self.setMinimumSize(1180, 820)

        # CORE STATE
        self.original_audio = None
        self.current_audio = None
        self.sr = 44100
        self.stream = None
        self.play_idx = 0

        self.click_enabled = False
        self.temp_dir = tempfile.mkdtemp(prefix="AICOPILOT_DRE_")

        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self.update_playhead)

        self.click_timer = QTimer()
        self.click_timer.timeout.connect(self.play_click)

        # Metronome click
        t = np.linspace(0, 0.03, int(44100 * 0.03))
        self.click_buffer = (np.sin(2 * np.pi * 1000 * t) * 0.5).astype(np.float32)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # TOP BAR
        top = QHBoxLayout()
        self.load_btn = StyledButton("LOAD SOURCE")
        self.load_btn.clicked.connect(self.load_file)

        self.reset_btn = StyledButton("RESET TO ORIGIN", accent="#ff6b8b")
        self.reset_btn.clicked.connect(self.reset_audio)
        self.reset_btn.setEnabled(False)

        self.clean_btn = StyledButton("CLEAN CACHE", accent="#ffaa33")
        self.clean_btn.clicked.connect(self.manual_cleanup)

        self.file_info = QLineEdit("System idle. Awaiting audio source.")
        self.file_info.setReadOnly(True)

        top.addWidget(self.load_btn)
        top.addWidget(self.reset_btn)
        top.addWidget(self.clean_btn)
        top.addWidget(self.file_info, 1)
        root.addLayout(top)

        # TEMPO GRID
        tempo_grid = QGridLayout()
        tempo_grid.setHorizontalSpacing(10)
        tempo_grid.setVerticalSpacing(4)

        self.guessed_bpm = QLineEdit("")
        self.guessed_bpm.setReadOnly(True)

        self.manual_bpm = QLineEdit("120.0")
        self.manual_bpm.editingFinished.connect(self.log_manual_tempo)

        tempo_grid.addWidget(AccentLabel("AUTO-DETECTED"), 0, 0)
        tempo_grid.addWidget(self.guessed_bpm, 0, 1)
        tempo_grid.addWidget(AccentLabel("MANUAL INPUT"), 0, 2)
        tempo_grid.addWidget(self.manual_bpm, 0, 3)

        tempo_ctrls = QHBoxLayout()
        half_btn = StyledButton("½")
        half_btn.clicked.connect(lambda ch=False, f=0.5: self.scale_bpm(f))
        dbl_btn = StyledButton("2x")
        dbl_btn.clicked.connect(lambda ch=False, f=2.0: self.scale_bpm(f))
        tempo_ctrls.addWidget(half_btn)
        tempo_ctrls.addWidget(dbl_btn)

        self.click_btn = StyledButton("METRONOME: OFF", accent="#00ffc8")
        self.click_btn.clicked.connect(self.toggle_metronome)
        tempo_ctrls.addWidget(self.click_btn)

        tempo_grid.addLayout(tempo_ctrls, 0, 4)
        root.addLayout(tempo_grid)

        # VISUAL STRIP
        self.sweep = TempoSweepIndicator()
        root.addWidget(self.sweep)

        # WAVEFORM
        self.waveform = WaveformWidget()
        root.addWidget(self.waveform, 1)

        # MODES
        modes = QHBoxLayout()
        modes.setSpacing(8)
        mode_labels = [
            ("TRUE_REVERSE", "#00ffc8"),
            ("HQ_REVERSE", "#4dd2ff"),
            ("TATUM_REVERSE", "#ffb347"),
            ("STUDIO_MODE", "#ff6b8b"),
        ]
        for mode, color in mode_labels:
            btn = StyledButton(mode.replace("_", " "), accent=color)
            btn.clicked.connect(lambda ch=False, m=mode: self.apply_reverse(m))
            modes.addWidget(btn)
        root.addLayout(modes)

        # TRANSPORT
        transport = QHBoxLayout()
        self.play_btn = StyledButton("START ENGINE", accent="#00ffc8")
        self.play_btn.clicked.connect(self.play_audio)

        self.stop_btn = StyledButton("STOP", accent="#ff6b8b")
        self.stop_btn.clicked.connect(self.stop_audio)

        self.save_btn = StyledButton("EXPORT MASTER", accent="#ffffff")
        self.save_btn.clicked.connect(self.save_file)

        transport.addWidget(self.play_btn)
        transport.addWidget(self.stop_btn)
        transport.addWidget(self.save_btn)
        root.addLayout(transport)

        # LOG
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(160)
        root.addWidget(self.log)

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #050608;
                color: #e6e6e6;
                font-family: 'Segoe UI';
                font-size: 10pt;
            }
            QLineEdit {
                background-color: #050509;
                border: 1px solid #2a2a33;
                border-radius: 4px;
                padding: 6px;
                color: #00ffc8;
                font-family: 'Consolas';
                font-size: 10pt;
            }
            QTextEdit {
                background-color: #050507;
                border: 1px solid #1b1b22;
                border-radius: 4px;
                color: #9fe8ff;
                font-family: 'Consolas';
                font-size: 10px;
            }
        """)

    def log_manual_tempo(self):
        self.log.append(f"[USER] Manual Tempo Update → {self.manual_bpm.text()} BPM")

    def scale_bpm(self, factor):
        try:
            old_val = float(self.manual_bpm.text())
            new_val = old_val * factor
            self.manual_bpm.setText(f"{new_val:.2f}")
            self.log.append(f"[USER] Tempo scaled {factor}x: {old_val:.2f} → {new_val:.2f} BPM")
            if self.click_enabled:
                self.click_timer.stop()
                self.click_timer.start(int(60000 / new_val))
        except Exception:
            self.log.append("[SAFETY] Invalid BPM scaling input.")

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Audio",
            "",
            "Audio Files (*.wav *.mp3 *.flac)"
        )
        if not path:
            return

        self.log.append(f"[FILE] Loading: {os.path.basename(path)}")
        y, sr = librosa.load(path, sr=None, mono=False)

        self.original_audio = y.T if y.ndim > 1 else y
        self.current_audio = self.original_audio.copy()
        self.sr = sr

        vis = y.mean(axis=0) if y.ndim > 1 else y
        self.waveform.set_waveform(vis, sr)

        self.file_info.setText(os.path.basename(path))
        self.reset_btn.setEnabled(True)

        self.worker = TempoWorker(y, sr)
        self.worker.tempo_ready.connect(self.on_tempo_detected)
        self.worker.start()

    def on_tempo_detected(self, bpm):
        self.guessed_bpm.setText(f"{bpm:.2f}")
        self.manual_bpm.setText(f"{bpm:.2f}")
        self.log.append(f"[ENGINE] Detected Tempo: {bpm:.2f} BPM")

    def toggle_metronome(self):
        self.click_enabled = not self.click_enabled
        self.click_btn.setText(f"METRONOME: {'ON' if self.click_enabled else 'OFF'}")
        if self.click_enabled:
            try:
                bpm = float(self.manual_bpm.text())
                self.click_timer.start(int(60000 / bpm))
                self.log.append(f"[SYSTEM] Metronome active at {bpm:.2f} BPM")
            except Exception:
                self.log.append("[SAFETY] Metronome failed: Enter valid BPM.")
                self.click_enabled = False
        else:
            self.click_timer.stop()

    def play_click(self):
        sd.play(self.click_buffer, 44100)

    def play_audio(self):
        if self.current_audio is None:
            self.log.append("[SAFETY] Playback blocked: LOAD SOURCE first.")
            return

        self.stop_audio()
        self.play_idx = 0

        chs = self.current_audio.shape[1] if self.current_audio.ndim > 1 else 1
        self.stream = sd.OutputStream(
            samplerate=self.sr,
            channels=chs,
            callback=self.audio_callback
        )
        self.stream.start()
        self.play_timer.start(25)

        self.sweep.set_bpm(self.manual_bpm.text())
        self.sweep.start()
        self.log.append("[ENGINE] Playback stream initiated.")

    def audio_callback(self, outdata, frames, time_info, status):
        chunk = self.current_audio[self.play_idx:self.play_idx + frames]
        if len(chunk) < frames:
            outdata[:len(chunk)] = chunk
            outdata[len(chunk):].fill(0)
            self.play_idx = 0
            raise sd.CallbackStop()
        else:
            outdata[:] = chunk
            self.play_idx += frames

    def stop_audio(self):
        self.play_timer.stop()
        self.sweep.stop()
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.waveform.set_position_ms(0)

    def update_playhead(self):
        if self.stream and self.stream.active:
            ms = (self.play_idx / self.sr) * 1000
            self.waveform.set_position_ms(ms)

    def apply_reverse(self, mode):
        if self.current_audio is None:
            self.log.append(f"[SAFETY] {mode} blocked: LOAD SOURCE first.")
            return

        bpm_val = self.manual_bpm.text()
        self.log.append("── RENDER START ──")
        self.log.append(f"[CONFIG] Mode: {mode} | BPM Grid: {bpm_val}")

        try:
            tempo = float(bpm_val)
        except Exception:
            tempo = 120.0

        self.rev_worker = ReverseWorker(self.current_audio, self.sr, mode, tempo)
        self.rev_worker.finished.connect(self.on_rev_done)
        self.rev_worker.start()

    def on_rev_done(self, audio, mode):
        self.current_audio = audio
        vis = audio.T.mean(axis=0) if audio.ndim > 1 else audio
        self.waveform.set_waveform(vis, self.sr)

        if mode == "ERROR_FALLBACK":
            self.log.append("[WARN] Reverse pipeline failed. Original buffer preserved.")
        else:
            self.log.append(f"[SUCCESS] {mode} completed at {self.manual_bpm.text()} BPM.")
        self.log.append("──────────────────")

    def reset_audio(self):
        if self.original_audio is not None:
            self.current_audio = self.original_audio.copy()
            vis = self.current_audio.T.mean(axis=0) if self.current_audio.ndim > 1 else self.current_audio
            self.waveform.set_waveform(vis, self.sr)
            self.log.append("[MIX] Reset to Original Buffer.")

    def manual_cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        self.log.append("[SYSTEM] Cache purged.")

    def save_file(self):
        if self.current_audio is None:
            self.log.append("[SAFETY] Export blocked: No audio buffer to save.")
            return

        # --- UPDATED SAVE AS WITH MP3 OPTION ---
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Master",
            "",
            "WAV (*.wav);;MP3 (*.mp3);;FLAC (*.flac)"
        )
        if path:
            try:
                # soundfile handles wav/flac natively. 
                # Note: Exporting to MP3 via soundfile requires libsndfile 1.1+
                sf.write(path, self.current_audio, self.sr)
                self.log.append(f"[EXPORT] Final master saved: {path}")
            except Exception as e:
                self.log.append(f"[ERROR] Export failed: {str(e)}")

    def closeEvent(self, event):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        event.accept()

# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AiCopilotReverseEngine()
    gui.show()
    sys.exit(app.exec())
