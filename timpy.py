'''
Created on Aug 26, 2013

@author: avneeshsarwate
'''

def testfun(*args, **kwargs):
    print args[0]
    if(kwargs["toggle"] == ""):
        print "nothing hurr"
    else:
        print kwargs["toggle"]

testfun("", toggle="malaka")
