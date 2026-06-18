"""
命令编辑对话框
"""

from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLineEdit, QTextEdit, QCheckBox, QPushButton,
                              QLabel, QFileDialog, QWidget)
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont


class CommandEditDialog(QDialog):
    """新增 / 编辑命令对话框"""

    def __init__(self, parent=None, name="", command="", work_dir="",
                 auto_start=False, minimized=False):
        super().__init__(parent)
        self._setup_ui()
        self._apply_style()

        if name:
            self.setWindowTitle("编辑命令")
            self._name_edit.setText(name)
            self._cmd_edit.setPlainText(command)
            self._dir_edit.setText(work_dir)
            self._autostart_check.setChecked(auto_start)
            self._minimized_check.setChecked(minimized)
        else:
            self.setWindowTitle("添加命令")

    def _setup_ui(self):
        self.setFixedSize(500, 410)
        self.setModal(True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(22, 22, 22, 22)
        main_layout.setSpacing(12)

        # 标题
        title = QLabel("命令配置", self)
        title_font = title.font()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #FFFFFF;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        main_layout.addSpacing(4)

        # 表单
        form = QFormLayout()
        form.setSpacing(10)

        input_style = """
            QLineEdit, QTextEdit {
                background-color: #1E1E1E;
                color: #E0E0E0;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                padding: 7px 10px;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus { border-color: #5C6BC0; }
        """
        label_style = "color: #B0B0B0; font-size: 12px;"

        # 命令名称
        name_lbl = QLabel("命令名称:", self)
        name_lbl.setStyleSheet(label_style)
        self._name_edit = QLineEdit(self)
        self._name_edit.setPlaceholderText("输入命令显示名称...")
        self._name_edit.setStyleSheet(input_style)
        form.addRow(name_lbl, self._name_edit)

        # 执行命令
        cmd_lbl = QLabel("执行命令:", self)
        cmd_lbl.setStyleSheet(label_style)
        self._cmd_edit = QTextEdit(self)
        self._cmd_edit.setPlaceholderText("输入要执行的命令...")
        self._cmd_edit.setFixedHeight(90)
        self._cmd_edit.setStyleSheet(input_style)
        form.addRow(cmd_lbl, self._cmd_edit)

        # 工作目录
        dir_lbl = QLabel("工作目录:", self)
        dir_lbl.setStyleSheet(label_style)
        dir_widget = QWidget(self)
        dir_layout = QHBoxLayout(dir_widget)
        dir_layout.setContentsMargins(0, 0, 0, 0)
        dir_layout.setSpacing(6)

        self._dir_edit = QLineEdit(self)
        self._dir_edit.setPlaceholderText("留空使用默认目录...")
        self._dir_edit.setStyleSheet(input_style)

        browse_btn = QPushButton("浏览...", self)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A; color: #E0E0E0;
                border: 1px solid #4A4A4A; border-radius: 4px;
                padding: 7px 14px; font-size: 12px;
            }
            QPushButton:hover { background-color: #4A4A4A; }
        """)
        browse_btn.clicked.connect(self._browse_dir)

        dir_layout.addWidget(self._dir_edit)
        dir_layout.addWidget(browse_btn)
        form.addRow(dir_lbl, dir_widget)

        # 复选框
        checks_widget = QWidget(self)
        checks_layout = QHBoxLayout(checks_widget)
        checks_layout.setContentsMargins(0, 0, 0, 0)
        checks_layout.setSpacing(20)

        check_style = """
            QCheckBox { color: #E0E0E0; font-size: 12px; spacing: 8px; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QCheckBox::indicator:unchecked {
                background-color: #2A2A2A; border: 1px solid #4A4A4A; border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #5C6BC0; border: 1px solid #5C6BC0; border-radius: 3px;
            }
        """

        self._autostart_check = QCheckBox("开机启动", self)
        self._autostart_check.setStyleSheet(check_style)

        self._minimized_check = QCheckBox("启动时最小化", self)
        self._minimized_check.setStyleSheet(check_style)

        checks_layout.addWidget(self._autostart_check)
        checks_layout.addWidget(self._minimized_check)
        checks_layout.addStretch()
        form.addRow(checks_widget)

        main_layout.addLayout(form)
        main_layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = QPushButton("取消", self)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A; color: #E0E0E0;
                border: 1px solid #4A4A4A; border-radius: 4px;
                padding: 9px 28px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #4A4A4A; }
        """)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("保存", self)
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #283593; color: #FFFFFF;
                border: 1px solid #3949AB; border-radius: 4px;
                padding: 9px 28px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3949AB; }
        """)
        ok_btn.clicked.connect(self._on_ok)

        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)

        main_layout.addLayout(btn_layout)

    def _apply_style(self):
        self.setStyleSheet("QDialog { background-color: #252525; }")

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择工作目录")
        if path:
            self._dir_edit.setText(path)

    def _on_ok(self):
        if not self._name_edit.text().strip():
            return
        if not self._cmd_edit.toPlainText().strip():
            return
        self.accept()

    # --- 公共接口 ---

    def get_name(self) -> str:
        return self._name_edit.text().strip()

    def get_command(self) -> str:
        return self._cmd_edit.toPlainText().strip()

    def get_work_dir(self) -> str:
        return self._dir_edit.text().strip()

    def is_auto_start(self) -> bool:
        return self._autostart_check.isChecked()

    def is_minimized(self) -> bool:
        return self._minimized_check.isChecked()
