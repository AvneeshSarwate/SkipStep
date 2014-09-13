

/*
set n - number of instruments
create n tempo clocks (and associated beat variables?)
create n old/new time variables for touch tempo
create n OSCFunc objects for touch tempo



*/

SystemClock.beats
(
var cf, midiOut, tempClock;

MIDIClient.init;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");

cf = {|msg, time, addr, recvPort|
	if (msg[2] == 'normal',
		{
			msg.postln;
			msg[3..].do({|i| midiOut.noteOn(msg[1], i)});
			/*hit noteOn messages*/
			/*schedule clock to hit noteOff messages with annoymous function*/
		},
		{
			msg[2].class.postln;
			if (msg[2] == "on",
				{msg[3..].do({|i| midiOut.noteOn(msg[1], i)}); /*noteon messages*/},
				{msg[3..].do({|i| midiOut.noteOff(msg[1], i)}); /*noteoff messages*/},
		)},
	)
};

OSCFunc(cf, "/playChord");

OSCFunc.trace(true);
)



MIDIClient.init;
MIDIClient.destinations.postln
(
var mid;
MIDIClient.init;
mid = MIDIOut.newByName("IAC Driver", "Bus 1");
mid.postln;
mid.noteOff(0);
)

a = [1, 2, 5, 3, 4, 5];
a[2..].do({|i| i.postln});


