__author__ = 'avneeshsarwate1'

import copy
import random

def gridShift(g, direction):
    grid = copy.deepcopy(g)

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

def rotateGridLeft(grid):
    newGrid = [[0 for i in range(16)] for j in range(16)]
    for i in range(16):
        for j in range(16):
            newGrid[15-j][i] = grid[i][j]
    return newGrid

## helper function for game of life that counts the number of neighbors (with wraparound) of a cell
def neighborCount(grid, i, j):
    count = 0
    for m in [-1, 0, 1]:
        for k in [-1, 0, 1]:
            if abs(m) + abs(k) == 0:
                continue
            if grid[(i+m)%len(grid)][(j+k)%len(grid)] != 0:
                count += 1
    return count

## transformation helper function that transforms a grid to its next step according to conways game of life
def gameOfLife(oldG):
    newG = [[0 for i in range(len(oldG))] for j in range(len(oldG))]
    for i in range(len(oldG)):
        for j in range(len(oldG)):
            c = neighborCount(oldG, i, j)
            if c < 2 or c > 3:
                newG[i][j] = 0
            if c in [2, 3]:
                newG[i][j] = oldG[i][j]
            if c == 3:
                newG[i][j] = 1
    return newG

def blend(grid1, grid2, direction, amount):
    blendGrid = [[0 for i in range(len(grid1))] for j in range (len(grid1))]
    allslots = range(len(grid1))
    set1 = []
    for i in range(amount):
        k = random.choice(allslots)
        allslots.remove(k)
        set1.append(k)
    if direction == "hor":  #blending columns
        for i in range(len(grid1)):
            if i in set1:
                blendGrid[i] = copy.copy(grid1[i])
            else:
                blendGrid[i] = copy.copy(grid2[i])
    if direction == "vert":
        for i in range(len(grid1)):
            if i in set1:
                for j in range(len(grid1)):
                    blendGrid[j][i] = grid1[j][i]
            else:
                for j in range(len(grid1)):
                    blendGrid[j][i] = grid2[j][i]

def smartNoise(grid, noise):
    newgrid = [[0 for i in range(16)] for j in range (16)]
    vert = [i for i in range(1, 6)] + [i for i in range(-5, 0)]
    hor = [i for i in range(1, 4)] + [i for i in range(-3, 0)]

    for i in range(len(grid)):
        for j in range(len(grid)):
            if grid[i][j] != 0:
                if random.uniform(0, 1) < (1.0 * noise) / 10: #if any change happens
                    v = random.choice(vert)
                    h = random.choice(hor)
                    if random.uniform(0, 1) < .2: #probability of add/remove
                        if random.uniform(0, 1) < .5:
                            newgrid[i][j] = 0
                        else:
                            newgrid[(i+h)%len(grid)][(j+v)%len(grid)] = 1
                    else:
                        newgrid[i][(j+v)%len(grid)] = 1
                else:
                    newgrid[i][j] = 1
    return newgrid

def rhythmBreak(grid, noise):
    newgrid = copy.deepcopy(grid)
    cols = range(16)
    if random.uniform(0, 1) < .5:
        numDrop = 2*(noise-1) + 1
    else:
        numDrop = 2*(noise-1) + 2
    colDrop = random.sample(cols, numDrop)
    print colDrop
    for i in colDrop:
        print i
        newgrid[i] = [0 for j in range(16)]
    print newgrid
    return newgrid

## transformation helper function that adds harmonies to the grid
def chordify(grid, noise):
    def smartNoiseMod(grid, noise):
        newgrid = [[0 for i in range(16)] for j in range (16)]
        vertRad = noise/2 + 1
        vert = [i for i in range(1, 1+vertRad)] + [i for i in range(-(1+vertRad), 0)]

        for i in range(len(grid)):
            for j in range(len(grid)):
                if grid[i][j] != 0:
                    if random.uniform(0, 1) < (1.0 * noise) / 20: #if any change happens
                        v = random.choice(vert)
                        if random.uniform(0, 1) < .2: #probability of add/remove
                            if random.uniform(0, 1) < .5:
                                newgrid[i][j] = 0
                            else:
                                newgrid[i%len(grid)][(j+v)%len(grid)] = 1
                        else:
                            newgrid[i][(j+v)%len(grid)] = 1
                    else:
                        newgrid[i][j] = 1
        return newgrid

    newgrid = copy.deepcopy(grid)
    offsetRange= range(1, 1+noise) + range(-noise, 0)
    offsets = random.sample(offsetRange, 2)

    gridz = [copy.deepcopy(newgrid), copy.deepcopy(newgrid)]
    for i in range(2):
        if offsets[i] > 0: direction = "up"
        else: direction = "down"
        for j in range(abs(offsets[i])):
            gridz[i] = gridShift(gridz[i], direction)
        gridz[i] = smartNoiseMod(gridz[i], noise)

    for g in gridz:
        for i in range(16):
            for j in range(16):
                if g[i][j] != 0:
                    newgrid[i][j] = 1.0

    return newgrid


def simplify(grid, voices):
    sets = [[] for i in range(len(grid))]
    newG = [[0 for i in range(16)] for j in range (16)]
    for i in range(len(grid)):
        for j in range(len(grid)):
            if grid[i][j] != 0:
                sets[i].append(j)
    for i in range(len(sets)):
        for j in range(voices):
            if len(sets[i]) == 0: break
            k = random.choice(sets[i])
            newG[i][k] = 1
            sets[i].remove(k)
    return newG


def columnOverlay(baseGrid, overlayGrid, columnSet):
    g = [[0 for i in range(16)] for j in range(16)]
    for i in range(16):
        if i in columnSet:
            g[i] = copy.deepcopy(overlayGrid[i])
        else:
            g[i] = copy.deepcopy(baseGrid[i])
    return g

def naiveNoise(grid, lev):
    l = len(grid)
    p = 1.0 * lev / (l*l)
    newG = [[0 for i in range(l)] for k in range(l)]
    for i in range(l):
        for j in range(l):
            if random.uniform(0, 1) < p:
                if grid[i][j] != 0:
                    newG[i][j] = 0
                else:
                    newG[i][j] = 1
            else:
                newG[i][j] = grid[i][j]
    return newG


def gridDiff(newGrid, oldGrid):
    diff =  [[0 for i in range(16)] for j in range(16)]
    for i in range(len(newGrid)):
        for j in range(len(newGrid)):
            diff[i][j] = newGrid[i][j] - oldGrid[i][j]
    return diff

def bit(i):
    return 1 if i >= 1 else 0

def quadShift(oldGrid, newGrid, targetGrid):
    shifts = [0] * 4
    g =  [[0 for i in range(16)] for j in range(16)]
    for i1 in range(4):
        oldYsum = 0
        newYsum = 0
        oldYcount = 0
        newYcount = 0
        for i2 in range(4):
            for j in range(16):
                oldYcount += oldGrid[4*i1+i2][j]
                newYcount += newGrid[4*i1+i2][j]
                if oldGrid[4*i1+i2][j] == 1 : oldYsum += j
                if newGrid[4*i1+i2][j] == 1 : newYsum += j
        print "oldYsum", oldYsum, "newYsum", newYsum, "oldYcount", oldYcount, "newYcount", newYcount
        shifts[i1] = int(1.0*newYsum/newYcount - 1.0*oldYsum/oldYcount)

        if shifts[i1] == 0 : continue
        if shifts[i1] > 0:
            oldCopy = copy.deepcopy(oldGrid)
            for i in range(shifts[i1]):
                oldCopy = gridShift(oldCopy, "up")
            g = columnOverlay(g, oldCopy, range(4*i1, 4*i1+4))
        if shifts[i1] < 0:
            oldCopy = copy.deepcopy(oldGrid)
            for i in range(abs(shifts[i1])):
                oldCopy = gridShift(oldCopy, "down")
            g = columnOverlay(g, oldCopy, range(4*i1, 4*i1+4))
    return g

def percentDiff(oldGrid, newGrid, targetGrid):
    percent = .5

    diff = gridDiff(newGrid, oldGrid)

    diffList = [(i, j, diff[i][j]) for i in range(16) for j in range(16)]

    random.shuffle(diffList)

    randDiff = diffList[0:int(percent*len(diffList))]

    for d in randDiff:
        targetGrid[d[0]][d[1]] = bit((targetGrid[d[0]][d[1]] + d[2]))


def correlatedDensity(oldGrid, newGrid, targetGrid):

    diff = gridDiff(newGrid, oldGrid)

    netDiff = sum([sum(i) for i in diff])





class ResponseFunctionManager:

    def __init__(self, responseFunc):
        self.functionMap = {}
        self.triggerMap = {}

    ##holds a dict of [key, set((oldGrid, newGrid, targetGrid, responseFunc))]
    def add(self, key, responseFunc, oldGrid, newGrid, targetGrid):
        if key in self.functionMap.keys():
            self.functionMap[key].add((responseFunc, oldGrid, newGrid, targetGrid))
        else:
            self.functionMap[key] = {(responseFunc, oldGrid, newGrid, targetGrid)}

    ## calls responseFunc(newGrid, oldGrid, targetGrid) for all tuples specified by the key
    def call(self, key):
        if key in self.functionMap.keys():
            for tup in self.functionMap[key]:
                tup[0](tup[1], tup[2], tup[3])

    ##stateHolderObj holds some state
    # triggerEvaluatorFunc takes stateHolderObj (and optionally other things) as arguments,
    #   updates the stateHolderObj based on the args and returns true or false
    # pingTrigger(key) calls triggerEvaluatorFunc(stateHolderObj, *args) and if it returns true,
    #   calls responseFunc(newGrid, oldGrid, targetGrid) for all tuples specified by the key
    #
    #   If true is returned the the response function is called on the registered grids
    def setTrigger(self, key, stateHolderObj, triggerEvaluatorFunc, responseFunc, oldGrid, newGrid, targetGrid):
        if key in self.triggerMap.keys():
            self.triggerMap[key].add(
                {
                    "obj": stateHolderObj,
                    "evalFunc": triggerEvaluatorFunc,
                    "responseFunc": (responseFunc, oldGrid, newGrid, targetGrid)
                }
            )
        else:
            self.triggerMap[key] = {{
                                        "obj": stateHolderObj,
                                        "evalFunc": triggerEvaluatorFunc,
                                        "responseFunc": (responseFunc, oldGrid, newGrid, targetGrid)
                                    }}

    def pingTrigger(self, key, *args):
        if key in self.triggerMap.keys():
            for trigger in self.triggerMap[key]:
                if trigger["evalFunc"](trigger["obj"], *args):
                    func = trigger["responseFunc"]
                    func[0](func[1], func[2], func[3])














