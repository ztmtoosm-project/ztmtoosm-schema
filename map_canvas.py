import math
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import *
from shapely.geometry import LineString, Point
from lluk import LLuk
from geospatial_container import GeospatialContainer

class PainterLine:
    def __init__(self, x1, y1, x2, y2, color=QtGui.QColor('black'), stroke=1):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2
        self.selected = False
        self.color = color
        self.stroke = stroke

    @staticmethod
    def tmp_convert1(coords):
        y, x = coords
        x = (x - 20.5) * 61290
        y = (y - 52.05) * 100000
        return x, y

    @staticmethod
    def tmp_convert2(coords):
        x, y = coords
        x = (x / 61290) + 20.5
        y = (y / 100000) + 52.05
        return y, x


    def getCanvasCoordinates(self, position):
        pos1x, pos1y = position.deg2num(*self.tmp_convert2((self.x1, self.y1)))
        pos2x, pos2y = position.deg2num(*self.tmp_convert2((self.x2, self.y2)))
        return (pos1x, pos1y, pos2x, pos2y)

    def paintMe(self, qp, position):
        if(self.selected):
            qp.setPen(QtGui.QPen(QtGui.QColor('red'), self.stroke, QtCore.Qt.SolidLine))

        else:
            qp.setPen(QtGui.QPen(self.color, self.stroke, QtCore.Qt.SolidLine))
        qline = QtCore.QLine(*self.getCanvasCoordinates(position))
        qp.drawLine(qline)
        qp.setPen(QtGui.QColor('black'))

    def getDistance(self, position):
        pos1x, pos1y, pos2x, pos2y = self.getCanvasCoordinates(position)
        return LineString([(pos1x, pos1y), (pos2x, pos2y)]).distance(Point((0,0)))

    def get_border_coordinates(self):
        c1x, c1y = self.tmp_convert2((self.x1, self.y1))
        c2x, c2y = self.tmp_convert2((self.x2, self.y2))

        x_min = min(c1x, c2x)
        y_min = min(c1y, c2y)
        x_max = max(c1x, c2x)
        y_max = max(c1y, c2y)
        return x_min, x_max, y_min, y_max

    def select(self):
        self.selected = True

    def clear_selection(self):
        self.selected = False

class PainterLLuk:
    def __init__(self, luk):
        self.luk = luk
        self.selected = False

    @staticmethod
    def tmp_convert1(coords):
        y, x = coords
        x = (x - 20.5) * 1290
        y = (y - 52.05) * 100000
        return x, y

    @staticmethod
    def tmp_convert2(coords):
        x, y = coords
        x = (x / 61290) + 20.5
        y = (y / 100000) + 52.05
        return y, x

    #def getCanvasCoordinates(self, position):
    #    pass

    def paintMe(self, qp, position):
        if(self.selected):
            qp.setPen(QtGui.QColor('red'))
        else:
            qp.setPen(QtGui.QPen(QtCore.Qt.blue, 4, QtCore.Qt.SolidLine))

        p1, p2 = self.luk.additional_line
        p1, p2 = self.tmp_convert2(p1), self.tmp_convert2(p2)
        pos1x, pos1y = position.deg2num(p1[0], p1[1])
        pos2x, pos2y = position.deg2num(p2[0], p2[1])
        arcx, arcy = self.luk.arc_center
        arc1x, arc1y = position.deg2num(*self.tmp_convert2((arcx - self.luk.arc_radius, arcy - self.luk.arc_radius)))
        arc2x, arc2y = position.deg2num(*self.tmp_convert2((arcx + self.luk.arc_radius, arcy + self.luk.arc_radius)))
        arcx, rx = min(arc1x, arc2x), max(arc1x, arc2x) - min(arc1x, arc2x)
        arcy, ry = min(arc1y, arc2y), max(arc1y, arc2y) - min(arc1y, arc2y)
        rect = QtCore.QRectF(arcx, arcy, rx, ry)
        qline = QtCore.QLine(pos1x, pos1y, pos2x, pos2y)
        qp.drawLine(qline)
        foo, k1, k2 = self.luk.get_pygame_arc()
        qp.drawArc(rect, k1/3.142*180*-16, LLuk.right3(k1,k2)/3.142*180*-16)
        #print(k1/3.142*180)
        #print(LLuk.right3(k1,k2)/3.142*180)
        qp.setPen(QtGui.QColor('black'))
        qp.setPen(1)

    def getDistance(self, position):
        return 2000

    def get_border_coordinates(self):
        arcx, arcy = self.luk.arc_center
        poss = []
        poss.append(self.tmp_convert2((arcx - self.luk.arc_radius, arcy - self.luk.arc_radius)))
        poss.append(self.tmp_convert2((arcx + self.luk.arc_radius, arcy + self.luk.arc_radius)))
        poss.append(self.tmp_convert2(self.luk.additional_line[0]))
        poss.append(self.tmp_convert2(self.luk.additional_line[1]))
        x_min, x_max, y_min, y_max = None, None, None, None
        for x, y in poss:
            if x_min is None:
                x_min = x
            if x_max is None:
                x_max = x
            if y_min is None:
                y_min = y
            if y_max is None:
                y_max = y
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)
        return x_min, x_max, y_min, y_max

    def select(self):
        self.selected = True

    def clear_selection(self):
        self.selected = False

class TilePosition:
    def fix(self):
        while self.possx > 256:
            self.possx -= 256
            self.poss1 += 1
        while self.possy > 256:
            self.possy -= 256
            self.poss2 += 1
        while self.possx < 0:
            self.possx += 256
            self.poss1 -= 1
        while self.possy < 0:
            self.possy += 256
            self.poss2 -= 1
    def __init__(self):
        self.poss1 = 18310
        self.poss2 = 10786
        self.possx = 0
        self.possy = 0
        self.zoom = 15

    def copyMe(self):
        newPosition = TilePosition()
        newPosition.poss1 = self.poss1
        newPosition.poss2 = self.poss2
        newPosition.possx = self.possx
        newPosition.possy = self.possy
        newPosition.zoom = self.zoom
        newPosition.fix()
        return newPosition

    def shiftCopy(self, x, y):
        newPosition = self.copyMe()
        newPosition.possx -= x
        newPosition.possy -= y
        newPosition.fix()
        return newPosition

    def zoomOut(self):
        newPosition = self.copyMe()
        newPosition.zoom -= 1
        newPosition.poss1 = int(newPosition.poss1 / 2)
        newPosition.poss2 = int(newPosition.poss2 / 2)
        newPosition.possx = int(self.possx/2) + self.poss1 % 2 * 128
        newPosition.possy = int(self.possy/2) + self.poss2 % 2 * 128
        return newPosition

    def zoomIn(self):
        newPosition = self.copyMe()
        newPosition.zoom += 1
        newPosition.poss1 *= 2
        newPosition.poss2 *= 2
        newPosition.possx *= 2
        newPosition.possy *= 2
        newPosition.fix()
        return newPosition

    def deg2num(self, lat_deg, lon_deg):
        zoom = self.zoom
        newPosition = TilePosition()
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = (lon_deg + 180.0) / 360.0 * n
        ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
        newPosition.zoom = zoom
        newPosition.poss1 = int(xtile)
        newPosition.poss2 = int(ytile)
        newPosition.possx = int((xtile - int(xtile)) * 256)
        newPosition.possy = int((ytile - int(ytile)) * 256)
        newPosition.fix()
        return ((newPosition.poss1-self.poss1) * 256 + newPosition.possx-self.possx, (newPosition.poss2-self.poss2) * 256 + newPosition.possy-self.possy)

    def get_coordinates(self):
        n = 2.0 ** self.zoom
        xtile = self.poss1 + self.possx / 256.0
        ytile = self.poss2 + self.possy / 256.0
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)



class MapCanvas(QtGui.QWidget):
    def __init__(self, width=900, height=650, tiles=True):
        super(MapCanvas, self).__init__()
        self.widget_width = width
        self.widget_height = height
        self.setFixedSize(width, height)
        self.position = TilePosition()
        self.tiles = tiles
        self.paint_tiles = True

        self.shapes = GeospatialContainer(51, 54, 19, 22, 8)

    def drawTiles(self, painter, position):
        if not self.tiles:
            return
        scale = 1
        if position.zoom > 15 and position.zoom < 20:
            zoomx = position.zoom
            while zoomx > 15:
                zoomx -= 1
                scale *= 2
                position = position.zoomOut()
        for i in range(position.poss1, position.poss1+6):
            for j in range(position.poss2, position.poss2+6):
                strpath = "/home/dell/tiles-osm/tiles/" + str(position.zoom) + "/" + str(i) + "/" + str(j) + ".png"
                image = QImage(strpath)
                if(scale > 1):
                    image = image.scaled(256 * scale, 256 * scale)
                painter.drawImage((i-position.poss1)*256*scale-position.possx*scale, (j-position.poss2)*256*scale-position.possy*scale, image)

    def get_border_coordinates(self):
        lat1, lon1 = self.position.get_coordinates()
        lat2, lon2 = self.position.shiftCopy(self.widget_width * -1, self.widget_height * -1).get_coordinates()
        lon_min = min(lon1, lon2)
        lon_max = max(lon1, lon2)
        lat_min = min(lat1, lat2)
        lat_max = max(lat1, lat2)
        return lat_min, lat_max, lon_min, lon_max

    def current_visible_collection(self):
        return self.shapes.get_objects(*self.get_border_coordinates())

    def paintEvent(self, event):

        qp = QtGui.QPainter()
        qp.begin(self)


        qp.fillRect(event.rect(), QtGui.QBrush(QtGui.QColor(255, 255, 255)))


        if self.paint_tiles:
            self.drawTiles(qp, self.position)


        for x in self.current_visible_collection():
            x.paintMe(qp, self.position)

        qp.end()

    def getClosestObject(self, shift_x, shift_y):
        distance = 5000
        obj_current = None
        position = self.position.shiftCopy(shift_x * -1, shift_y * -1)
        for x in self.current_visible_collection():
            distance_current = x.getDistance(position)
            if distance_current < distance:
                distance = distance_current
                obj_current = x
        return distance, obj_current

    def getCoordinates(self, shift_x, shift_y):
        position = self.position.shiftCopy(shift_x * -1, shift_y * -1)
        return position.get_coordinates()