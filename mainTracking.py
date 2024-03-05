from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMenu, QAction
from main_win.trkWin import Ui_mainWindow
from PyQt5.QtCore import Qt, QPoint, QTimer,pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import sys
import json
import os
from cv2 import resize, cvtColor, COLOR_BGR2RGB
from threads.TrackingThread import  TrkThread
from utils.CustomMessageBox import MessageBox
from utils.capnums import Camera
from dialog.rtsp_win import Window


class trkMainWindow(QMainWindow, Ui_mainWindow):
    closed = pyqtSignal()
    def __init__(self, parent=None):
        super(trkMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.m_flag = False
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint
                            | Qt.WindowSystemMenuHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.minButton.clicked.connect(self.showMinimized)
        self.maxButton.clicked.connect(self.max_or_restore)
        # show Maximized window
        self.maxButton.animateClick(10)
        self.closeButton.clicked.connect(self.close)

        self.qtimer = QTimer(self)
        self.qtimer.setSingleShot(True)
        self.qtimer.timeout.connect(lambda: self.statistic_label.clear())

        self.comboBox.clear()
        self.pt_list = os.listdir(os.path.join(os.getcwd(), './pt/tracking/'))
        self.pt_list = [file for file in self.pt_list if file.endswith('')]
        self.pt_list.sort(key=lambda x: os.path.getsize(os.path.join(os.getcwd(), './pt/tracking/') + x))
        self.comboBox.clear()
        self.comboBox.addItems(self.pt_list)
        self.qtimer_search = QTimer(self)
        self.qtimer_search.timeout.connect(lambda: self.search_pt())
        self.qtimer_search.start(2000)


        self.trk_thread = TrkThread()
        self.model_type = self.comboBox.currentText()
        self.trk_thread.source = '0'
        self.trk_thread.percent_length = self.progressBar.maximum() #进度条
        self.trk_thread.send_raw.connect(lambda x: self.show_image(x, self.raw_video))
        self.trk_thread.send_img.connect(lambda x: self.show_image(x, self.VIDEO))
        self.trk_thread.send_statistic.connect(self.show_statistic)
        self.trk_thread.send_msg.connect(lambda x: self.show_msg(x))
        self.trk_thread.send_percent.connect(lambda x: self.progressBar.setValue(x))
        self.trk_thread.send_fps.connect(lambda x: self.fps_label.setText(x))
        self.trk_thread.send_ROIflag.connect(lambda x: self.VIDEO.updateROIflag(x))
        self.trk_thread.send_clearflag.connect(lambda x: self.VIDEO.clearflag(x))
        self.trk_thread.send_clearlabel.connect(lambda : self.VIDEO.clearlabel())
        self.trk_thread.send_displayraw.connect(lambda  : self.splitter.setSizes([self.splitter.size().width() // 2, self.splitter.size().width() // 2]))
        self.trk_thread.send_closedisplayraw.connect(lambda: self.splitter.setSizes([0, self.splitter.size().width() ]))
        self.fileButton.clicked.connect(self.open_file)
        self.fileButton.clicked.connect(lambda :self.resultWidget.clear())
        self.fileButton.clicked.connect(lambda : self.setVideo())
        self.resetButton.clicked.connect(lambda: self.setReset())
        self.cameraButton.clicked.connect(self.chose_cam)
        self.cameraButton.clicked.connect(lambda : self.setCam())
        self.cameraButton.clicked.connect(lambda :self.resultWidget.clear())
        self.rtspButton.clicked.connect(self.chose_rtsp)  #
        self.rtspButton.clicked.connect(lambda :self.resultWidget.clear())
        self.rtspButton.clicked.connect(lambda: self.setVideo())
        self.runButton.clicked.connect(self.run_or_continue)
        self.stopButton.clicked.connect(self.stop)
        self.stopButton.clicked.connect(lambda :self.resultWidget.clear())
        self.comboBox.currentTextChanged.connect(self.change_model)
        self.confSpinBox.valueChanged.connect(lambda x: self.change_val(x, 'confSpinBox'))
        self.confSlider.valueChanged.connect(lambda x: self.change_val(x, 'confSlider'))
        self.iouSpinBox.valueChanged.connect(lambda x: self.change_val(x, 'iouSpinBox'))
        self.iouSlider.valueChanged.connect(lambda x: self.change_val(x, 'iouSlider'))
        self.checkBox.clicked.connect(self.checkrate)
        self.saveCheckBox.clicked.connect(self.is_save)
        self.load_setting()

    def search_pt(self):
        pt_list = os.listdir(os.path.join(os.getcwd(), './pt/tracking/'))
        pt_list = [file for file in pt_list if file.endswith('')]
        pt_list.sort(key=lambda x: os.path.getsize(os.path.join(os.getcwd(), './pt/tracking/' + x)))
        if pt_list != self.pt_list:
            self.pt_list = pt_list
            self.comboBox.clear()
            self.comboBox.addItems(self.pt_list)

    def is_save(self):
        if self.saveCheckBox.isChecked():
            path = os.path.join(os.getcwd(), 'result/tracking')
            self.trk_thread.save_fold = path
        else:
            self.trk_thread.save_fold = None

    def checkrate(self):
        if self.checkBox.isChecked():
            self.trk_thread.displayflag =True
        else:
            self.trk_thread.closedisplayflag=True

    def setCam(self):
        self.trk_thread.cam=True

    def setVideo(self):
        self.trk_thread.video =True


    def setReset(self):
        self.trk_thread.reset =True


    def chose_rtsp(self):
        self.rtsp_window = Window()
        path =  os.path.join(os.getcwd(), 'config/ip.json')
        config_file = path
        if not os.path.exists(config_file):
            ip = "rtsp://admin:admin888@192.168.1.67:555"
            new_config = {"ip": ip}
            new_json = json.dumps(new_config, ensure_ascii=False, indent=2)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_json)
        else:
            config = json.load(open(config_file, 'r', encoding='utf-8'))
            ip = config['ip']
        self.rtsp_window.rtspEdit.setText(ip)
        self.rtsp_window.show()
        self.rtsp_window.rtspButton.clicked.connect(lambda: self.load_rtsp(self.rtsp_window.rtspEdit.text()))

    def load_rtsp(self, ip):
        try:
            self.stop()
            MessageBox(
                self.closeButton, title='Tips', text='Loading rtsp stream', time=1000, auto=True).exec_()
            self.trk_thread.source = ip
            path = os.path.join(os.getcwd(), 'config/ip.json')
            new_config = {"ip": ip}
            new_json = json.dumps(new_config, ensure_ascii=False, indent=2)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_json)
            self.statistic_msg('Loading rtsp：{}'.format(ip))
            self.rtsp_window.close()
        except Exception as e:
            self.statistic_msg('%s' % e)

    def chose_cam(self):
        try:
            self.stop()
            MessageBox(
                self.closeButton, title='Tips', text='Loading camera', time=2000, auto=True).exec_()
            # get the number of local cameras
            _, cams = Camera().get_cam_num()
            popMenu = QMenu()
            popMenu.setFixedWidth(self.cameraButton.width())
            popMenu.setStyleSheet('''
                                            QMenu {
                                            font-size: 16px;
                                            font-family: "Microsoft YaHei UI";
                                            font-weight: light;
                                            color:white;
                                            padding-left: 5px;
                                            padding-right: 5px;
                                            padding-top: 4px;
                                            padding-bottom: 4px;
                                            border-style: solid;
                                            border-width: 0px;
                                            border-color: rgba(255, 255, 255, 255);
                                            border-radius: 3px;
                                            background-color: rgba(200, 200, 200,50);}
                                            ''')

            for cam in cams:
                exec("action_%s = QAction('%s')" % (cam, cam))
                exec("popMenu.addAction(action_%s)" % cam)

            x = self.groupBox_5.mapToGlobal(self.cameraButton.pos()).x()
            y = self.groupBox_5.mapToGlobal(self.cameraButton.pos()).y()
            y = y + self.cameraButton.frameGeometry().height()
            pos = QPoint(x, y)
            action = popMenu.exec_(pos)
            if action:
                self.trk_thread.source = action.text()
                self.statistic_msg('Loading camera：{}'.format(action.text()))
        except Exception as e:
            self.statistic_msg('%s' % e)

    def load_setting(self):
        path = os.path.join(os.getcwd(), 'config/trksetting.json')
        config_file = path
        if not os.path.exists(config_file):
            searchfactor = 4.0
            conf = 0.33
            rate = 10
            check = 0
            savecheck = 0
            new_config = {"searchfactor": searchfactor,
                          "conf": conf,
                          "rate": rate,
                          "check": check,
                          "savecheck": savecheck
                          }
            new_json = json.dumps(new_config, ensure_ascii=False, indent=2)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_json)
        else:
            config = json.load(open(config_file, 'r', encoding='utf-8'))
            if len(config) != 5:
                searchfactor = 4.0
                conf = 0.
                rate = 10
                check = 0
                savecheck = 0
            else:
                searchfactor = config['searchfactor']
                conf = config['conf']
                rate = config['rate']
                check = config['check']
                savecheck = config['savecheck']
        self.confSpinBox.setValue(conf)
        self.iouSpinBox.setValue(searchfactor)
        self.checkBox.setCheckState(check)
        self.trk_thread.rate_check = check
        self.saveCheckBox.setCheckState(savecheck)
        self.is_save()

    def change_val(self, x, flag):
        if flag == 'confSpinBox':
            self.confSlider.setValue(int(x*100))
        elif flag == 'confSlider':
            self.confSpinBox.setValue(x/100)
            self.trk_thread.conf = x/100
        elif flag == 'iouSpinBox':
            self.iouSlider.setValue(int(x*100))
        elif flag == 'iouSlider':
            self.iouSpinBox.setValue(x/100)
            self.trk_thread.search_factor = x/100
        elif flag == 'rateSpinBox':
            self.rateSlider.setValue(x)
        elif flag == 'rateSlider':
            self.rateSpinBox.setValue(x)
            self.trk_thread.rate = x * 10
        else:
            pass

    def statistic_msg(self, msg):
        self.statistic_label.setText(msg)
        # self.qtimer.start(3000)

    def show_msg(self, msg):
        self.runButton.setChecked(Qt.Unchecked)
        self.statistic_msg(msg)
        if msg == "Finished":
            self.saveCheckBox.setEnabled(True)

    def change_model(self, x):
        self.model_type = self.comboBox.currentText()
        self.trk_thread.weights = "./pt/%s" % self.model_type
        self.statistic_msg('Change model to %s' % x)

    def open_file(self):
        path = os.path.join(os.getcwd(), 'config/fold.json')
        config_file = path
        config = json.load(open(config_file, 'r', encoding='utf-8'))
        open_fold = config['open_fold']
        if not os.path.exists(open_fold):
            open_fold = os.getcwd()
        name, _ = QFileDialog.getOpenFileName(self, 'Video/image', open_fold, "Pic File(*.mp4 *.mkv *.avi *.flv "
                                                                          "*.jpg *.png)")
        if name:
            self.trk_thread.source = name
            self.statistic_msg('Loaded file：{}'.format(os.path.basename(name)))
            config['open_fold'] = os.path.dirname(name)
            config_json = json.dumps(config, ensure_ascii=False, indent=2)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_json)
            self.stop()

    def max_or_restore(self):
        if self.maxButton.isChecked():
            self.showMaximized()
        else:
            self.showNormal()



    def run_or_continue(self):
        self.trk_thread.jump_out = False
        if self.runButton.isChecked():
            self.saveCheckBox.setEnabled(False)
            self.trk_thread.is_continue = True
            if not self.trk_thread.isRunning():
                self.trk_thread.start()
            source = os.path.basename(self.trk_thread.source)
            source = 'camera' if source.isnumeric() else source
            self.statistic_msg('Tracking >> model：{}，file：{}'.
                               format(os.path.basename('PromptVT.onnx'),
                                      source))

        else:
            self.trk_thread.is_continue = False
            self.statistic_msg('Pause')

    def stop(self):
        self.trk_thread.jump_out = True
        self.saveCheckBox.setEnabled(True)

    def mousePressEvent(self, event):
        self.m_Position = event.pos()
        if event.button() == Qt.LeftButton:
            if 0 < self.m_Position.x() < self.groupBox.pos().x() + self.groupBox.width() and \
                    0 < self.m_Position.y() < self.groupBox.pos().y() + self.groupBox.height():
                self.m_flag = True

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_flag = False

    @staticmethod
    def show_image(img_src, label):
        try:
            ih, iw, _ = img_src.shape
            w = label.geometry().width()
            h = label.geometry().height()
            # keep original aspect ratio
            if iw/w > ih/h:
                scal = w / iw
                nw = w
                nh = int(scal * ih)
                img_src_ = resize(img_src, (nw, nh))
            else:
                scal = h / ih
                nw = int(scal * iw)
                nh = h
                img_src_ = resize(img_src, (nw, nh))
            frame = cvtColor(img_src_, COLOR_BGR2RGB)
            img = QImage(frame.data, frame.shape[1], frame.shape[0], frame.shape[2] * frame.shape[1],
                         QImage.Format_RGB888)
            label.setPixmap(QPixmap.fromImage(img))

        except Exception as e:
            print(repr(e))

    def show_statistic(self, statistic_dic):
        results = [str(statistic_dic[0]) + ',' + str(statistic_dic[1]) + ',' + str(statistic_dic[2]) + ',' + str(statistic_dic[2])]
        self.resultWidget.addItems(results)
        self.resultWidget.scrollToBottom()


    def closeEvent(self, event):
        self.trk_thread.jump_out = True
        path = os.path.join(os.getcwd(), 'config/setting.json')
        config_file = path
        config = dict()
        config['iou'] = self.confSpinBox.value()
        config['conf'] = self.iouSpinBox.value()
        config['check'] = self.checkBox.checkState()
        config['savecheck'] = self.saveCheckBox.checkState()
        config_json = json.dumps(config, ensure_ascii=False, indent=2)
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_json)
        MessageBox(
            self.closeButton, title='Tips', text='Closing the program', time=500, auto=True).exec_()
        self.closed.emit()






if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin = trkMainWindow()
    myWin.show()
    # myWin.showMaximized()
    sys.exit(app.exec_())
