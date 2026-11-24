import sys
from PyQt5.QtCore import QPointF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class HourglassCanvas(QWidget):
    """Custom widget rendering an animated sand timer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ratio = 1.0  # 1.0 = full top bulb, 0.0 = empty top bulb
        self.running = False
        self.tick_phase = 0
        self.setMinimumSize(260, 320)

    def set_state(self, ratio: float, running: bool, tick_phase: int = 0):
        self.ratio = max(0.0, min(1.0, ratio))
        self.running = running
        self.tick_phase = tick_phase
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        bulb_w = min(w * 0.62, 190.0)
        bulb_h = min(h * 0.36, 125.0)
        neck_half = 5.0
        half_w = bulb_w / 2.0

        top_y = cy - bulb_h
        bot_y = cy + bulb_h

        # Glass paths (top and bottom chambers)
        top_glass = QPainterPath()
        top_glass.moveTo(cx - half_w, top_y)
        top_glass.lineTo(cx + half_w, top_y)
        top_glass.lineTo(cx + neck_half, cy)
        top_glass.lineTo(cx - neck_half, cy)
        top_glass.closeSubpath()

        bot_glass = QPainterPath()
        bot_glass.moveTo(cx - neck_half, cy)
        bot_glass.lineTo(cx + neck_half, cy)
        bot_glass.lineTo(cx + half_w, bot_y)
        bot_glass.lineTo(cx - half_w, bot_y)
        bot_glass.closeSubpath()

        # Subtle glass fill
        glass_fill = QColor(30, 41, 59, 170)
        painter.fillPath(top_glass, glass_fill)
        painter.fillPath(bot_glass, glass_fill)

        sand_color = QColor("#f59e0b")
        sand_highlight = QColor("#fbbf24")

        # 1. Top sand (drains downward as ratio decreases)
        if self.ratio > 0.002:
            painter.save()
            painter.setClipPath(top_glass)
            sand_h = bulb_h * (self.ratio ** 0.72)
            sand_top_y = cy - sand_h
            dip = 6.0 * (1.0 - self.ratio)
            top_sand_poly = QPolygonF(
                [
                    QPointF(cx - half_w, sand_top_y),
                    QPointF(cx, sand_top_y + dip),
                    QPointF(cx + half_w, sand_top_y),
                    QPointF(cx + half_w, cy),
                    QPointF(cx - half_w, cy),
                ]
            )
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(sand_color))
            painter.drawPolygon(top_sand_poly)
            painter.restore()

        # 2. Bottom sand mound (grows upward as 1 - ratio increases)
        bottom_fill = 1.0 - self.ratio
        if bottom_fill > 0.002:
            painter.save()
            painter.setClipPath(bot_glass)
            mound_h = bulb_h * (bottom_fill ** 0.72)
            mound_base_y = bot_y - mound_h
            peak_y = max(cy + 4.0, mound_base_y - 16.0 * min(1.0, bottom_fill * 2.0))
            bot_sand_poly = QPolygonF(
                [
                    QPointF(cx - half_w, bot_y),
                    QPointF(cx - half_w, mound_base_y),
                    QPointF(cx, peak_y),
                    QPointF(cx + half_w, mound_base_y),
                    QPointF(cx + half_w, bot_y),
                ]
            )
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(sand_color))
            painter.drawPolygon(bot_sand_poly)
            painter.restore()

        # 3. Falling sand stream when running and sand remains
        if self.running and self.ratio > 0.002:
            stream_pen = QPen(sand_highlight, 2.5)
            painter.setPen(stream_pen)
            painter.drawLine(QPointF(cx, cy), QPointF(cx, bot_y - 2.0))

            # Animated falling grain dots
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#fde68a")))
            for offset in range(0, int(bulb_h), 18):
                grain_y = cy + ((offset + self.tick_phase * 5) % max(1, int(bulb_h - 4)))
                painter.drawEllipse(QPointF(cx, grain_y), 1.8, 1.8)

        # Glass outline
        outline_pen = QPen(QColor("#94a3b8"), 2.5)
        painter.setPen(outline_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(top_glass)
        painter.drawPath(bot_glass)

        # Top & bottom caps
        cap_w = bulb_w + 26.0
        cap_h = 10.0
        cap_brush = QBrush(QColor("#38bdf8"))
        painter.setPen(Qt.NoPen)
        painter.setBrush(cap_brush)
        painter.drawRoundedRect(
            int(cx - cap_w / 2.0), int(top_y - cap_h), int(cap_w), int(cap_h), 5, 5
        )
        painter.drawRoundedRect(
            int(cx - cap_w / 2.0), int(bot_y), int(cap_w), int(cap_h), 5, 5
        )


class HourglassApp(QWidget):
    def __init__(self):
        super().__init__()
        self.total_ms = 5 * 60 * 1000
        self.remaining_ms = self.total_ms
        self.running = False
        self.tick_phase = 0

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.on_tick)

        self.init_ui()
        self.sync_view()

    def init_ui(self):
        self.setWindowTitle("Hourglass — Sand Timer")
        self.resize(440, 620)

        root = QVBoxLayout()
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Hourglass")
        title.setObjectName("title_label")

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status_label")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.status_label)

        # Animated canvas
        self.canvas = HourglassCanvas()

        # Digital readout
        self.time_label = QLabel("05:00")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setObjectName("time_label")

        # Quick presets
        preset_row = QHBoxLayout()
        for label, mins in [("1m", 1), ("5m", 5), ("15m", 15), ("25m", 25)]:
            btn = QPushButton(label)
            btn.setObjectName("preset_btn")
            btn.clicked.connect(lambda _, m=mins: self.set_duration(m, 0))
            preset_row.addWidget(btn)

        # Custom duration row
        custom_row = QHBoxLayout()
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 180)
        self.min_spin.setValue(5)
        self.min_spin.setSuffix(" min")

        self.sec_spin = QSpinBox()
        self.sec_spin.setRange(0, 59)
        self.sec_spin.setValue(0)
        self.sec_spin.setSuffix(" sec")

        self.apply_btn = QPushButton("Set")
        self.apply_btn.setObjectName("neutral_btn")
        self.apply_btn.clicked.connect(self.apply_custom_time)

        custom_row.addWidget(self.min_spin, stretch=1)
        custom_row.addWidget(self.sec_spin, stretch=1)
        custom_row.addWidget(self.apply_btn)

        # Primary controls
        ctrl_row = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("primary_btn")
        self.start_btn.clicked.connect(self.toggle_timer)

        self.flip_btn = QPushButton("Flip")
        self.flip_btn.setObjectName("secondary_btn")
        self.flip_btn.clicked.connect(self.flip_hourglass)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setObjectName("danger_btn")
        self.reset_btn.clicked.connect(self.reset_timer)

        ctrl_row.addWidget(self.start_btn, stretch=2)
        ctrl_row.addWidget(self.flip_btn, stretch=1)
        ctrl_row.addWidget(self.reset_btn, stretch=1)

        root.addLayout(header)
        root.addWidget(self.canvas, stretch=1)
        root.addWidget(self.time_label)
        root.addLayout(preset_row)
        root.addLayout(custom_row)
        root.addLayout(ctrl_row)

        self.setLayout(root)
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #0b1120;
                color: #e2e8f0;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 14px;
            }
            QLabel#title_label {
                font-size: 24px;
                font-weight: bold;
                color: #38bdf8;
            }
            QLabel#status_label {
                color: #94a3b8;
                font-weight: bold;
            }
            QLabel#time_label {
                font-size: 36px;
                font-weight: bold;
                color: #f8fafc;
                letter-spacing: 2px;
            }
            QSpinBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                color: #f8fafc;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 9px 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton#primary_btn {
                background-color: #0284c7;
            }
            QPushButton#primary_btn:hover {
                background-color: #0369a1;
            }
            QPushButton#secondary_btn {
                background-color: #0d9488;
            }
            QPushButton#secondary_btn:hover {
                background-color: #0f766e;
            }
            QPushButton#danger_btn {
                background-color: #b91c1c;
            }
            QPushButton#danger_btn:hover {
                background-color: #991b1b;
            }
            QPushButton#preset_btn, QPushButton#neutral_btn {
                background-color: #1e293b;
                border: 1px solid #334155;
                color: #e2e8f0;
            }
            QPushButton#preset_btn:hover, QPushButton#neutral_btn:hover {
                background-color: #334155;
            }
            """
        )

    def set_duration(self, minutes: int, seconds: int):
        total = (minutes * 60 + seconds) * 1000
        if total <= 0:
            self.status_label.setText("Set > 0s")
            return
        self.timer.stop()
        self.running = False
        self.total_ms = total
        self.remaining_ms = total
        self.min_spin.setValue(minutes)
        self.sec_spin.setValue(seconds)
        self.start_btn.setText("Start")
        self.status_label.setText("Ready")
        self.sync_view()

    def apply_custom_time(self):
        self.set_duration(self.min_spin.value(), self.sec_spin.value())

    def toggle_timer(self):
        if self.remaining_ms <= 0:
            self.remaining_ms = self.total_ms

        if self.running:
            self.timer.stop()
            self.running = False
            self.start_btn.setText("Resume")
            self.status_label.setText("Paused")
        else:
            self.running = True
            self.timer.start()
            self.start_btn.setText("Pause")
            self.status_label.setText("Running")
        self.sync_view()

    def flip_hourglass(self):
        elapsed_ms = self.total_ms - self.remaining_ms
        if elapsed_ms <= 0:
            return
        self.remaining_ms = elapsed_ms
        self.status_label.setText("Flipped")
        self.sync_view()

    def reset_timer(self):
        self.timer.stop()
        self.running = False
        self.remaining_ms = self.total_ms
        self.start_btn.setText("Start")
        self.status_label.setText("Ready")
        self.sync_view()

    def on_tick(self):
        self.remaining_ms = max(0, self.remaining_ms - self.timer.interval())
        self.tick_phase = (self.tick_phase + 1) % 100

        if self.remaining_ms == 0:
            self.timer.stop()
            self.running = False
            self.start_btn.setText("Start")
            self.status_label.setText("Time's up!")
            QApplication.beep()

        self.sync_view()

    def sync_view(self):
        total_secs = (self.remaining_ms + 999) // 1000
        mins, secs = divmod(total_secs, 60)
        self.time_label.setText(f"{mins:02d}:{secs:02d}")
        ratio = (self.remaining_ms / self.total_ms) if self.total_ms > 0 else 0.0
        self.canvas.set_state(ratio, self.running, self.tick_phase)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HourglassApp()
    window.show()
    sys.exit(app.exec_())