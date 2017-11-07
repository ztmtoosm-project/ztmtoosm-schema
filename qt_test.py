#!/usr/bin/env python3

# http://zetcode.com/gui/pyqt4/drawing/
# https://pl.python.org/forum/index.php?topic=6010.msg25683#msg25683

# maybe better to use QGraphicsView, QGraphicsScene, QGraphicsItem

import sys
import math
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from map_canvas import PainterLine, MapCanvas

my_canvases = []

class MyCanvas(MapCanvas):
    def __init__(self, width, height):
        MapCanvas.__init__(self, width, height)
        self.selection_x1 = None
        self.selection_y1 = None
        self.selection_x2 = None
        self.selection_y2 = None
        self.selected_object = None
        self.move = False

    '''
    def drawHexagon(self, event, qp, args):

        # change border color
        if args['color']:
            qp.setPen(QtGui.QColor(args['color']))
        else:
            qp.setPen(QtCore.Qt.NoPen)
    '''

    def mousePressEvent(self, event):
        print("release!!!")
        # print('pressed:', event.button())
        distance, foo = self.getClosestObject(event.x(), event.y())
        print(distance)
        if distance < 10:
            if self.selected_object is not None:
                self.selected_object.clear_selection()
            self.selected_object = foo
            self.selected_object.select()
        else:
            if self.selected_object is not None:
                self.selected_object.clear_selection()
                self.selected_object = None
            self.move = True
            self.selection_x1 = event.x()
            self.selection_y1 = event.y()
        self.update()
    def mouseReleaseEvent(self, event):
        if self.move:
            self.selection_x2 = event.x()
            self.selection_y2 = event.y()
            self.move = False
            for x in my_canvases:
                x.position = x.position.shiftCopy(self.selection_x2 - self.selection_x1, self.selection_y2 - self.selection_y1)
                x.update()

    def mouseMoveEvent(self, event):
        self.currentx = event.x()
        self.currenty = event.y()


    def pluss(self):
        if self.position.zoom == 18:
            return
        self.position = self.position.shiftCopy(self.currentx * -1, self.currenty * -1).zoomIn().shiftCopy(self.currentx, self.currenty)
        self.update()

    def minuss(self):
        if self.position.zoom == 10:
            return
        self.position = self.position.shiftCopy(self.currentx * -1, self.currenty * -1).zoomOut().shiftCopy(self.currentx, self.currenty)
        self.update()


class App(QtGui.QWidget):
    def __init__(self):
        super(App, self).__init__()
        self.initUI()

    def initUI(self):

        self.vbox = QtGui.QVBoxLayout(self)
        self.setLayout(self.vbox)

        # --- canvas - created to get tool list ---

        self.canvas = MyCanvas(1000, 700)
        #self.canvas2 = MyCanvas(500, 400)
        global my_canvases
        my_canvases = [self.canvas]

        # --- tool buttons ---

        self.hboxTools = QtGui.QHBoxLayout()

        '''
        for name, shape in self.canvas.tools:
            btn = QtGui.QPushButton(name)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda x, s=shape: self.canvas.setShape(s))
            self.hboxTools.addWidget(btn)

            if name == 'Rectangle':
                btn.setChecked(True)
        '''
        self.btnToolsGroup = QtGui.QGroupBox("Tool")
        self.btnToolsGroup.setLayout(self.hboxTools)
        self.vbox.addWidget(self.btnToolsGroup)

        # --- canvas - add to window ---

        self.vbox.addWidget(self.canvas)
        #self.vbox.addWidget(self.canvas2)

        # --- color buttons ----

        self.hboxColors = QtGui.QHBoxLayout()

        '''
        for name, color in self.canvas.pallete:

            btn = QtGui.QPushButton(name, self)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda x, c=color: self.canvas.setColor(c))
            self.hboxColors.addWidget(btn)

            if name == 'Black':
                btn.setChecked(True)
        '''
        self.btnColorsGroup = QtGui.QGroupBox("Border")
        self.btnColorsGroup.setLayout(self.hboxColors)
        self.vbox.addWidget(self.btnColorsGroup)

        # --- fill buttons ----

        self.hboxFills = QtGui.QHBoxLayout()
        '''
        for name, color in self.canvas.pallete:

            btn = QtGui.QPushButton(name, self)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.clicked.connect(lambda x, c=color: self.canvas.setFill(c))
            self.hboxFills.addWidget(btn)

            if name == 'None':
                btn.setChecked(True)
        '''
        self.btnFillsGroup = QtGui.QGroupBox("Fill")
        self.btnFillsGroup.setLayout(self.hboxFills)
        self.vbox.addWidget(self.btnFillsGroup)

        # ---

        # self.setGeometry(300, 300, 600, 170)
        self.setWindowTitle('MyCanvas')
        self.show()


    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Plus :
            self.canvas.pluss()
        if key == QtCore.Qt.Key_Minus :
            self.canvas.minuss()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())

#    52.3148, 20.8431
#   52.1263, 21.2585