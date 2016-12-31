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


class HebelkiDfsBriges(object):

    def rundfs(self, current, parent):
        if(current not in self.parentx.visited):
            if parent == self.startnode:
                self.tostn = self.tostn + 1
            self.parentdict[current] = parent
            self.idarray.append(current)
            self.iddict[current] = self.currentid
            self.currentid = self.currentid + 1
            self.parentx.visited.add(current)
            is_middle = current in self.parentx.hebelki_longline
            for x in (current.nast | current.bef):
                if is_middle and (x in self.parentx.hebelki_longline):
                    pass
                else:
                    self.rundfs(x, current)

    def calculatelow(self, current):
        low = self.iddict[current]
        for x in (current.nast | current.bef):
            if x in self.lowdict and self.parentdict[x] == current:
                low = min(low, self.lowdict[x])
                if self.lowdict[x] >= self.iddict[current]:
                    self.artic.add(current)
        for x in (current.nast | current.bef):
            if x in self.iddict:
                if self.parentdict[current] != x:
                    low = min(low, self.iddict[x])
        self.lowdict[current] = low

    def __init__(self, parentx, startnode):
        self.startnode = startnode
        self.parentx = parentx
        self.idarray = []
        self.lowdict = dict()
        self.parentdict = dict()
        self.iddict = dict()
        self.currentid = 0
        self.tostn = 0
        self.artic = set()
        self.rundfs(startnode, None)
        for i in reversed(range(1, len(self.idarray))):
            self.calculatelow(self.idarray[i])
        if len((startnode.bef | startnode.nast) - set([startnode])) <= 1:
            self.artic.add(startnode)
        elif self.tostn >= 2:
            self.artic.add(startnode)

class HebelkiDfs(object):
    def dfscore(self, current_obj):
        if current_obj not in self.visited:
            self.visited.add(current_obj)
            if current_obj.is_middle():
                self.hebelki_map[current_obj] = self.counter
                for x in list(current_obj.nast):
                    self.dfscore(x)
                for x in list(current_obj.bef):
                    self.dfscore(x)

    def __init__(self, hebelki_all):
        self.counter = 0
        self.hebelki_all = hebelki_all
        self.visited = set()
        self.hebelki_map = dict()
        for x in hebelki_all:
            if x not in self.visited:
                self.dfscore(x)
                self.counter = self.counter + 1
        self.hebelki_longline = set()
        self.artic = set()
        setpom = dict()
        for x in self.hebelki_map:
            val = self.hebelki_map[x]
            if val in setpom:
                setpom[val] = setpom[val] + 1
            else:
                setpom[val] = 1
        for x in self.hebelki_map:
            val = self.hebelki_map[x]
            if val in setpom:
                if setpom[val] > 2:
                    self.hebelki_longline.add(x)
        self.visited = set()
        for x in hebelki_all:
            if x not in self.visited:
                if x not in self.hebelki_longline:
                    self.artic.update(HebelkiDfsBriges(self, x).artic)
def draw_all(dataset, imagex, color, zoom_mode):
    for x in dataset.values():
        for t in range(0, len(x) - 1):
            pygame.draw.line(imagex, color, zoom_mode.get_zoom((x[t][0], x[t][1])),
                             zoom_mode.get_zoom((x[t + 1][0], x[t + 1][1])))

def srumpy(coords):
    return coords[0] - 1.0j*(coords[1])


def manage_vals(id, cbc):
    #if cbc not in dfs_costam.hebelki_longline:
    #    if cbc not in dfs_costam.artic:
    #       return "b"
    return "r"
    #id2 = id % 12
    #zupa = ['a', 'b', 'c', 'd', 'g', 'l', 'm', 'p', 'q', 's', 'v', 'z']
    #return zupa[id2]



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
                    for t in range(40, int(y.length - 39), 40):
                        hhh = libmrc.Hebelek(y, t, 50)
                        inter = False
                        for p in hlist:
                            if (p.intersects(hhh)):
                                inter = True
                        if not inter:
                            hlist.append(hhh)
                            hhh.set_intersections(st3)
                            self.hebelki.append(hhh)
        for a in self.trasy:
            self.trasy[a].extend_hebelki(self.lamane)


def hebelek_in_zakres(hebelek, x, y, zakres):
    ptt = hebelek.get_average_point().coords[0]
    if(ptt[0] >= x-zakres and ptt[0] <= x+zakres):
        if(ptt[1] >= y-zakres and ptt[1] <= y+zakres):
            return True

pkl_file = open('hebelki.pickle', 'rb')
pick = pickle.load(pkl_file)

hebelki_all = pick.hebelki

paths = []
stroke_widths = []

dfs_costam = HebelkiDfs(hebelki_all)

hebelki_all2 = set()


for a in hebelki_all:
    if a not in dfs_costam.hebelki_longline:
        if a not in dfs_costam.artic:
            a.todelete = True
    if a.todelete == False:
        hebelki_all2.add(a)
    a.nast.clear()
    a.bef.clear()

for a in pick.trasy:
    trasa = pick.trasy[a]
    trasa.extend_hebelki(pick.lamane)
hebelki_all = hebelki_all2
dfs_costam = HebelkiDfs(hebelki_all)

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

colors = ""
srodes = []
radii = []
for a in hebelki_all:
    if hebelek_in_zakres(a, xxx, yyy, 1500):
        current_color = "k"
        colors = colors + "c"
        stroke_widths.append(1)
        paths.append(Line(srumpy(a.linestring.coords[0]), srumpy(a.linestring.coords[1])))
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
