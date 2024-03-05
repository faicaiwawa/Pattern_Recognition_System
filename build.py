import sys
from PyQt5.QtWidgets import QApplication
import main

app = QApplication(sys.argv)
main_window = main.MainWindow()
main_window.show()

# 打包应用程序
import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--windowed',
    '--onefile',
    '--add-data', 'appr;appr',
    '--add-data', 'components;components',
    '--add-data', 'config;config',
    '--add-data', 'dialog;dialog',
    '--add-data', 'icon;icon',
    '--add-data', 'main_win;main_win',
    '--add-data', 'models;models',
    '--add-data', 'pt;pt',
    '--add-data', 'threads;threads',
    '--add-data', 'utils;utils',

])
