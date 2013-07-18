'''
Created on Mar 24, 2013

@author: avneeshsarwate
'''
from music21 import *
import phrase
import Levenshtein as lv
import string


#midfile.measures(1,4).parts[0].show('text')
#for i in midfile.measure(4):
#    if i.isNote:
#        print i.midi
#    if i.isRest:
#        print 0
#for i in midfile.parts[0].notesAndRests:
#    if(i.isNote):    
#        print i.midi
#    else:
#        print 0
#    print i.duration.quarterLength
#
#print midfile.parts[0][0].ratioString

#timesignature.ratioString
#note.midi
#print dir(midfile)
#midfile.write("lily.png", "/Users/avneeshsarwate/Desktop/abletonStuff/1mid.png")

def scoreToPhrase(score):
    p = phrase.Phrase()
    for i in score.parts[0].notesAndRests:
        if(i.isNote):    
            n = i.midi
        else:
            n = -1
        t = i.duration.quarterLength
        p.append((n, t))
    p.timesig = score.parts[0][0].ratioString
    return p 

def phraseToScore(phr):
    sc = stream.Score()
    p = stream.Part()
    ratioString = bestSig(phr)
    ts = meter.TimeSignature(ratioString)
    sc.append(p)
    p.append(ts)
    for i in range(len(phr.n)):
        n = note.Note()
        if phr.n[i] < 0:
            n = note.Rest()
        else:
            n.midi = phr.n[i]
        n.duration.quarterLength = phr.t[i]
        p.append(n)
    return sc

def measureToPhrase(mes):
    p = phrase.Phrase()
    for i in mes.notesAndRests:
        if(i.isNote):    
            n = i.midi
        else:
            n = -1
        t = i.duration.quarterLength
        p.append((n, t))
    return p


#for i in midfile[0]:
#    print i
#print midfile[0][0].ratioString
#print midfile[0][0].ratioString
#print "lets get dat png"
#print type(midfile.parts[0]), len(midfile.parts[0].notesAndRests)
#print type(midfile.measures(1,4)), len(midfile.measures(1,4).parts[0].notesAndRests)
#for i in midfile.measures(0,100).parts[0]:
#    print type(i)
#    print len(i.notesAndRests)
#    print measureToPhrase(i)
#print midfile.measures(1,4).hasPartLikeStreams()



def conjMel(phr):
    ns = []
    for i in phr.n:
        if i > 0:
            ns.append(i)
    total = 0
    for i in range(len(ns)-1):
        total += abs(ns[i] - ns[i+1])
    return 1.0 * total / (len(ns)-1)

def conjRyth(phr):
    rs = []
    for i in range(len(phr.t)):
        if phr.n[i] == -1:
            continue
        rs.append(phr.t[i])
        if i < len(phr.t)-1 and phr.n[i+1] == -1:
            t = rs.pop()
            rs.append(phr.t[i+1] + t)
    prod = 1
    for i in range(len(rs)-1):
        prod *= max(rs[i]/rs[i+1], rs[i+1]/rs[i])
    return prod**(1.0/(len(rs)-1))

def macroMel(phr):
    
    key = phrase.key(lv.bestkey(phr))
    ns = []
    ts = []
    for i in range(len(phr)):
        if phr.n[i] < 0:
            continue
        ns.append(phr.n[i])
        ts.append(phr.t[i])
        if i < len(phr.t)-1 and phr.n[i+1] == -1:
            t = ts.pop()
            ts.append(t + phr.t[i+1])
    inkey = 0
    ttot = 0
    for i in range(len(ns)):
        if ns[i] in key:
            inkey += ts[i]
        ttot += ts[i]
    ratio = 1.0 * inkey/ttot
    
    tpair = {}

    for i in range(len(ns)):
        if ns[i] not in tpair:
            tpair[ns[i]] = ts[i]
        else:
             tpair[ns[i]] += ts[i]
    
    ctot = 0
    for i in tpair.values():
        ctot += i
    cavg = 1.0 * ctot / len(tpair)
    
    varn = 0
    for i in tpair.values():
        varn += (i-cavg)**2
    if varn == 0:
        return 2 * ratio / (1.0 / len(phr))
    return ratio / varn

def macroRyth(midfile):
    ps = []
    levs = []
    for i in midfile.measures(0, 1000).parts[0]:
        ps.append(measureToPhrase(i))
    for i in range(len(ps)):
        for j in range(i+1,len(ps)):
            levs.append(lv.levd(ps[i].n, ps[j].n) + lv.levd(ps[i].t, ps[j].t))
#    print
#    print levs
#    print
    j = 0
    for i in levs:
        j += i
    
    return 1.0 * j / len(levs)
    

def centMel(phr):
    
    keystr = lv.bestkey(phr)
    root = int(phrase.roots[string.lower(keystr.split(" ")[0])])
    keyl = phrase.key(keystr)
    ind = keyl.index(root)
    top3 = [keyl[ind]%12, keyl[ind+4]%12, keyl[ind+2]]
    
    ns = []
    ts = []
    for i in range(len(phr)):
        if phr.n[i] < 0:
            continue
        ns.append(phr.n[i])
        ts.append(phr.t[i])
        if i < len(phr.t)-1 and phr.n[i+1] == -1:
            t = ts.pop()
            ts.append(t + phr.t[i+1])
    
    inbest = 0
    ttot = 0
    for i in range(len(ns)):
        if ns[i] in top3:
            inbest += ts[i]
        ttot += ts[i]
    
    return inbest/ttot

sigs = [4*i for i in [.5, .75, 1, .625, .875]]
strings = ["2/4", "3/4", "4/4", "5/8", "7/8"]
sigHits = {"4/4":[1, 3], "2/4":[1], "3/4":[1], "5/8":[]}

def centRyth(phr):
    
    bsigS = bestSig(phr)
    step = float(bsigS.split("/")[1])
    numer = float(bsigS.split("/")[0])
    
    def approx(a, b):
        return a > b - .001 and a < b + .001
    
    tsum = 0
    centhits = 0
    for i in range(len(phr.t)):
        tsum += phr.t[i]
        if approx(tsum%step, 0):
            centhits += 1
    return 1.0 * centhits / (tsum / step)

def bestSig(phr):
    
    
    minover = 100
    minsig = -1
    for i in range(len(sigs)):
        prev = 0
        now = 0
        measurecount = 0
        overcount = 0
        for k in phr.t:
            prev = now
            now += k
            if measurecount * sigs[i] > prev and measurecount * sigs[i] < now:
                overcount += 1
            if measurecount * sigs[i] < now:
                measurecount += 1
        if overcount < minover:
            minsig = i
            minover = overcount
    return strings[minsig]
                
        

def vect(arg):
    if type(arg) == type(""):
        midfile = converter.parse(arg)
    if type(arg) == type(stream.Score()) or type(arg) == type(stream.Stream()):
        midfile = arg
    p = scoreToPhrase(midfile)
#    print
#    print
#    print p, "vector"
#    print 
#    print
    v = []
    v.append(conjMel(p))
    #print "post conjmel"
    v.append(macroMel(p))
    #print "post macromel"
    v.append(centMel(p))
    #print "post centmel"
    v.append(conjRyth(p))
    #print "post conjrhy"
    v.append(macroRyth(midfile))
    v.append(centRyth(p))
    #centRyth
    return v

midfile = converter.parse("/Users/avneeshsarwate/Desktop/abletonStuff/mid2.mid")
g = scoreToPhrase(midfile)
print g
phraseToScore(g).show("text")
print vect("/Users/avneeshsarwate/Desktop/abletonStuff/mid2.mid")

