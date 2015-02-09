(
OSCFunc.trace
)
//Main code block
(
var drumTypes, midiSend, midiOut, drumChan, twiddle, maxDrums, ind;

MIDIClient.init;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

drumChan = 0;

//do we need something so you can't "overflow" the index of a drum
// and accidentally play another (ex bd:11 -> lt:0 unintentionally)
maxDrums = 10;

drumTypes = Dictionary();
drumTypes.put("bd", 30);
drumTypes.put("lt", 40);
drumTypes.put("ht", 50);
drumTypes.put("sn", 60);
drumTypes.put("ho", 70);
drumTypes.put("hc", 75);
drumTypes.put("cr", 80);
drumTypes.put("rd", 85);
drumTypes.put("bot", 90);
drumTypes.put("cp", 100);
drumTypes.put("bin", 102);
drumTypes.put("bend", 104);

//TODO: BUILD MAP FROM TIDAL SYNTH PARAMS TO MIDI-CC PARAMS
//TODO: BUILD WAY TO MANUALLY MAP MIDI-CC PARAMS FROM CODE TO ABLETON

ind = 0;

midiSend =  {|msg, time, addr, recvPort|
	var drumInd, drumType, drumStr;

	drumStr = msg[1].asString;
	drumInd = drumStr.split($:)[1];
	drumInd = if(drumInd.isNil, 0, {drumInd.asInteger});
	drumType = drumTypes[drumStr.split($:)[0]].asInteger;

	msg.postln;

	//send cc map stuff if applicable
	Task({
		midiOut.noteOn(drumChan, drumType+drumInd); //maybe add velocity based on gain?
		0.001.wait;
		midiOut.noteOff(drumChan, drumType+drumInd);
	}).play;
	ind = ind+1;
	ind.postln;
	if(ind%100 == 50, {"aaaaaay".postln});


};

OSCFunc(midiSend, "/play");

)
//------------------------------------------------------------------------
//minimal example to test where the quantization was coming from
(
var midiSend, midiOut;
	MIDIClient.init;
	midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
	midiOut.latency = 0;
midiSend =  {|msg, time, addr, recvPort|
	midiOut.noteOff(3, 30);
};

OSCFunc(midiSend, "/play");
)


//------------------------------------------------------------------------
//IGNORE: scratch code
(
var midiOut;
MIDIClient.init;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;
Task({
	(true).while({
		midiOut.noteOn(3, 30);
		0.01.wait;
		midiOut.noteOn(3, 30);
	})
}).play;
)

(
//FUNCTION TO "TWIDDLE KNOB" FOR A MIDI-CC
twiddle = {|chan, ccNum|

	MIDIClient.init;
	midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
	midiOut.latency = 0;

	Task({
		midiOut.control(chan, ccNum, 0);
		0.01.wait;
		midiOut.control(chan, ccNum, 128);
	}).play;
};
twiddle.value(0, 1);
)

"a:b".split($l)[1]

if("sn".split($:)[1] == nil, 0, 1)
if("a:b".split($l)[1] == nil, 1, 3)
