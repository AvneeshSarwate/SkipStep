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
drumTypes.put("aud", 108);

//TODO: BUILD MAP FROM TIDAL SYNTH PARAMS TO MIDI-CC PARAMS

midiSend =  {|msg, time, addr, recvPort, chanInd|
	var drumInd, drumType, drumStr;

	drumStr = msg[1].asString;
	drumInd = drumStr.split($:)[1];
	drumInd = if(drumInd.isNil, 0, {drumInd.asInteger});
	drumType = drumTypes[drumStr.split($:)[0]].asInteger;

	msg.postln;

	(2..(msg.size - 1)).do({|i|
		if(msg[i] > -1, {midiOut.control(chanInd-1, i-2, (msg[i]*127).round)});
	});

	//send cc map stuff if applicable
	Task({
		midiOut.noteOn(chanInd-1, drumType+drumInd); //maybe add velocity based on gain?
		0.001.wait;
		midiOut.noteOff(chanInd-1, drumType+drumInd);
	}).play;
};

(1..4).do({|i|
	OSCFunc(midiSend.value(_, _, _, _, i), "play-"++i.asString);
});

)


(
//FUNCTION TO "TWIDDLE KNOB" FOR A MIDI-CC
var twiddle = {|chan, ccNum|
	var midiOut;

	MIDIClient.init;
	midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
	midiOut.latency = 0;

	Task({
		midiOut.control(chan, ccNum, 0);
		0.01.wait;
		midiOut.control(chan, ccNum, 127);
	}).play;
};
twiddle.value(0, 0);
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
//OLD FUNC
(

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
	//ind = ind+1;
	//ind.postln;
	//if(ind%100 == 50, {"aaaaaay".postln});

};

OSCFunc(midiSend, "/play");
)

//------------------------------------------------------------------------
//IGNORE: scratch code

(
var fu, bu;
fu = {|ar, br, cr|
	[ar, br, cr].postln;
};
fu.value(1, 2, 3);
bu = fu.value(1,2, _);
bu.value(5);
)

"ab" ++ 5.asString

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
var j, func;
j = List();
func = {i*2};
(1..5).do({|i| j.add(func)});
j[2].value();
)
[1, 2, 4].size

(0.5*127).round

"a:b".split($l)[1]

if("sn".split($:)[1] == nil, 0, 1)
if("a:b".split($l)[1] == nil, 1, 3)
