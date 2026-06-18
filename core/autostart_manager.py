"""
自启动管理器 - Windows 注册表操作
"""

import os
import sys
from PySide2.QtCore import QSettings


class AutoStartManager:
    """管理应用和命令的开机自启动（通过 Windows 注册表）"""

    AUTO_START_PATH = (
        "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    )

    @staticmethod
    def app_path() -> str:
        """获取应用完整路径"""
        return sys.executable

    @staticmethod
    def app_script_path() -> str:
        """获取主脚本路径"""
        if getattr(sys, 'frozen', False):
            return sys.executable
        return os.path.abspath(sys.argv[0])

    def is_app_auto_start(self) -> bool:
        """检查应用是否开机启动"""
        settings = QSettings(self.AUTO_START_PATH, QSettings.NativeFormat)
        return settings.contains("CmdManager")

    def set_app_auto_start(self, enabled: bool):
        """设置应用开机启动"""
        settings = QSettings(self.AUTO_START_PATH, QSettings.NativeFormat)
        if enabled:
            script = self.app_script_path()
            if script.endswith(".py"):
                python = sys.executable
                settings.setValue("CmdManager", f'"{python}" "{script}" --minimized')
            else:
                settings.setValue("CmdManager", f'"{script}" --minimized')
        else:
            settings.remove("CmdManager")
        settings.sync()

    def is_command_auto_start(self, command_name: str) -> bool:
        """检查命令是否开机启动"""
        settings = QSettings(self.AUTO_START_PATH, QSettings.NativeFormat)
        return settings.contains(f"CmdManager_{command_name}")

    def set_command_auto_start(self, command_name: str, command: str, enabled: bool):
        """设置命令开机启动（直接添加到注册表 Run 键）"""
        settings = QSettings(self.AUTO_START_PATH, QSettings.NativeFormat)
        if enabled:
            settings.setValue(
                f"CmdManager_{command_name}",
                f'cmd.exe /c "{command}"'
            )
        else:
            settings.remove(f"CmdManager_{command_name}")
        settings.sync()
