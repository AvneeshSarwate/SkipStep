(
var midiOut, noteToInd, noteToXY, isPadNote, padOn, padOff, octaveShift, padIndToNote, rootMove, scale, root;

MIDIIn.connectAll;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

noteToInd = {|x| x - 36}; //convert note to pad index
noteToXY = {|x| [noteToInd.(x)%4, floor(noteToInd.(x)/4)]}; //convert note to pad xy (bottom left 0,0)
isPadNote = {|x| (noteToInd.(x) >=0) && (noteToInd.(x) < 16)};

//give names to midiNotes of up/down/left/right controls from Quneo

/*
padIndToNote - mapping from padIndex to midi note
scale - scale defined by degrees/distances
root - root of scale

*/

//construct initial pad-note mapping

a = {|vel, note, chan, port|
	if(isPadNote.value(note), {
		//noteOn
		//if highest note shift up
		//if lowest note shift down

	});
};
padOn = MIDIFunc.noteOn(a, nil, nil, 2017846184);


b = {|vel, note, chan, port|
	if(isPadNote.value(note), {
		//noteOff
		//if highest note shift up
		//if lowest note shift down

	});
};
padOff = MIDIFunc.noteOff(a, nil, nil, 2017846184);

//shifts pad-note mapping up or down an octave
//args: direction is +-1 indicating octave shift
octaveShift = {|direction|
};

//changes the pad-note mapping s.t the roots move up/down/left/right
//args: direction is midiNote for up/down/left/right controls from Quneo
rootMove = {|direction|
};

)


//-----  SCRATCH CODE ------------------------------------------------------------------------------------------------

(
MIDIClient.init;
MIDIClient.sources[1].uid;
)