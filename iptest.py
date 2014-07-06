import subprocess

#k = subprocess.check_output(["ifconfig | grep \"inet \" | grep -v 127.0.0.1"], shell=True)
#ip = k.split(" ")[1]
#print k, "\n"+ip

j = raw_input("\nyo:\n")
f = open("iptest.txt", "r+")
print  f.read()
f.close()

f = open("iptest.txt", "w")
f.write(j)
f.close()
f = open("iptest.txt")
print f.read()
print "------"

