import pygame
import sys
import ast
import psycopg2
import re
import shapely.geometry
import shapely.wkb as wkb
from pprint import pprint as pp

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

  def get_zoom(self, smiesznakrotka):
    zoom = (self.maxY - self.minY)/(self.height-10)
    if(self.ratio_type):
      zoom = (self.maxX - self.minX)/(self.width-10)
    a = (smiesznakrotka[0] - self.avgX())/zoom + self.width/2
    b = (0 - smiesznakrotka[1] + self.avgY())/zoom + self.height/2
    return (int(a),int(b))     

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

zoom = 0.2
startx = 4000
starty = 2800
 
def lol(smiesznakrotka):
 #return ((int)((smiesznakrotka[0]-startx)*zoom), 480-(int)((smiesznakrotka[1]-starty)*zoom))
 return ((int)(smiesznakrotka[0]*zoom)-startx, 1080-((int)((smiesznakrotka[1])*zoom)-starty))

conn = psycopg2.connect(dbname="nextx", user="netbook")

cur = conn.cursor()

#cur.execute("SELECT * FROM (SELECT l1, l2, count(*) FROM graph2 GROUP BY l1, l2) xxx WHERE count > 2;");
#cur.execute("SELECT * FROM lol WHERE visited=true");
#xyz = cur.fetchall()
pygame.init()

screen = pygame.display.set_mode((800,550))


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

for alfa in abc:
  color = (88, 88, 88)
  print(alfa[0])
  if not alfa[0] in ds.leader.keys():
    color = (255, 0, 0)
  else:
    sl = len(ds.group[ds.leader[alfa[0]]])
    if(sl == 1):
      color = (0, 255, 0)
    if(sl == 2):
      color = (120, 120, 255)
  lll = lll+1
  x = wkb.loads(alfa[1], hex=True).coords
  pdict.update({alfa[0] : x})
  if(lll%1000 == 0):
    pygame.display.update()
  for t in range(0, len(x)-1):
    pygame.draw.line(screen, color, zkt.get_zoom((x[t][0], x[t][1])), zkt.get_zoom((x[t+1][0], x[t+1][1])))

pygame.display.update()
pygame.image.save(screen, 'aaa.png')

for k in ds.group.keys():
  k2 = ds.group[k]
  if(len(k2) > 2):
    screen.fill((0, 0, 0))
    st = set()
    for k3 in k2:
      st |= set(pdict[k3])
    zs = ZoomSet(st, 600, 600)
    for k3 in k2:
      color = (255, 255, 255)
      x = pdict[k3]
      for t in range(0, len(x)-1):
        pygame.draw.line(screen, color, zs.get_zoom((x[t][0], x[t][1])), zs.get_zoom((x[t+1][0], x[t+1][1])))
    pygame.display.update()

     

input("Press enter to exit ;)")

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
