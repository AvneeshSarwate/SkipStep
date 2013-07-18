'''
Created on Jun 9, 2013

@author: avneeshsarwate
'''
import phrase
import Levenshtein as lv
import Looper

t  = [1, 1, 1, .5, .5, 1, 1, 1, .5, .5 ]
n = [60, 58, 60, 65, 63, 60, 58, 60, 65, 63]

p = phrase.Phrase(n, t)

#phrase.play(p)
#loop = Looper(p)

def scaleNotes(root, scale):
    notes = [0]*16
    for i in range(16):
        notes[i] = root + (i/len(scale))*12 + scale[i%len(scale)] 
        print i, (i/len(scale))*12, i%len(scale)
    return notes

callbacks = [[0 for i in range(16)] for j in range (16)]
g = [[0 for i in range(16)] for j in range (16)]

def assign(a, b, c, d):
    a[b][c] = d[0]
    
def gridToProg(grid, root, scale):
    notes = scaleNotes(root, scale)
    prog = phrase.Progression()
    for i in range(len(grid)):
        if sum(grid[i]) == 0:
            print "zero"
            prog.append((phrase.Chord([-1]), .25))
            continue
        else: 
            c = phrase.Chord()
            for j in range(len(grid[i])):
                if grid[i][j] != 0:
                    c.append(notes[j])
            prog.append((c, .25))
    return prog
            
def colToChord(col, root, scale):
    notes = scaleNotes(root, scale)
    if sum(col[i]) == 0:
        print "zero"
        return phrase.Chord([-1])
        continue
    else: 
        c = phrase.Chord()
        for j in range(len(col)):
            if col[j] != 0:
                c.append(notes[j])
        return c
    

#for i in range(1, 17):
#    for j in range(1, 17):
#        callbacks[i][j] = lambda addr, tags, stuff, source: assign(g, i, j, stuff[0])
#        #set as handler
#        

#scope of lambda functons         
#pr = phrase.Progression()
#c = []
#c.append(phrase.Chord([60, 63, 67]))
#c.append(phrase.Chord([-1]))
#c.append(phrase.Chord([60, 63, 67]))
#c.append(phrase.Chord([-1]))
#c.append(phrase.Chord([60, 63, 67]))
#t = [.5, 2, .5, 2, 5]
#pr.c = c
#pr.t = t
#phrase.play(pr)
print g 
g[0][0] = 1
g[0][2] = 1
g[0][4] = 1
pr = gridToProg(g, 60, phrase.modes["major"])
print g
print pr