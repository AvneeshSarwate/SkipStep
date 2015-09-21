import phrase as phr

class Class1:

	def __init__(self):
		self.instVar1 = 5
		self.instVar2 = []

	def printList(self, x):
		for i in self.instVar2:
			print i
		print "\n Class2 list printed \n"



class Class2:

	def __init__(self):
		self.instVar1 = 5
		self.selfList = []

	def printList(self):
		for i in self.selfList:
			print i
		print "\n Class2 list printed \n" 



j1 = Class1()
j1.instVar2.append(5)
j1.instVar2.append(6)

j2 = Class2()
j2.selfList = [1, 2, 3, 4, 5]

j2.list2 = [5, 6, 7]

def printFunc(someClass):
	someClass.printList(4)


# printFunc(j1)
# printFunc(j2)
# print j2.list2

p1 = phr.Phrase([60, 62, 65], [2, 2, 4])
p2 = phr.Phrase([63, 65, 67], [2, 4, 4])

p1[2] = (67, 25)

print p1, print 
print p2

p3 = p1 + p2

print p3

