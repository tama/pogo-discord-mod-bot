from collections import OrderedDict
import random

def get_prb_for(index, lines):
    d = OrderedDict()
    acc = 0
    for line in lines:
        parts = line.split(";")
        d[parts[0]] = acc + int(parts[index])
        acc += int(parts[index])
    return d

def roulette(username, prbFile="probas.csv"):
    lines = [line.strip() for line in open(prbFile, "r", encoding="utf-8")]
    plist = lines[0].split(';')
    if username not in plist:
        return None
    index = plist.index(username)
    prb = get_prb_for(index, lines[1:])
    r = random.randint(1, 100)
    victim = None
    for k in prb.keys():
        if r > prb[k]:
            continue
        victim = k
        break
    #print("{0} {1} {2}".format(r, prb[victim], victim))
    if victim == "0":
        return None
    return victim

if __name__ == "__main__":
    d = {}
    for i in range(10000):
        v = roulette("Killerlolo")
        if v not in d:
            d[v] = 0
        d[v] = d[v] + 1
    print(d)
