"""PyInstaller build script"""
import os
import PyInstaller.__main__

UNUSED = [
    "--exclude-module=tcl", "--exclude-module=tk", "--exclude-module=tkinter",
    "--exclude-module=unittest", "--exclude-module=test", "--exclude-module=pydoc",
    "--exclude-module=distutils", "--exclude-module=setuptools",
    "--exclude-module=numpy", "--exclude-module=pandas",
    "--exclude-module=matplotlib", "--exclude-module=jupyter",
    "--exclude-module=IPython", "--exclude-module=scipy",
    "--exclude-module=cv2", "--exclude-module=tensorflow",
    "--exclude-module=torch", "--exclude-module=PIL.ImageQt",
]

SHARED = [
    "--onedir",
    "--clean",
    "-y",
    "--noupx",
    "--optimize=2",
    "--noconfirm",
    "--log-level=WARN",
    *UNUSED,
]


def build_client():
    PyInstaller.__main__.run([
        "main.py",
        "--name=cmdManager",
        "--add-data=icon.png:.",
        "--add-data=icon.ico:.",
        f"--icon={os.path.abspath('icon.ico')}",
        "--windowed",
        "--hidden-import=shiboken2",
        "--hidden-import=PySide2.QtXml",
        "--hidden-import=PySide2.QtNetwork",
        "--hidden-import=PySide2.QtMultipart",
        "--exclude-module=starlette",
        "--exclude-module=pydantic_settings",
        *SHARED,
    ])


if __name__ == "__main__":
    import sys
    build_client()

