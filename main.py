"""
CmdManager - PySide2 命令管理器
支持 Windows 自定义命令执行、开机启动、实时控制台输出
"""

import sys
import os

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt

from ui.main_window import MainWindow


def main():
    # 高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("CmdManager")
    app.setOrganizationName("CmdManager")

    # 检查是否以最小化启动
    start_minimized = "--minimized" in sys.argv

    window = MainWindow()
    if not start_minimized:
        window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
