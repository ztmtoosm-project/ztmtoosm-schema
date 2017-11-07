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
    def dfscore(self, current_obj, list_cnc=None):
        if current_obj not in self.visited:
            self.visited.add(current_obj)
            if current_obj.is_middle():
                if list_cnc is not None:
                    list_cnc.append(current_obj)
                self.hebelki_map[current_obj] = self.__counter
                for x in list(current_obj.nast):
                    self.dfscore(x, list_cnc)
                for x in list(current_obj.bef):
                    self.dfscore(x, list_cnc)

    def __middleinfo(self, x):
        ltt = []
        if x.is_middle():
            setu = (x.nast | x.bef)
            for y in setu:
                if not y.is_middle():
                    ltt.append(y)
        return ltt


    def __init__(self, hebelki_all):
        self.__counter = 0
        self.hebelki_all = hebelki_all
        self.visited = set()
        self.hebelki_map = dict()
        self.hebelki_longline = set()
        self.artic = set()
        for x in hebelki_all:
            if x not in self.visited:
                self.dfscore(x)
                self.__counter = self.__counter + 1
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
        self.visited = set()
        self.epsilon = dict()
        for x in hebelki_all:
            if x not in self.visited:
                if len(self.__middleinfo(x)) == 1:
                    curlist = [self.__middleinfo(x)[0]]
                    self.dfscore(x, curlist)
                    kup = self.__middleinfo(curlist[-1])
                    if len(kup) == 1:
                        curlist.append(kup[0])
                        self.epsilon[self.hebelki_map[x]] = curlist
                if len(self.__middleinfo(x)) == 2:
                    kop = self.__middleinfo(x)
                    curlist = [kop[0], x, kop[1]]
                    self.epsilon[self.hebelki_map[x]] = curlist

class JoinLamanaPrinter(object):
    def __init__(self, idx, epsilon):
        self.idx = idx
        self.wszystkie_hebelki = epsilon
        self.wszystkie_hebelki_set = set(epsilon)
        self.wszystkie_lamane = set()
        self.niepelne_lamane = set()
        for x in self.wszystkie_hebelki:
            for t in x.intersections:
                self.wszystkie_lamane.add(x.intersections[t])
        for x in self.wszystkie_lamane:
            for y in hebelki:
                if(y.todelete==False):
                    pass

def draw_all(dataset, imagex, color, zoom_mode):
    for x in dataset.values():
        for t in range(0, len(x) - 1):
            pygame.draw.line(imagex, color, zoom_mode.get_zoom((x[t][0], x[t][1])),
                             zoom_mode.get_zoom((x[t + 1][0], x[t + 1][1])))

def srumpy(coords):
    return coords[0] - 1.0j*(coords[1])


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

def part_mn(twoargs=False):
    pkl_file = open('hebelki.pickle', 'rb')
    pick = pickle.load(pkl_file)

    hebelki_all = pick.hebelki
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
    if twoargs:
        return hebelki_all2, pick.lamane, pick.trasy
    else:
        return hebelki_all2