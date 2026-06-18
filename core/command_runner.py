"""
命令执行器 - 封装 QProcess，支持异步输出和崩溃重启
"""

import os
import subprocess
import tempfile
from datetime import datetime

from PySide2.QtCore import QProcess, QTimer, Signal, QObject


class CommandRunner(QObject):
    """命令执行器"""

    output_received = Signal(str)
    finished = Signal(int)
    started = Signal()
    error_occurred = Signal(str)
    restarted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = None
        self._name = ""
        self._command = ""
        self._work_dir = ""
        self._output = ""
        self._running = False
        self._restart_on_crash = False
        self._restart_delay = 3000
        self._restart_timer = QTimer(self)
        self._restart_timer.setSingleShot(True)
        self._restart_timer.timeout.connect(self._on_restart_timeout)
        self._start_time = None
        self._batch_file = ""

    def run(self, name: str, command: str, work_dir: str = ""):
        """执行命令（通过临时 bat 文件，兼容任意 Windows 命令）"""
        self._name = name
        self._command = command
        self._work_dir = work_dir
        self._output = ""

        # 清理旧进程（杀死整个进程树）
        if self._process:
            self._kill_process_tree()
            self._process.waitForFinished(3000)
            self._process.deleteLater()
            self._process = None

        # 清理旧临时文件
        self._cleanup_batch()

        self._process = QProcess(self)

        if work_dir and os.path.exists(work_dir):
            self._process.setWorkingDirectory(work_dir)

        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)
        self._process.errorOccurred.connect(self._on_error)

        # 写入临时 bat 文件执行，避免 cmd /c 中批处理链调用问题
        self._batch_file = self._create_batch(command)
        self._process.setProgram("cmd.exe")
        self._process.setArguments(["/c", self._batch_file])
        self._process.start()
        self._running = True
        self._start_time = datetime.now()
        self.started.emit()

    def _create_batch(self, command: str) -> str:
        """创建临时 bat 文件"""
        fd, path = tempfile.mkstemp(suffix=".bat", prefix="cmd_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("@echo off\r\n")
            f.write("chcp 65001 >nul\r\n")
            f.write("set PYTHONIOENCODING=utf-8\r\n")
            f.write("set PYTHONUTF8=1\r\n")
            f.write(command + "\r\n")
        return path

    def _cleanup_batch(self):
        """删除临时 bat 文件"""
        if self._batch_file and os.path.exists(self._batch_file):
            try:
                os.remove(self._batch_file)
            except OSError:
                pass
            self._batch_file = ""

    def stop(self):
        """停止命令"""
        self._restart_on_crash = False
        self._restart_timer.stop()

        if self._process:
            self._kill_process_tree()
            self._process.waitForFinished(3000)
            self._process.deleteLater()
            self._process = None
        self._running = False
        self._cleanup_batch()

    def _kill_process_tree(self):
        """杀死整个进程树（cmd.exe + 其启动的 python 等子进程）"""
        if not self._process:
            return
        pid = self._process.processId()
        if pid and pid > 0:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    timeout=5
                )
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                # 备选：只杀当前进程
                self._process.kill()

    def restart(self):
        """重启命令"""
        self.stop()
        self._restart_on_crash = True
        self.run(self._name, self._command, self._work_dir)

    def is_running(self) -> bool:
        return self._running

    def output(self) -> str:
        return self._output

    def name(self) -> str:
        return self._name

    def pid(self) -> int:
        if self._process and self._running:
            return int(self._process.processId())
        return -1

    def set_restart_on_crash(self, enabled: bool):
        self._restart_on_crash = enabled

    # --- private ---

    def _on_stdout(self):
        text = bytes(self._process.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._output += text
        self.output_received.emit(text)

    def _on_stderr(self):
        text = bytes(self._process.readAllStandardError()).decode("utf-8", errors="replace")
        self._output += text
        self.output_received.emit(text)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        self._running = False
        self._cleanup_batch()
        self.finished.emit(exit_code)

        if self._restart_on_crash and exit_status == QProcess.CrashExit:
            self.restarted.emit()
            self._restart_timer.start(self._restart_delay)

    def _on_error(self, error: QProcess.ProcessError):
        messages = {
            QProcess.FailedToStart: "无法启动进程",
            QProcess.Crashed: "进程崩溃",
            QProcess.Timedout: "进程超时",
        }
        self.error_occurred.emit(messages.get(error, "未知错误"))

    def _on_restart_timeout(self):
        self.run(self._name, self._command, self._work_dir)
