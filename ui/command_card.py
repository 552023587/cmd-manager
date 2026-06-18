"""
命令卡片组件 - 侧边栏中的命令项
"""

from PySide2.QtWidgets import (QFrame, QLabel, QPushButton,
                              QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect)
from PySide2.QtCore import Signal, Qt
from PySide2.QtGui import QFont, QColor


class CommandCard(QFrame):
    """命令卡片"""

    run_clicked = Signal()
    stop_clicked = Signal()
    restart_clicked = Signal()
    edit_clicked = Signal()
    delete_clicked = Signal()
    auto_start_toggled = Signal(bool)
    clicked = Signal()

    def __init__(self, name: str, command: str, auto_start: bool,
                 running: bool = False, parent=None):
        super().__init__(parent)
        self._name = name
        self._command = command
        self._auto_start = auto_start
        self._running = running
        self._selected = False
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setFixedHeight(105)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(5)

        # --- 顶部：名称 + 状态灯 ---
        top = QHBoxLayout()
        top.setSpacing(8)

        self._name_label = QLabel(self._name, self)
        name_font = self._name_label.font()
        name_font.setPointSize(10)
        name_font.setBold(True)
        self._name_label.setFont(name_font)
        self._name_label.setStyleSheet("color: #E0E0E0; border: none; background: transparent;")

        self._status_dot = QLabel(self)
        self._status_dot.setFixedSize(8, 8)
        self._update_status_dot()

        top.addWidget(self._name_label)
        top.addStretch()
        top.addWidget(self._status_dot)

        # --- 命令预览 ---
        self._cmd_label = QLabel(self._command, self)
        cmd_font = self._cmd_label.font()
        cmd_font.setPointSize(8)
        self._cmd_label.setFont(cmd_font)
        self._cmd_label.setStyleSheet("color: #909090; border: none; background: transparent;")
        self._cmd_label.setWordWrap(True)

        # --- 按钮行 ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        base_btn = """
            QPushButton {
                background-color: #3A3A3A; color: #D0D0D0;
                border: 1px solid #4A4A4A; border-radius: 3px;
                padding: 4px 10px; font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4A4A4A; border-color: #5A5A5A;
            }
        """

        self._run_btn = QPushButton("▶ 运行", self)
        self._run_btn.setStyleSheet(base_btn + """
            QPushButton { background-color: #1B5E20; border-color: #2E7D32; }
            QPushButton:hover { background-color: #2E7D32; }
        """)
        self._run_btn.clicked.connect(self.run_clicked.emit)

        self._stop_btn = QPushButton("■ 停止", self)
        self._stop_btn.setStyleSheet(base_btn + """
            QPushButton { background-color: #B71C1C; border-color: #C62828; }
            QPushButton:hover { background-color: #C62828; }
        """)
        self._stop_btn.clicked.connect(self.stop_clicked.emit)
        self._stop_btn.setVisible(False)

        self._restart_btn = QPushButton("↻ 重启", self)
        self._restart_btn.setStyleSheet(base_btn + """
            QPushButton { background-color: #E65100; border-color: #EF6C00; }
            QPushButton:hover { background-color: #EF6C00; }
        """)
        self._restart_btn.clicked.connect(self.restart_clicked.emit)

        self._autostart_btn = QPushButton(self)
        self._autostart_btn.clicked.connect(self._toggle_autostart)
        self._update_autostart_btn()

        self._edit_btn = QPushButton("✎", self)
        self._edit_btn.setStyleSheet(base_btn + "QPushButton { padding: 4px 7px; font-size: 13px; }")
        self._edit_btn.clicked.connect(self.edit_clicked.emit)

        self._delete_btn = QPushButton("✕", self)
        self._delete_btn.setStyleSheet(base_btn + """
            QPushButton { padding: 4px 7px; font-size: 13px; }
            QPushButton:hover { background-color: #B71C1C; border-color: #C62828; }
        """)
        self._delete_btn.clicked.connect(self.delete_clicked.emit)

        btn_layout.addWidget(self._run_btn)
        btn_layout.addWidget(self._stop_btn)
        btn_layout.addWidget(self._restart_btn)
        btn_layout.addWidget(self._autostart_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self._edit_btn)
        btn_layout.addWidget(self._delete_btn)

        main_layout.addLayout(top)
        main_layout.addWidget(self._cmd_label)
        main_layout.addLayout(btn_layout)

    def _apply_style(self):
        self.setStyleSheet("""
            CommandCard {
                background-color: #2B2B2B;
                border: 1px solid #3A3A3A;
                border-radius: 6px;
            }
            CommandCard:hover {
                background-color: #303030;
                border-color: #4A4A4A;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 1)
        self.setGraphicsEffect(shadow)

    def _update_status_dot(self):
        color = "#4CAF50" if self._running else "#555555"
        self._status_dot.setStyleSheet(
            f"background-color: {color}; border-radius: 4px;"
        )

    def _update_autostart_btn(self):
        if self._auto_start:
            self._autostart_btn.setText("⚡ 开机启动")
            self._autostart_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1A237E; color: #90CAF9;
                    border: 1px solid #283593; border-radius: 3px;
                    padding: 4px 8px; font-size: 10px;
                }
                QPushButton:hover { background-color: #283593; }
            """)
        else:
            self._autostart_btn.setText("开机启动")
            self._autostart_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3A3A3A; color: #888888;
                    border: 1px solid #4A4A4A; border-radius: 3px;
                    padding: 4px 8px; font-size: 10px;
                }
                QPushButton:hover { background-color: #4A4A4A; color: #D0D0D0; }
            """)

    def _toggle_autostart(self):
        self._auto_start = not self._auto_start
        self._update_autostart_btn()
        self.auto_start_toggled.emit(self._auto_start)

    def mousePressEvent(self, event):
        """点击卡片时发出 clicked 信号（不阻止按钮点击）"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    # --- 公共接口 ---

    def set_running(self, running: bool):
        self._running = running
        self._update_status_dot()
        self._run_btn.setVisible(not running)
        self._stop_btn.setVisible(running)

    def set_selected(self, selected: bool):
        """高亮选中状态"""
        self._selected = selected
        if selected:
            self.setStyleSheet("""
                CommandCard {
                    background-color: #1A237E;
                    border: 2px solid #5C6BC0;
                    border-radius: 6px;
                }
            """)
        else:
            self._apply_style()

    def set_command(self, command: str):
        self._command = command
        self._cmd_label.setText(command)

    def set_name(self, name: str):
        self._name = name
        self._name_label.setText(name)

    def set_auto_start(self, enabled: bool):
        self._auto_start = enabled
        self._update_autostart_btn()

    @property
    def name(self) -> str:
        return self._name

    @property
    def command(self) -> str:
        return self._command

    @property
    def is_auto_start(self) -> bool:
        return self._auto_start

    # --- hover 效果 ---

    def enterEvent(self, event):
        if not self._selected:
            self.setStyleSheet("""
                CommandCard {
                    background-color: #303030;
                    border: 1px solid #4A4A4A;
                    border-radius: 6px;
                }
            """)

    def leaveEvent(self, event):
        if not self._selected:
            self.setStyleSheet("""
                CommandCard {
                    background-color: #2B2B2B;
                    border: 1px solid #3A3A3A;
                    border-radius: 6px;
                }
            """)
