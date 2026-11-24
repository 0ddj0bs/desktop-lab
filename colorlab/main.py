import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ColorLabApp(QWidget):
    def __init__(self):
        super().__init__()
        self.updating = False
        self.current_color = QColor("#38bdf8")
        self.init_ui()
        self.sync_from_color(self.current_color)

    def init_ui(self):
        self.setWindowTitle("ColorLab — HEX & RGB Converter")
        self.resize(500, 440)

        root = QVBoxLayout()
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Header
        top_bar = QHBoxLayout()
        title = QLabel("ColorLab")
        title.setObjectName("title_label")

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("status_label")

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.status_label)

        # Live swatch + picker button
        swatch_row = QHBoxLayout()
        self.swatch = QFrame()
        self.swatch.setObjectName("swatch")
        self.swatch.setMinimumHeight(90)

        self.pick_btn = QPushButton("Pick Color")
        self.pick_btn.setObjectName("neutral_btn")
        self.pick_btn.clicked.connect(self.open_color_picker)

        swatch_row.addWidget(self.swatch, stretch=1)
        swatch_row.addWidget(self.pick_btn)

        # HEX row
        hex_row = QHBoxLayout()
        hex_label = QLabel("HEX:")
        hex_label.setMinimumWidth(55)

        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("#38bdf8")
        self.hex_input.textChanged.connect(self.on_hex_changed)

        self.copy_hex_btn = QPushButton("Copy HEX")
        self.copy_hex_btn.setObjectName("primary_btn")
        self.copy_hex_btn.clicked.connect(self.copy_hex)

        hex_row.addWidget(hex_label)
        hex_row.addWidget(self.hex_input, stretch=1)
        hex_row.addWidget(self.copy_hex_btn)

        # RGB output + Copy RGB row
        rgb_summary_row = QHBoxLayout()
        rgb_label = QLabel("RGB:")
        rgb_label.setMinimumWidth(55)

        self.rgb_value_label = QLabel("rgb(56, 189, 248)")
        self.rgb_value_label.setObjectName("rgb_label")

        self.copy_rgb_btn = QPushButton("Copy RGB")
        self.copy_rgb_btn.setObjectName("secondary_btn")
        self.copy_rgb_btn.clicked.connect(self.copy_rgb)

        rgb_summary_row.addWidget(rgb_label)
        rgb_summary_row.addWidget(self.rgb_value_label, stretch=1)
        rgb_summary_row.addWidget(self.copy_rgb_btn)

        root.addLayout(top_bar)
        root.addLayout(swatch_row)
        root.addLayout(hex_row)
        root.addLayout(rgb_summary_row)

        # R, G, B sliders & spinboxes
        self.sliders = {}
        self.spins = {}
        for channel in ("R", "G", "B"):
            row = QHBoxLayout()
            lbl = QLabel(f"{channel}:")
            lbl.setMinimumWidth(55)

            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)

            spin = QSpinBox()
            spin.setRange(0, 255)

            slider.valueChanged.connect(lambda val, ch=channel: self.on_channel_changed(ch, val))
            spin.valueChanged.connect(lambda val, ch=channel: self.on_channel_changed(ch, val))

            self.sliders[channel] = slider
            self.spins[channel] = spin

            row.addWidget(lbl)
            row.addWidget(slider, stretch=1)
            row.addWidget(spin)
            root.addLayout(row)

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
                color: #4ade80;
                font-weight: bold;
            }
            QLabel#rgb_label {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                color: #f8fafc;
            }
            QLineEdit, QSpinBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                color: #f8fafc;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
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
            QPushButton#neutral_btn {
                background-color: #334155;
            }
            QPushButton#neutral_btn:hover {
                background-color: #475569;
            }
            """
        )

    def sync_from_color(self, color: QColor):
        self.updating = True
        self.current_color = color
        hex_str = color.name().lower()
        r, g, b = color.red(), color.green(), color.blue()

        if self.hex_input.text().strip().lower() != hex_str:
            self.hex_input.setText(hex_str)

        for ch, val in (("R", r), ("G", g), ("B", b)):
            self.sliders[ch].setValue(val)
            self.spins[ch].setValue(val)

        self.rgb_value_label.setText(f"rgb({r}, {g}, {b})")
        self.swatch.setStyleSheet(
            f"background-color: {hex_str}; border: 1px solid #334155; border-radius: 8px;"
        )
        self.updating = False

    def on_hex_changed(self, text: str):
        if self.updating:
            return
        cleaned = text.strip()
        if not cleaned.startswith("#"):
            cleaned = f"#{cleaned}"
        color = QColor(cleaned)
        if color.isValid() and len(cleaned) == 7:
            self.sync_from_color(color)
            self.status_label.setText("Synced")

    def on_channel_changed(self, channel: str, value: int):
        if self.updating:
            return
        r = value if channel == "R" else self.spins["R"].value()
        g = value if channel == "G" else self.spins["G"].value()
        b = value if channel == "B" else self.spins["B"].value()
        self.sync_from_color(QColor(r, g, b))
        self.status_label.setText("Synced")

    def open_color_picker(self):
        chosen = QColorDialog.getColor(self.current_color, self, "Pick a Color")
        if chosen.isValid():
            self.sync_from_color(chosen)
            self.status_label.setText("Picked")

    def copy_hex(self):
        val = self.current_color.name().lower()
        QApplication.clipboard().setText(val)
        self.status_label.setText(f"Copied {val}")

    def copy_rgb(self):
        c = self.current_color
        val = f"rgb({c.red()}, {c.green()}, {c.blue()})"
        QApplication.clipboard().setText(val)
        self.status_label.setText(f"Copied {val}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorLabApp()
    window.show()
    sys.exit(app.exec_())
