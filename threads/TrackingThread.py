from PyQt5.QtCore import  QThread, pyqtSignal
import numpy as np
import torch
import os
import time
from components.PromptVT.lib.test.tracker.PromptVT import PromptVT_onnx
import cv2 as cv

class TrkThread(QThread):
    send_img = pyqtSignal(np.ndarray)
    send_raw = pyqtSignal(np.ndarray)
    send_statistic = pyqtSignal(list)
    send_msg = pyqtSignal(str)
    send_percent = pyqtSignal(int)
    send_fps = pyqtSignal(str)
    send_ROIflag = pyqtSignal(bool)
    send_clearflag = pyqtSignal(bool)
    send_clearlabel = pyqtSignal()
    send_displayraw =pyqtSignal()
    send_closedisplayraw = pyqtSignal()

    def __init__(self):
        super(TrkThread, self).__init__()
        self.weights_dtp = './tracking/DTP.onnx'
        self.weights_template = './tracking/Template_Branch,onnx'
        self.weights_search = './tracking/Search_Branch.onnx'
        self.intervals = 20
        self.conf = 0.1
        self.search_factor = 5
        self.jump_out = False                   # jump out of the loop
        self.is_continue = True                 # continue/pause
        self.percent_length = 1000              # progress bar
        self.save_fold = './result/tracking'
        self.displayflag =  False
        self.closedisplayflag = False
        self.cam = False
        self.video =False
        self.rstp = False
        self.reset = False

    @torch.no_grad()
    def run(self,
            z_path = './pt/tracking/PromptVT_onnx/Template_Branch.onnx',
            x_path = './pt/tracking/PromptVT_onnx/Search_Branch.onnx',
            dtp_path = './pt/tracking/PromptVT_onnx/DTP.onnx'
            ):

        try:
            if(self.cam == True):
                cap = cv.VideoCapture(0)
                self.cam = False
            if(self.video == True):
                cap = cv.VideoCapture(self.source)
                self.video = False

            count = 0
            start_time = time.time()
            tracker = PromptVT_onnx(None, None, z_path, x_path, dtp_path)
            output_boxes = []
            display_name = 'DisplayTest'
            cv.namedWindow(display_name, cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
            cv.resizeWindow(display_name, 1500, 900)
            success, frame = cap.read()
            cv.imshow(display_name, frame)
            frame_disp = frame.copy()
            cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30),
                       cv.FONT_HERSHEY_COMPLEX_SMALL,
                       1.5, (0, 0, 0), 1)
            x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
            init_state = [x, y, w, h]
            cv.destroyAllWindows()
            tracker.initialize(frame, _build_init_info(init_state))
            self.reset = False
            self.send_statistic.emit(init_state)
            output_boxes.append(init_state)
            while True:
                if self.jump_out:
                    cap.release()
                    self.send_percent.emit(0)
                    self.send_msg.emit('Stop')
                    if hasattr(self, 'out'):
                        self.out.release()
                    break
                # change model

                if self.is_continue:
                    if(self.displayflag == True ):
                        self.send_displayraw.emit()
                        self.displayflag = False
                    if(self.closedisplayflag == True):
                        self.send_closedisplayraw.emit()
                        self.closedisplayflag = False

                    count += 1
                    if count % 30 == 0 and count >= 30:
                        fps = int(30 / ( time.time() - start_time ))
                        self.send_fps.emit('fps：'+str(fps))
                        start_time = time.time()

                    percent = int(count/cap.get(cv.CAP_PROP_FRAME_COUNT)*self.percent_length)
                    self.send_percent.emit(percent)
                    if (self.reset):
                        tracker = PromptVT_onnx(None, None, z_path, x_path, dtp_path)
                        output_boxes = []
                        display_name = 'DisplayTest'
                        cv.namedWindow(display_name, cv.WINDOW_NORMAL | cv.WINDOW_KEEPRATIO)
                        cv.resizeWindow(display_name, 1500, 900)
                        success, frame = cap.read()
                        cv.imshow(display_name, frame)
                        frame_disp = frame.copy()
                        cv.putText(frame_disp, 'Select target ROI and press ENTER', (20, 30),
                                   cv.FONT_HERSHEY_COMPLEX_SMALL,
                                   1.5, (0, 0, 0), 1)
                        x, y, w, h = cv.selectROI(display_name, frame_disp, fromCenter=False)
                        init_state = [x, y, w, h]
                        cv.destroyAllWindows()
                        tracker.initialize(frame, _build_init_info(init_state))
                        self.send_statistic.emit(init_state)
                        output_boxes.append(init_state)
                        self.reset = False
                    else:
                        ret, frame = cap.read()
                    if frame is None:
                        self.send_percent.emit(0)
                        self.send_msg.emit('finished')
                        if hasattr(self, 'out'):
                            self.out.release()
                        break
                    frame_disp = frame.copy()
                    out = tracker.track(frame,None,self.intervals,self.search_factor, self.conf)
                    state = [int(s) for s in out['target_bbox']]
                    output_boxes.append(state)
                    conf = out['conf']
                    if(conf > self.conf):
                        cv.rectangle(frame_disp, (state[0], state[1]), (state[2] + state[0], state[3] + state[1]),
                                 (0, 69, 255), 5)
                    self.send_raw.emit(frame if isinstance(frame, np.ndarray) else frame[0])
                    self.send_img.emit(frame_disp) #im0 : result
                    self.send_statistic.emit(state)
                    if self.save_fold:
                        os.makedirs(self.save_fold, exist_ok=True)
                        if cap is None:
                            save_path = os.path.join(self.save_fold,
                                                     time.strftime('%Y_%m_%d_%H_%M_%S',
                                                                   time.localtime()) + '.jpg')
                            cv.imwrite(save_path, frame_disp)
                        else:
                            if count == 1:
                                ori_fps = int(cap.get(cv.CAP_PROP_FPS))
                                if ori_fps == 0:
                                    ori_fps = 25
                                width, height = frame_disp.shape[1], frame_disp.shape[0]
                                save_path = os.path.join(self.save_fold, time.strftime('%Y_%m_%d_%H_%M_%S', time.localtime()) + '.mp4')
                                self.out = cv.VideoWriter(save_path, cv.VideoWriter_fourcc(*"mp4v"), ori_fps,
                                                           (width, height))
                            self.out.write(frame_disp)
                    if percent == self.percent_length:
                        print(count)
                        self.send_percent.emit(0)
                        self.send_msg.emit('finished')
                        if hasattr(self, 'out'):
                            self.out.release()
                        break

        except Exception as e:
            print(e)
            self.send_msg.emit('%s' % e)

def _build_init_info(box):
    return {'init_bbox': box}