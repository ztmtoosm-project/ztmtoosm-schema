from libmrc2 import part_mn, HebelkiDfs, hebelek_in_zakres, PackAllMy, srumpy, manage_vals
from svgpathtools import Path, Line, QuadraticBezier, CubicBezier, Arc, wsvg

import shapely.geometry
import shapely.affinity
import shapely.wkb as wkb
hebelki_all = part_mn()
dfs_costam = HebelkiDfs(hebelki_all)
'''
conn = psycopg2.connect(dbname="nexty", user="marcin")

cur = conn.cursor()
x = input('What is your name?')
x = '%'+x+'%'
print(x)
cur.execute('SELECT * FROM OPERATOR_STOPS WHERE NAME LIKE %s', [x]);
abc = cur.fetchall()
for x in abc:
    print('Id: {0} o nazwie {1}'.format(x[0], x[1]))
x = input('give me id')
cur.execute("SELECT x, y FROM OSM_PATHS, nicepaths_node_coordinates_normalized niz WHERE ref_begin=%s AND node_id=id AND ORDINAL_ID=1;"
, [x]);
abc = cur.fetchall()
xxx = 0
yyy = 0
for x in abc:
    xxx = x[0]
    yyy = x[1]

print(xxx)
print(yyy)
'''

paths = []
stroke_widths = []

colors = ""
srodes = []
radii = []
for a in hebelki_all:
    if hebelek_in_zakres(a, 30000, 30000, 2000):
        current_color = "k"
        colors = colors + "c"
        stroke_widths.append(1)
        paths.append(Line(srumpy(a.linestring.coords[0]), srumpy(a.linestring.coords[1])))
        if a not in dfs_costam.hebelki_longline:
            if a not in dfs_costam.artic:
                srodes.append(srumpy(a.get_average_point().coords[0]))
                radii.append(5)
        if a in dfs_costam.hebelki_map:
            vals = dfs_costam.hebelki_map[a]
            current_color = manage_vals(vals, a)
        current_color1 = current_color
        for b in a.nast:
            current_color = current_color1
            if b in dfs_costam.hebelki_map:
                vals = dfs_costam.hebelki_map[b]
                current_color = manage_vals(vals, a)
            lenx = shapely.geometry.LineString([a.get_average_point().coords[0], b.get_average_point().coords[0]]).length
            paths.append(Line(srumpy(a.get_average_point().coords[0]), srumpy(b.get_average_point().coords[0])))
            if lenx > 70:
                stroke_widths.append(3.5)
            else:
                stroke_widths.append(1)
            colors = colors + current_color
print(len(paths))
wsvg(paths, colors=colors, nodes=srodes, node_radii=radii, filename='output1.svg', stroke_widths=stroke_widths)
