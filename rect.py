from shapely.geometry import MultiLineString, LineString


class Rect:
    def __reverse(self, point_to_start, point_to_stop):
        p1, p2 = self.main_line
        l1_start = LineString([p1, point_to_start]).length
        l1_stop = LineString([p1, point_to_stop]).length
        l2_start = LineString([p2, point_to_start]).length
        l2_stop = LineString([p2, point_to_stop]).length
        if l2_start < l1_start and l2_stop > l1_stop:
            self.main_line = (p2, p1)

    @staticmethod
    def __intersection1(line, collection):
        x = line.intersection(collection)
        if x.is_empty:
            return 0
        inside_rect = x.minimum_rotated_rectangle
        try:
            coords = inside_rect.exterior.coords
            lli = [LineString([line.coords[0], x]).length for x in coords]
            return max(lli) - min(lli)
        except Exception:
            try:
                return inside_rect.length
            except Exception:
                return 0

    def __get_shortest_bock(self):
        coords = self.rectangle.exterior.coords
        len1 = LineString([coords[0], coords[1]]).length
        len2 = LineString([coords[1], coords[2]]).length
        ccw = False
        if self.rectangle.exterior.is_ccw:
            ccw = True
        if(len1 < len2):
            if ccw:
                return LineString([coords[0], coords[1]])
            else:
                return LineString([coords[1], coords[0]])
        if ccw:
            return LineString([coords[1], coords[2]])
        else:
            return LineString([coords[2], coords[1]])



    def get_covering(self):
        if self.type > 0:
            return 0
        bock = self.__get_shortest_bock()
        vll = None
        for i in range(30, int(self.len2), 30):
            tmp = Rect.__intersection1(bock.parallel_offset(i, 'left'), self.collection)
            if tmp > 0:
                if vll is not None:
                    vll = min(vll, tmp)
                else:
                    vll = tmp
        if vll is None:
            return 0
        return vll


    def __init__(self, lineset):
        self.collection = MultiLineString(lineset)
        rectangle = self.collection.minimum_rotated_rectangle
        self.rectangle = rectangle
        self.type = 0
        try:
            coords = rectangle.exterior.coords
            self.len1 = LineString([coords[0], coords[1]]).length
            self.len2 = LineString([coords[1], coords[2]]).length
            if self.len1 < self.len2:
                p1 = ((coords[0][0] + coords[1][0]) / 2, (coords[0][1] + coords[1][1]) / 2)
                p2 = ((coords[2][0] + coords[3][0]) / 2, (coords[2][1] + coords[3][1]) / 2)
            else:
                self.len2, self.len1 = self.len1, self.len2
                p1 = ((coords[0][0] + coords[3][0]) / 2, (coords[0][1] + coords[3][1]) / 2)
                p2 = ((coords[1][0] + coords[2][0]) / 2, (coords[1][1] + coords[2][1]) / 2)
            self.main_line = (p1, p2)
        except Exception:
            try:
                self.type = 1
                self.main_line = (rectangle.coords[0], rectangle.coords[1])
                self.len1 = 0
                self.len2 = rectangle.length
            except Exception:
                self.type = 2
                self.len1 = 0
                self.len2 = 0