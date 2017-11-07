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
cols = ""


def srumpy(coords):
    return coords[0] + 1.0j*(coords[1])



def drawcurve(counter, pos, window):
    global cols
    if counter == 1:
        pygame.draw.circle(window, (0, 255, 0), pos[0], 5)
    if counter == 2:
        pygame.draw.line(window, (255, 0, 0), pos[0], pos[1])

    if counter == 3:
         pygame.draw.line(window, (255, 0, 0), pos[0], pos[1])
         pygame.draw.circle(window, (0, 255, 0), pos[2], 5)
    if counter == 0:
         pygame.draw.line(window, (255, 0, 0), pos[0], pos[1])
         pygame.draw.line(window, (255, 0, 0), pos[2], pos[3])
         rect_lol, kosmos1, kosmos2 = LLuk(pos).get_pygame_arc()
         pygame.draw.arc(window, (255, 255, 0), rect_lol, kosmos1, kosmos2)

         srodes.append(srumpy(pos[0]))
         stroke_widths.append(2)
         srodes.append(srumpy(pos[3]))
         stroke_widths.append(2)

         lines.append(Line(srumpy(pos[0]), srumpy(pos[1])))
         lines.append(Line(srumpy(pos[2]), srumpy(pos[3])))
         luck = LLuk(pos)
         lines.append(Line(srumpy(luck.additional_line[0]), srumpy(luck.additional_line[1])))
         lines.append(luck.get_svg_arc())
         cols = cols + "kkkk"

import signal
import sys


#def signal_term_handler(signal, frame):
#    print("####")
#    wsvg(lines, colors=cols, nodes=srodes, node_radii=stroke_widths, filename='output16.svg')
#    sys.exit(0)


#signal.signal(signal.SIGTERM, signal_term_handler)

while True:
    try:
        ev = pygame.event.get()
    except KeyboardInterrupt:
        print("####")
        wsvg(lines, colors=cols, nodes=srodes, node_radii=stroke_widths, filename='output16.svg')
        sys.exit(0)
    # handle MOUSEBUTTONUP
    for event in ev:
        if event.type == pygame.MOUSEBUTTONUP:
            pos[counter] = pygame.mouse.get_pos()
            #print("clicked")
            #print(pos)
            counter = counter + 1
            counter = counter % 4
            window.fill((0, 0, 0))
            drawcurve(counter, pos, window)
            pygame.display.update()