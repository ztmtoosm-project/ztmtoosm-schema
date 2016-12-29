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
from svgpathtools import Path, Line, QuadraticBezier, CubicBezier, Arc, wsvg


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


def azimuth(point1, point2):
    angle = np.arctan2(point2[0] - point1[0], point2[1] - point1[1])
    return angle


def line_angle(point, length, azimuth):
    nextx = shapely.geometry.Point(point[0], point[1] + length)
    ls = shapely.geometry.LineString([point, nextx])
    return shapely.affinity.rotate(ls, azimuth, origin=shapely.geometry.Point(point), use_radians=True)


class Lamana(shapely.geometry.LineString):
    def __init__(self, idx, linestring):
        super(Lamana, self).__init__(linestring.coords) 
        self.idx = idx
        self.linestring = linestring
        self.hebelki = dict()
    def hebelki_sorted(self):
        return sorted(self.hebelki.items(), key=operator.itemgetter(0))
    def hebelki_sorted_desc(self):
        return sorted(self.hebelki.items(), key=operator.itemgetter(0), reverse=True)

class Hebelek(object):
    def __init__(self, line, distance, length):
        line_length = line.length
        p0 = line.interpolate(distance)
        p1 = line.interpolate(max(distance - 1, 0))
        p2 = line.interpolate(min(distance + 1, line_length))
        az = azimuth(p1.coords[0], p2.coords[0])
        self.nast = set()
        self.bef = set()
        self.intersections = dict()
        self.uuk = shapely.geometry.LineString(
            [line_angle(p0.coords[0], length / 2, (az + 3.142 / 2) * (-1.0)).coords[1],
             line_angle(p0.coords[0], length / 2, (az - 3.142 / 2) * (-1.0)).coords[1]])
        self.p0 = p0
        self.angle = az
        self.todelete = False

    def set_intersections(self, lamane):
        for k in lamane:
            if (self.uuk.intersects(k.linestring)):
                intr = self.uuk.intersection(k.linestring)
                if (intr.geom_type == "Point"):
                    odl_lamana = k.linestring.project(intr)
                    p1 = k.linestring.interpolate(max(odl_lamana - 1, 0))
                    p2 = k.linestring.interpolate(min(odl_lamana + 1, k.linestring.length))
                    az = azimuth(p1.coords[0], p2.coords[0])
                    az2 = self.angle
                    az3 = (abs(az-az2) % 3.142)
                    if az3 < 3.142/4.0 or az3 > 3.142/4.0*3.0:
                        odl_hebelek = self.uuk.project(intr)
                        k.hebelki[odl_lamana] = self
                        self.intersections[odl_hebelek] = k

    def get_average_point(self):
        avv = 0.0
        lenx = len(self.intersections)
        for k in self.intersections:
            avv = avv + k
        avv = avv / lenx
        return self.uuk.interpolate(avv)

    def is_middle(self):
        if len(self.nast | self.bef) == 2:
            return True
        return False


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
                print("XX")
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
            print(str(len(self.idarray))+"@")
            print(i)
            self.calculatelow(self.idarray[i])
        if len((startnode.bef | startnode.nast) - set([startnode])) <= 1:
            self.artic.add(startnode)
        elif self.tostn >= 2:
            self.artic.add(startnode)
        print("HebelkiDFSBrigEND " + str(len(self.idarray)) + " " + str(len(self.artic)))

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
        for x in self.res2:
            tmpp = []
            for y in x:
                if(y[0] in lamane_set and y[1]==1):
                    prepared_hebelki = reversed(lamane_set[y[0]].hebelki_sorted())
                    prepared_hebelki2 = []
                    for x in prepared_hebelki:
                        #if not x.todelete:
                            prepared_hebelki2.append(x)
                    tmpp.extend(prepared_hebelki2)
                elif y[0] in lamane_set:
                    prepared_hebelki = lamane_set[y[0]].hebelki_sorted()
                    prepared_hebelki2 = []
                    for x in prepared_hebelki:
                        #if not x.todelete:
                            prepared_hebelki2.append(x)
                    tmpp.extend(prepared_hebelki2)
            self.hebelki.append(tmpp)
        self.extend_hebelki2()

    def extend_hebelki2(self):
        for x in self.hebelki:
            for i in range(0, len(x)-1):
                x[i][1].nast.add(x[i+1][1])
                x[i+1][1].bef.add(x[i][1])





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
                    self.ztmAll[(currentLine, currentWar)] = ZtmRoute(currentLine, currentWar, currentSet, self.middledict_all, self.dict_bezpo)
                    currentSet = []
                    currentLine = x[0]
                    currentWar = x[1]
            currentSet.append(x[3])
        if len(currentSet) > 0:
            self.ztmAll[(currentLine, currentWar)] = ZtmRoute(currentLine, currentWar, currentSet, self.middledict_all, self.dict_bezpo)

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


class DisjointSetCreator(object):
    def __init__(self, cur):
        self.ds = DisjointSet()
        cur.execute("SELECT * FROM nicepaths_fin2");
        abc = cur.fetchall()
        for alfa in abc:
            self.ds.add(alfa[0], alfa[1])

   
 


conn = psycopg2.connect(dbname="nexty", user="marcin")

cur = conn.cursor()


ztmAll0 = Dict_Bezpo(cur)
ds0 = DisjointSetCreator(cur)
ds = ds0.ds
ztmAll = ztmAll0.ztmAll



cur.execute("SELECT * FROM nicepaths_vertices_coordinates;")

abc = cur.fetchall()


linie_prz_all = dict()

for alfa in abc:
    linie_prz_all[alfa[0]] = Lamana(alfa[0], wkb.loads(alfa[1], hex=True))

hebelki_all = set()


for k in ds.group.keys():
    k2 = ds.group[k]
    if (len(k2) >= 1):
        st3 = []
        for k3 in k2:
            lmn = linie_prz_all[k3]
            st3.append(lmn)
        hlist = []
        for k3 in k2:
            y = linie_prz_all[k3].linestring
            for t in range(40, int(y.length - 39), 40):
                hhh = Hebelek(y, t, 50)
                inter = False
                for p in hlist:
                    if (p.intersects(hhh.uuk)):
                        inter = True
                if not inter:
                    hlist.append(hhh.uuk)
                    hhh.set_intersections(st3)
                    hebelki_all.add(hhh)

for a in ztmAll:
    #if(a[0]=="147" and a[1]==1):
        ztmAll[a].extend_hebelki(linie_prz_all)


#pickle.dump(hebelki_all, 'hebelki.pickle')

paths = []
stroke_widths = []

print("Hebelki start")
dfs_costam = HebelkiDfs(hebelki_all)
print("Hebelki stop")




colors = ""
srodes = []
radii = []
for a in hebelki_all:
    current_color = "k"
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

