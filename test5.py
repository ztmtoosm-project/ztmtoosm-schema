import pygame
import shapely.geometry
import numpy as np
import shapely.affinity
pygame.init()
pygame.display.set_caption('Crash!')
window = pygame.display.set_mode((600, 600))
running = True
#Draw Once
#Main Loop


def azimuth(point1, point2):
    angle = np.arctan2(point2[0] - point1[0], point2[1] - point1[1])
    return angle


def line_angle(point, length, azimuth):
    nextx = shapely.geometry.Point(point[0], point[1] + length)
    ls = shapely.geometry.LineString([point, nextx])
    return shapely.affinity.rotate(ls, azimuth, origin=shapely.geometry.Point(point), use_radians=True)


def line_angle2(point, length, azimuth):
    p1 = line_angle(point, length, azimuth)
    p2 = line_angle(point, length, azimuth+3.14)
    return shapely.geometry.LineString([p1.coords[1], p2.coords[1]])

counter = 0

pos = [None, None, None, None]

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
         #pygame.draw.line(window, (255, 0, 0), pos[0], pos[1])
         #pygame.draw.line(window, (255, 0, 0), pos[2], pos[3])
         pos1a = line_angle2(pos[1], 800, azimuth(pos[0], pos[1])*-1.0)
         pos11 = pos1a.coords
        # pygame.draw.line(window, (255, 255, 255), pos11[0], pos11[1])
         pos3a = line_angle2(pos[2], 800, azimuth(pos[3], pos[2])*-1.0)
         pos33 = pos3a.coords
         krop = pos1a.intersection(pos3a).coords[0]
         sub1 = shapely.geometry.LineString([krop, pos[1]])
         sub2 = shapely.geometry.LineString([krop, pos[2]])
         print(sub1.length)
         print(sub2.length)
         dupa = [None, None, None]
         dupa2 = [None, None, None]
         lnn = 0
         if sub1.length > sub2.length:
             lnn = sub2.length
             dupa = [sub1.interpolate(sub2.length).coords[0], krop, pos[2]]
             dupa2 = [pos[1], sub1.interpolate(sub2.length).coords[0], pos[2]]
         else:
             lnn = sub1.length
             dupa = [pos[1], krop, sub2.interpolate(sub1.length).coords[0]]
             dupa2 = [pos[2], sub2.interpolate(sub1.length).coords[0], pos[1]]
         #for dup in dupa:
         #   pygame.draw.circle(window, (255, 255, 0), (int(dup[0]), int(dup[1])), 8)
         #pygame.draw.line(window, (255, 255, 255), pos33[0], pos33[1])
         pros1 = line_angle2(dupa[0], 800, azimuth(dupa[0], dupa[1])*-1-3.14/2)
         pros2 = line_angle2(dupa[2], 800, azimuth(dupa[1], dupa[2])*-1-3.14/2)
         #pygame.draw.line(window, (0, 0, 255), pros1.coords[0], pros1.coords[1])
         #pygame.draw.line(window, (0, 0, 255), pros2.coords[0], pros2.coords[1])
         pygame.draw.line(window, (255, 255, 255), dupa2[0], dupa2[1])
         intergreat = pros1.intersection(pros2).coords[0]
         intergreat_len =  shapely.geometry.LineString([dupa[0], pros1.intersection(pros2).coords[0]]).length

         rect_lol = pygame.Rect(intergreat[0] - intergreat_len, intergreat[1] - intergreat_len, intergreat_len*2, intergreat_len*2)

         kosmos1 = azimuth(dupa[0], dupa[1])-3.142
         kosmos2 = azimuth(dupa[1], dupa[2])-3.142


         left_top = [intergreat[0] - intergreat_len, intergreat[1] - intergreat_len]
         right_top = [intergreat[0] + intergreat_len, intergreat[1] - intergreat_len]
         left_bottom = [intergreat[0] - intergreat_len, intergreat[1] + intergreat_len]
         right_bottom = [intergreat[0] + intergreat_len, intergreat[1] + intergreat_len]

         #pygame.draw.line(window, (255, 255, 0), left_top, right_top)
         #pygame.draw.line(window, (255, 255, 0), right_top, right_bottom)
         #pygame.draw.line(window, (255, 255, 0), right_bottom, left_bottom)
         #pygame.draw.line(window, (255, 255, 0), left_bottom, left_top)
         pygame.draw.arc(window, (255, 255, 0), rect_lol, kosmos1, kosmos2)
         #pygame.draw.circle(window, (255, 255, 0), (int(intergreat[0]), int(intergreat[1])), 8)

while True:
    ev = pygame.event.get()
    # handle MOUSEBUTTONUP
    for event in ev:
        if event.type == pygame.MOUSEBUTTONUP:
            pos[counter] = pygame.mouse.get_pos()
            print("clicked")
            print(pos)
            counter = counter + 1
            counter = counter % 4
            window.fill((0, 0, 0))
            drawcurve(counter, pos, window)
            pygame.display.update()