"""
配置管理器 - 持久化存储命令配置和窗口状态
"""

import json
import os
from PySide2.QtCore import QSettings


class SettingsManager:
    """单例配置管理器"""

    _instance = None
    KEY_COMMANDS = "commands"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._settings = QSettings("CmdManager", "CmdManager")

    def save_command(self, name: str, command: str, work_dir: str,
                     auto_start: bool, minimized: bool):
        """保存命令"""
        commands = self.load_commands()
        cmd = {
            "name": name,
            "command": command,
            "workDir": work_dir,
            "autoStart": auto_start,
            "minimized": minimized
        }
        commands.append(cmd)
        self._settings.setValue(self.KEY_COMMANDS, json.dumps(commands, ensure_ascii=False))

    def remove_command(self, name: str):
        """删除命令"""
        commands = self.load_commands()
        commands = [c for c in commands if c.get("name") != name]
        self._settings.setValue(self.KEY_COMMANDS, json.dumps(commands, ensure_ascii=False))

    def update_command(self, old_name: str, name: str, command: str,
                       work_dir: str, auto_start: bool, minimized: bool):
        """更新命令"""
        commands = self.load_commands()
        for c in commands:
            if c.get("name") == old_name:
                c["name"] = name
                c["command"] = command
                c["workDir"] = work_dir
                c["autoStart"] = auto_start
                c["minimized"] = minimized
                break
        self._settings.setValue(self.KEY_COMMANDS, json.dumps(commands, ensure_ascii=False))

    def load_commands(self) -> list:
        """加载所有命令"""
        data = self._settings.value(self.KEY_COMMANDS, "")
        if not data:
            return []
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return []

    def set_value(self, key: str, value):
        """设置通用配置值"""
        self._settings.setValue(key, value)

    def value(self, key: str, default=None):
        """获取通用配置值"""
        return self._settings.value(key, default)

    def set_window_geometry(self, geometry: bytes):
        self.set_value("windowGeometry", geometry)

    def window_geometry(self) -> bytes:
        return self.value("windowGeometry", b"")

    def set_splitter_state(self, state: bytes):
        self.set_value("splitterState", state)

    def splitter_state(self) -> bytes:
        return self.value("splitterState", b"")
