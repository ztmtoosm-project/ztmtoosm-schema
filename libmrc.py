import operator
import pygame
import sys
import ast
import psycopg2
import re
import shapely.geometry
import shapely.affinity
import shapely.wkb as wkb
from pprint import pprint as pp
import numpy as np
import pickle
import math
from svgpathtools import Path, Line, QuadraticBezier, CubicBezier, Arc, wsvg
sys.setrecursionlimit(50000)

def azimuth(point1, point2):
    angle = np.arctan2(point2[0] - point1[0], point2[1] - point1[1])
    return angle


def line_angle(point, length, azimuth):
    nextx = shapely.geometry.Point(point[0], point[1] + length)
    ls = shapely.geometry.LineString([point, nextx])
    return shapely.affinity.rotate(ls, azimuth, origin=shapely.geometry.Point(point), use_radians=True)


class Lamana(object):
    def __init__(self, idx, linestringx):
        self.linestring = shapely.geometry.LineString(linestringx)
        self.idx = idx
        self.hebelki = dict()
    def hebelki_sorted(self):
        return sorted(self.hebelki.items(), key=operator.itemgetter(0))
    def hebelki_sorted_desc(self):
        return sorted(self.hebelki.items(), key=operator.itemgetter(0), reverse=True)

class Hebelek(object):
    def __init__(self, line, distance, length):
        line_length = line.linestring.length
        p0 = line.linestring.interpolate(distance)
        p1 = line.linestring.interpolate(max(distance - 1, 0))
        p2 = line.linestring.interpolate(min(distance + 1, line_length))
        az = azimuth(p1.coords[0], p2.coords[0])
        self.linestring = shapely.geometry.LineString([line_angle(p0.coords[0], length / 2, (az + math.pi / 2) * (-1.0)).coords[1],
             line_angle(p0.coords[0], length / 2, (az - math.pi / 2) * (-1.0)).coords[1]])
        self.nast = set()
        self.bef = set()
        self.intersections = dict()
        self.p0 = p0
        self.angle = az
        self.todelete = False
    def set_intersection(self, lamana, nice_angle=0.25):
        if (self.linestring.intersects(lamana.linestring)):
            intr = self.linestring.intersection(lamana.linestring)
            if (intr.geom_type == "Point"):
                odl_lamana = lamana.linestring.project(intr)
                p1 = lamana.linestring.interpolate(max(odl_lamana - 1, 0))
                p2 = lamana.linestring.interpolate(min(odl_lamana + 1, lamana.linestring.length))
                az = azimuth(p1.coords[0], p2.coords[0])
                az2 = self.angle
                az3 = (abs(az-az2) % math.pi)
                if az3 < math.pi*(nice_angle) or az3 > math.pi*(1-nice_angle):
                    odl_hebelek = self.linestring.project(intr)
                    lamana.hebelki[odl_lamana] = self
                    self.intersections[odl_hebelek] = lamana

    def set_intersections(self, lamane):
        for k in lamane:
            self.set_intersection(k)

    def get_average_point(self):
        avv = 0.0
        lenx = len(self.intersections)
        if lenx == 0:
            return self.linestring.interpolate(0.5, normalized=True)
        for k in self.intersections:
            avv = avv + k
        avv = avv / lenx
        return self.linestring.interpolate(avv)

    def is_middle(self):
        if len(self.nast | self.bef) == 2:
            return True
        return False

class ZtmRoute(object):
    def __init__(self, lineid, wariant, stoplist, middledict, bezpo):
        self.res = []
        self.res2 = []
        self.stoplist = stoplist
        self.lineid = lineid
        self.wariant = wariant
        self.hebelki = []
        current_res_list = []
        for x in range(0, len(stoplist)-1):
            start = stoplist[x]
            stop = stoplist[x+1]
            if (start, stop) in middledict:
                for y in middledict[(start, stop)]:
                    if len(current_res_list) == 0 or current_res_list[-1] != y:
                        current_res_list.append(y)
            else:
                if len(current_res_list) > 0:
                    self.res.append(current_res_list)
                    current_res_list = []
        if len(current_res_list) > 0:
            self.res.append(current_res_list)

        for x in self.res:
            tmpp = []
            for y in range(0, len(x)-1):
                if (x[y], x[y+1]) in bezpo:
                    if len(tmpp) == 0 or tmpp[-1] != (bezpo[(x[y], x[y+1])], 0):
                        tmpp.append((bezpo[(x[y], x[y+1])], 0))
                elif (x[y+1], x[y]) in bezpo:
                    if len(tmpp) == 0 or tmpp[-1] != (bezpo[(x[y+1], x[y])], 1):
                        tmpp.append((bezpo[(x[y+1], x[y])], 1))
            self.res2.append(tmpp)

    def extend_hebelki(self, lamane_set):
        self.hebelki.clear()
        for x in self.res2:
            tmpp = []
            for y in x:
                if(y[0] in lamane_set and y[1]==1):
                    prepared_hebelki = reversed(lamane_set[y[0]].hebelki_sorted())
                    prepared_hebelki2 = []
                    for dd in prepared_hebelki:
                        if dd[1].todelete == False:
                            prepared_hebelki2.append(dd)
                    tmpp.extend(prepared_hebelki2)
                elif y[0] in lamane_set:
                    prepared_hebelki = lamane_set[y[0]].hebelki_sorted()
                    prepared_hebelki2 = []
                    for dd in prepared_hebelki:
                        if dd[1].todelete == False:
                            prepared_hebelki2.append(dd)
                    tmpp.extend(prepared_hebelki2)
            self.hebelki.append(tmpp)
        self.__extend_hebelki2()

    def __extend_hebelki2(self):
        for x in self.hebelki:
            for i in range(0, len(x)-1):
                x[i][1].nast.add(x[i+1][1])
                x[i+1][1].bef.add(x[i][1])



class PackAll(object):
    def __init__(self, lamane, trasy):
        self.lamane = lamane
        self.trasy = trasy
        self.hebelki = []
