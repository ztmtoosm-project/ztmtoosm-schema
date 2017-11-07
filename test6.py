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
from map_canvas import PainterLine, PainterLLuk, MapCanvas

from shapely import speedups

my_canvases = []

class PainterLineNormal(PainterLine):
    def __init__(self, x1, y1, x2, y2, color=QtGui.QColor('black'), stroke=1):
        PainterLine.__init__(self, x1, y1, x2, y2, color, stroke)
    def getDistance(self, position):
        return 2000

class PainterLinePazur(PainterLine):
    def __init__(self, x1, y1, x2, y2, color=QtGui.QColor('black'), stroke=1, pazur=None):
        PainterLine.__init__(self, x1, y1, x2, y2, color, stroke)
        self.pazur = pazur
    def select(self):
        my_canvases[1].shapes.clear()
        drawPazur(self.pazur, my_canvases[1].shapes)
        my_canvases[1].update()
        self.selected = True

class PainterLineHebelek(PainterLine):
    def __init__(self, x1, y1, x2, y2, color=QtGui.QColor('black'), stroke=1, hebelek=None):
        PainterLine.__init__(self, x1, y1, x2, y2, color, stroke)
        self.hebelek = hebelek
    def select(self):
        print("========")
        print(self.hebelek)
        print("before:")
        for x in self.hebelek.bef:
            print(x)
        print("after:")
        for x in self.hebelek.nast:
            print(x)
        for aaa, x in trasy.items():
            contains = False
            for c in x.hebelki:
                for a, b in c:
                    if b == self.hebelek:
                        contains = True
            if contains:
                print("LINIA " + str(x.lineid) + " " + str(x.wariant))
                print(len(x.hebelki2))
                for z in x.hebelki2:
                    print("^^^")
                    for zz in z:
                        print(zz)
        my_canvases[1].update()
        self.selected = True

class MyCanvas(MapCanvas):
    def __init__(self, width, height):
        MapCanvas.__init__(self, width, height)
        self.selection_x1 = None
        self.selection_y1 = None
        self.selection_x2 = None
        self.selection_y2 = None
        self.selected_object = None
        self.move = False
        self.paint_tiles = False

    def mousePressEvent(self, event):
        # print('pressed:', event.button())
        distance, foo = self.getClosestObject(event.x(), event.y())
        if distance < 10:
            if self.selected_object is not None:
                self.selected_object.clear_selection()
            self.selected_object = foo
            self.selected_object.select()
        else:
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

        self.canvas = MyCanvas(620, 600)
        self.canvas2 = MyCanvas(620, 600)
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
            self.canvas.pluss()
        if key == QtCore.Qt.Key_Minus :
            self.canvas.minuss()
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
def manage_vals(id, cbc):
    if cbc not in dfs_costam.hebelki_longline:
        if cbc not in dfs_costam.artic:
            return "yellow"
    return "black"

def drawPazur(p, canvas_shapes):
    print(p.get_hash())
    bef = None
    for x in p.hebelek_list:
        if bef is not None:
            x1, y1 = bef.get_average_point().coords[0]
            x2, y2 = x.get_average_point().coords[0]
            #canvas_shapes.add(PainterLineNormal(x1, y1, x2, y2, QtGui.QColor("black"), 3))
        bef = x
    for x in p.pazur_start:
        x1, y1 = x.get_average_point().coords[0]
        x2, y2 = p.hebelek_list[0].get_average_point().coords[0]
        #canvas_shapes.add(PainterLineNormal(x1, y1, x2, y2, QtGui.QColor("black"), 1))
    for x in p.pazur_stop:
        x1, y1 = x.get_average_point().coords[0]
        x2, y2 = p.hebelek_list[-1].get_average_point().coords[0]
        #canvas_shapes.add(PainterLineNormal(x1, y1, x2, y2, QtGui.QColor("black"), 1))

    for y in p.core_linestring_set:
        bef = None
        for x in y.coords:
            if bef is not None:
                x1, y1 = bef
                x2, y2 = x
                canvas_shapes.add(PainterLineNormal(x1, y1, x2, y2))
            bef = x

    for a in p.hebelek_list:
        x1, y1 = a.linestring.coords[0]
        x2, y2 = a.linestring.coords[1]
        canvas_shapes.add(PainterLineHebelek(x1, y1, x2, y2, QtGui.QColor('blue'), hebelek=a))

    for a in p.man_rect:
        try:
            bef = a.rectangle.exterior.coords[-1]
            for x in a.rectangle.exterior.coords:
                if bef is not None:
                    x1, y1 = bef
                    x2, y2 = x
                    canvas_shapes.add(PainterLineNormal(x1, y1, x2, y2, QtGui.QColor('red'), 2))
                bef = x
        except Exception:
            pass

    if p.luck2 is not None:
        if len(p.luck2.exterior.coords) > 0:
            bef = p.luck2.exterior.coords[-1]
            for x in p.luck2.exterior.coords:
                if bef is not None:
                    my_canvases[1].shapes.add(PainterLineNormal(bef[0], bef[1], x[0], x[1]))
                bef = x


if __name__ == '__main__':

    hebelki_all, lamane, trasy = part_mn(True)
    dfs_costam = HebelkiDfs(hebelki_all)

    svg = False

    if svg:
        colors = ""
        paths = []
        stroke_widths = []
        srodes = []
        radii = []
        for a in hebelki_all:
            if hebelek_in_zakres(a, 30000, 30000, 2000):
                current_color = "k"
                colors = colors + "c"
                stroke_widths.append(1)
                paths.append(Line(srumpy(a.linestring.coords[0]), srumpy(a.linestring.coords[1])))
                zzz = a.get_average_point().coords[0]
                if a not in dfs_costam.hebelki_longline:
                    if a not in dfs_costam.artic:
                        srodes.append(srumpy(a.get_average_point().coords[0]))
                        radii.append(5)
                if a in dfs_costam.hebelki_map:
                    vals = dfs_costam.hebelki_map[a]
                    current_color = manage_vals(vals, a)
                current_color1 = current_color
                for b in a.nast:
                    current_color = current_color1
                    if b in dfs_costam.hebelki_map:
                        vals = dfs_costam.hebelki_map[b]
                        current_color = manage_vals(vals, a)
                    lenx = shapely.geometry.LineString([a.get_average_point().coords[0], b.get_average_point().coords[0]]).length
                    paths.append(Line(srumpy(a.get_average_point().coords[0]), srumpy(b.get_average_point().coords[0])))
                    if lenx > 70:
                        stroke_widths.append(3.5)
                    else:
                        stroke_widths.append(1)
                    colors = colors + current_color
        wsvg(paths, colors=colors, nodes=srodes, node_radii=radii, filename='output1.svg', stroke_widths=stroke_widths)
    else:
        print(speedups.available)
        speedups.enable()
        app = QtGui.QApplication(sys.argv)
        ex = App()



        for p in Pazur.create_pazurs(trasy, hebelki_all):

            if p.luck is not None:
                my_canvases[0].shapes.add(PainterLLuk(p.luck))





            bef = None
            for x in p.hebelek_list:
                if bef is not None:
                    x1, y1 = bef.get_average_point().coords[0]
                    x2, y2 = x.get_average_point().coords[0]
                    collor = "black"
                    my_canvases[0].shapes.add(PainterLinePazur(x1, y1, x2, y2, QtGui.QColor(collor), 1, p))
                bef = x

            for a, b, c in p.luck3:
                if a is None:
                    my_canvases[0].shapes.add(PainterLineNormal(b[0], b[1], c[0], c[1], QtGui.QColor("blue"), 3))
                else:
                    my_canvases[0].shapes.add(PainterLLuk(a))

            if p.best_bef is not None:
                x = (p.hebelek_list[0].get_average_point().coords[0], p.best_bef[0].hebelek_list[p.best_bef[1]].get_average_point().coords[0])
                my_canvases[0].shapes.add(PainterLineNormal(x[0][0], x[0][1], x[1][0], x[1][1], QtGui.QColor('black'), 3))
            if p.best_nex is not None:
                x = (p.hebelek_list[-1].get_average_point().coords[0], p.best_nex[0].hebelek_list[p.best_nex[1]].get_average_point().coords[0])
                my_canvases[0].shapes.add(PainterLineNormal(x[0][0], x[0][1], x[1][0], x[1][1], QtGui.QColor('black'), 3))

            '''
            try:
                bef = None
                rml = p.get_rects_main_line()
                if len(rml) == 1:
                    x = rml[0]
                    my_canvases[0].shapes.add(PainterLineNormal(x[0][0], x[0][1], x[1][0], x[1][1], QtGui.QColor('blue'), 3))
                for x in rml:
                    try:
                        if bef is not None:
                            luck = LLuk.create_lluk_special([bef[0], bef[1], x[0], x[1]], 50)
                            my_canvases[0].shapes.add(PainterLLuk(luck[0]))
                            my_canvases[0].shapes.add(PainterLineNormal(luck[1][0], luck[1][1], luck[2][0], luck[2][1], QtGui.QColor('blue'), 3))
                        bef = x
                    except Exception as e:
                        print('Handling run-time error:', e)
                        bef = None
                if len(rml) > 0:
                    for p2, mode in p.ancestor_bef:
                        if len(p2.get_rects_main_line()) > 0:
                            bef = p2.get_rects_main_line()[mode]
                            x = p.get_rects_main_line()[0]
                            try:
                                if bef is not None:
                                    luck = LLuk.create_lluk_special([bef[0], bef[1], x[0], x[1]], 50)
                                    my_canvases[0].shapes.add(PainterLLuk(luck[0]))
                                    my_canvases[0].shapes.add(
                                        PainterLineNormal(luck[1][0], luck[1][1], luck[2][0], luck[2][1],
                                                          QtGui.QColor('blue'), 3))
                            except Exception as e:
                                pass
                    for p2, mode in p.ancestor_nex:
                        if len(p2.get_rects_main_line()) > 0:
                            bef = p2.get_rects_main_line()[mode]
                            x = p.get_rects_main_line()[-1]
                            try:
                                if bef is not None:
                                    luck = LLuk.create_lluk_special([bef[0], bef[1], x[0], x[1]], 50)
                                    my_canvases[0].shapes.add(PainterLLuk(luck[0]))
                                    my_canvases[0].shapes.add(
                                        PainterLineNormal(luck[1][0], luck[1][1], luck[2][0], luck[2][1],
                                                          QtGui.QColor('blue'), 3))
                            except Exception as e:
                                pass
                                #my_canvases[0].shapes.add(
                                #    PainterLineNormal(x[0][0], x[0][1], x[1][0], x[1][1], QtGui.QColor('blue'), 3))
            except Exception as e:
                print('GLOB-ERR:', e)
            '''
            '''
            try:
                bef = p.rect.exterior.coords[-1]
                for x in p.rect.exterior.coords:
                    if bef is not None:
                        x1, y1 = bef
                        x2, y2 = x
                        bef = x
                        my_canvases[0].shapes.add(PainterLineNormal(x1, y1, x2, y2, QtGui.QColor('red'), 1))
            except Exception:
                pass
            '''

        for a in hebelki_all:
            x1, y1 = a.linestring.coords[0]
            x2, y2 = a.linestring.coords[1]
            #my_canvases[0].shapes.add(PainterLine(x1, y1, x2, y2, QtGui.QColor('blue')))
            x1, y1 = a.get_average_point().coords[0]
            current_color = "green"
            current_stroke = 1
            for b in a.nast:
                x2, y2 = b.get_average_point().coords[0]
                if b in dfs_costam.hebelki_map:
                    vals = dfs_costam.hebelki_map[b]
                    current_color = manage_vals(vals, a)
                my_canvases[0].shapes.add(PainterLineNormal(x1, y1, x2, y2, QtGui.QColor(current_color), current_stroke))
        sys.exit(app.exec_())