import pygame
import sys
import ast
import psycopg2
import re
import shapely.geometry
import shapely.wkb as wkb

zoom = 10000
startx = 21.04
starty = 52.221
 
def lol(smiesznakrotka):
 return ((int)((smiesznakrotka[1]-startx)*zoom), (int)((smiesznakrotka[0]-starty)*zoom*1.7))

conn = psycopg2.connect(dbname="nextx", user="netbook")

cur = conn.cursor()

#cur.execute("SELECT * FROM (SELECT l1, l2, count(*) FROM graph2 GROUP BY l1, l2) xxx WHERE count > 2;");
cur.execute("SELECT * FROM lol WHERE visited=true");
xyz = cur.fetchall()
pygame.init()

screen = pygame.display.set_mode((640,480))


cur.execute("SELECT * FROM SZTACHETY;")
abc = cur.fetchall()
for alfa in abc:
  if(alfa[1] is not None and alfa[2] is not None and alfa[3] is not None):
  	pygame.draw.line(screen, (111, 111, 111), lol((alfa[0], alfa[1])), lol((alfa[2], alfa[3])))

for alfa in xyz:
  txt = alfa[3]
  txt = txt.replace('"', '')
  txt = txt.replace("{", "")
  txt = txt.replace("}", "")
  txt = txt.replace("(", "")
  txt = txt.replace(")", "")
  txt2 = txt.split(",")
  txt3 = [float(x) for x in txt2]
  for x in range(0, len(txt3)-3, 2):
    pygame.draw.line(screen, (255,255,255), lol((txt3[x], txt3[x+1])), lol((txt3[x+2], txt3[x+3])))
#  if(alfa[2]>1):
#    pygame.draw.circle(screen, (0,0,alfa[3]*30), lol((alfa[0], alfa[1])), 5, 0)
#  else:
#    pygame.draw.circle(screen, (255,0,alfa[3]*30), lol((alfa[0], alfa[1])), 3, 0)




pygame.display.update()



input("Press enter to exit ;)")
