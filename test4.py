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
import libmrc

class ZoomSet(object):
    def __init__(self, setx, width, heigth):
        ratio_window = width / heigth
        ratio_data = 1
        self.width = width
        self.height = heigth
        for crd in setx:
            try:
                self.minX
                self.maxX
                self.minY
                self.maxY
            except AttributeError:
                self.minX = crd[0]
                self.maxX = crd[0]
                self.minY = crd[1]
                self.maxY = crd[1]
            self.minX = min(crd[0], self.minX)
            self.minY = min(crd[1], self.minY)
            self.maxX = max(crd[0], self.maxX)
            self.maxY = max(crd[1], self.maxY)
        ratio_data = (self.maxX - self.minX) / (self.maxY - self.minY)
        self.ratio_type = (ratio_window < ratio_data)

    def avgX(self):
        return (self.maxX + self.minX) / 2

    def avgY(self):
        return (self.maxY + self.minY) / 2

    def get_zoom_all(self, smiesznakrotka):
        zoom = (self.maxY - self.minY) / (self.height - 10)
        if (self.ratio_type):
            zoom = (self.maxX - self.minX) / (self.width - 10)
        return zoom

    def get_zoom(self, smiesznakrotka, posl=(0, 0)):
        zoom = (self.maxY - self.minY) / (self.height - 10)
        if (self.ratio_type):
            zoom = (self.maxX - self.minX) / (self.width - 10)
        a = (smiesznakrotka[0] - self.avgX()) / zoom + self.width / 2
        b = (0 - smiesznakrotka[1] + self.avgY()) / zoom + self.height / 2
        return (int(a) + posl[0], int(b) + posl[1])


class DisjointSet(object):
    def __init__(self):
        self.leader = {}  # maps a member to the group's leader
        self.group = {}  # maps a group leader to the group (which is a set)

    def add(self, a, b):
        leadera = self.leader.get(a)
        leaderb = self.leader.get(b)
        if leadera is not None:
            if leaderb is not None:
                if leadera == leaderb: return  # nothing to do
                groupa = self.group[leadera]
                groupb = self.group[leaderb]
                if len(groupa) < len(groupb):
                    a, leadera, groupa, b, leaderb, groupb = b, leaderb, groupb, a, leadera, groupa
                groupa |= groupb
                del self.group[leaderb]
                for k in groupb:
                    self.leader[k] = leadera
            else:
                self.group[leadera].add(b)
                self.leader[b] = leadera
        else:
            if leaderb is not None:
                self.group[leaderb].add(a)
                self.leader[a] = leaderb
            else:
                self.leader[a] = self.leader[b] = a
                self.group[a] = set([a, b])
class DisjointSetCreator(DisjointSet):
    def __init__(self, cur):
        super(DisjointSetCreator, self).__init__() 
        cur.execute("SELECT * FROM nicepaths_fin2");
        abc = cur.fetchall()
        for alfa in abc:
            self.add(alfa[0], alfa[1])

class PackAllMy(libmrc.PackAll):
    def __init__(self, lamane, trasy, ds):
        super(PackAllMy, self).__init__(lamane, trasy) 
        for k in ds.group.keys():
            k2 = ds.group[k]
            if (len(k2) >= 1):
                st3 = []
                for k3 in k2:
                    lmn = self.lamane[k3]
                    st3.append(lmn)
                hlist = []
                for k3 in k2:
                    y = self.lamane[k3]
                    for t in range(40, int(y.linestring.length - 39), 40):
                        hhh = libmrc.Hebelek(y, t, 50)
                        inter = False
                        for p in hlist:
                            if (p.linestring.intersects(hhh.linestring)):
                                inter = True
                        if not inter:
                            hlist.append(hhh)
                            hhh.set_intersections(st3)
                            self.hebelki.append(hhh)
        for a in self.trasy:
            self.trasy[a].extend_hebelki(self.lamane)


class Dict_Bezpo(object):
    def __init__(self, cur):
        self.dict_bezpo = dict()
        cur.execute("SELECT * FROM (SELECT y.elem,\
                            y.nr,\
                            s9.id\
                           FROM ( SELECT nicepaths_long_vertices.id,\
                                    nicepaths_long_vertices.ar\
                                   FROM nicepaths_long_vertices) s9\
                             LEFT JOIN LATERAL unnest(s9.ar) WITH ORDINALITY y(elem, nr) ON true) tut ORDER BY id, nr;");
        abc = cur.fetchall()
        lastit = None
        for x in abc:
            if lastit is not None:
                if lastit[2] == x[2]:
                    self.dict_bezpo[(lastit[0], x[0])] = lastit[2]
            lastit = x
        self.middledict_all = dict()
        cur.execute("SELECT ref_begin, ref_end, ordinal_id, node_id FROM osm_paths ORDER BY ref_begin, ref_end, ordinal_id");
        abc = cur.fetchall()
        for x in abc:
            ref_begin = x[0]
            ref_end = x[1]
            node_id = x[3]
            if (ref_begin, ref_end) not in self.middledict_all:
                self.middledict_all[(ref_begin, ref_end)] = []
            self.middledict_all[(ref_begin, ref_end)].append(node_id)
        cur.execute("SELECT * FROM operator_routes ORDER BY route_id, direction, stop_on_direction_number;"); #order_by
        abc = cur.fetchall()

        currentLine = ""
        currentWar = -1
        currentSet = []
        self.ztmAll = dict()


        for x in abc:
            if currentLine != x[0] or x[1] != currentWar:
                if len(currentSet) > 0:
                    self.ztmAll[(currentLine, currentWar)] = libmrc.ZtmRoute(currentLine, currentWar, currentSet, self.middledict_all, self.dict_bezpo)
                    currentSet = []
                    currentLine = x[0]
                    currentWar = x[1]
            currentSet.append(x[3])
        if len(currentSet) > 0:
            self.ztmAll[(currentLine, currentWar)] = libmrc.ZtmRoute(currentLine, currentWar, currentSet, self.middledict_all, self.dict_bezpo)




conn = psycopg2.connect(dbname="nexty", user="marcin")

cur = conn.cursor()


ztmAll0 = Dict_Bezpo(cur)
ds = DisjointSetCreator(cur)



cur.execute("SELECT * FROM nicepaths_vertices_coordinates;")

abc = cur.fetchall()


linie_prz_all = dict()

for alfa in abc:
    linie_prz_all[alfa[0]] = libmrc.Lamana(alfa[0], wkb.loads(alfa[1], hex=True))


pack = PackAllMy(linie_prz_all, ztmAll0.ztmAll, ds)

with open('hebelki.pickle', 'wb') as pickle_file:
    pickle.dump(pack, pickle_file)
