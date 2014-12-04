'''
Created on Jun 9, 2013

@author: avneeshsarwate
'''
import copy
import random
import phrase
import socket
#import Levenshtein as lv
#import Looper
#
#t  = [1, 1, 1, .5, .5, 1, 1, 1, .5, .5 ]
#n = [60, 58, 60, 65, 63, 60, 58, 60, 65, 63]
#
##p = phrase.Phrase(n, t)
#
##phrase.play(p)
##loop = Looper(p)
#
#def scaleNotes(root, scale):
#    notes = [0]*16
#    for i in range(16):
#        notes[i] = root + (i/len(scale))*12 + scale[i%len(scale)] 
#        print i, (i/len(scale))*12, i%len(scale)
#    return notes
#
#callbacks = [[0 for i in range(16)] for j in range (16)]
#g = [[0 for i in range(16)] for j in range (16)]
#
#def assign(a, b, c, d):
#    a[b][c] = d[0]
#    
#def gridToProg(grid, root, scale):
#    notes = scaleNotes(root, scale)
#    prog = phrase.Progression()
#    for i in range(len(grid)):
#        if sum(grid[i]) == 0:
#            print "zero"
#            prog.append((phrase.Chord([-1]), .25))
#            continue
#        else: 
#            c = phrase.Chord()
#            for j in range(len(grid[i])):
#                if grid[i][j] != 0:
#                    c.append(notes[j])
#            prog.append((c, .25))
#    return prog
#            
#def colToChord(col, root, scale):
#    notes = scaleNotes(root, scale)
#    if sum(col[i]) == 0:
#        print "zero"
#        return phrase.Chord([-1])
#        
#    else: 
#        c = phrase.Chord()
#        for j in range(len(col)):
#            if col[j] != 0:
#                c.append(notes[j])
#        return c

def gridShift(grid, direction):
        #grid = [[0 for i in range(16)] for j in range (16)]
        #grid = g
        
        if direction == "up":
            print "up"
            for i in range(len(grid)):
                grid[i].insert(0, grid[i].pop())            
                    
        if direction == "down":
            for i in range(len(grid)):
                grid[i] = grid[i][1:len(grid[i])] + [grid[i][0]]
                    
        if direction == "right":
            grid.insert(0, grid.pop())
        
        if direction == "left": 
            grid = grid[1:len(grid)] + [grid[0]]
        
        return grid
    
def gridKeyToString(grid, key):
    sgrid = [[str(grid[i][j]) for i in range(len(grid))] for j in range(len(grid))]
    print sgrid
    
def neighborCount(grid, i, j):
    count = 0
    looper = 0
    for m in [-1, 0, 1]:
        for k in [-1, 0, 1]:
            looper+=1 
            if abs(m) + abs(k) == 0:
                continue
            #print (i+m)%len(grid), (j+k)%len(grid), grid[(i+m)%len(grid)][(j+k)%len(grid)] != 0
            if grid[(i+m)%len(grid)][(j+k)%len(grid)] != 0:
                count += 1
    return count     
      
def gameOfLife(oldG):
    newG = [[0 for i in range(len(oldG))] for j in range(len(oldG))]
    for i in range(len(oldG)):
        for j in range(len(oldG)):
            c = neighborCount(oldG, i, j)
            print i, j, c
            if c < 2 or c > 3:
                newG[i][j] = 0
            if c in [2, 3]:
                newG[i][j] = oldG[i][j]
            if c == 3:
                newG[i][j] = 1
    return newG

def blend(grid1, grid2, direction, amount):
    blend = [[0 for i in range(len(grid1))] for j in range (len(grid1))]
    allslots = range(len(grid1))
    set1 = []
    for i in range(amount):
        k = random.choice(allslots)
        allslots.remove(k)
        set1.append(k)
    print set1
    if direction == "hor":  #blending columns  
        for i in range(len(grid1)):
            if i in set1:
                blend[i] = copy.deepcopy(grid1[i])
            else:
                blend[i] = copy.deepcopy(grid2[i])
    if direction == "vert":
        for i in range(len(grid1)):
            if i in set1:
                for j in range(len(grid1)):
                    blend[j][i] = grid1[j][i]
            else:
                for j in range(len(grid1)):
                    blend[j][i] = grid2[j][i]
    return blend


grid1 = [[1 for i in range(5)] for j in range(5)]
grid0 = [[0 for i in range(5)] for j in range(5)]
#print blend(grid1, grid0, "vert", 2)




def argTest(*args, **kwargs):
    if "list" in kwargs.keys(): args = args[0]
    print args

#argTest([1, 2, 3], "wat", "huh", list="wat")


c = phrase.Chord([60])
d = phrase.Chord([67])
e = phrase.Chord([74])
#phrase.play(c, d, e, channel=[2, 1, 0])



j = lambda arg1: arg1+5

def print2(a):
    print a

def func(f, a):
    f(a)

func(lambda a: print2(a), 5)
    

#n = ["1", "2", "3", "4", "5"]
#c = ["a", "b", "c", "d", "e"]
#
#k = [[i+j for i in n] for j in c]
#
#print k 
#print 
#print 
#print gridShift(k, "left")
























