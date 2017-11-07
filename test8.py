from libmrc2 import part_mn, HebelkiDfs, hebelek_in_zakres, PackAllMy, srumpy
from svgpathtools import Path, Line, QuadraticBezier, CubicBezier, Arc, wsvg

import shapely.geometry
import shapely.affinity
import shapely.wkb as wkb

import sys
import math
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *

from lluk import LLuk
from pazur import Pazur
from map_canvas import PainterLine, MapCanvas, PainterLLuk

my_canvases = []

class PainterLineNormal(PainterLine):
    def __init__(self, x1, y1, x2, y2, color=QtGui.QColor('black'), stroke=1):
        PainterLine.__init__(self, x1, y1, x2, y2, color, stroke)
    def getDistance(self, position):
        return 2000

class Canvas1(MapCanvas):
    def __init__(self, width, height):
        MapCanvas.__init__(self, width, height)
        self.positions = []
        self.paint_tiles = False
        self.mode = 0

    def mousePressEvent(self, event):
        pos = self.position.shiftCopy(event.x() * -1, event.y() * -1).get_coordinates()
        self.positions.append(pos)
        if self.mode == 1:
            xxx = []
            xxx.extend(PainterLineNormal.tmp_convert1(self.positions[0]))
            xxx.extend(PainterLineNormal.tmp_convert1(self.positions[1]))
            self.shapes.add(PainterLineNormal(xxx[0], xxx[1], xxx[2], xxx[3]))
        if self.mode == 3:
            self.shapes.clear()
            xxx = []
            xxx.extend(PainterLineNormal.tmp_convert1(self.positions[0]))
            xxx.extend(PainterLineNormal.tmp_convert1(self.positions[1]))
            xxx.extend(PainterLineNormal.tmp_convert1(self.positions[2]))
            xxx.extend(PainterLineNormal.tmp_convert1(self.positions[3]))
            self.shapes.add(PainterLineNormal(xxx[0], xxx[1], xxx[2], xxx[3]))
            self.shapes.add(PainterLineNormal(xxx[4], xxx[5], xxx[6], xxx[7]))
            dtt = LLuk.create_lluk_special([(xxx[0], xxx[1]), (xxx[2], xxx[3]), (xxx[4], xxx[5]), (xxx[6], xxx[7])], 60, 2000)
            ls = dtt[0].get_shapely_linestring(70)
            bef = None
            for x in ls.coords:
                if bef is not None:
                    my_canvases[1].shapes.add(PainterLine(bef[0], bef[1], x[0], x[1]))
                bef = x

            my_canvases[1].shapes.add(PainterLine(dtt[1][0], dtt[1][1], dtt[2][0], dtt[2][1]))
            self.positions = []
        self.mode += 1
        self.mode %= 4
        self.update()
        my_canvases[1].update()

    def mouseReleaseEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pass

    def pluss(self):
        if self.position.zoom == 18:
            return
        self.position = self.position.shiftCopy(self.currentx * -1, self.currenty * -1).zoomIn().shiftCopy(self.currentx, self.currenty)
        for x in my_canvases:
            x.position = self.position
            x.update()

    def minuss(self):
        self.position = self.position.shiftCopy(self.currentx * -1, self.currenty * -1).zoomOut().shiftCopy(self.currentx, self.currenty)
        self.update()
        for x in my_canvases:
            x.position = self.position
            x.update()


class Canvas2(MapCanvas):
    def __init__(self, width, height):
        MapCanvas.__init__(self, width, height)
        self.selection_x1 = None
        self.selection_y1 = None
        self.selection_x2 = None
        self.selection_y2 = None
        self.selected_object = None
        self.paint_tiles = False

    def mousePressEvent(self, event):
        # print('pressed:', event.button())
        self.selection_x1 = event.x()
        self.selection_y1 = event.y()
        self.update()

    def mouseReleaseEvent(self, event):
        self.selection_x2 = event.x()
        self.selection_y2 = event.y()
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
        for x in my_canvases:
            x.position = self.position
            x.update()

    def minuss(self):
        #if self.position.zoom == 10:
        #    return
        self.position = self.position.shiftCopy(self.currentx * -1, self.currenty * -1).zoomOut().shiftCopy(self.currentx, self.currenty)
        self.update()
        for x in my_canvases:
            x.position = self.position
            x.update()


class App(QtGui.QWidget):
    def __init__(self):
        super(App, self).__init__()
        self.initUI()

    def initUI(self):

        self.vbox = QtGui.QVBoxLayout(self)
        self.hbox = QtGui.QHBoxLayout(self)
        self.setLayout(self.vbox)

        # --- canvas - created to get tool list ---

        self.canvas = Canvas1(620, 600)
        self.canvas2 = Canvas2(620, 600)
        global my_canvases
        my_canvases = [self.canvas, self.canvas2]

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
        self.vbox.addLayout(self.hbox)
        # --- canvas - add to window ---

        self.hbox.addWidget(self.canvas)
        self.hbox.addWidget(self.canvas2)

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
            self.canvas2.pluss()
        if key == QtCore.Qt.Key_Minus :
            self.canvas2.minuss()
'''
conn = psycopg2.connect(dbname="nexty", user="marcin")

cur = conn.cursor()
x = input('What is your name?')
x = '%'+x+'%'
print(x)
cur.execute('SELECT * FROM OPERATOR_STOPS WHERE NAME LIKE %s', [x]);
abc = cur.fetchall()
for x in abc:
    print('Id: {0} o nazwie {1}'.format(x[0], x[1]))
x = input('give me id')
cur.execute("SELECT x, y FROM OSM_PATHS, nicepaths_node_coordinates_normalized niz WHERE ref_begin=%s AND node_id=id AND ORDINAL_ID=1;"
, [x]);
abc = cur.fetchall()
xxx = 0
yyy = 0
for x in abc:
    xxx = x[0]
    yyy = x[1]

print(xxx)
print(yyy)
'''

if __name__ == '__main__':


    app = QtGui.QApplication(sys.argv)
    ex = App()



                #my_canvases[1].shapes.add(PainterLineNormal(x1, y1, x2, y2, QtGui.QColor("black"), 1))
    sys.exit(app.exec_())