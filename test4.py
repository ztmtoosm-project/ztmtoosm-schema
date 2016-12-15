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

class ZoomSet(object):
  def __init__(self, setx, width, heigth):
    ratio_window = width/heigth
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
    ratio_data = (self.maxX - self.minX)/(self.maxY - self.minY)
    self.ratio_type = (ratio_window < ratio_data)

  def avgX(self):
    return (self.maxX + self.minX)/2
  
  def avgY(self):
    return (self.maxY + self.minY)/2

  def get_zoom_all(self, smiesznakrotka):
    zoom = (self.maxY - self.minY)/(self.height-10)
    if(self.ratio_type):
      zoom = (self.maxX - self.minX)/(self.width-10)
    return zoom
  


  def get_zoom(self, smiesznakrotka, posl=(0,0)):
    zoom = (self.maxY - self.minY)/(self.height-10)
    if(self.ratio_type):
      zoom = (self.maxX - self.minX)/(self.width-10)
    a = (smiesznakrotka[0] - self.avgX())/zoom + self.width/2
    b = (0 - smiesznakrotka[1] + self.avgY())/zoom + self.height/2
    return (int(a)+posl[0],int(b)+posl[1])     

def azimuth(point1, point2):
  angle = np.arctan2(point2[0] - point1[0], point2[1] - point1[1])
  return angle

def line_angle(point, length, azimuth):
  nextx = shapely.geometry.Point(point[0], point[1]+length)
  ls = shapely.geometry.LineString([point, nextx])
  return shapely.affinity.rotate(ls, azimuth, origin=shapely.geometry.Point(point), use_radians=True)


class Lamana(object):
  def __init__(self, idx, linestring):
    self.idx = idx
    self.linestring = linestring
    self.hebelki = dict()

class Hebelek(object):
  def __init__(self, line, distance, length):
    line_length = line.length
    p0 = line.interpolate(distance)
    p1 = line.interpolate(max(distance-1,0))
    p2 = line.interpolate(min(distance+1,line_length))
    az = azimuth(p1.coords[0], p2.coords[0])
    self.intersections = dict()
    self.uuk = shapely.geometry.LineString([line_angle(p0.coords[0], length/2, (az+3.142/2)*(-1.0)).coords[1], line_angle(p0.coords[0], length/2, (az-3.142/2)*(-1.0)).coords[1]])
    self.p0 = p0
    self.angle = az
  def set_intersections(self, lamane):
    for k in lamane:
      if(self.uuk.intersects(k.linestring)):
        intr = self.uuk.intersection(k.linestring)
        if(intr.geom_type=="Point"):
          odl_lamana = k.linestring.project(intr)
          odl_hebelek = self.uuk.project(intr)
          k.hebelki[odl_lamana] = self
          self.intersections[odl_hebelek] = k
  def get_average_point(self):
    avv = 0.0
    lenx = len(self.intersections)
    for k in self.intersections:
      avv = avv + k
    avv = avv / lenx
    print("AVERAGE: "+str(avv))
    return self.uuk.interpolate(avv)

class DisjointSet(object):

  def __init__(self):
    self.leader = {} # maps a member to the group's leader
    self.group = {} # maps a group leader to the group (which is a set)

  def add(self, a, b):
    leadera = self.leader.get(a)
    leaderb = self.leader.get(b)
    if leadera is not None:
      if leaderb is not None:
        if leadera == leaderb: return # nothing to do
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

screen = pygame.display.set_mode((800, 600))

conn = psycopg2.connect(dbname="nextx", user="netbook")

cur = conn.cursor()

#cur.execute("SELECT * FROM (SELECT l1, l2, count(*) FROM graph2 GROUP BY l1, l2) xxx WHERE count > 2;");
#cur.execute("SELECT * FROM lol WHERE visited=true");
#xyz = cur.fetchall()
pygame.init()



ds = DisjointSet()

#cur.execute("SELECT yyy.id, spec_lines3.id FROM yyy, spec_lines3 WHERE ST_Intersects(spec_lines3.line, yyy.create_line_crazy2);");
cur.execute("SELECT * FROM hebelki_przecinanie;");
abc = cur.fetchall()
for alfa in abc:
  ds.add(alfa[0], alfa[1])


cur.execute("SELECT * FROM spec_lines;")

abc = cur.fetchall()
lll = 0

ccc = set()
for alfa in abc:
  x = wkb.loads(alfa[1], hex=True).coords
  for t in range(0, len(x)):
    ccc.add(x[t])

zkt = ZoomSet(ccc, 800, 550)

pdict = dict()
pdict2 = dict()

for alfa in abc:
#  color = (88, 88, 88)
#  print(alfa[0])
#  if not alfa[0] in ds.leader.keys():
#    color = (255, 0, 0)
#  else:
#    sl = len(ds.group[ds.leader[alfa[0]]])
#    if(sl == 1):
#      color = (0, 255, 0)
#    if(sl == 2):
#      color = (120, 120, 255)
#  lll = lll+1
  x = wkb.loads(alfa[1], hex=True).coords
  pdict.update({alfa[0] : x})
  pdict2.update({alfa[0] : wkb.loads(alfa[1], hex=True)})
#  if(lll%1000 == 0):
#    pygame.display.update()
#  for t in range(0, len(x)-1):
#    pygame.draw.line(screen, color, zkt.get_zoom((x[t][0], x[t][1])), zkt.get_zoom((x[t+1][0], x[t+1][1])))

def draw_all(dataset, imagex, color, zoom_mode):
  for x in dataset.values():
    for t in range(0, len(x)-1):
      pygame.draw.line(imagex, color, zoom_mode.get_zoom((x[t][0], x[t][1])), zoom_mode.get_zoom((x[t+1][0], x[t+1][1])))
    

lcz = 0
for k in ds.group.keys():
  k2 = ds.group[k]
  if(len(k2) > 1):
    lcz = lcz + 1
    image = pygame.Surface([1200,600], pygame.SRCALPHA, 32)
    image = image.convert_alpha()
    st = set()
    st2 = []
    st3 = []
    for k3 in k2:
      st |= set(pdict[k3])
      st2.append(pdict2[k3])
      st3.append(Lamana(k3, pdict2[k3]))
    zs = ZoomSet(st, 600, 600)
    hlist = []
    #draw_all(pdict, image, (255, 0, 0), zs)
    for k3 in k2:
      color = (0, 0, 0)
      x = pdict[k3]
      y = pdict2[k3]
      cl2 = (0, 255, 0)
      for t in range(60, int(y.length-59), 60):
        hhh = Hebelek(y, t, 50)
        inter = False
        for p in hlist:
          if(p.intersects(hhh.uuk)):
            inter = True
        if not inter:
          cl2 = (255, 255, 0)
          hlist.append(hhh.uuk)
          hhh.set_intersections(st3)
        pygame.draw.line(image, cl2, zs.get_zoom(hhh.uuk.coords[0]), zs.get_zoom(hhh.uuk.coords[1]))
        pygame.draw.circle(image, (0, 0, 255, 200), zs.get_zoom(hhh.p0.coords[0]), 8)
      for t in range(0, len(x)-1):
        pygame.draw.line(image, color, zs.get_zoom((x[t][0], x[t][1])), zs.get_zoom((x[t+1][0], x[t+1][1])))
      pygame.draw.circle(image, (0, 255, 255, 128), zs.get_zoom(x[0]), 5)
      pygame.draw.circle(image, (0, 255, 255, 128), zs.get_zoom(x[len(x)-1]), 5)
    #image.update()
    for k3 in st3:
      print(k3.idx)
      pnt = []
      for k, v in sorted(k3.hebelki.items(), key=operator.itemgetter(0)):
        print("__" + str(k))
        pnt.append(v.get_average_point())
      for i in range(0, len(pnt)-1):
      #print(pnt[i].coords)
      #print(pnt[i+1].coords)
        print(pnt[i].coords[0])
        print(pnt[i+1].coords[0])
        print(zs.get_zoom(pnt[i].coords[0]))
        pygame.draw.line(image, (0, 0, 255, 200), zs.get_zoom(pnt[i].coords[0], (600, 0)), zs.get_zoom(pnt[i+1].coords[0], (600, 0)))
    pygame.image.save(image, "lcz" + str(lcz) + ".png")
      #for uuk in k3.hebelki:
      #  stra = "  " + str(uuk) + " :"
      #  for j in k3.hebelki[uuk].intersections:
      #    stra = stra + " " + str(j) + "@" + str(k3.hebelki[uuk].intersections[j].idx)
      #  print(stra)

#cur.execute("SELECT * FROM yyy;")

#abc = cur.fetchall()
#lll = 0
#for alfa in abc:
#  lll = lll+1
#  x = wkb.loads(alfa[1], hex=True).coords
#  print(lol((x[0][0], x[0][1])))
#  print(lol((x[1][0], x[1][1])))
#  if(lll%1000 == 0):
#    pygame.display.update()
#  if(len(x) >= 2):
#    pygame.draw.line(screen, (111, 111, 111), lol((x[0][0], x[0][1])), lol((x[1][0], x[1][1])))

#cur.execute("SELECT * FROM SZTACHETY;")
#abc = cur.fetchall()
#for alfa in abc:
#  if(alfa[1] is not None and alfa[2] is not None and alfa[3] is not None):
#  	pygame.draw.line(screen, (111, 111, 111), lol((alfa[0], alfa[1])), lol((alfa[2], alfa[3])))
#
#for alfa in xyz:
#  txt = alfa[3]
#  txt = txt.replace('"', '')
#  txt = txt.replace("{", "")
#  txt = txt.replace("}", "")
#  txt = txt.replace("(", "")
#  txt = txt.replace(")", "")
#  txt2 = txt.split(",")
#  txt3 = [float(x) for x in txt2]
#  for x in range(0, len(txt3)-3, 2):
#    pygame.draw.line(screen, (255,255,255), lol((txt3[x], txt3[x+1])), lol((txt3[x+2], txt3[x+3])))
#  if(alfa[2]>1):
#    pygame.draw.circle(screen, (0,0,alfa[3]*30), lol((alfa[0], alfa[1])), 5, 0)
#  else:
#    pygame.draw.circle(screen, (255,0,alfa[3]*30), lol((alfa[0], alfa[1])), 3, 0)




#pygame.display.update()



#input("Press enter to exit ;)")
