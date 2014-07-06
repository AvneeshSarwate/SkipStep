import subprocess
import threading

def chuckthread():
    subprocess.call("chuck LooperBackendMulti.ck", shell=True)
    

t = threading.Thread(target=chuckthread)
t.start()

print "post chuck launch"



try :
            #print "starting loop"
    while 1 :
        continue

except KeyboardInterrupt :
            #print "\nClosing oscServSelf."
    t.join()
