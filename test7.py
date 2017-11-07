import pickle
import random
from shapely.geometry import LineString
class Duda(LineString):
    def __eq__(self, other): return self is other
    def __hash__(self): return hash(id(self))
    def __init__(self, alfa, beta):
        super(Duda, self).__init__([[0,0],[alfa,beta]])
        self.alfa = alfa * beta
        self.beta = beta
        self.cuck = set()

    def __setstate__(self, state):
        print("setstate")
        self.alfa, self.beta, self.cuck = state

    def __getstate__(self):
        print("getstate")
        return (self.alfa, self.beta, self.cuck)

    def __reduce__(self):
        print("reduce")
        print(self.__class__)
        return (type(self), super(Duda, self).__reduce__(), self.__getstate__(), )

class Dupa(object):
    def __init__(self, ksi):
        self.cuck = set()
        self.ksi = ksi * 2


tbl = []
tbl2 = []
for i in range(0, 15):
    tbl.append(Duda(random.random(), random.random()))
    print(type(tbl[i]))
    tbl2.append(Dupa(random.random()))

for i in range(0, 111):
    rnd1 = int(random.random()*14.0)
    rnd2 = int(random.random()*14.0)
    tbl[rnd1].cuck.add(tbl2[rnd2])
    tbl2[rnd2].cuck.add(tbl[rnd1])

with open('aaa.pickle', 'wb') as pickle_file:
    pickle.dump((tbl, tbl2), pickle_file)

pkl_file = open('aaa.pickle', 'rb')
t1, t2 = pickle.load(pkl_file)

for x in t1:
    print("#####")
    print(x.alfa)
    print(x.beta)
    print(x.dupa.coords)
    print("//")
    for y in x.cuck:
        print(y.ksi)


