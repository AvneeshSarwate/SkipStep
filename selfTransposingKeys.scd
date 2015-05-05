(
var midiOut, noteToInd, noteToXY, isPadNote, padOn, padOff, octaveShift, padIndToNote, rootMove, scale, root, indToNote, padToOnPitch, dUP, dDOWN, dLEFT, dRIGHT, startInd, rootMoveHelper, createPadToNoteMap, directions;

MIDIIn.connectAll;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

noteToInd = {|x| x - 36}; //convert note to pad index
noteToXY = {|x| [noteToInd.(x)%4, floor(noteToInd.(x)/4)]}; //convert note to pad xy (bottom left 0,0)
isPadNote = {|x| (noteToInd.(x) >=0) && (noteToInd.(x) < 16)};

//give names to midiNotes of up/down/left/right controls from Quneo
//dUP, dDOWN, dLEFT, dRIGHT
dUP = 20;
dDOWN = 21;
dLEFT = 18;
dRIGHT = 17;
directions = Set[17, 18, 20, 21];


scale = [0, 2, 4, 5, 7, 9, 11];
root = 48;
startInd = -3;

//pad->on-notes mapping to handle case where pad->pitch mapping changes while notes are still on
padToOnPitch = Dictionary.new();

indToNote = {|ind, scale, root|
	root + scale[ind%scale.size()] + ((ind / scale.size).floor * 12);
	/*("   " + root).postln;
	("   " + scale[ind%scale.size()]).postln;
	("   " + ((ind / scale.size).floor * 12)).postln;
	("   " + (root + scale[ind%scale.size()] + ((ind / scale.size).floor * 12))).postln;*/
};

createPadToNoteMap = {|ind|
	var newMap = List.new();
	ind.postln;
	newMap.class.postln;
	(ind..(ind+15)).do({|i|
		i.postln;
		newMap.add(indToNote.(i, scale, root));
		("  " + indToNote.(i, scale, root)).postln;
	});
	newMap;
};

padIndToNote = createPadToNoteMap.(startInd);

padIndToNote.postln;

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
	startInd.postln;
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
		var padNote = padIndToNote[noteToInd.(note)];
		midiOut.noteOn(0, padNote, vel);
		padToOnPitch.put(noteToInd.(note), padNote);
		(padNote + "ON").postln;
	});

	//otherwise call rootMove based on which direction pad was hit
	if(directions.includes(note),
		{rootMove.(note)}
	);

};
padOn = MIDIFunc.noteOn(a, nil, nil, 2017846184);


b = {|vel, note, chan, port|
	if(isPadNote.(note), {
		//noteOff
		var padNote = padToOnPitch.at(noteToInd.(note));
		midiOut.noteOff(0, padNote);
		padToOnPitch.removeAt(noteToInd.(note));
		(padNote + "OFF").postln;
		//if highest note shift up
		if(noteToInd.(note) == 15, {octaveShift.(1)});

		//TODO: add toggle for turning "auto transposing" on or off

		//if lowest note shift down
		if(noteToInd.(note) == 0, {octaveShift.(-1)});
	});
};
padOff = MIDIFunc.noteOff(b, nil, nil, 2017846184);


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