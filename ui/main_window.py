"""
主窗口 - PySide2 命令管理器
"""

import json

from PySide2.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QScrollArea, QSplitter, QPushButton, QLabel,
                              QSystemTrayIcon, QMenu, QAction, QMessageBox,
                              QApplication, QGraphicsDropShadowEffect)
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont, QColor, QIcon

from utils.settings_manager import SettingsManager
from utils import resource_path
from core.autostart_manager import AutoStartManager
from core.command_runner import CommandRunner
from ui.command_card import CommandCard
from ui.console_widget import ConsoleWidget
from ui.command_dialog import CommandEditDialog


# ── 全局暗色主题样式表 ───────────────────────────────────────────

DARK_THEME = """
    QMainWindow {
        background-color: transparent;
    }
    * {
        font-family: "Microsoft YaHei", "Segoe UI", "Helvetica Neue", sans-serif;
    }
    QToolTip {
        background-color: #333333;
        color: #E0E0E0;
        border: 1px solid #555555;
        padding: 4px 8px;
        border-radius: 4px;
    }
"""


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 设置窗口图标（用 .ico 支持多尺寸）
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        self._settings = SettingsManager()
        self._autostart = AutoStartManager()

        self._command_cards: dict[str, CommandCard] = {}
        self._runners: dict[str, CommandRunner] = {}
        self._active_command = ""
        self._drag_pos = None
        self._is_maximized = False

        self._setup_ui()
        self._apply_theme()
        self._setup_tray()
        self._load_saved_commands()
        self._restore_state()

    # ── UI 构建 ─────────────────────────────────────────────────

    def _setup_ui(self):
        # 中央容器（圆角边框）
        central = QWidget(self)
        central.setObjectName("centralWidget")
        central.setStyleSheet("""
            #centralWidget {
                background-color: #1E1E1E;
                border: 1px solid #333333;
                border-radius: 10px;
            }
        """)

        root = QVBoxLayout(central)
        root.setContentsMargins(1, 1, 1, 1)
        root.setSpacing(0)

        root.addWidget(self._create_title_bar())

        # 主分割器
        self._splitter = QSplitter(Qt.Horizontal, self)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #333333;
            }
            QSplitter::handle:hover {
                background-color: #5C6BC0;
            }
        """)

        self._splitter.addWidget(self._create_sidebar())
        self._splitter.addWidget(self._create_content_area())

        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)
        self._splitter.setSizes([260, 840])

        root.addWidget(self._splitter)
        self.setCentralWidget(central)

        # 窗口阴影
        shadow = QGraphicsDropShadowEffect(central)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 4)
        central.setGraphicsEffect(shadow)

    def _create_title_bar(self) -> QWidget:
        """标题栏"""
        bar = QWidget(self)
        bar.setFixedHeight(42)
        bar.setObjectName("titleBar")
        bar.setStyleSheet("""
            #titleBar {
                background-color: #1A1A1A;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #2A2A2A;
            }
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 6, 0)
        layout.setSpacing(6)

        title = QLabel("⚡ CmdManager", bar)
        f = title.font()
        f.setPointSize(11)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet("color: #E0E0E0; background: transparent; border: none;")

        layout.addWidget(title)
        layout.addStretch()

        # 最小化按钮
        min_btn = QPushButton("─", bar)
        min_btn.setFixedSize(32, 28)
        min_btn.setStyleSheet(self._title_btn_style())
        min_btn.clicked.connect(self.showMinimized)
        layout.addWidget(min_btn)

        # 最大化/还原按钮
        self._max_btn = QPushButton("□", bar)
        self._max_btn.setFixedSize(32, 28)
        self._max_btn.setStyleSheet(self._title_btn_style())
        self._max_btn.clicked.connect(self._toggle_maximize)
        layout.addWidget(self._max_btn)

        # 关闭按钮
        close_btn = QPushButton("✕", bar)
        close_btn.setFixedSize(32, 28)
        close_btn.setStyleSheet(self._title_btn_style() + """
            QPushButton:hover { background-color: #D32F2F; color: white; border-radius: 4px; }
        """)
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)

        # 拖拽
        bar.mousePressEvent = self._title_mouse_press
        bar.mouseMoveEvent = self._title_mouse_move

        return bar

    def _create_sidebar(self) -> QWidget:
        """侧边栏"""
        sidebar = QWidget(self)
        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(500)
        sidebar.setStyleSheet("""
            QWidget { background-color: #222222; }
            QScrollBar:vertical {
                background-color: #222222; width: 6px; border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #424242; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background-color: #555555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 侧边栏头部
        header = QWidget(sidebar)
        header.setFixedHeight(50)
        header.setStyleSheet("background-color: #1A1A1A; border-bottom: 1px solid #2A2A2A;")

        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 0, 10, 0)

        self._sidebar_title = QLabel("📋 命令列表", header)
        sf = self._sidebar_title.font()
        sf.setPointSize(10)
        sf.setBold(True)
        self._sidebar_title.setFont(sf)
        self._sidebar_title.setStyleSheet("color: #E0E0E0; border: none;")

        self._add_btn = QPushButton("+ 新增", header)
        self._add_btn.setStyleSheet("""
            QPushButton {
                background-color: #283593; color: #FFFFFF;
                border: none; border-radius: 4px;
                padding: 6px 14px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3949AB; }
        """)
        self._add_btn.clicked.connect(self._on_add_command)

        h_layout.addWidget(self._sidebar_title)
        h_layout.addStretch()
        h_layout.addWidget(self._add_btn)

        layout.addWidget(header)

        # 可滚动的命令列表
        scroll = QScrollArea(sidebar)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #222222; }")

        scroll_widget = QWidget(scroll)
        scroll_widget.setStyleSheet("background-color: #222222;")
        self._card_layout = QVBoxLayout(scroll_widget)
        self._card_layout.setContentsMargins(8, 8, 8, 8)
        self._card_layout.setSpacing(6)
        self._card_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 侧边栏底部（应用开机启动开关）
        footer = QWidget(sidebar)
        footer.setFixedHeight(44)
        footer.setStyleSheet("background-color: #1A1A1A; border-top: 1px solid #2A2A2A;")

        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(12, 0, 12, 0)

        self._app_autostart_btn = QPushButton(sidebar)
        self._app_autostart_btn.clicked.connect(self._toggle_app_autostart)
        self._update_app_autostart_btn()

        f_layout.addWidget(self._app_autostart_btn)
        f_layout.addStretch()

        layout.addWidget(footer)

        return sidebar

    def _create_content_area(self) -> QWidget:
        """右侧内容区"""
        content = QWidget(self)
        content.setStyleSheet("background-color: #1E1E1E;")

        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        # 欢迎页
        self._welcome = QLabel(content)
        self._welcome.setAlignment(Qt.AlignCenter)
        self._welcome.setText("""
            <div style='text-align: center; color: #666666;'>
                <div style='font-size: 64px; margin-bottom: 20px;'>⚡</div>
                <div style='font-size: 22px; font-weight: bold; color: #888888; margin-bottom: 12px;'>
                    欢迎使用 CmdManager
                </div>
                <div style='font-size: 13px; color: #666666; line-height: 1.8;'>
                    点击左侧 <span style='color: #7986CB;'>+ 新增</span> 按钮添加命令<br>
                    支持开机启动 · 实时控制台输出 · 多命令管理
                </div>
            </div>
        """)
        self._content_layout.addWidget(self._welcome)

        # 控制台
        self._console = ConsoleWidget(content)
        self._console.setVisible(False)
        self._content_layout.addWidget(self._console)

        return content

    def _apply_theme(self):
        self.setStyleSheet(DARK_THEME)

    def _title_btn_style(self) -> str:
        return """
            QPushButton {
                background-color: transparent; color: #E0E0E0;
                border: none; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #333333; border-radius: 4px; }
        """

    def _toggle_maximize(self):
        """切换最大化/还原"""
        if self._is_maximized:
            self._restore_window()
        else:
            self._maximize_window()

    def _maximize_window(self):
        """最大化窗口"""
        self._is_maximized = True
        self._max_btn.setText("❐")
        self._normal_geometry = self.geometry()
        screen = QApplication.primaryScreen()
        self.setGeometry(screen.availableGeometry())

    def _restore_window(self):
        """还原窗口"""
        self._is_maximized = False
        self._max_btn.setText("□")
        if hasattr(self, '_normal_geometry'):
            self.setGeometry(self._normal_geometry)

    # ── 系统托盘 ─────────────────────────────────────────────────

    def _setup_tray(self):
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(QIcon(resource_path("icon.png")))
        self._tray.setToolTip("CmdManager - 命令管理器")

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2B2B2B; color: #E0E0E0;
                border: 1px solid #3A3A3A; padding: 4px;
            }
            QMenu::item {
                padding: 8px 30px; border-radius: 4px;
            }
            QMenu::item:selected { background-color: #3A3A3A; }
            QMenu::separator {
                height: 1px; background-color: #3A3A3A; margin: 4px 8px;
            }
        """)

        show_action = menu.addAction("显示窗口")
        show_action.triggered.connect(self._show_window)

        menu.addSeparator()

        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(QApplication.quit)

        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    # ── 命令管理 ─────────────────────────────────────────────────

    def _on_add_command(self):
        dlg = CommandEditDialog(self)
        if dlg.exec_() == CommandEditDialog.Accepted:
            name = dlg.get_name()
            cmd = dlg.get_command()
            if not name or not cmd:
                QMessageBox.warning(self, "提示", "命令名称和命令不能为空！")
                return

            self._add_command_internal(name, cmd, dlg.get_work_dir(),
                                       dlg.is_auto_start(), dlg.is_minimized())
            self._settings.save_command(name, cmd, dlg.get_work_dir(),
                                        dlg.is_auto_start(), dlg.is_minimized())

    def _add_command_internal(self, name: str, command: str, work_dir: str,
                               auto_start: bool, minimized: bool):
        """内部：添加命令到 UI 和数据结构"""
        if name in self._command_cards:
            QMessageBox.warning(self, "提示", f'命令名称 "{name}" 已存在！')
            return

        card = CommandCard(name, command, auto_start, False, self)

        # 插入到 stretch 之前
        self._card_layout.takeAt(self._card_layout.count() - 1)
        self._card_layout.addWidget(card)
        self._card_layout.addStretch()

        self._command_cards[name] = card

        runner = CommandRunner(self)
        self._runners[name] = runner

        # 信号连接
        card.run_clicked.connect(lambda: self._run_command(name))
        card.stop_clicked.connect(lambda: self._stop_command(name))
        card.restart_clicked.connect(lambda: self._restart_command(name))
        card.edit_clicked.connect(lambda: self._edit_command(name))
        card.delete_clicked.connect(lambda: self._delete_command(name))
        card.auto_start_toggled.connect(lambda enabled, n=name: self._on_autostart_toggle(n, enabled))

    def _run_command(self, name: str):
        """运行命令"""
        self._show_console(name)
        self._active_command = name

        runner = self._runners[name]
        card = self._command_cards[name]

        # 断开旧连接再重新连接（避免重复）
        try:
            runner.output_received.disconnect()
            runner.finished.disconnect()
        except Exception:
            pass

        runner.output_received.connect(lambda text, n=name: self._on_output(n, text))
        runner.finished.connect(lambda code, n=name: self._on_command_finished(n, code))

        runner.run(name, card.command, "")
        card.set_running(True)
        self._console.set_running(True)

    def _stop_command(self, name: str):
        """停止命令"""
        if name in self._runners:
            self._runners[name].stop()
        if name in self._command_cards:
            self._command_cards[name].set_running(False)
        if self._active_command == name:
            self._console.set_running(False)

    def _restart_command(self, name: str):
        """重启命令"""
        self._show_console(name)
        self._active_command = name

        runner = self._runners[name]
        card = self._command_cards[name]

        runner.stop()
        self._console.clear()

        try:
            runner.output_received.disconnect()
            runner.finished.disconnect()
        except Exception:
            pass

        runner.output_received.connect(lambda text, n=name: self._on_output(n, text))
        runner.finished.connect(lambda code, n=name: self._on_command_finished(n, code))

        runner.run(name, card.command, "")
        card.set_running(True)
        self._console.set_running(True)

    def _edit_command(self, name: str):
        """编辑命令"""
        card = self._command_cards[name]

        dlg = CommandEditDialog(
            self, name, card.command, "",
            card.is_auto_start, False
        )
        if dlg.exec_() == CommandEditDialog.Accepted:
            new_name = dlg.get_name()
            new_cmd = dlg.get_command()
            if not new_name or not new_cmd:
                QMessageBox.warning(self, "提示", "命令名称和命令不能为空！")
                return

            # 处理重命名
            if new_name != name:
                if new_name in self._command_cards:
                    QMessageBox.warning(self, "提示", f'命令名称 "{new_name}" 已存在！')
                    return
                self._command_cards[new_name] = self._command_cards.pop(name)
                self._runners[new_name] = self._runners.pop(name)
                self._command_cards[new_name].set_name(new_name)
                if self._active_command == name:
                    self._active_command = new_name

            self._command_cards[new_name].set_command(new_cmd)
            self._command_cards[new_name].set_auto_start(dlg.is_auto_start())

            self._settings.update_command(
                name, new_name, new_cmd, dlg.get_work_dir(),
                dlg.is_auto_start(), dlg.is_minimized()
            )

    def _delete_command(self, name: str):
        """删除命令"""
        reply = QMessageBox.question(
            self, "确认删除",
            f'确定要删除命令 "{name}" 吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        if name in self._command_cards:
            card = self._command_cards.pop(name)
            self._card_layout.removeWidget(card)
            card.deleteLater()

        if name in self._runners:
            runner = self._runners.pop(name)
            runner.stop()
            runner.deleteLater()

        self._settings.remove_command(name)

        if self._active_command == name:
            self._active_command = ""
            self._console.setVisible(False)
            self._welcome.setVisible(True)

    def _show_console(self, name: str):
        """显示控制台"""
        self._welcome.setVisible(False)
        self._console.setVisible(True)
        self._console.set_command_name(name)
        self._console.clear()

    # ── 信号处理 ─────────────────────────────────────────────────

    def _on_output(self, name: str, text: str):
        if self._active_command == name:
            self._console.append(text)

    def _on_command_finished(self, name: str, exit_code: int):
        if self._active_command == name:
            self._console.append(f"\n── 进程结束，退出码: {exit_code} ──\n")
            self._console.set_running(False)
        if name in self._command_cards:
            self._command_cards[name].set_running(False)

    def _on_autostart_toggle(self, name: str, enabled: bool):
        """切换单个命令的开机启动"""
        commands = self._settings.load_commands()
        for c in commands:
            if c.get("name") == name:
                c["autoStart"] = enabled
                break
        self._settings.set_value("commands", json.dumps(commands, ensure_ascii=False))

    # ── 应用开机启动 ─────────────────────────────────────────────

    def _toggle_app_autostart(self):
        current = self._autostart.is_app_auto_start()
        self._autostart.set_app_auto_start(not current)
        self._update_app_autostart_btn()

    def _update_app_autostart_btn(self):
        enabled = self._autostart.is_app_auto_start()
        self._app_autostart_btn.setText("⚡ 应用开机启动" if enabled else "应用开机启动")
        self._app_autostart_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #1A237E; color: #90CAF9;
                border: none; border-radius: 4px;
                padding: 6px 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: #283593; }
            """ if enabled else """
            QPushButton {
                background-color: transparent; color: #9E9E9E;
                border: none; border-radius: 4px;
                padding: 6px 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: #333333; color: #E0E0E0; }
            """
        )

    # ── 持久化 ───────────────────────────────────────────────────

    def _load_saved_commands(self):
        commands = self._settings.load_commands()
        for c in commands:
            self._add_command_internal(
                c.get("name", ""),
                c.get("command", ""),
                c.get("workDir", ""),
                c.get("autoStart", False),
                c.get("minimized", False)
            )

    def _restore_state(self):
        geom = self._settings.window_geometry()
        if geom:
            self.restoreGeometry(geom)
        else:
            self.resize(1100, 720)
            screen = QApplication.primaryScreen()
            rect = screen.availableGeometry()
            self.move((rect.width() - 1100) // 2, (rect.height() - 720) // 2)

        state = self._settings.splitter_state()
        if state:
            self._splitter.restoreState(state)

    def _save_state(self):
        self._settings.set_window_geometry(self.saveGeometry())
        self._settings.set_splitter_state(self._splitter.saveState())

    # ── 窗口事件 ─────────────────────────────────────────────────

    def _title_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos()

    def _title_mouse_move(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPos()

    def _on_close(self):
        self._save_state()
        self.hide()
        self._tray.showMessage(
            "CmdManager", "应用已最小化到系统托盘",
            QSystemTrayIcon.Information, 2000
        )

    def _show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_window()

    def closeEvent(self, event):
        self._save_state()
        self.hide()
        self._tray.showMessage(
            "CmdManager", "应用已最小化到系统托盘",
            QSystemTrayIcon.Information, 2000
        )
        event.ignore()
