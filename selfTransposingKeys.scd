(
var midiOut, noteToInd, noteToXY, isPadNote, padOn, padOff, octaveShift, padIndToNote, rootMove, scale, root, indToNote, padToOnPitch, dUP, dDOWN, dLEFT, dRIGHT, startInd, rootMoveHelper;

MIDIIn.connectAll;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

noteToInd = {|x| x - 36}; //convert note to pad index
noteToXY = {|x| [noteToInd.(x)%4, floor(noteToInd.(x)/4)]}; //convert note to pad xy (bottom left 0,0)
isPadNote = {|x| (noteToInd.(x) >=0) && (noteToInd.(x) < 16)};

//give names to midiNotes of up/down/left/right controls from Quneo
//dUP, dDOWN, dLEFT, dRIGHT


scale = [0, 2, 4, 5, 7, 9, 11];
root = 48;
startInd = -3;

//pad->on-notes mapping to handle case where pad->pitch mapping changes while notes are still on
padToOnPitch = Dictionary.new();

indToNote = {|ind, scale, root|
	root + scale[ind%scale.size()] + ((ind.12).floor * 12);
};

createPadToNoteMap = {|ind|
	var newMap = {}
	(-3..12).do({|i|
		newMap.add(indToNote.(i, scale, root));
	});
};

padIndToNote = createPadToNoteMap.(startInd);

//shifts pad->pitch mapping up or down an octave
//args: direction is +-1 indicating octave shift
octaveShift = {|direction|
	//shift startInd
	startInd = startInd + (direction * scale.size());

	//shift pad->pitch map
	padIndToNote = createPadToNoteMap.(startInd);
};

rootMoveHelper = {|i|
	startInd = startInd + i;
	padIndToNote = createPadToNoteMap.(startInd);
	//do stuff for updating lighted root notes on Quneo
};

//changes the pad->pitch mapping s.t the roots move up/down/left/right
//args: direction is midiNote for up/down/left/right controls from Quneo
rootMove = {|direction|
	switch (direction,
		dUP, {rootMoveHelper.(4)},
		dDOWN, {rootMoveHelper.(-4)},
		dLEFT, {rootMoveHelper.(1)},
		dRIGHT, {rootMoveHelper.(-1)}
	);
};

a = {|vel, note, chan, port|
	if(isPadNote.(note), {
		//noteOn
		var padNote = padIndToNote[padToInd.(note)];
		midiOut.noteOn(0, padNote, vel);
		padToOnPitch.put(padToInd.(note), padNote);
	});

	//otherwise call rootMove based on which direction pad was hit

};
padOn = MIDIFunc.noteOn(a, nil, nil, 2017846184);


b = {|vel, note, chan, port|
	if(isPadNote.(note), {
		//noteOff
		var padNote = padToOnNote.get(padToInd.(note));
		midiOut.noteOff(0, padNote);
		padToOnNote.removeAt(padNote);

		//if highest note shift up
		if(padToInd == 15, {octaveShift.(1)});

		//if lowest note shift down
		if(padToInd == 0, {octaveShift.(-1)});
	});
};
padOff = MIDIFunc.noteOff(a, nil, nil, 2017846184);


)


//-----  SCRATCH CODE ------------------------------------------------------------------------------------------------
(
j = [1, 2, 4];
k = [1, 2, 3, 5];
c = k.size();
)

(
MIDIClient.init;
MIDIClient.sources[1].uid;
)