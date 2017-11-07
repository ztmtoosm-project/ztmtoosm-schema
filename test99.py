import pygame
import shapely.geometry
import numpy as np
import shapely.affinity
from svgpathtools import Path, Line, QuadraticBezier, CubicBezier, Arc, wsvg
from lluk import LLuk
pygame.init()
pygame.display.set_caption('Crash!')
window = pygame.display.set_mode((900, 900))
running = True
colrs = ""
counter = 0

pos = [None, None, None, None]

lines = []
srodes = []
stroke_widths = []



def srumpy(coords):
    return coords[0] + 1.0j*(coords[1])



def drawcurve(counter, pos, window):
    if counter == 1:
        pygame.draw.circle(window, (0, 255, 0), pos[0], 5)
    if counter == 2:
        line = shapely.geometry.LineString([pos[0], pos[1]])
        pygame.draw.line(window, (255, 0, 0), pos[0], pos[1])

    if counter == 3:
         pygame.draw.line(window, (255, 0, 0), pos[0], pos[1])
         pygame.draw.circle(window, (0, 255, 0), pos[2], 5)
    if counter == 0:
         pygame.draw.line(window, (255, 0, 0), pos[0], pos[1])
         pygame.draw.line(window, (255, 0, 0), pos[2], pos[3])
         rect_lol, kosmos1, kosmos2 = LLuk(pos).get_pygame_arc()
         pygame.draw.arc(window, (255, 255, 0), rect_lol, kosmos1, kosmos2)


         lines.append(Line(srumpy(pos[0]), srumpy(pos[1])))
         lines.append(Line(srumpy(pos[2]), srumpy(pos[3])))
         print(kosmos2-kosmos1)
         if (is_right_to(kosmos1, kosmos2)):
            lines.append(Arc(srumpy(pos[1]), srumpy((intergreat_len, intergreat_len)), 0, False, False, srumpy(pos[2])))
         else:
            lines.append(Arc(srumpy(pos[1]), srumpy((intergreat_len, intergreat_len)), 0, False, True, srumpy(pos[2])))
         srodes.append(srumpy(pos[0]))
         stroke_widths.append(2)
         srodes.append(srumpy(pos[3]))
         stroke_widths.append(2)
         return "kcc"
    return ""
         #pygame.draw.circle(window, (255, 255, 0), (int(intergreat[0]), int(intergreat[1])), 8)

while True:
    ev = pygame.event.get()
    # handle MOUSEBUTTONUP
    for event in ev:
        if event.type == pygame.MOUSEBUTTONUP:
            for i in range(0, 8):
                for j in range(0, 8):
                    az1 = (i*3.14/8)*2-3.14
                    az2 = (j*3.14/8)*2-3.14
                    center = (i*180+180, j*180+180)
                    p1 = line_angle(center, 80, az1).coords[1]
                    p2 = line_angle(center, 40, az1).coords[1]
                    p3 = line_angle(center, 40, az2).coords[1]
                    p4 = line_angle(center, 80, az2).coords[1]
                    if i != j and i+4 != j and j+4 != i:
                        print(i)
                        print(j)
                        colrs += drawcurve(0, [p1, p2, p3, p4], window)


            #pos[counter] = pygame.mouse.get_pos()
            #print("clicked")
            #print(pos)
            #counter = counter + 1
            #counter = counter % 4
            #window.fill((0, 0, 0))
            #drawcurve(counter, pos, window)
            pygame.display.update()
            wsvg(lines, colors = colrs, nodes = srodes, node_radii = stroke_widths, filename='output16.svg')
