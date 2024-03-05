from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt,QRect,pyqtSignal
from PyQt5.QtGui import QPainter,QPen



class Label(QLabel):
    x0=0
    y0=0
    x1=0
    y1=0
    open_mouse_flag=False
    select_roi_flag=False
    draw_roi_flag=False
    clear_flag=False
    rect = QRect()
    #send_co = pyqtSignal(int,int,int,int)


    #按下鼠标
    def mousePressEvent(self, event):
        if self.open_mouse_flag is True:
            self.select_roi_flag= True
            self.x0=event.x()
            self.y0=event.y()

    #释放鼠标
    def mouseReleaseEvent(self, event):
        self.select_roi_flag=False

    #移动鼠标
    def mouseMoveEvent(self, event):
        if self.select_roi_flag is True:
            self.x1=event.x()
            self.y1=event.y()
            if self.draw_roi_flag is True:
                self.update()

    #绘制事件
    def paintEvent(self,event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 5, Qt.SolidLine))
        if self.clear_flag is True:
            self.x0=0
            self.y0=0
            self.x1=0
            self.y1=0
        self.rect = QRect(self.x0, self.y0, abs(self.x1 - self.x0), abs(self.y1 - self.y0))
        painter.drawRect(self.rect)
        self.update()

    def updateROIflag(self, flag):
        if(flag == True):
            self.open_mouse_flag = True
            self.select_roi_flag = True
            self.draw_roi_flag = True
        if (flag == False):
            self.open_mouse_flag = False
            self.select_roi_flag = False
            self.draw_roi_flag = False

    def clearflag(self,flag):
        self.clear_flag == flag

    def clearlabel(self):
        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.rect = QRect(self.x0, self.y0, abs(self.x1 - self.x0), abs(self.y1 - self.y0))
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 5, Qt.SolidLine))
        painter.drawRect(self.rect)
        self.update()


    def get_rect_coordinates(self):
            x = min(self.x0, self.x1)
            y = min(self.y0, self.y1)
            width = abs(self.x0 - self.x1)
            height = abs(self.y0 - self.y1)
            self.send_co.emit(x, y, width, height)


