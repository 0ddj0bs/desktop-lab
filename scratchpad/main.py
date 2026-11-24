import sys
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ScratchpadApp(QWidget):
    def __init__(self):
        super().__init__()
        self.note_path = Path(__file__).resolve().parent / "scratchpad.txt"
        self.dirty = False
        self.init_ui()
        self.load_note()

        self.save_timer = QTimer(self)
        self.save_timer.setInterval(800)
        self.save_timer.timeout.connect(self.flush_save)
        self.save_timer.start()

    def init_ui(self):
        self.setWindowTitle("Scratchpad — Quick Desktop Notes")
        self.resize(520, 460)

        root = QVBoxLayout()
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        top_bar = QHBoxLayout()
        title = QLabel("Scratchpad")
        title.setObjectName("title_label")

        self.status_label = QLabel("Saved")
        self.status_label.setObjectName("status_label")

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.status_label)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Jot down quick notes, reminders, or random thoughts...")
        self.editor.textChanged.connect(self.mark_dirty)

        bottom_bar = QHBoxLayout()
        self.info_label = QLabel("0 chars  |  0 lines")
        self.info_label.setObjectName("info_label")

        self.copy_btn = QPushButton("Copy All")
        self.copy_btn.setObjectName("secondary_btn")
        self.copy_btn.clicked.connect(self.copy_all)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("danger_btn")
        self.clear_btn.clicked.connect(self.clear_note)

        bottom_bar.addWidget(self.info_label)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.copy_btn)
        bottom_bar.addWidget(self.clear_btn)

        root.addLayout(top_bar)
        root.addWidget(self.editor, stretch=1)
        root.addLayout(bottom_bar)

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
            QLabel#info_label {
                color: #94a3b8;
                font-size: 13px;
            }
            QPlainTextEdit {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
                color: #f8fafc;
                font-size: 15px;
            }
            QPushButton {
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: bold;
                color: white;
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
            """
        )

    def update_counts(self):
        text = self.editor.toPlainText()
        chars = len(text)
        lines = len(text.splitlines()) if text else 0
        self.info_label.setText(f"{chars} chars  |  {lines} lines")

    def mark_dirty(self):
        self.dirty = True
        self.status_label.setStyleSheet("color: #fbbf24; font-weight: bold;")
        self.status_label.setText("Saving...")
        self.update_counts()

    def flush_save(self):
        if not self.dirty:
            return
        self.note_path.write_text(self.editor.toPlainText(), encoding="utf-8")
        self.dirty = False
        self.status_label.setStyleSheet("color: #4ade80; font-weight: bold;")
        self.status_label.setText("Saved")

    def load_note(self):
        if self.note_path.exists():
            self.editor.blockSignals(True)
            self.editor.setPlainText(self.note_path.read_text(encoding="utf-8"))
            self.editor.blockSignals(False)
        self.update_counts()

    def copy_all(self):
        text = self.editor.toPlainText()
        if not text:
            self.status_label.setStyleSheet("color: #94a3b8; font-weight: bold;")
            self.status_label.setText("Nothing to copy")
            return
        QApplication.clipboard().setText(text)
        self.status_label.setStyleSheet("color: #38bdf8; font-weight: bold;")
        self.status_label.setText("Copied all")

    def clear_note(self):
        self.editor.clear()
        self.flush_save()
        self.status_label.setStyleSheet("color: #94a3b8; font-weight: bold;")
        self.status_label.setText("Cleared")

    def closeEvent(self, event):
        self.flush_save()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScratchpadApp()
    window.show()
    sys.exit(app.exec_())