"""
Digital Reverse Engine AGI-aiPilotGEM-build 3.2
aiCOPILOT Reverse Engine | BUILD 3.2
A tempo-aware, reversible audio engine with upgraded UX, logging, and visual feedback.
"""

# gui_player.py

import sys
import os
import time
import shutil
import tempfile
import numpy as np
import soundfile as sf
import sounddevice as sd
import librosa

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout,
    QTextEdit, QSizePolicy, QFrame
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# ============================================================
# MODERN CYBER-TECH STYLED CONTROLS
# ============================================================
class ControlPod(QFrame):
    """A container for grouping related controls with a subtle border."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.header = QLabel(title.upper())
        self.header.setStyleSheet(
            "color: #58a6ff; font-size: 8pt; font-weight: bold; "
            "border: none; background: transparent;"
        )
        self.layout.addWidget(self.header)


class CyberButton(QPushButton):
    def __init__(self, text, accent="#00ffc8", parent=None):
        super().__init__(text, parent)
        self.accent = accent
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #161b22;
                color: {accent};
                border-radius: 2px;
                border: 1px solid #30363d;
                font-family: 'Segoe UI';
                font-size: 9pt;
                text-transform: uppercase;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {accent};
                background-color: #21262d;
            }}
            QPushButton:pressed {{
                background-color: #000000;
            }}
        """)

# ============================================================
# ENHANCED VISUALIZERS
# ============================================================
class SweepIndicator(QWidget):
    """A rhythmic pulse bar that reacts to the set BPM."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.bpm = 120.0
        self.progress = 0.0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

    def set_bpm(self, bpm_val: float):
        try:
            v = float(bpm_val)
            self.bpm = v if v > 0 else 120.0
        except Exception:
            self.bpm = 120.0

    def animate(self):
        bps = self.bpm / 60.0
        self.progress = (time.time() * bps) % 1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(22, 27, 34))

        w = self.width()
        indicator_x = int(self.progress * w)
        grad = QLinearGradient(indicator_x - 100, 0, indicator_x, 0)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(1, QColor(0, 255, 200))

        p.fillRect(0, 0, indicator_x, self.height(), grad)


class NeonWaveform(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.peaks = None
        self.playhead_pos = 0
        self.sr = 44100
        self.audio_len = 0
        self.setMinimumHeight(250)
        self.setMouseTracking(True)

        # Zoom + hint state
        self.zoom_active = False
        self.sel_start = 0
        self.sel_end = 0
        self.hint_opacity = 1.0

        self.hint_timer = QTimer()
        self.hint_timer.setInterval(40)
        self.hint_timer.timeout.connect(self.fade_hint)
        self.hint_timer.start()

    # ============================================================
    # ZOOM + TIME MARKERS + CYBER HINT OVERLAY
    # ============================================================
    def set_waveform(self, audio, sr):
        self.sr = sr
        self.audio_len = len(audio)

        samples = 2000
        step = max(1, len(audio) // samples)
        self.peaks = np.array([
            np.max(np.abs(audio[i:i + step]))
            for i in range(0, len(audio), step)
        ])
        self.total_peaks = len(self.peaks)

        # Reset zoom
        self.zoom_active = False
        self.sel_start = 0
        self.sel_end = self.total_peaks

        # Reset hint
        self.hint_opacity = 1.0

        self.update()

    def fade_hint(self):
        if self.hint_opacity > 0:
            self.hint_opacity -= 0.02
            self.update()

    def update_playhead(self, ms):
        if self.audio_len == 0:
            return

        total_ms = (self.audio_len / self.sr) * 1000
        ratio = ms / total_ms
        self.playhead_pos = ratio * self.width()
        self.update()

    def mousePressEvent(self, event):
        if self.peaks is None or len(self.peaks) == 0:
            return

        x = event.pos().x()

        # LEFT CLICK → SNAP PLAYHEAD
        if event.button() == Qt.MouseButton.LeftButton:
            total_ms = (self.audio_len / self.sr) * 1000
            ratio = x / max(self.width(), 1)
            ms = ratio * total_ms
            parent = self.parent()
            if parent and hasattr(parent, "snap_to_ms"):
                parent.snap_to_ms(ms)
            return

        # RIGHT CLICK → ZOOM TO REGION
        if event.button() == Qt.MouseButton.RightButton:
            if not self.zoom_active:
                self.zoom_active = True
                center = int((x / self.width()) * self.total_peaks)
                win = int(self.total_peaks * 0.15)
                self.sel_start = max(0, center - win // 2)
                self.sel_end = min(self.total_peaks, self.sel_start + win)
            else:
                # Reset zoom
                self.zoom_active = False
                self.sel_start = 0
                self.sel_end = self.total_peaks

            self.hint_opacity = 1.0
            self.update()

    def mouseMoveEvent(self, event):
        if self.zoom_active and self.peaks is not None:
            x = event.pos().x()
            center = int((x / self.width()) * self.total_peaks)
            win = int(self.total_peaks * 0.15)
            self.sel_start = max(0, center - win // 2)
            self.sel_end = min(self.total_peaks, self.sel_start + win)
            self.hint_opacity = 1.0
            self.update()

    def paintEvent(self, event):
        if self.peaks is None:
            return

        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(13, 17, 23))

        # Determine visible region
        start = self.sel_start if self.zoom_active else 0
        end = self.sel_end if self.zoom_active else self.total_peaks
        visible = self.peaks[start:end]

        # Draw waveform
        if len(visible) > 0:
            step = w / len(visible)
            p.setPen(QPen(QColor(0, 255, 200, 180), 1))
            for i, amp in enumerate(visible):
                x = int(i * step)
                line_h = int(amp * (h * 0.8))
                p.drawLine(x, h // 2 - line_h // 2, x, h // 2 + line_h // 2)

        # Time axis
        p.setPen(QPen(QColor(0, 255, 200, 80), 1))
        total_duration = self.audio_len / self.sr
        start_time = (start / self.total_peaks) * total_duration
        end_time = (end / self.total_peaks) * total_duration
        visible_duration = max(end_time - start_time, 1e-9)

        # ============================================================
        # SMART TICK SPACING (seconds, but spaced by pixel density)
        # ============================================================

        # Base tick step (seconds)
        if visible_duration > 120:
            tick_step = 10.0
        elif visible_duration > 60:
            tick_step = 5.0
        elif visible_duration > 20:
            tick_step = 2.0
        elif visible_duration > 10:
            tick_step = 1.0
        else:
            tick_step = 0.5

        # Minimum pixel spacing between labels
        MIN_LABEL_SPACING = 50
        last_label_x = -999

        t = np.ceil(start_time / tick_step) * tick_step
        while t <= end_time:
            rel = (t - start_time) / visible_duration
            tx = int(rel * w)

            # Only draw label if far enough from previous
            if tx - last_label_x >= MIN_LABEL_SPACING:
                p.drawLine(tx, h - 20, tx, h)
                p.setPen(QColor(200, 200, 200))
                p.drawText(tx + 2, h - 5, f"{t:.0f}s")
                p.setPen(QPen(QColor(0, 255, 200, 80), 1))
                last_label_x = tx

            t += tick_step

        # ============================================================
        # PLAYHEAD — ALWAYS VISIBLE
        # ============================================================
        playhead_x = int(self.playhead_pos)
        if 0 <= playhead_x <= w:
            p.setPen(QPen(Qt.GlobalColor.white, 2))
            p.drawLine(playhead_x, 0, playhead_x, h)

        # Hint overlay
        if self.hint_opacity > 0:
            p.setOpacity(self.hint_opacity)
            p.setPen(QColor(200, 200, 210))
            p.setFont(QFont("Segoe UI", 9))
            hint = "Left-click: Jump | Right-click: Zoom | Drag: Pan | Right-click again: Reset"
            tw = p.fontMetrics().horizontalAdvance(hint)
            p.drawText((w - tw) // 2, 20, hint)
            p.setOpacity(1.0)


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
            if y.ndim > 1:
                y = y.mean(axis=0)
            if len(y) < 2048:
                self.tempo_ready.emit(120.0)
                return
            onset_env = librosa.onset.onset_strength(y=y.astype(np.float32), sr=self.sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=self.sr, aggregate=None)

            if hasattr(tempo, "__len__"):
                val = float(tempo[0])
            else:
                val = float(tempo)
            self.tempo_ready.emit(val if val > 0 else 120.0)
        except Exception:
            self.tempo_ready.emit(120.0)


class ReverseWorker(QThread):
    finished = pyqtSignal(np.ndarray, str)

    def __init__(self, audio, sr, mode, tempo, grid_params, parent=None):
        super().__init__(parent)
        self.params = {
            "audio": audio,
            "sample_rate": sr,
            "mode": mode,
            "tempo": tempo,
            **grid_params,
        }

    def run(self):
        try:
            from core.hybrid.pipeline import process_audio
            processed = process_audio(**self.params)
            self.finished.emit(processed, self.params["mode"])
        except Exception as e:
            print("PIPELINE ERROR:", e)
            self.finished.emit(self.params["audio"], "ERROR_FALLBACK")

# ============================================================
# MAIN APPLICATION: "VIRTUAL STUDIO 3.2"
# ============================================================
class CyberReverseEngine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AGI-aiPilotGEM // REVERSE ENGINE v3.2")
        self.resize(1200, 850)

        # Shared Audio State
        self.original_audio = None
        self.current_audio = None
        self.sr = 44100
        self.stream = None
        self.play_idx = 0
        self.temp_dir = tempfile.mkdtemp()

        # Metronome
        self.click_enabled = False
        self.click_timer = QTimer()
        self.click_timer.timeout.connect(self.play_click)
        t = np.linspace(0, 0.03, int(44100 * 0.03))
        self.click_buffer = (np.sin(2 * np.pi * 1000 * t) * 0.1).astype(np.float32)

        # Playback timer
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self.sync_ui)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # --- ROW 1: FILE OPERATIONS POD ---
        file_pod = ControlPod("Source Input")
        file_layout = QHBoxLayout()
        self.load_btn = CyberButton("Import Wave", "#58a6ff")
        self.load_btn.clicked.connect(self.load_file)
        self.file_path_display = QLineEdit("NO_FILE_LOADED")
        self.file_path_display.setReadOnly(True)
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.file_path_display, 1)
        file_pod.layout.addLayout(file_layout)
        main_layout.addWidget(file_pod)

        # --- ROW 2: CENTER WORKSPACE ---
        center_layout = QHBoxLayout()

        # Visualization
        vis_layout = QVBoxLayout()
        self.sweep = SweepIndicator()
        self.waveform = NeonWaveform()
        vis_layout.addWidget(self.sweep)
        vis_layout.addWidget(self.waveform, 1)
        center_layout.addLayout(vis_layout, 3)

        # Grid Logic Pod
        math_pod = ControlPod("Grid Logic")
        math_pod.setFixedWidth(280)
        m_grid = QGridLayout()
        m_grid.setHorizontalSpacing(1)

        # ============================================================
        # BPM STRIP — unified look with ½ and 2× buttons
        # ============================================================
        m_grid.addWidget(QLabel("BPM:"), 0, 0)

        total_width = 180  # keep your existing width

        bpm_container = QWidget()
        bpm_container.setFixedWidth(total_width)
        bpm_container_layout = QHBoxLayout(bpm_container)
        bpm_container_layout.setContentsMargins(0, 0, 0, 0)
        bpm_container_layout.setSpacing(0)

        # BPM textbox styled like the buttons
        self.bpm_in = QLineEdit("120")
        self.bpm_in.setFixedSize(total_width - 80, 30)  # 100px BPM + 40 + 40 buttons
        self.bpm_in.editingFinished.connect(self.refresh_metronome_bpm)
        self.bpm_in.setStyleSheet("""
            QLineEdit {
                background-color: #161b22;
                color: #79c0ff;
                border: 1px solid #30363d;
                border-right: none;
                border-radius: 0px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
                padding-left: 6px;
            }
        """)

        # ½ button
        self.half_btn = CyberButton("½", "#79c0ff")
        self.half_btn.setFixedSize(40, 30)
        self.half_btn.clicked.connect(self.half_bpm)
        self.half_btn.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #79c0ff;
                border: 1px solid #30363d;
                border-left: none;
                border-right: none;
                border-radius: 0px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #79c0ff;
                background-color: #21262d;
            }
        """)

        # 2× button
        self.double_btn = CyberButton("2×", "#79c0ff")
        self.double_btn.setFixedSize(40, 30)
        self.double_btn.clicked.connect(self.double_bpm)
        self.double_btn.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #79c0ff;
                border: 1px solid #30363d;
                border-left: none;
                border-radius: 0px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #79c0ff;
                background-color: #21262d;
            }
        """)

        bpm_container_layout.addWidget(self.bpm_in)
        bpm_container_layout.addWidget(self.half_btn)
        bpm_container_layout.addWidget(self.double_btn)

        m_grid.addWidget(bpm_container, 0, 1)

        # ============================================================
        # BARS / BEATS / TATUM — exact same width as BPM strip
        # ============================================================

        m_grid.addWidget(QLabel("BARS:"), 1, 0)
        self.bars_in = QLineEdit("1")
        self.bars_in.setFixedWidth(total_width)
        m_grid.addWidget(self.bars_in, 1, 1)

        m_grid.addWidget(QLabel("BEATS:"), 2, 0)
        self.beats_in = QLineEdit("4")
        self.beats_in.setFixedWidth(total_width)
        m_grid.addWidget(self.beats_in, 2, 1)

        m_grid.addWidget(QLabel("TATUM:"), 3, 0)
        self.tatum_in = QLineEdit("16")
        self.tatum_in.setFixedWidth(total_width)
        m_grid.addWidget(self.tatum_in, 3, 1)

        math_pod.layout.addLayout(m_grid)

        # Metronome toggle
        self.metro_btn = CyberButton("Metronome: OFF", "#00ffc8")
        self.metro_btn.clicked.connect(self.toggle_metronome)
        math_pod.layout.addWidget(self.metro_btn)

        math_pod.layout.addStretch()

        self.reset_btn = CyberButton("Clear Buffer", "#ff6b8b")
        self.reset_btn.clicked.connect(self.reset_audio)
        math_pod.layout.addWidget(self.reset_btn)

        center_layout.addWidget(math_pod)
        main_layout.addLayout(center_layout)

        # --- ROW 3: EXTRACTION MODES ---
        mode_pod = ControlPod("Extraction Algorithms")
        modes_layout = QHBoxLayout()

        btn_true = CyberButton("Standard Rev", "#d2a8ff")
        btn_hq = CyberButton("High Fidelity", "#00ffc8")
        btn_tatum = CyberButton("Tatum Logic", "#ff7b72")
        btn_studio = CyberButton("Studio Shuf", "#79c0ff")

        btn_true.clicked.connect(lambda: self.trigger_process("TRUE_REVERSE"))
        btn_hq.clicked.connect(lambda: self.trigger_process("HQ_REVERSE"))
        btn_tatum.clicked.connect(lambda: self.trigger_process("TATUM_REVERSE"))
        btn_studio.clicked.connect(lambda: self.trigger_process("STUDIO_MODE"))

        modes_layout.addWidget(btn_true)
        modes_layout.addWidget(btn_hq)
        modes_layout.addWidget(btn_tatum)
        modes_layout.addWidget(btn_studio)
        mode_pod.layout.addLayout(modes_layout)
        main_layout.addWidget(mode_pod)

        # --- ROW 4: TRANSPORT & LOGS ---
        bottom_layout = QHBoxLayout()

        transport_pod = ControlPod("Master Transport")
        t_layout = QHBoxLayout()
        self.play_btn = CyberButton("Initialize Playback", "#afff33")
        self.play_btn.clicked.connect(self.toggle_play)
        self.save_btn = CyberButton("Export Master", "#f2f2f2")
        self.save_btn.clicked.connect(self.save_file)
        t_layout.addWidget(self.play_btn)
        t_layout.addWidget(self.save_btn)
        transport_pod.layout.addLayout(t_layout)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(100)

        bottom_layout.addWidget(transport_pod, 1)
        bottom_layout.addWidget(self.log, 1)
        main_layout.addLayout(bottom_layout)

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #010409;
                color: #c9d1d9;
                font-family: 'Consolas', 'Courier New';
            }
            QLabel { font-size: 8pt; color: #8b949e; }
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                color: #58a6ff;
                padding: 4px;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                color: #d2a8ff;
                font-size: 8pt;
            }
        """)

    # --------------------------------------------------------
    # BPM CONTROL HELPERS
    # --------------------------------------------------------
    def refresh_metronome_bpm(self):
        """Refresh metronome interval when BPM changes."""
        self.log.append(f"[BPM] Updated → {self.bpm_in.text()}")

        if not self.click_enabled:
            return
        try:
            bpm = float(self.bpm_in.text())
            interval = int(60000 / max(bpm, 1.0))
            self.click_timer.start(interval)
            self.sweep.set_bpm(bpm)
            self.log.append(f"[METRO] BPM updated → {bpm:.2f}")
        except Exception:
            self.log.append("[METRO] Invalid BPM; cannot refresh.")

    def half_bpm(self):
        """Halve the BPM value."""
        try:
            bpm = float(self.bpm_in.text())
            bpm = max(bpm / 2, 1.0)
            self.bpm_in.setText(f"{bpm:.2f}")
            self.refresh_metronome_bpm()
            self.log.append(f"[BPM] Halved → {bpm:.2f}")
        except ValueError:
            self.log.append("[ERROR] Invalid BPM; cannot halve.")

    def double_bpm(self):
        """Double the BPM value."""
        try:
            bpm = float(self.bpm_in.text())
            bpm = min(bpm * 2, 999.0)
            self.bpm_in.setFixedWidth(60)

            self.refresh_metronome_bpm()
            self.log.append(f"[BPM] Doubled → {bpm:.2f}")
        except ValueError:
            self.log.append("[ERROR] Invalid BPM; cannot double.")

    # --------------------------------------------------------
    # FUNCTIONALITY
    # --------------------------------------------------------
    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio", "", "Audio (*.wav *.mp3 *.flac)"
        )
        if not path:
            return
        y, sr = librosa.load(path, sr=None, mono=False)
        self.original_audio = y.T if y.ndim > 1 else y
        self.current_audio = self.original_audio.copy()
        self.sr = sr
        self.file_path_display.setText(os.path.basename(path))

        vis = y.mean(axis=0) if y.ndim > 1 else y
        self.waveform.set_waveform(vis, sr)
        self.log.append(f"[INIT] Loaded {path}")

        # Optional: auto tempo detection
        self.log.append("[ENGINE] Detecting BPM…")
        self.tempo_worker = TempoWorker(y, sr)
        self.tempo_worker.tempo_ready.connect(self.on_tempo_detected)
        self.tempo_worker.start()

    def on_tempo_detected(self, bpm):
        self.bpm_in.setText(f"{bpm:.2f}")
        self.sweep.set_bpm(bpm)
        self.log.append(f"[ENGINE] Detected BPM: {bpm:.2f}")

    def trigger_process(self, mode):
        if self.current_audio is None:
            self.log.append("[WARN] No buffer loaded.")
            return

        try:
            tempo = float(self.bpm_in.text())
            bars = int(self.bars_in.text())
            beats = int(self.beats_in.text())
            tatum = int(self.tatum_in.text())
        except ValueError:
            self.log.append("[ERROR] Invalid grid or tempo values.")
            return

        grid_params = {
            "bars_per_slice": bars,
            "beats_per_bar": beats,
            "tatum_fraction": tatum,
        }

        self.log.append(
            f"[COMPUTE] {mode} | BPM={tempo:.2f} | bars={bars}, beats={beats}, tatum={tatum}"
        )

        self.rev_worker = ReverseWorker(
            self.current_audio, self.sr, mode, tempo, grid_params
        )
        self.rev_worker.finished.connect(self.on_rev_done)
        self.rev_worker.start()

    def on_rev_done(self, audio, mode):
        self.current_audio = audio
        vis = audio.T.mean(axis=0) if audio.ndim > 1 else audio
        self.waveform.set_waveform(vis, self.sr)
        if mode == "ERROR_FALLBACK":
            self.log.append("[FAIL] DSP pipeline failed, fallback buffer used.")
        else:
            self.log.append(f"[DONE] {mode} Applied.")

    # --------------------------------------------------------
    # METRONOME
    # --------------------------------------------------------
    def toggle_metronome(self):
        self.click_enabled = not self.click_enabled
        if self.click_enabled:
            try:
                bpm = float(self.bpm_in.text())
                interval = int(60000 / max(bpm, 1.0))
                self.click_timer.start(interval)
                self.metro_btn.setText("Metronome: ON")
                self.log.append(f"[METRO] ON @ {bpm:.2f} BPM")
            except Exception:
                self.log.append("[METRO] Invalid BPM; metronome disabled.")
                self.click_enabled = False
                self.metro_btn.setText("Metronome: OFF")
        else:
            self.click_timer.stop()
            self.metro_btn.setText("Metronome: OFF")
            self.log.append("[METRO] OFF")

    def play_click(self):
        sd.play(self.click_buffer, 44100)

    # --------------------------------------------------------
    # PLAYBACK
    # --------------------------------------------------------
    def toggle_play(self):
        # --- STOP PLAYBACK ---
        if self.stream is not None and self.stream.active:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass

            self.stream = None
            self.play_timer.stop()

            # Auto-stop sweep indicator
            self.sweep.timer.stop()
            self.sweep.progress = 0.0
            self.sweep.update()

            self.play_btn.setText("Initialize Playback")
            return

        # --- START PLAYBACK ---
        if self.current_audio is None:
            return

        self.play_idx = 0
        audio = self.current_audio

        # Determine channel count
        chs = 1 if audio.ndim == 1 else audio.shape[1]

        # Start audio stream
        self.stream = sd.OutputStream(
            samplerate=self.sr,
            channels=chs,
            callback=self.audio_callback,
        )
        self.stream.start()

        # UI sync timer
        self.play_timer.start(30)

        # Auto-start sweep indicator with BPM
        try:
            bpm = float(self.bpm_in.text())
            self.sweep.set_bpm(bpm)
        except Exception:
            pass
        self.sweep.timer.start()

        self.play_btn.setText("Cease Playback")


    def audio_callback(self, outdata, frames, time_info, status):
        audio = self.current_audio
        n = len(audio)

        start = self.play_idx
        end = min(start + frames, n)

        # MONO
        if audio.ndim == 1:
            chunk = audio[start:end]
            if len(chunk) < frames:
                outdata[:len(chunk), 0] = chunk
                outdata[len(chunk):].fill(0)
                self.play_idx = 0
                raise sd.CallbackStop()
            else:
                outdata[:, 0] = chunk
                if outdata.shape[1] > 1:
                    outdata[:, 1:] = 0
                self.play_idx = end

        # MULTICHANNEL
        else:
            chunk = audio[start:end, :]
            if len(chunk) < frames:
                outdata[:len(chunk)] = chunk
                outdata[len(chunk):].fill(0)
                self.play_idx = 0
                raise sd.CallbackStop()
            else:
                outdata[:] = chunk
                self.play_idx = end


"""
Digital Reverse Engine AGI-aiPilotGEM-build 3.2
aiCOPILOT Reverse Engine | BUILD 3.2
A tempo-aware, reversible audio engine with upgraded UX, logging, and visual feedback.
"""

# gui_player.py

import sys
import os
import time
import shutil
import tempfile
import numpy as np
import soundfile as sf
import sounddevice as sd
import librosa

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit,
    QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout,
    QTextEdit, QSizePolicy, QFrame
)
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# ============================================================
# MODERN CYBER-TECH STYLED CONTROLS
# ============================================================
class ControlPod(QFrame):
    """A container for grouping related controls with a subtle border."""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.header = QLabel(title.upper())
        self.header.setStyleSheet(
            "color: #58a6ff; font-size: 8pt; font-weight: bold; "
            "border: none; background: transparent;"
        )
        self.layout.addWidget(self.header)


class CyberButton(QPushButton):
    def __init__(self, text, accent="#00ffc8", parent=None):
        super().__init__(text, parent)
        self.accent = accent
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #161b22;
                color: {accent};
                border-radius: 2px;
                border: 1px solid #30363d;
                font-family: 'Segoe UI';
                font-size: 9pt;
                text-transform: uppercase;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {accent};
                background-color: #21262d;
            }}
            QPushButton:pressed {{
                background-color: #000000;
            }}
        """)

# ============================================================
# ENHANCED VISUALIZERS
# ============================================================
class SweepIndicator(QWidget):
    """A rhythmic pulse bar that reacts to the set BPM."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self.bpm = 120.0
        self.progress = 0.0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(20)

    def set_bpm(self, bpm_val: float):
        try:
            v = float(bpm_val)
            self.bpm = v if v > 0 else 120.0
        except Exception:
            self.bpm = 120.0

    def animate(self):
        bps = self.bpm / 60.0
        self.progress = (time.time() * bps) % 1.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(22, 27, 34))

        w = self.width()
        indicator_x = int(self.progress * w)
        grad = QLinearGradient(indicator_x - 100, 0, indicator_x, 0)
        grad.setColorAt(0, QColor(0, 0, 0, 0))
        grad.setColorAt(1, QColor(0, 255, 200))

        p.fillRect(0, 0, indicator_x, self.height(), grad)


class NeonWaveform(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.peaks = None
        self.playhead_pos = 0
        self.sr = 44100
        self.audio_len = 0
        self.setMinimumHeight(250)
        self.setMouseTracking(True)

        # Zoom + hint state
        self.zoom_active = False
        self.sel_start = 0
        self.sel_end = 0
        self.hint_opacity = 1.0

        self.hint_timer = QTimer()
        self.hint_timer.setInterval(40)
        self.hint_timer.timeout.connect(self.fade_hint)
        self.hint_timer.start()

    # ============================================================
    # ZOOM + TIME MARKERS + CYBER HINT OVERLAY
    # ============================================================
    def set_waveform(self, audio, sr):
        self.sr = sr
        self.audio_len = len(audio)

        samples = 2000
        step = max(1, len(audio) // samples)
        self.peaks = np.array([
            np.max(np.abs(audio[i:i + step]))
            for i in range(0, len(audio), step)
        ])
        self.total_peaks = len(self.peaks)

        # Reset zoom
        self.zoom_active = False
        self.sel_start = 0
        self.sel_end = self.total_peaks

        # Reset hint
        self.hint_opacity = 1.0

        self.update()

    def fade_hint(self):
        if self.hint_opacity > 0:
            self.hint_opacity -= 0.02
            self.update()

    def update_playhead(self, ms):
        if self.audio_len == 0:
            return

        total_ms = (self.audio_len / self.sr) * 1000
        ratio = ms / total_ms
        self.playhead_pos = ratio * self.width()
        self.update()

    def mousePressEvent(self, event):
        if self.peaks is None or len(self.peaks) == 0:
            return

        x = event.pos().x()

        # LEFT CLICK → SNAP PLAYHEAD
        if event.button() == Qt.MouseButton.LeftButton:
            total_ms = (self.audio_len / self.sr) * 1000
            ratio = x / max(self.width(), 1)
            ms = ratio * total_ms
            parent = self.parent()
            if parent and hasattr(parent, "snap_to_ms"):
                parent.snap_to_ms(ms)
            return

        # RIGHT CLICK → ZOOM TO REGION
        if event.button() == Qt.MouseButton.RightButton:
            if not self.zoom_active:
                self.zoom_active = True
                center = int((x / self.width()) * self.total_peaks)
                win = int(self.total_peaks * 0.15)
                self.sel_start = max(0, center - win // 2)
                self.sel_end = min(self.total_peaks, self.sel_start + win)
            else:
                # Reset zoom
                self.zoom_active = False
                self.sel_start = 0
                self.sel_end = self.total_peaks

            self.hint_opacity = 1.0
            self.update()

    def mouseMoveEvent(self, event):
        if self.zoom_active and self.peaks is not None:
            x = event.pos().x()
            center = int((x / self.width()) * self.total_peaks)
            win = int(self.total_peaks * 0.15)
            self.sel_start = max(0, center - win // 2)
            self.sel_end = min(self.total_peaks, self.sel_start + win)
            self.hint_opacity = 1.0
            self.update()

    def paintEvent(self, event):
        if self.peaks is None:
            return

        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(13, 17, 23))

        # Determine visible region
        start = self.sel_start if self.zoom_active else 0
        end = self.sel_end if self.zoom_active else self.total_peaks
        visible = self.peaks[start:end]

        # Draw waveform
        if len(visible) > 0:
            step = w / len(visible)
            p.setPen(QPen(QColor(0, 255, 200, 180), 1))
            for i, amp in enumerate(visible):
                x = int(i * step)
                line_h = int(amp * (h * 0.8))
                p.drawLine(x, h // 2 - line_h // 2, x, h // 2 + line_h // 2)

        # Time axis
        p.setPen(QPen(QColor(0, 255, 200, 80), 1))
        total_duration = self.audio_len / self.sr
        start_time = (start / self.total_peaks) * total_duration
        end_time = (end / self.total_peaks) * total_duration
        visible_duration = max(end_time - start_time, 1e-9)

        # ============================================================
        # SMART TICK SPACING (seconds, but spaced by pixel density)
        # ============================================================

        # Base tick step (seconds)
        if visible_duration > 120:
            tick_step = 10.0
        elif visible_duration > 60:
            tick_step = 5.0
        elif visible_duration > 20:
            tick_step = 2.0
        elif visible_duration > 10:
            tick_step = 1.0
        else:
            tick_step = 0.5

        # Minimum pixel spacing between labels
        MIN_LABEL_SPACING = 50
        last_label_x = -999

        t = np.ceil(start_time / tick_step) * tick_step
        while t <= end_time:
            rel = (t - start_time) / visible_duration
            tx = int(rel * w)

            # Only draw label if far enough from previous
            if tx - last_label_x >= MIN_LABEL_SPACING:
                p.drawLine(tx, h - 20, tx, h)
                p.setPen(QColor(200, 200, 200))
                p.drawText(tx + 2, h - 5, f"{t:.0f}s")
                p.setPen(QPen(QColor(0, 255, 200, 80), 1))
                last_label_x = tx

            t += tick_step

        # ============================================================
        # PLAYHEAD — ALWAYS VISIBLE
        # ============================================================
        playhead_x = int(self.playhead_pos)
        if 0 <= playhead_x <= w:
            p.setPen(QPen(Qt.GlobalColor.white, 2))
            p.drawLine(playhead_x, 0, playhead_x, h)

        # Hint overlay
        if self.hint_opacity > 0:
            p.setOpacity(self.hint_opacity)
            p.setPen(QColor(200, 200, 210))
            p.setFont(QFont("Segoe UI", 9))
            hint = "Left-click: Jump | Right-click: Zoom | Drag: Pan | Right-click again: Reset"
            tw = p.fontMetrics().horizontalAdvance(hint)
            p.drawText((w - tw) // 2, 20, hint)
            p.setOpacity(1.0)


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
            if y.ndim > 1:
                y = y.mean(axis=0)
            if len(y) < 2048:
                self.tempo_ready.emit(120.0)
                return
            onset_env = librosa.onset.onset_strength(y=y.astype(np.float32), sr=self.sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=self.sr, aggregate=None)

            if hasattr(tempo, "__len__"):
                val = float(tempo[0])
            else:
                val = float(tempo)
            self.tempo_ready.emit(val if val > 0 else 120.0)
        except Exception:
            self.tempo_ready.emit(120.0)


class ReverseWorker(QThread):
    finished = pyqtSignal(np.ndarray, str)

    def __init__(self, audio, sr, mode, tempo, grid_params, parent=None):
        super().__init__(parent)
        self.params = {
            "audio": audio,
            "sample_rate": sr,
            "mode": mode,
            "tempo": tempo,
            **grid_params,
        }

    def run(self):
        try:
            from core.hybrid.pipeline import process_audio
            processed = process_audio(**self.params)
            self.finished.emit(processed, self.params["mode"])
        except Exception as e:
            print("PIPELINE ERROR:", e)
            self.finished.emit(self.params["audio"], "ERROR_FALLBACK")

# ============================================================
# MAIN APPLICATION: "VIRTUAL STUDIO 3.2"
# ============================================================
class CyberReverseEngine(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AGI-aiPilotGEM // REVERSE ENGINE v3.2")
        self.resize(1200, 850)

        # Shared Audio State
        self.original_audio = None
        self.current_audio = None
        self.sr = 44100
        self.stream = None
        self.play_idx = 0
        self.temp_dir = tempfile.mkdtemp()

        # Metronome
        self.click_enabled = False
        self.click_timer = QTimer()
        self.click_timer.timeout.connect(self.play_click)
        t = np.linspace(0, 0.03, int(44100 * 0.03))
        self.click_buffer = (np.sin(2 * np.pi * 1000 * t) * 0.1).astype(np.float32)

        # Playback timer
        self.play_timer = QTimer()
        self.play_timer.timeout.connect(self.sync_ui)

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # --- ROW 1: FILE OPERATIONS POD ---
        file_pod = ControlPod("Source Input")
        file_layout = QHBoxLayout()
        self.load_btn = CyberButton("Import Wave", "#58a6ff")
        self.load_btn.clicked.connect(self.load_file)
        self.file_path_display = QLineEdit("NO_FILE_LOADED")
        self.file_path_display.setReadOnly(True)
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.file_path_display, 1)
        file_pod.layout.addLayout(file_layout)
        main_layout.addWidget(file_pod)

        # --- ROW 2: CENTER WORKSPACE ---
        center_layout = QHBoxLayout()

        # Visualization
        vis_layout = QVBoxLayout()
        self.sweep = SweepIndicator()
        self.waveform = NeonWaveform()
        vis_layout.addWidget(self.sweep)
        vis_layout.addWidget(self.waveform, 1)
        center_layout.addLayout(vis_layout, 3)

        # Grid Logic Pod
        math_pod = ControlPod("Grid Logic")
        math_pod.setFixedWidth(280)
        m_grid = QGridLayout()
        m_grid.setHorizontalSpacing(1)

        # ============================================================
        # BPM STRIP — unified look with ½ and 2× buttons
        # ============================================================
        m_grid.addWidget(QLabel("BPM:"), 0, 0)

        total_width = 180  # keep your existing width

        bpm_container = QWidget()
        bpm_container.setFixedWidth(total_width)
        bpm_container_layout = QHBoxLayout(bpm_container)
        bpm_container_layout.setContentsMargins(0, 0, 0, 0)
        bpm_container_layout.setSpacing(0)

        # BPM textbox styled like the buttons
        self.bpm_in = QLineEdit("120")
        self.bpm_in.setFixedSize(total_width - 80, 30)  # 100px BPM + 40 + 40 buttons
        self.bpm_in.editingFinished.connect(self.refresh_metronome_bpm)
        self.bpm_in.setStyleSheet("""
            QLineEdit {
                background-color: #161b22;
                color: #79c0ff;
                border: 1px solid #30363d;
                border-right: none;
                border-radius: 0px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
                padding-left: 6px;
            }
        """)

        # ½ button
        self.half_btn = CyberButton("½", "#79c0ff")
        self.half_btn.setFixedSize(40, 30)
        self.half_btn.clicked.connect(self.half_bpm)
        self.half_btn.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #79c0ff;
                border: 1px solid #30363d;
                border-left: none;
                border-right: none;
                border-radius: 0px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #79c0ff;
                background-color: #21262d;
            }
        """)

        # 2× button
        self.double_btn = CyberButton("2×", "#79c0ff")
        self.double_btn.setFixedSize(40, 30)
        self.double_btn.clicked.connect(self.double_bpm)
        self.double_btn.setStyleSheet("""
            QPushButton {
                background-color: #161b22;
                color: #79c0ff;
                border: 1px solid #30363d;
                border-left: none;
                border-radius: 0px;
                font-family: 'Segoe UI';
                font-size: 9pt;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #79c0ff;
                background-color: #21262d;
            }
        """)

        bpm_container_layout.addWidget(self.bpm_in)
        bpm_container_layout.addWidget(self.half_btn)
        bpm_container_layout.addWidget(self.double_btn)

        m_grid.addWidget(bpm_container, 0, 1)

        # ============================================================
        # BARS / BEATS / TATUM — exact same width as BPM strip
        # ============================================================

        m_grid.addWidget(QLabel("BARS:"), 1, 0)
        self.bars_in = QLineEdit("1")
        self.bars_in.setFixedWidth(total_width)
        m_grid.addWidget(self.bars_in, 1, 1)

        m_grid.addWidget(QLabel("BEATS:"), 2, 0)
        self.beats_in = QLineEdit("4")
        self.beats_in.setFixedWidth(total_width)
        m_grid.addWidget(self.beats_in, 2, 1)

        m_grid.addWidget(QLabel("TATUM:"), 3, 0)
        self.tatum_in = QLineEdit("16")
        self.tatum_in.setFixedWidth(total_width)
        m_grid.addWidget(self.tatum_in, 3, 1)

        math_pod.layout.addLayout(m_grid)

        # Metronome toggle
        self.metro_btn = CyberButton("Metronome: OFF", "#00ffc8")
        self.metro_btn.clicked.connect(self.toggle_metronome)
        math_pod.layout.addWidget(self.metro_btn)

        math_pod.layout.addStretch()

        self.reset_btn = CyberButton("Clear Buffer", "#ff6b8b")
        self.reset_btn.clicked.connect(self.reset_audio)
        math_pod.layout.addWidget(self.reset_btn)

        center_layout.addWidget(math_pod)
        main_layout.addLayout(center_layout)

        # --- ROW 3: EXTRACTION MODES ---
        mode_pod = ControlPod("Extraction Algorithms")
        modes_layout = QHBoxLayout()

        btn_true = CyberButton("Standard Rev", "#d2a8ff")
        btn_hq = CyberButton("High Fidelity", "#00ffc8")
        btn_tatum = CyberButton("Tatum Logic", "#ff7b72")
        btn_studio = CyberButton("Studio Shuf", "#79c0ff")

        btn_true.clicked.connect(lambda: self.trigger_process("TRUE_REVERSE"))
        btn_hq.clicked.connect(lambda: self.trigger_process("HQ_REVERSE"))
        btn_tatum.clicked.connect(lambda: self.trigger_process("TATUM_REVERSE"))
        btn_studio.clicked.connect(lambda: self.trigger_process("STUDIO_MODE"))

        modes_layout.addWidget(btn_true)
        modes_layout.addWidget(btn_hq)
        modes_layout.addWidget(btn_tatum)
        modes_layout.addWidget(btn_studio)
        mode_pod.layout.addLayout(modes_layout)
        main_layout.addWidget(mode_pod)

        # --- ROW 4: TRANSPORT & LOGS ---
        bottom_layout = QHBoxLayout()

        transport_pod = ControlPod("Master Transport")
        t_layout = QHBoxLayout()
        self.play_btn = CyberButton("Initialize Playback", "#afff33")
        self.play_btn.clicked.connect(self.toggle_play)
        self.save_btn = CyberButton("Export Master", "#f2f2f2")
        self.save_btn.clicked.connect(self.save_file)
        t_layout.addWidget(self.play_btn)
        t_layout.addWidget(self.save_btn)
        transport_pod.layout.addLayout(t_layout)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(100)

        bottom_layout.addWidget(transport_pod, 1)
        bottom_layout.addWidget(self.log, 1)
        main_layout.addLayout(bottom_layout)

    def apply_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #010409;
                color: #c9d1d9;
                font-family: 'Consolas', 'Courier New';
            }
            QLabel { font-size: 8pt; color: #8b949e; }
            QLineEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                color: #58a6ff;
                padding: 4px;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                color: #d2a8ff;
                font-size: 8pt;
            }
        """)

    # --------------------------------------------------------
    # BPM CONTROL HELPERS
    # --------------------------------------------------------
    def refresh_metronome_bpm(self):
        """Refresh metronome interval when BPM changes."""
        self.log.append(f"[BPM] Updated → {self.bpm_in.text()}")

        if not self.click_enabled:
            return
        try:
            bpm = float(self.bpm_in.text())
            interval = int(60000 / max(bpm, 1.0))
            self.click_timer.start(interval)
            self.sweep.set_bpm(bpm)
            self.log.append(f"[METRO] BPM updated → {bpm:.2f}")
        except Exception:
            self.log.append("[METRO] Invalid BPM; cannot refresh.")

    def half_bpm(self):
        """Halve the BPM value."""
        try:
            bpm = float(self.bpm_in.text())
            bpm = max(bpm / 2, 1.0)
            self.bpm_in.setText(f"{bpm:.2f}")
            self.refresh_metronome_bpm()
            self.log.append(f"[BPM] Halved → {bpm:.2f}")
        except ValueError:
            self.log.append("[ERROR] Invalid BPM; cannot halve.")

    def double_bpm(self):
        """Double the BPM value."""
        try:
            bpm = float(self.bpm_in.text())
            bpm = min(bpm * 2, 999.0)
            self.bpm_in.setFixedWidth(60)

            self.refresh_metronome_bpm()
            self.log.append(f"[BPM] Doubled → {bpm:.2f}")
        except ValueError:
            self.log.append("[ERROR] Invalid BPM; cannot double.")

    # --------------------------------------------------------
    # FUNCTIONALITY
    # --------------------------------------------------------
    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio", "", "Audio (*.wav *.mp3 *.flac)"
        )
        if not path:
            return
        y, sr = librosa.load(path, sr=None, mono=False)
        self.original_audio = y.T if y.ndim > 1 else y
        self.current_audio = self.original_audio.copy()
        self.sr = sr
        self.file_path_display.setText(os.path.basename(path))

        vis = y.mean(axis=0) if y.ndim > 1 else y
        self.waveform.set_waveform(vis, sr)
        self.log.append(f"[INIT] Loaded {path}")

        # Optional: auto tempo detection
        self.log.append("[ENGINE] Detecting BPM…")
        self.tempo_worker = TempoWorker(y, sr)
        self.tempo_worker.tempo_ready.connect(self.on_tempo_detected)
        self.tempo_worker.start()

    def on_tempo_detected(self, bpm):
        self.bpm_in.setText(f"{bpm:.2f}")
        self.sweep.set_bpm(bpm)
        self.log.append(f"[ENGINE] Detected BPM: {bpm:.2f}")

    def trigger_process(self, mode):
        if self.current_audio is None:
            self.log.append("[WARN] No buffer loaded.")
            return

        try:
            tempo = float(self.bpm_in.text())
            bars = int(self.bars_in.text())
            beats = int(self.beats_in.text())
            tatum = int(self.tatum_in.text())
        except ValueError:
            self.log.append("[ERROR] Invalid grid or tempo values.")
            return

        grid_params = {
            "bars_per_slice": bars,
            "beats_per_bar": beats,
            "tatum_fraction": tatum,
        }

        self.log.append(
            f"[COMPUTE] {mode} | BPM={tempo:.2f} | bars={bars}, beats={beats}, tatum={tatum}"
        )

        self.rev_worker = ReverseWorker(
            self.current_audio, self.sr, mode, tempo, grid_params
        )
        self.rev_worker.finished.connect(self.on_rev_done)
        self.rev_worker.start()

    def on_rev_done(self, audio, mode):
        self.current_audio = audio
        vis = audio.T.mean(axis=0) if audio.ndim > 1 else audio
        self.waveform.set_waveform(vis, self.sr)
        if mode == "ERROR_FALLBACK":
            self.log.append("[FAIL] DSP pipeline failed, fallback buffer used.")
        else:
            self.log.append(f"[DONE] {mode} Applied.")

    # --------------------------------------------------------
    # METRONOME
    # --------------------------------------------------------
    def toggle_metronome(self):
        self.click_enabled = not self.click_enabled
        if self.click_enabled:
            try:
                bpm = float(self.bpm_in.text())
                interval = int(60000 / max(bpm, 1.0))
                self.click_timer.start(interval)
                self.metro_btn.setText("Metronome: ON")
                self.log.append(f"[METRO] ON @ {bpm:.2f} BPM")
            except Exception:
                self.log.append("[METRO] Invalid BPM; metronome disabled.")
                self.click_enabled = False
                self.metro_btn.setText("Metronome: OFF")
        else:
            self.click_timer.stop()
            self.metro_btn.setText("Metronome: OFF")
            self.log.append("[METRO] OFF")

    def play_click(self):
        sd.play(self.click_buffer, 44100)

    # --------------------------------------------------------
    # PLAYBACK
    # --------------------------------------------------------
    def toggle_play(self):
        # --- STOP PLAYBACK ---
        if self.stream is not None and self.stream.active:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass

            self.stream = None
            self.play_timer.stop()

            # Auto-stop sweep indicator
            self.sweep.timer.stop()
            self.sweep.progress = 0.0
            self.sweep.update()

            self.play_btn.setText("Initialize Playback")
            return

        # --- START PLAYBACK ---
        if self.current_audio is None:
            return

        self.play_idx = 0
        audio = self.current_audio

        # Determine channel count
        chs = 1 if audio.ndim == 1 else audio.shape[1]

        # Start audio stream
        self.stream = sd.OutputStream(
            samplerate=self.sr,
            channels=chs,
            callback=self.audio_callback,
        )
        self.stream.start()

        # UI sync timer
        self.play_timer.start(30)

        # Auto-start sweep indicator with BPM
        try:
            bpm = float(self.bpm_in.text())
            self.sweep.set_bpm(bpm)
        except Exception:
            pass
        self.sweep.timer.start()

        self.play_btn.setText("Cease Playback")


    def audio_callback(self, outdata, frames, time_info, status):
        audio = self.current_audio
        n = len(audio)

        start = self.play_idx
        end = min(start + frames, n)

        # MONO
        if audio.ndim == 1:
            chunk = audio[start:end]
            if len(chunk) < frames:
                outdata[:len(chunk), 0] = chunk
                outdata[len(chunk):].fill(0)
                self.play_idx = 0
                raise sd.CallbackStop()
            else:
                outdata[:, 0] = chunk
                if outdata.shape[1] > 1:
                    outdata[:, 1:] = 0
                self.play_idx = end

        # MULTICHANNEL
        else:
            chunk = audio[start:end, :]
            if len(chunk) < frames:
                outdata[:len(chunk)] = chunk
                outdata[len(chunk):].fill(0)
                self.play_idx = 0
                raise sd.CallbackStop()
            else:
                outdata[:] = chunk
                self.play_idx = end


    def sync_ui(self):
        # Auto-reset when playback ends naturally
        if self.stream is not None and not self.stream.active:
            self.play_btn.setText("Initialize Playback")
            self.sweep.timer.stop()
            self.sweep.progress = 0.0
            self.sweep.update()
            return

        # Normal UI updates while playing
        if self.current_audio is None or self.sr <= 0:
            return

        # Update waveform playhead
        ms = (self.play_idx / self.sr) * 1000.0
        self.waveform.update_playhead(ms)

        # Keep sweep BPM synced
        try:
            bpm = float(self.bpm_in.text())
            self.sweep.set_bpm(bpm)
        except Exception:
            pass


    def snap_to_ms(self, ms):
        """Called by NeonWaveform on click to snap playback and playhead."""
        if self.current_audio is None or self.sr <= 0:
            return

        # Clamp MS
        total_ms = (len(self.current_audio) / self.sr) * 1000.0
        ms = max(0.0, min(total_ms, ms))

        # Convert ms → sample index
        sample_pos = int((ms / 1000.0) * self.sr)
        self.play_idx = max(0, min(sample_pos, len(self.current_audio) - 1))

        # Update waveform playhead
        self.waveform.update_playhead(ms)

        # Keep sweep synced if playing
        if self.stream is not None and self.stream.active:
            try:
                bpm = float(self.bpm_in.text())
                self.sweep.set_bpm(bpm)
            except Exception:
                pass
            if not self.sweep.timer.isActive():
                self.sweep.timer.start()
        else:
            # Freeze sweep when not playing
            self.sweep.timer.stop()
            self.sweep.progress = 0.0
            self.sweep.update()

        self.log.append(f"[NAV] Snapped to {ms/1000.0:.2f}s")


    # --------------------------------------------------------
    # BUFFER + SAVE
    # --------------------------------------------------------
    def reset_audio(self):
        if self.original_audio is not None:
            self.current_audio = self.original_audio.copy()
            vis = (
                self.current_audio.T.mean(axis=0)
                if self.current_audio.ndim > 1
                else self.current_audio
            )
            self.waveform.set_waveform(vis, self.sr)
            self.log.append("[MIX] Buffer Purged to Original.")

    def save_file(self):
        if self.current_audio is None:
            self.log.append("[SAVE] No buffer to export.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export",
            "",
            "WAV (*.wav);;MP3 (*.mp3);;FLAC (*.flac)",
        )
        if not path:
            return

        try:
            sf.write(path, self.current_audio, self.sr)
            self.log.append(f"[SAVE] Exported to {path}")
        except Exception as e:
            self.log.append(f"[ERROR] Export failed: {e}")

    def closeEvent(self, event):
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
        except Exception:
            pass

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        event.accept()


# --------------------------------------------------------
# MAIN ENTRY POINT
# --------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CyberReverseEngine()
    window.show()
    sys.exit(app.exec())
