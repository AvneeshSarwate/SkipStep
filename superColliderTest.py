import OSC
import phrase

client = OSC.OSCClient()
client.connect(("127.0.0.1", 57120))


msg = OSC.OSCMessage()
msg.setAddress("/testMessage")
msg.append([5, [6,7]])
client.send(msg)


#sends channel, piano status (non, on, off), and list of notes
def playChord(chord, channel = 0, piano = "normal"):
	msg = OSC.OSCMessage()
	msg.setAddress("/playChord")
	msg.append(channel)
	msg.append(piano)
	for i in chord.n:
		msg.append(i)
	client.send(msg)


c = phrase.Chord([60, 63, 67])

playChord(c)



