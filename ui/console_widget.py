"""
控制台输出组件 - 模拟终端样式
"""

from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QTextEdit, QPushButton, QLabel)
from PySide2.QtCore import Signal
from PySide2.QtGui import QFont, QTextCursor


class ConsoleWidget(QWidget):
    """控制台输出面板"""

    clear_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._command_name = ""
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- 标题栏 ---
        header = QWidget(self)
        header.setFixedHeight(36)
        header.setStyleSheet("background-color: #1E1E1E; border-bottom: 1px solid #3A3A3A;")

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(12, 0, 8, 0)

        self._header_label = QLabel("控制台输出", header)
        header_font = self._header_label.font()
        header_font.setPointSize(10)
        header_font.setBold(True)
        self._header_label.setFont(header_font)
        self._header_label.setStyleSheet("color: #E0E0E0; border: none;")

        self._status_dot = QLabel(header)
        self._status_dot.setFixedSize(8, 8)
        self._status_dot.setStyleSheet(
            "background-color: #757575; border-radius: 4px; border: none;"
        )

        self._clear_btn = QPushButton("清除", header)
        self._clear_btn.setFixedSize(50, 24)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A; color: #B0B0B0;
                border: 1px solid #4A4A4A; border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4A4A4A; color: #E0E0E0;
            }
        """)
        self._clear_btn.clicked.connect(self._on_clear)

        h_layout.addWidget(self._header_label)
        h_layout.addSpacing(8)
        h_layout.addWidget(self._status_dot)
        h_layout.addStretch()
        h_layout.addWidget(self._clear_btn)

        # --- 控制台输出区 ---
        self._console = QTextEdit(self)
        self._console.setReadOnly(True)
        self._console.setStyleSheet("""
            QTextEdit {
                background-color: #1A1A1A;
                color: #D4D4D4;
                border: none;
                padding: 10px;
                font-family: "Consolas", "Courier New", "Menlo", monospace;
                font-size: 13px;
                line-height: 1.5;
                selection-background-color: #264F78;
            }
            QScrollBar:vertical {
                background-color: #1A1A1A;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #424242;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                height: 0px;
            }
        """)

        layout.addWidget(header)
        layout.addWidget(self._console)

    def _apply_style(self):
        self.setStyleSheet("background-color: #1A1A1A;")

    def append(self, text: str):
        """追加输出文本"""
        self._console.moveCursor(QTextCursor.End)
        self._console.insertPlainText(text)
        self._console.moveCursor(QTextCursor.End)

        # 限制输出量防止内存溢出
        if len(self._console.toPlainText()) > 100000:
            content = self._console.toPlainText()
            self._console.setPlainText(content[-50000:])

    def set_command_name(self, name: str):
        self._command_name = name
        self._header_label.setText(f"控制台 - {name}")

    def clear(self):
        self._console.clear()

    def set_running(self, running: bool):
        color = "#4CAF50" if running else "#757575"
        self._status_dot.setStyleSheet(
            f"background-color: {color}; border-radius: 4px; border: none;"
        )

    def command_name(self) -> str:
        return self._command_name

    def _on_clear(self):
        self.clear()
        self.clear_requested.emit()
