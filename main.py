from PyQt5.QtWidgets import QApplication, QMainWindow
from main_win.new_firstmain import  Ui_MainWindow
from PyQt5.QtCore import Qt, QTimer
from mainDetection import detMainWindow
from mainTracking import trkMainWindow
import sys

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.m_flag = False
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.minButton_4.clicked.connect(self.showMinimized)
        self.maxButton_4.clicked.connect(self.max_or_restore)
        self.closeButton_4.clicked.connect(self.close)
        self.pushButton.clicked.connect(self.open_detection)
        self.pushButton_3.clicked.connect(self.open_tracking)
        self.qtimer = QTimer(self)
        self.qtimer.setSingleShot(True)
        self.qtimer.timeout.connect(lambda: self.statistic_label.clear())
        self.mousePressed = False
        self.oldPos = self.pos()

        self.det_window = None
        self.trk_window = None

    def open_detection(self):
        self.hide()
        self.det_window = detMainWindow()
        self.det_window.closed.connect(self.show_main_window)
        self.det_window.show()
    def open_tracking(self):
        self.hide()
        self.trk_window = trkMainWindow()
        self.trk_window.closed.connect(self.show_main_window)
        self.trk_window.show()

    def show_main_window(self):
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousePressed = True
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.mousePressed and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self.oldPos
            self.move(self.pos() + delta)
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mousePressed = False

    def max_or_restore(self):
        if self.maxButton.isChecked():
            self.showMaximized()
        else:
            self.showNormal()

if __name__ == "__main__":

    app = QApplication(sys.argv)
    myWin = MainWindow()
    myWin.show()
    sys.exit(app.exec_())

import appr.apprcc