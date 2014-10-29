(
var ccP, ccX, ccY, padX, padXY, ccToInd, ccToXY, noteToInd, noteToXY, activeChord, pianoOn, pianoOff, padOn, padOff, midiOut, channel, chordMap, bendCenter, bendCenterSet, bendSignalCenter, bendScale, semaphore, ccHandler, padDownCount, vibratoInd;
ccP = {|x| (x%3) == 2}; //check if cc is pressure value
ccX = {|x| (x%3) == 0}; //check if cc is x position
ccY = {|x| (x%3) == 1}; //check if cc is y position
noteToInd = {|x| x - 36}; //convert note to pad index
noteToXY = {|x| [noteToInd.value(x)%4, floor(noteToInd.value(x)/4)]}; //convert note to pad xy (bottom left 0,0)
ccToInd = {|x| floor((x-23)/3)}; //convert cc number to pad index
ccToXY = {|x| [(ccToInd.value(x)%4), floor(ccToInd.value(x)/4)]}; //convert cc number to pad xy

semaphore = Semaphore(1);
activeChord = SortedList.new(); //the base chord from which inversions will be made

//function that maps a chord to its inversion
chordMap = {|chord, ind|
	var len = chord.size();
	if (ind < 8,
		{//maps bottom two rows of pads in Quneo to chord inversions
			(ind..ind+len-1).postln;
			(all {: floor((x-2)/len), x <- (ind..ind+len-1)}).postln;
			all {: (floor((x-2)/len)*12) + chord[(x-2)%len], x <- (ind..ind+len-1)};
		},
		{//maps top two rows of pads in Quneo to adjacent notes in chord inversions
			(ind-8..ind-8+1).postln;
			(all {: floor((x-3)/len), x <- (ind-8..ind-8+1)}).postln;
			all {: (floor((x-3)/len)*12) + chord[(x-3)%len], x <- (ind-8..ind-8+1)};
	})
};

channel = 3; //hard coded,
bendSignalCenter = 8192;
bendScale = 100;
padDownCount = 0; //update this, and when it returns to zero, set bend position back to bendSignalCenter

MIDIIn.connectAll;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

//id numbers used in MIDIFunc hardcoded, found using MIDIClient.prlist

//functions for noteOn/Off messages from piano
pianoOn = MIDIFunc.noteOn({|vel, note, chan, port| activeChord.add(note);}, nil, nil, 23048651);

pianoOff = MIDIFunc.noteOff({|vel, note, chan, port|
	activeChord.remove(note);
	midiOut.noteOff(channel, note, vel);}, //so there are no "hanging" notes when you release a piano note before a pad
	nil, nil, 23048651);

//functions for noteOn/off messages from Queneo
a = {|vel, note, chan, port|
	var newChord = chordMap.value(activeChord, noteToInd.value(note));
	newChord.do({|i| midiOut.noteOn(channel, i, vel)});
	semaphore.wait;
	padDownCount = padDownCount + 1;
	if(padDownCount == 1,  //if several pads pressed at once, first pad determines vibrato
		{
			bendCenterSet = true;
			"BEND CENTER SETABLE".postln;
			vibratoInd = noteToInd.value(note);
		}
	);
	semaphore.signal;
	vel.postln;
};
padOn = MIDIFunc.noteOn(a, nil, nil, 536587261);

b = {|vel, note, chan, port|
	var newChord = chordMap.value(activeChord, noteToInd.value(note));
	newChord.do({|i| midiOut.noteOff(channel, i, vel)});
	semaphore.wait;
	padDownCount = padDownCount - 1;
	semaphore.signal;
}; //if two pads share a note and one pad turns off, the shared note turns off - fix this so shared note stays on
padOff = MIDIFunc.noteOff(b, nil, nil, 536587261);

c = {|vel, note, chan, port|
	if (ccX.value(note) && vibratoInd == ccToInd.value(note),
		{
			semaphore.wait;
			if(bendCenterSet,
				{
					bendCenter = vel;
					bendCenterSet = false;
					format("bendCenter %", bendCenter).postln;
				}
			);
			semaphore.signal;
			//make this a function of the physical movement rather than directly linear
			format("center: %, cc: %, dif: %", bendCenter, vel, (vel - bendCenter)).postln;
			midiOut.bend(channel, bendSignalCenter + (bendScale * (vel - bendCenter)));
	});
};
ccHandler = MIDIFunc.cc(c, nil, nil, 536587261);

)



//-------------------------------SCRATCH CODE BELOW----------------------------------------------------

// MIDIClient.init;
// MIDIIn.connect(0, MIDIClient.sources[1]);
// MIDIIn.noteOn = { |port, chan, note, vel| a = vel; [port, chan, note, vel].postln };
// MIDIIn.control = { |port, chan, note, vel|
// 	if (ccX.value(note),
// 		{[port, chan, note, a, vel].postln;
// 		ccToXY.value(note).postln};
// )};
(
a = SortedList.new();
a.add(30);
a.add(5);
a[1].postln;
a.postln;
a.remove(30);
a.postln;
a.size()
)

(
j = (1..8);
)

(
j = 5;
j = j+ 1
)
floor(-1/5)

(
MIDIIn.connectAll;
a = MIDIFunc.noteOn({|port, chan, note, vel| [port, chan, note, vel].postln; "quneo".postln;}, nil, nil, 23048651);


)



(
var chordMap, activeChord;
activeChord = [55, 58, 62, 66];
chordMap = {|chord, ind|
	var len = chord.size();
	if (ind < 8,
		{
			(ind..ind+len-1).postln;
			(all {: floor((x-2)/len), x <- (ind..ind+len-1)}).postln;
			all {: (floor((x-2)/len)*12) + chord[(x-2)%len], x <- (ind..ind+len-1)};
		},
		{
			all {: (floor((x-3)/len)*12) + chord[(x-3)%len], x <- (ind-8..ind-8+1)};
	})
};

chordMap.value(activeChord, 10);

)


(
var ccToPadXY, ccToInd, indToXY, ccToXY;
ccToInd = {|x| floor((x-23)/3)};
indToXY = {|x| a = [(ccToInd.value(x)%4),
	floor(ccToInd.value(x)/4)]};
ccToPadXY = {|x| indToXY.value(ccToInd.value(x))};
g = 56;

ccToInd.value(g).postln;
(ccToInd.value(g)%4).postln;
floor(ccToInd.value(g)/4).postln;

[(ccToInd.value(g)%4), floor(ccToInd.value(g)/4)].postln;
ccToXY = {|x| [(ccToInd.value(g)%4), floor(ccToInd.value(g)/4)]};
ccToXY.value(g);
ccToPadXY.value(g);
)

MIDIClient.sources
MIDIClient.prList

/*
objects:
    activeChord: an ordered list of notes
    mappings: a set of pad/inversion mappings, with a different mapping for each size of activeChord (3, 4, 5)
          f: int -> {|noteList| *stuff* newNoteList}

piano noteOn/noteOff - add/remote note from activeChord
padHit 1. apply inversion 2. play inversion with velocity from hit




*/