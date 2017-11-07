import pygame
import shapely.geometry
import numpy as np
import shapely.affinity
from shapely.geometry import LineString
from svgpathtools import Arc


def srumpy(coords):
    return coords[0] + 1.0j*(coords[1])

class LLuk:

    @staticmethod
    def azimuth(point1, point2):
        angle = np.arctan2(point2[0] - point1[0], point2[1] - point1[1])
        return angle

    @staticmethod
    def line_angle(point, length, azimuth):
        nextx = shapely.geometry.Point(point[0], point[1] + length)
        ls = shapely.geometry.LineString([point, nextx])
        return shapely.affinity.rotate(ls, azimuth, origin=shapely.geometry.Point(point), use_radians=True)

    @staticmethod
    def line_angle2(point, length, azimuth):
        p1 = LLuk.line_angle(point, length, azimuth)
        p2 = LLuk.line_angle(point, length, azimuth + LLuk.pi())
        return shapely.geometry.LineString([p1.coords[1], p2.coords[1]])

    @staticmethod
    def line_angle3(point1, point2, length):
        azimuth = LLuk.azimuth(point1, point2) * -1
        p1 = LLuk.line_angle(point2, length, azimuth)
        p2 = LLuk.line_angle(point1, length, azimuth + LLuk.pi())
        return shapely.geometry.LineString([p2.coords[1], p1.coords[1]])

    @staticmethod
    def is_right_to(angle1, angle2):
        if angle2 - angle1 < (LLuk.pi() * -1):
            return True
        if angle2 - angle1 < 0:
            return False
        if angle2 - angle1 > LLuk.pi():
            return False
        return True

    @staticmethod
    def right2(angle1, angle2):
        if(angle2 > angle1):
            dist0 = angle2 - angle1
        else:
            dist0 = LLuk.pi() - angle1 + angle2 + LLuk.pi()
        return dist0 > LLuk.pi()

    @staticmethod
    def right3(angle1, angle2):
        if(angle2 > angle1):
            dist0 = angle2 - angle1
        else:
            dist0 = LLuk.pi() - angle1 + angle2 + LLuk.pi()
        if(dist0 > LLuk.pi()):
            return LLuk.pi() * 2 - dist0
        return dist0

    @staticmethod
    def pi():
        return 3.142

    def __init__(self, pos, tmp_length=800):
        self.pos = pos
        pos1a = self.line_angle2(pos[1], tmp_length, self.azimuth(pos[0], pos[1]) * -1.0)
        pos3a = self.line_angle2(pos[2], tmp_length, self.azimuth(pos[3], pos[2]) * -1.0)
        krop = pos1a.intersection(pos3a).coords[0]
        self.inter = krop
        sub1 = shapely.geometry.LineString([krop, pos[1]])
        sub2 = shapely.geometry.LineString([krop, pos[2]])

        lnn = 0
        if sub1.length > sub2.length:
            lnn = sub2.length
            lvals = [sub1.interpolate(sub2.length).coords[0], krop, pos[2]]
            self.additional_line = (pos[1], sub1.interpolate(sub2.length).coords[0])
            self.additional_type = 1
        else:
            lnn = sub1.length
            lvals = [pos[1], krop, sub2.interpolate(sub1.length).coords[0]]
            self.additional_line = (sub2.interpolate(sub1.length).coords[0], pos[2])
            self.additional_type = 2
        pros1 = self.line_angle2(lvals[0], tmp_length, self.azimuth(lvals[0], lvals[1]) * -1 - self.pi() / 2)
        pros2 = self.line_angle2(lvals[2], tmp_length, self.azimuth(lvals[1], lvals[2]) * -1 - self.pi() / 2)
        self.arc_center = pros1.intersection(pros2).coords[0]
        self.arc_radius = shapely.geometry.LineString([lvals[0], pros1.intersection(pros2).coords[0]]).length
        self.azimuth1 = self.azimuth(lvals[0], lvals[1])
        self.azimuth2 = self.azimuth(lvals[1], lvals[2])
        self.arc_start = lvals[0]
        self.arc_end = lvals[2]

    def get_svg_arc(self):
        if (self.is_right_to(self.azimuth1, self.azimuth2)):
            return Arc(srumpy(self.arc_start), srumpy((self.arc_radius, self.arc_radius)), 0, False, False, srumpy(self.arc_end))
        else:
            return Arc(srumpy(self.arc_start), srumpy((self.arc_radius, self.arc_radius)), 0, False, True, srumpy(self.arc_end))

    def get_pygame_arc(self):
        rect = pygame.Rect(self.arc_center[0] - self.arc_radius, self.arc_center[1] - self.arc_radius, self.arc_radius * 2, self.arc_radius * 2)
        kosmos1 = self.azimuth1
        kosmos2 = self.azimuth2
        if(self.right2(kosmos1, kosmos2)):
            tmp = kosmos2
            kosmos2 = kosmos1
            kosmos1 = tmp
        else:
            kosmos1 += self.pi()
            kosmos2 += self.pi()
        return (rect, kosmos1, kosmos2)

    @staticmethod
    def create_lluk_triangle(pos, arc):
        azimuth = LLuk.azimuth(pos[0], pos[1])
        len1 = shapely.geometry.LineString([pos[0], pos[1]]).length
        len2 = shapely.geometry.LineString([pos[1], pos[2]]).length
        p0 = LLuk.line_angle(pos[0], arc, azimuth * -1 + LLuk.pi()).coords[1]
        p2 = shapely.geometry.LineString([pos[1], pos[2]]).interpolate(arc).coords[0]
        return (LLuk([p0, pos[0], p2, pos[2]]), p2, pos[2])

    @staticmethod
    def create_lluk_triangle_inf_arc(pos, tmp_length, tmp_length2):
        azimuth = LLuk.azimuth(pos[0], pos[1])
        azimuth2 = LLuk.azimuth(pos[1], pos[2])
        len1 = shapely.geometry.LineString([pos[0], pos[1]]).length
        len2 = shapely.geometry.LineString([pos[1], pos[2]]).length
        p0 = LLuk.line_angle(pos[0], tmp_length2, azimuth - LLuk.pi()).coords[1]
        p2 = LLuk.line_angle(pos[2], tmp_length2, azimuth2 + LLuk.pi()).coords[1]
        return LLuk([p0, pos[0], pos[2], p2], tmp_length)

    @staticmethod
    def __get_closest_point2(p1, p2, p):
        l1 = shapely.geometry.LineString([p1, p]).length
        if l1 < shapely.geometry.LineString([p1, p2]).length / 2:
            return p2
        return p1

    @staticmethod
    def check_arc(luck, arc):
        if luck.arc_radius < arc:
            return LLuk.create_lluk_triangle([luck.pos[0], luck.inter, luck.pos[3]], arc)
        p0 = LLuk.line_angle(luck.pos[0], arc, LLuk.azimuth(luck.pos[0], luck.pos[1]) * -1 + LLuk.pi()).coords[1]
        return (LLuk([p0, luck.pos[0], luck.arc_end, luck.pos[3]]), luck.arc_end, luck.pos[3])

    def get_shapely_linestring(self, numsegments):
        centerx, centery = self.arc_center
        radius = self.arc_radius
        kosmos1 = self.azimuth1 - LLuk.pi()
        kosmos2 = self.azimuth2 - LLuk.pi()
        if kosmos1 < -LLuk.pi():
            kosmos1 += 2 * LLuk.pi()
        if kosmos2 < -LLuk.pi():
            kosmos2 += 2 * LLuk.pi()

        kosmos1 *= -1
        kosmos2 *= -1

        if (self.right2(kosmos1, kosmos2)):
            pass
        else:
            kosmos1 += self.pi()
            kosmos2 += self.pi()

        if (kosmos1 > kosmos2 + LLuk.pi()):
            kosmos1 -= 2 * LLuk.pi()
        if (kosmos2 > kosmos1 + LLuk.pi()):
            kosmos2 -= 2 * LLuk.pi()

        theta = np.radians(np.linspace(kosmos1*180/LLuk.pi(), kosmos2*180/LLuk.pi(), numsegments))
        x = centerx + radius * np.cos(theta)
        y = centery + radius * np.sin(theta)
        coords = []
        if self.additional_type == 1:
            coords = list(self.additional_line)
        coords.extend(list(np.column_stack([x, y])))
        if self.additional_type == 2:
            coords.extend(list(self.additional_line))
        return LineString(coords)

    @staticmethod
    def create_lluk_angle(point1, angle1, point2, angle2, tmp_len, tmp_len2):
        inter = LLuk.line_angle2(point1, tmp_len, angle1).intersection(LLuk.line_angle2(point2, tmp_len, angle2)).coords[0]
        return LLuk.create_lluk_triangle_inf_arc([point1, inter, point2], tmp_len, tmp_len2)

    @staticmethod
    def create_lluk_special(pos, arc, tmp_length=800):
        ll1 = LLuk.line_angle3(pos[0], pos[1], tmp_length)
        ll2 = LLuk.line_angle3(pos[2], pos[3], tmp_length)
        p = ll1.intersection(ll2).coords[0]
        l1 = shapely.geometry.LineString([ll1.coords[0], p]).length
        l2 = shapely.geometry.LineString([ll2.coords[0], p]).length
        len1 = shapely.geometry.LineString([pos[0], pos[1]]).length
        len2 = shapely.geometry.LineString([pos[2], pos[3]]).length
        if l1 < tmp_length:
            if l2 < tmp_length:
                print("@1")
                return LLuk.check_arc(LLuk([pos[1], pos[0], pos[2], pos[3]], tmp_length), arc)
            elif l2 < tmp_length + len2:
                print("@2")
                aa = pos[1]
                bb = LLuk.__get_closest_point2(pos[2], pos[3], p)
                return LLuk.create_lluk_triangle([aa, p, bb], arc)
            else:
                print("@3")
                return LLuk.check_arc(LLuk([pos[1], pos[0], pos[3], pos[2]], tmp_length), arc)
        elif l1 < tmp_length + len1:
            if l2 < tmp_length:
                print("@4")
                aa = LLuk.__get_closest_point2(pos[0], pos[1], p)
                bb = pos[3]
            elif l2 < tmp_length + len2:
                print("@5")
                aa = LLuk.__get_closest_point2(pos[0], pos[1], p)
                bb = LLuk.__get_closest_point2(pos[2], pos[3], p)
            else:
                print("@6")
                aa = LLuk.__get_closest_point2(pos[0], pos[1], p)
                bb = pos[2]
            return LLuk.create_lluk_triangle([aa, p, bb], arc)
        else:
            if l2 < tmp_length:
                print("@7")
                return LLuk.check_arc(LLuk(pos, tmp_length), arc)
            elif l2 < tmp_length + len2:
                print("@8")
                aa = pos[0]
                bb = LLuk.__get_closest_point2(pos[2], pos[3], p)
                return LLuk.create_lluk_triangle([aa, p, bb], arc)
            else:
                print("@9")
                return LLuk.check_arc(LLuk([pos[0], pos[1], pos[3], pos[2]], tmp_length), arc)