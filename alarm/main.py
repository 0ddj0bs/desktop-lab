import sys
from datetime import datetime, timedelta

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

try:
    import winsound
except ImportError:
    winsound = None


class AlarmApp(QWidget):
    def __init__(self):
        super().__init__()
        # Each alarm: {"hour": int, "minute": int, "label": str, "enabled": bool, "triggered_key": str | None}
        self.alarms = []
        self.ringing_alarm = None

        self.clock_timer = QTimer(self)
        self.clock_timer.setInterval(500)
        self.clock_timer.timeout.connect(self.on_tick)

        self.sound_timer = QTimer(self)
        self.sound_timer.setInterval(900)
        self.sound_timer.timeout.connect(self.play_chime)
        self.chime_step = 0

        self.init_ui()
        self.on_tick()
        self.clock_timer.start()

    def init_ui(self):
        self.setWindowTitle("Alarm — Desktop Alarm Clock")
        self.resize(480, 560)

        root = QVBoxLayout()
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        # Header + live clock
        top = QHBoxLayout()
        title = QLabel("Alarm")
        title.setObjectName("title_label")

        self.now_label = QLabel("00:00:00")
        self.now_label.setObjectName("now_label")

        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.now_label)

        # Active ringing banner (hidden until an alarm pops off)
        self.alert_box = QWidget()
        self.alert_box.setObjectName("alert_box")
        self.alert_box.hide()
        alert_layout = QHBoxLayout(self.alert_box)
        alert_layout.setContentsMargins(12, 10, 12, 10)

        self.alert_label = QLabel("ALARM RINGING")
        self.alert_label.setObjectName("alert_label")

        self.snooze_btn = QPushButton("Snooze 5m")
        self.snooze_btn.setObjectName("secondary_btn")
        self.snooze_btn.clicked.connect(self.snooze_alarm)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("danger_btn")
        self.stop_btn.clicked.connect(self.stop_ringing)

        alert_layout.addWidget(self.alert_label, stretch=1)
        alert_layout.addWidget(self.snooze_btn)
        alert_layout.addWidget(self.stop_btn)

        # Add alarm controls
        add_row = QHBoxLayout()
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setDisplayIntegerBase(10)
        self.hour_spin.setPrefix("HH ")
        now = datetime.now()
        next_min = (now + timedelta(minutes=1))
        self.hour_spin.setValue(next_min.hour)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 59)
        self.min_spin.setPrefix("MM ")
        self.min_spin.setValue(next_min.minute)

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Label (optional)")

        self.add_btn = QPushButton("Add")
        self.add_btn.setObjectName("primary_btn")
        self.add_btn.clicked.connect(self.add_alarm)

        add_row.addWidget(self.hour_spin)
        add_row.addWidget(self.min_spin)
        add_row.addWidget(self.label_input, stretch=1)
        add_row.addWidget(self.add_btn)

        # Alarms list
        self.alarm_list = QListWidget()
        self.alarm_list.itemDoubleClicked.connect(self.toggle_selected_alarm)

        # List action buttons
        list_actions = QHBoxLayout()
        self.toggle_btn = QPushButton("Toggle On/Off")
        self.toggle_btn.setObjectName("neutral_btn")
        self.toggle_btn.clicked.connect(self.toggle_selected_alarm)

        self.test_sound_btn = QPushButton("Test Sound")
        self.test_sound_btn.setObjectName("neutral_btn")
        self.test_sound_btn.clicked.connect(self.test_sound)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("danger_btn")
        self.delete_btn.clicked.connect(self.delete_selected_alarm)

        list_actions.addWidget(self.toggle_btn)
        list_actions.addWidget(self.test_sound_btn)
        list_actions.addWidget(self.delete_btn)

        root.addLayout(top)
        root.addWidget(self.alert_box)
        root.addLayout(add_row)
        root.addWidget(self.alarm_list, stretch=1)
        root.addLayout(list_actions)

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
            QLabel#now_label {
                font-size: 22px;
                font-weight: bold;
                color: #f8fafc;
            }
            QWidget#alert_box {
                background-color: #450a0a;
                border: 2px solid #ef4444;
                border-radius: 8px;
            }
            QLabel#alert_label {
                color: #fecaca;
                font-weight: bold;
                font-size: 15px;
            }
            QSpinBox, QLineEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                color: #f8fafc;
            }
            QListWidget {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 6px;
                color: #f8fafc;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #334155;
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
            QPushButton#danger_btn {
                background-color: #b91c1c;
            }
            QPushButton#danger_btn:hover {
                background-color: #991b1b;
            }
            QPushButton#neutral_btn {
                background-color: #334155;
            }
            QPushButton#neutral_btn:hover {
                background-color: #475569;
            }
            """
        )

    def refresh_list(self):
        current_row = self.alarm_list.currentRow()
        self.alarm_list.clear()
        for a in self.alarms:
            state = "ON" if a["enabled"] else "OFF"
            tag = f" — {a['label']}" if a["label"] else ""
            item = QListWidgetItem(f"[{state}]  {a['hour']:02d}:{a['minute']:02d}{tag}")
            self.alarm_list.addItem(item)
        if 0 <= current_row < self.alarm_list.count():
            self.alarm_list.setCurrentRow(current_row)

    def add_alarm(self):
        alarm = {
            "hour": self.hour_spin.value(),
            "minute": self.min_spin.value(),
            "label": self.label_input.text().strip(),
            "enabled": True,
            "triggered_key": None,
        }
        self.alarms.append(alarm)
        self.alarms.sort(key=lambda x: (x["hour"], x["minute"]))
        self.label_input.clear()
        self.refresh_list()

    def toggle_selected_alarm(self):
        row = self.alarm_list.currentRow()
        if 0 <= row < len(self.alarms):
            self.alarms[row]["enabled"] = not self.alarms[row]["enabled"]
            self.alarms[row]["triggered_key"] = None
            self.refresh_list()

    def delete_selected_alarm(self):
        row = self.alarm_list.currentRow()
        if 0 <= row < len(self.alarms):
            if self.ringing_alarm is self.alarms[row]:
                self.stop_ringing()
            self.alarms.pop(row)
            self.refresh_list()

    def play_chime(self):
        freqs = [880, 1046, 880, 1174]
        freq = freqs[self.chime_step % len(freqs)]
        self.chime_step += 1
        if winsound is not None:
            try:
                winsound.Beep(freq, 180)
                return
            except RuntimeError:
                pass
        QApplication.beep()

    def test_sound(self):
        self.play_chime()

    def trigger_alarm(self, alarm):
        self.ringing_alarm = alarm
        tag = f" — {alarm['label']}" if alarm["label"] else ""
        self.alert_label.setText(f"ALARM {alarm['hour']:02d}:{alarm['minute']:02d}{tag}")
        self.alert_box.show()
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.chime_step = 0
        self.play_chime()
        if not self.sound_timer.isActive():
            self.sound_timer.start()

    def stop_ringing(self):
        self.sound_timer.stop()
        self.alert_box.hide()
        if self.ringing_alarm is not None:
            self.ringing_alarm["enabled"] = False
            self.ringing_alarm = None
            self.refresh_list()

    def snooze_alarm(self):
        self.sound_timer.stop()
        self.alert_box.hide()
        if self.ringing_alarm is not None:
            snooze_dt = datetime.now() + timedelta(minutes=5)
            self.ringing_alarm["hour"] = snooze_dt.hour
            self.ringing_alarm["minute"] = snooze_dt.minute
            self.ringing_alarm["enabled"] = True
            self.ringing_alarm["triggered_key"] = None
            self.ringing_alarm = None
            self.alarms.sort(key=lambda x: (x["hour"], x["minute"]))
            self.refresh_list()

    def on_tick(self):
        now = datetime.now()
        self.now_label.setText(now.strftime("%H:%M:%S"))
        minute_key = now.strftime("%Y-%m-%d %H:%M")

        for a in self.alarms:
            if not a["enabled"]:
                continue
            if a["hour"] == now.hour and a["minute"] == now.minute:
                if a["triggered_key"] != minute_key:
                    a["triggered_key"] = minute_key
                    self.trigger_alarm(a)
                    break

    def closeEvent(self, event):
        self.sound_timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlarmApp()
    window.show()
    sys.exit(app.exec_())
