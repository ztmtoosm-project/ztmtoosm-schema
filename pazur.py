import pickle
from interval import interval

from shapely.geometry import *

from lluk import LLuk
from rect import Rect
from hashlib import md5

def cut(line, distance):
    # Cuts a line in two at a distance from its starting point
    if distance <= 0.0:
        return [None, LineString(line)]
    if distance >= line.length:
        return [LineString(line)]
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
                LineString(coords[:i+1]),
                LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]
def cut_piece(line, start, stop):
    """ From a linestring, this cuts a piece of length lgth at distance.
    Needs cut(line,distance) func from above ;-)
    """
    precut = cut(line,start)[1]
    result = cut(precut,stop-start)[0]
    return result

class ContinousSet:
    def __init__(self):
        self.objects = dict()
    def add(self, obj, fromm, too):
        if fromm > too:
            fromm, too = too, fromm
        if obj in self.objects:
            self.objects[obj] = self.objects[obj] | interval([fromm, too])
        else:
            self.objects[obj] = interval([fromm, too])
    def __or__(self, other):
        ret = ContinousSet()
        for obj, inter in self.objects.items():
            for a, b in inter:
                ret.add(obj, a, b)
        for obj, inter in other.objects.items():
            for a, b in inter:
                ret.add(obj, a, b)
        return ret
    def __ior__(self, other):
        for obj, inter in other.objects.items():
            for a, b in inter:
                self.add(obj, a, b)
        return self
    def __and__(self, other):
        ret = ContinousSet()
        for obj, inter in self.objects.items():
            if obj in other.objects:
                ret.objects[obj] = self.objects[obj] & other.objects[obj]
        return ret

    def linestring_set(self):
        ret = []
        for obj, inter in self.objects.items():
            for a, b in inter:
                ret.append(cut_piece(obj.linestring, a, b))
        return ret


class Pazur:
    @staticmethod
    def __mulist_converter(lst):
        dtc = dict()

        for h1, h2, x in lst:
            cs = ContinousSet()
            obj_bef, pos_bef = None, None
            for obj, pos in x:
                if obj_bef is not None and pos_bef is not None:
                    if obj_bef == obj:
                        cs.add(obj, pos_bef, pos)
                obj_bef, pos_bef = obj, pos
            if (h1, h2) in dtc:
                dtc[(h1, h2)] |= cs
            elif (h2, h1) in dtc:
                dtc[(h2, h1)] |= cs
            else:
                dtc[(h1, h2)] = cs
        return dtc


    @staticmethod
    def __linebrowser(hebelki_tuple_list_list):
        mulist = []
        for hebelki_tuple_list in hebelki_tuple_list_list:
            last_hebelek = None
            current_list = []
            for i in range(0, len(hebelki_tuple_list)):
                current_list.append((hebelki_tuple_list[i][0], hebelki_tuple_list[i][1]))
                if hebelki_tuple_list[i][2] is not None:
                    current_hebelek = hebelki_tuple_list[i][2]
                    if last_hebelek is not None:
                        mulist.append((last_hebelek, current_hebelek, current_list))
                    last_hebelek = current_hebelek
                    current_list = [(hebelki_tuple_list[i][0], hebelki_tuple_list[i][1])]
        return mulist

    @staticmethod
    def __mulist_gett(mulist, start, stop):
        if (start, stop) in mulist:
            return mulist[(start, stop)]
        if (stop, start) in mulist:
            return mulist[(stop, start)]
        return ContinousSet()

    @staticmethod
    def __goo(x1, x2, hebelki_visited):
        tbb = [x1, x2]
        while x2.is_middle() and (x2 not in hebelki_visited):
            hebelki_visited.add(x2)
            foo = ((x2.nast | x2.bef) - {x2} - {x1})
            foo = list(foo)[0]
            tbb.append(foo)
            x1 = x2
            x2 = foo
        return tbb

    def get_rects_main_line(self):
        ret = []
        for rect in self.man_rect:
            if rect.type < 2:
                ret.append(rect.main_line)
        return ret

    def __divide_rect(self, mulist):
        lenn = len(self.hebelek_list)
        curr = 0
        for i in range(0, lenn-1):
            if i >= curr:
                curr_rect = None
                core_linestrings1 = ContinousSet()
                for j in range(i, lenn-1):
                    current_set = Pazur.__mulist_gett(mulist, self.hebelek_list[j], self.hebelek_list[j + 1])
                    core_linestrings1 |= current_set
                    rect1 = Rect(core_linestrings1.linestring_set())
                    cov = rect1.get_covering()
                    if rect1.len1 < 30 and rect1.len2 > 50 and (cov + 5 >= rect1.len1*2/3):
                        print("***")
                        curr_rect = rect1
                        curr = j+1
                    if rect1.len1 > 30 or (cov + 5 < rect1.len1*2/3):
                        break
                if curr_rect is not None:
                    self.man_rect.append(curr_rect)

    def __add_to_dict(self, dictt, obj, mode):
        if obj not in dictt:
            dictt[obj] = set()
        dictt[obj].add((self, mode))


    @staticmethod
    def angle_to_lluk_distance(hebelek1, hebelek2):
        diff_angle = abs((hebelek1.angle % LLuk.pi()) - (hebelek2.angle % LLuk.pi()))
        return min(diff_angle, LLuk.pi() - diff_angle)

    @staticmethod
    def angle_to_lluk(hebelek1, hebelek2):
        if Pazur.angle_to_lluk_distance(hebelek1, hebelek2) > 0.06:
            return False
        return True

    def __get_best_possible_ancestor(self, is_bef=False):
        lst = self.ancestor_nex
        ret = None
        if len(self.hebelek_list) == 0:
            return
        hebelek_pos = -1
        if is_bef:
            lst = self.ancestor_bef
            hebelek_pos = 0
        ret_distance = 1000.0
        for pazur, val in lst:
            ok = False
            if val == 0 and pazur.best_bef is None:
                ok = True
            if val == -1 and pazur.best_nex is None:
                ok = True
            if len(pazur.hebelek_list) == 0:
                ok = False
            if ok:
                tmp = Pazur.angle_to_lluk_distance(self.hebelek_list[hebelek_pos], pazur.hebelek_list[val])
                if tmp < ret_distance:
                    ret_distance = tmp
                    ret = (pazur, val)
        return ret

    def set_best_ancestor(self, is_bef):
        if len(self.hebelek_list) == 0:
            return
        if is_bef and self.best_bef is not None:
            return
        if not is_bef and self.best_nex is not None:
            return
        v1 = self.__get_best_possible_ancestor(is_bef)
        is_beff = -1
        if is_bef:
            is_beff = 0
        if v1 is not None:
            pazur, direction = v1
            if direction == -1:
                direction2 = False
            else:
                direction2 = True
            v2 = pazur.__get_best_possible_ancestor(direction2)
            if v2 is not None and v2[0] == self:
                if is_bef:
                    self.best_bef = (pazur, direction)
                else:
                    self.best_nex = (pazur, direction)
                if direction2:
                    pazur.best_bef = (self, is_beff)
                else:
                    pazur.best_nex = (self, is_beff)


    def set_ancestor(self, dictt):
        self.best_bef = None
        self.best_nex = None
        if len(self.hebelek_list) == 0:
            return
        self.ancestor_bef = []
        self.ancestor_nex = []
        for x in self.pazur_start:
            if x in dictt:
                self.ancestor_bef.extend(dictt[x])
        for x in self.pazur_stop:
            if x in dictt:
                self.ancestor_nex.extend(dictt[x])



    @staticmethod
    def check_angle(hebelek1, hebelek2, linestring_set):
        try:
            if not Pazur.angle_to_lluk(hebelek1, hebelek2):
                luck = LineString([hebelek1.get_average_point(), hebelek2.get_average_point()])
            else:
                luck = LLuk.create_lluk_angle(hebelek1.get_average_point().coords[0],
                                          (hebelek1.angle + LLuk.pi()),
                                          hebelek2.get_average_point().coords[0],
                                          (hebelek2.angle + LLuk.pi()), 10000, 50).get_shapely_linestring(100)
            buffer = 30
            if luck.buffer(buffer).contains(MultiLineString(linestring_set)):
                return buffer
        except Exception:
            return 100
        return 100

    @staticmethod
    def bfs_path(listt, p0, p1):
        dtc = dict()
        for a, b in listt:
            if a not in dtc:
                dtc[a] = []
            dtc[a].append(b)
        visited = dict()
        to_visit = [(p0, p0)]
        while len(to_visit) > 0:
            current, bef = to_visit[0]
            to_visit = to_visit[1:]
            if current not in visited:
                visited[current] = bef
                if current == p1:
                    break
                if current in dtc:
                    for x in dtc[current]:
                        to_visit.append((x, current))
        current = p1
        ret = []
        try:
            while current != p0:
                ret.append(current)
                current = visited[current]
            ret.append(p0)
            return ret[::-1]
        except Exception:
            return []

    def check_angles(self, mulist):
        ret = []
        lenn = len(self.hebelek_list)
        curr = 0
        for i in range(0, lenn-1):
            core_linestrings1 = ContinousSet()
            for j in range(i, lenn-1):
                current_set = Pazur.__mulist_gett(mulist, self.hebelek_list[j], self.hebelek_list[j + 1])
                core_linestrings1 |= current_set
                dst = Pazur.check_angle(self.hebelek_list[i], self.hebelek_list[j+1], core_linestrings1.linestring_set())
                if dst < 100:
                    ret.append((i, j+1))
        return ret

    def create_luck_path(self, path):
        ret = []
        bef = None
        for x in path:
            if bef is not None:
                hebelek1 = self.hebelek_list[bef]
                hebelek2 = self.hebelek_list[x]
                if Pazur.angle_to_lluk(hebelek1, hebelek2):
                    luck = LLuk.create_lluk_angle(hebelek1.get_average_point().coords[0],
                                                  (hebelek1.angle + LLuk.pi()),
                                                  hebelek2.get_average_point().coords[0],
                                                  (hebelek2.angle + LLuk.pi()), 10000, 50)
                    ret.append((luck, None, None))
                else:
                    ret.append((None, hebelek1.get_average_point().coords[0], hebelek2.get_average_point().coords[0]))
            bef = x
        return ret

    def get_hash(self):
        mls = MultiLineString(self.core_linestring_set)
        print(mls.wkb)
        print(len(self.core_linestring_set))
        hashh = md5(mls.wkb)
        return hashh.hexdigest()

    def __init__(self, hebelek_list, pazur_map, pazur_map2, mulist, dictt, hashes):
        lenn = len(hebelek_list)
        start = hebelek_list[0]
        stop = hebelek_list[-1]
        self.hebelek_list = hebelek_list
        self.pazur_start = []
        self.pazur_stop = []
        if start in pazur_map:
            if hebelek_list[1] == pazur_map[start]:
                self.pazur_start = list(pazur_map2[start])
            else:
                self.hebelek_list = self.hebelek_list[1:]
                self.pazur_start.append(hebelek_list[0])
        else:
            pass
        if stop in pazur_map:
            if hebelek_list[-2] == pazur_map[stop]:
                self.pazur_stop = list(pazur_map2[stop])
            else:
                self.hebelek_list = self.hebelek_list[:-1]
                self.pazur_stop.append(hebelek_list[-1])
        else:
            pass

        if len(self.hebelek_list) > 0:
            self.__add_to_dict(dictt, self.hebelek_list[0], 0)
            self.__add_to_dict(dictt, self.hebelek_list[-1], -1)

        core_linestrings = ContinousSet()
        for i in range(0, len(self.hebelek_list)-1):
            current_set = Pazur.__mulist_gett(mulist, self.hebelek_list[i], self.hebelek_list[i+1])
            core_linestrings |= current_set
        self.core_linestring_set = core_linestrings.linestring_set()
        self.rect = Rect(self.core_linestring_set)
        self.man_rect = []
        self.luck_matching = []
        self.luck = None
        self.luck2 = None
        '''
        try:
            luck = LLuk.create_lluk_angle(self.hebelek_list[0].get_average_point().coords[0],
                                               (self.hebelek_list[0].angle + LLuk.pi()),
                                               self.hebelek_list[-1].get_average_point().coords[0],
                                               (self.hebelek_list[-1].angle + LLuk.pi()), 10000, 50)
            self.luck2 = luck.get_shapely_linestring(100).buffer(30)
            if luck.get_shapely_linestring(100).buffer(30).contains(MultiLineString(self.core_linestring_set)):
                self.luck = luck

        except Exception as e:
            print(e)
            pass
        '''
        self.luck3 = []
        '''
        hashh = self.get_hash()
        print(hashh)
        if hashh in hashes:
            print("loaded!")
            self.luck3 = hashes[hashh]
        else:
            path = Pazur.bfs_path(self.check_angles(mulist), 0, len(self.hebelek_list) - 1)
            self.luck3 = self.create_luck_path(path)
            hashes[hashh] = self.luck3
        '''
        '''
        if self.rect.len1 > 30:
            self.__divide_rect(mulist)
        else:
            self.man_rect = [self.rect]
        '''

    @staticmethod
    def create_pazurs(lines, hebelki_all):
        try:
            with open("/home/dell/lluck.pickle", 'rb') as f:
                hashes = pickle.load(f)
        except Exception as e:
            print(e)
            hashes = dict()
        print(len(hashes))
        hebelki_triples = dict()
        hebelki_szpice = dict()
        hebelki_szpice2 = dict()
        pazurs = []
        mulist = []
        for k, x in lines.items():
            mulist.extend(Pazur.__linebrowser(x.hebelki2))
            for uuu in x.hebelki:
                hebelki_len = len(uuu)
                for i in range(0, hebelki_len-2):
                    h1 = uuu[i][1]
                    h2 = uuu[i+1][1]
                    h3 = uuu[i+2][1]
                    if not h2.is_middle():
                        hebelki_triples.setdefault(h2, set())
                        hebelki_triples[h2].add((h1, h3))
        for h2, hh in hebelki_triples.items():
            tmp_map = dict()
            for h1, h3 in hh:
                tmp_map.setdefault(h1, set())
                tmp_map.setdefault(h3, set())
                tmp_map[h1].add(h3)
                tmp_map[h3].add(h1)
            checked = None
            c_none = False
            for key, value in tmp_map.items():
                if len(value) > 1 and checked is not None:
                    c_none = True
                if len(value) > 1 and checked is None:
                    checked = key
            if c_none:
                checked = None
            if checked is not None:
                hebelki_szpice.setdefault(h2, None)
                hebelki_szpice[h2] = checked
                hebelki_szpice2.setdefault(h2, None)
                hebelki_szpice2[h2] = tmp_map[checked]

        hebelki_visited = set()
        mulist = Pazur.__mulist_converter(mulist)
        pazur_dict = dict()
        counter1 = 0
        for x in hebelki_all:
            if not x.is_middle():
                hebelki_visited.add(x)
                for y in ((x.nast | x.bef) - {x}):
                    if not y in hebelki_visited:
                        counter1 += 1
                        print(counter1, ".....")
                        #if counter1 < 500:
                        pazurs.append(Pazur(Pazur.__goo(x, y, hebelki_visited), hebelki_szpice, hebelki_szpice2, mulist, pazur_dict, hashes))
        for x in pazurs:
            x.set_ancestor(pazur_dict)
        for x in pazurs:
            x.set_best_ancestor(False)
            x.set_best_ancestor(True)
            print((x.best_nex, x.best_bef))

        with open("/home/dell/lluck.pickle", 'wb') as f:
            pickle.dump(hashes, f)
        return pazurs

class MultiPazur:

    @staticmethod
    def get_next(tup):
        pazur, direction = tup
        if direction == -1:
            return pazur.best_bef
        return pazur.bef_nex

    def create_multi_pazur(self, pazur_start):
        visited = set()
        visited.add(pazur_start)
        #TODO CYCLE
        start = pazur_start.best_nex
        while MultiPazur.get_next(start) is not None:
            start = MultiPazur.get_next(start)
        start_pazur, direction = None
        if direction == -1:
            start = start_pazur.best_nex
        else:
            start = start_pazur.best_bef
        ret = [(start_pazur, None), start]
        while MultiPazur.get_next(start) is not None:
            start = MultiPazur.get_next(start)
            ret.append(start)
        return ret