(
var ccP, ccX, ccY, padX, padXY, ccToInd, ccToXY, noteToInd, noteToXY, activeChord, pianoOn, pianoOff, padOn, padOff, midiOut, channel, chordMap, bendCenter, bendCenterSet, bendSignalCenter, bendScale, semaphore, ccHandler, padDownCount, vibratoInd, xCounter, xBuffer, xAvgLen, xHitDelay, nonVibratoWindow, vibratoExp, onNotes, padsDown, padMap, hitVel, yBuffers, rollStates, yLow, yHigh, findRollState, padDiv, isFirstYCC, yCounter, yAvgLen, isRolling;
ccP = {|x| (x%3) == 2}; //check if cc is pressure value
ccX = {|x| (x%3) == 0}; //check if cc is x position
ccY = {|x| (x%3) == 1}; //check if cc is y position
noteToInd = {|x| x - 36}; //convert note to pad index
noteToXY = {|x| [noteToInd.value(x)%4, floor(noteToInd.value(x)/4)]}; //convert note to pad xy (bottom left 0,0)
ccToInd = {|x| floor((x-23)/3)}; //convert cc number to pad index
ccToXY = {|x| [(ccToInd.value(x)%4), floor(ccToInd.value(x)/4)]}; //convert cc number to pad xy

//objects
semaphore = Semaphore(1); //lock for thread safety
activeChord = SortedList.new(); //the base chord from which inversions will be made
onNotes = Set.new(); //collection that prevents pads with shared notes from turning off shared notes
xBuffer = List.new(); //buffer of x values for running average
padsDown = Set.new(); //set of what pads are down for help calculating what notes to turn off
padMap = Dictionary.new; //maps padInd -> [Dict, Dict] where first is piano -> inversion, second is inversion -> piano
yBuffers = all {: List.new(), x <- (1..16)}; //list of buffers of the last 3 y values for each pad
rollStates = all {: 0, x<-(1..16)}; //list of indexes of the current roll position of pads
isFirstYCC = all {: false, x<-(1..16)}; //list of flags indicating if the next cc is the first one after the noteOn message for that pad
isRolling = all {: false, x<-(1..16)}; //list of flags indicating if that pad is currently rolling the chord

//constants and default values
channel = 4; //hard coded,
bendSignalCenter = 8192;
padDownCount = 0; //update this, and when it returns to zero, set bend position back to bendSignalCenter
xCounter = 0;
bendCenter = 63;
hitVel = 0;
yLow = 15;
yHigh = 112; //127 - 15 - TODO: will need to tweak this and yLow if people want to play chords larger than 5
yAvgLen = 3;

//function that maps a chord to its inversion
//TODO: edge case when chord only has 1 note
chordMap = {|chord, ind|
	var len = chord.size();
	if (ind < 8,
		{//maps bottom two rows of pads in Quneo to chord inversions
			//(ind..ind+len-1).postln;
			//(all {: floor((x-2)/len), x <- (ind..ind+len-1)}).postln;
			all {: (floor((x-2)/len)*12) + chord[(x-2)%len], x <- (ind..ind+len-1)};
		},
		{//maps top two rows of pads in Quneo to adjacent notes in chord inversions
			//(ind-8..ind-8+1).postln;
			//(all {: floor((x-3)/len), x <- (ind-8..ind-8+1)}).postln;
			all {: (floor((x-3)/len)*12) + chord[(x-3)%len], x <- (ind-8..ind-8+1)};
	})
};

//given a particular chord size, this returns a list that indicates the positions
//on the pad's y axis that correspond to particular notes of the chord
padDiv = {|num|
	var segmentSize = floor(127/(num+1));
	all {: segmentSize * i, i <-(1..num)}.asList;
};

//given a buffer of y values and the result of padDiv, this
findRollState = {|yBuff, divList|
	var rollInd, segList, avg;
	segList = List.new();
	avg = yBuff.sum/yBuff.size;
	divList.addFirst(0);
	divList.add(127);
	(1..(divList.size-2)).do({|ind|
		segList.add([divList[ind]-5, divList[ind]+5]);
		segList.add([divList[ind]+5, divList[ind+1]-5]);
	});
	segList.addFirst([0, divList[1]-5]);
	(0..segList.size-1).do({|ind|
		if( (segList[ind][0] < avg) && (avg < segList[ind][1]), {rollInd = ind});
	});
	rollInd
};

//x-axis/vibrato stabilization parameters (tweakable)
bendScale = 50;
xAvgLen = 3;
xHitDelay = 9;
nonVibratoWindow = 13;
vibratoExp = 1.1;


MIDIIn.connectAll;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

//id numbers used in MIDIFunc hardcoded, found using MIDIClient.prlist

//functions for noteOn/Off messages from piano
pianoOn = MIDIFunc.noteOn({|vel, note, chan, port|
	semaphore.wait;
	activeChord.add(note);
	//activeChord.postln;
	semaphore.signal;}, nil, nil, 23048651);

pianoOff = MIDIFunc.noteOff({|vel, note, chan, port|
	var newInd, oldInd, newChord;
	semaphore.wait;
	padMap.values.do({|map| //not necessary now that each pad remembers its own "on" notes
		if(map.includesKey(note), {midiOut.noteOff(channel, map.at(note))});
		//format("removing % key from %", note, map).postln;
	});

	activeChord.remove(note);
	//TODO: padsDown.Do uses a function of activeChord and index to calculate which note to turn off.
	//Would changing the active chord here make it so that padsDown.Do would not be able to correctly
	//calculate which note to turn off because the activeChord used to calculate the new index has changed.
	//EX padsDown.Do:: f(oldIndex, g(activeChord, ind)) -> newIndex THUS changing active chord changes pads.Down
	//Should probably have each pad save what its "on" notes are and what piano key each "on" note maps to

	//activeChord.postln;
	semaphore.signal;}, //so there are no "hanging" notes when you release a piano note before a pad
	nil, nil, 23048651);

//functions for noteOn/off messages from Queneo
a = {|vel, note, chan, port|
	var newChord, padInd, noteMap;
	padInd = noteToInd.value(note);
	hitVel = vel;
	noteMap = Dictionary.new();

	semaphore.wait;
	isFirstYCC[padInd] = true;
	semaphore.signal;

	semaphore.wait;
	padsDown.add(noteToInd.value(note));
	if(activeChord.size != 0,
		{
			newChord = chordMap.value(activeChord, padInd);
			(0..newChord.size-1).do({|i|
				noteMap.put(activeChord[(padInd+i)%newChord.size], newChord[i]);
				//noteMap2.put(newChord[i], activeChord[(padInd+i)%newChord.size]); //not needed?
			});
			padMap.put(padInd, noteMap);
			newChord.do({|i| midiOut.noteOn(channel, i, vel)});
			onNotes = onNotes | newChord.as(Set);
			//onNotes.postln;
			padDownCount = padDownCount + 1;
			if(1 == 1,  //if several pads pressed at once, LAST pad determines vibrato (used to be first pad - padCounter==1
				{
					xCounter = 0;
					midiOut.bend(channel, bendSignalCenter);
					bendCenterSet = true;
					//"BEND CENTER SETABLE".postln;
					vibratoInd = noteToInd.value(note);
				}
			);
	});
	semaphore.signal;
	//vel.postln;
};
padOn = MIDIFunc.noteOn(a, nil, nil, 536587261);

b = {|vel, note, chan, port|
	var newChord, padInd, noteOffSet;
	padInd = noteToInd.value(note);
	semaphore.wait;
	if((activeChord.size != 0) && (onNotes.size != 0),
		{
			noteOffSet = padMap.at(padInd).values.asSet;
			(padMap.keys - Set[padInd]).do({|ind|
				noteOffSet = noteOffSet - padMap.at(ind).values.asSet;
				//format("notes on at %: %", ind, padMap.at(ind).values).postln;
			});
			//format("note off set %", noteOffSet).postln;
			noteOffSet.do({|i| midiOut.noteOff(channel, i)});
			onNotes = onNotes - noteOffSet;
			//onNotes.postln;
	});
	padMap.removeAt(padInd);
	padDownCount = padDownCount - 1;
	if (padDownCount == 0, {
		xCounter = 0;
		midiOut.bend(channel, bendSignalCenter);
	});
	yBuffers[padInd] = List.new();
	semaphore.signal;
}; //if two pads share a note and one pad turns off, the shared note turns off - fix this so shared note stays on
padOff = MIDIFunc.noteOff(b, nil, nil, 536587261);

//vibrato handling function
c = {|vel, note, chan, port|
	var avg, padInd;
	padInd = ccToInd.value(note);
	if (ccX.value(note) && vibratoInd == padInd,
		{
			semaphore.wait;
			xCounter = xCounter + 1;
			xBuffer.addFirst(vel);
			if(xBuffer.size == (xAvgLen+1), {xBuffer.pop});
			if(bendCenterSet && (xCounter > xHitDelay),
				{
					bendCenter = vel;
					bendCenterSet = false;
					//format("bendCenter %", bendCenter).postln;
				}
			);
			semaphore.signal;
			avg = ((xBuffer.sum / xBuffer.size) - bendCenter);
			//make this a function of the physical movement rather than directly linear
			if(xCounter > xHitDelay && (abs(avg) > nonVibratoWindow), {
				//format("ind: %, center: %, cc: %, hist: %, dif: %",
				//vibratoInd, bendCenter, vel, xBuffer.size, avg).postln;
				midiOut.bend(channel,
				bendSignalCenter + (bendScale * sign(avg) * ((abs(avg)-nonVibratoWindow)**vibratoExp)));
			});
	});
	if (ccY.value(note),
		{
			yBuffers[padInd].addFirst(vel);
			if(yBuffers[padInd].size == (yAvgLen+1), {yBuffers[padInd].pop});
			//vel.postln;
			semaphore.wait;
			if(isFirstYCC[padInd],
				{
					format("FIRST %, padInd:%", vel, padInd).postln;
					if((vel < yLow) || (yHigh < vel),
						{
							// format("args - yBuf:%   padDiv:%", yBuffers[padInd], padDiv.value(3)).postln;
							isRolling[padInd] = true;
							// rollStates[padInd] = findRollState.value(yBuffers[padInd], padDiv.value(3));
						},
						{

						}
					);
					isFirstYCC[padInd] = false;
				},
				{
					if(isRolling[padInd],
						{
							// "rolling".postln;
							// format("args - yBuf:%   padDiv:%", yBuffers[padInd], padDiv.value(3)).postln;
							rollStates[padInd] = findRollState.value(yBuffers[padInd], padDiv.value(3));
							rollStates[padInd].postln;
					});
				}
			);
			semaphore.signal;
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
var padDiv, findRollState;
//given a particular chord size, this returns a list that indicates the positions
//on the pad's y axis that correspond to particular notes of the chord
padDiv = {|num|
	var segmentSize = floor(127/(num+1));
	all {: segmentSize * i, i <-(1..num)}.asList;
};

//given a buffer of y values and the result of padDiv, this
findRollState = {|yBuff, divList|
	var rollInd, segList, avg;
	segList = List.new();
	avg = yBuff.sum/yBuff.size;
	divList.addFirst(0);
	divList.add(127);
	(1..(divList.size-2)).do({|ind|
		segList.add([divList[ind]-5, divList[ind]+5]);
		segList.add([divList[ind]+5, divList[ind+1]-5]);
	});
	segList.addFirst([0, divList[1]-5]);
	(0..segList.size-1).do({|ind|
		if( (segList[ind][0] < avg) && (avg < segList[ind][1]), {rollInd = ind});
	});
	rollInd
};

padDiv.value(6).postln;
findRollState.value([81, 82, 84], padDiv.value(5));

)




(
a = {|num|
	var segmentSize = floor(127/(num+1));
	all {: segmentSize * i, i <-(1..num)};
};
a.value(6);
)

(
var divList = [1, 2, 4];
divList.addFirst(0);
divList.add(127);
)

(
a = SortedList.new();
a.addFirst(30);
a.addFirst(5);
a.addFirst(2);
a.postln;
a.pop;
a.postln;
a.pop;
a.postln;
a.add(66);
a.add(77);
a.postln;
a.pop;
a.postln
// a.pop;
// a.postln;
// a.add(25);
// a.postln;
// a.pop;
// a.postln;
)




(
var ac = SortedList.new();
ac.size;
)

(
(0..5)
)
floor(-1/5)

false && false

(
MIDIIn.connectAll;
a = MIDIFunc.noteOn({|port, chan, note, vel| [port, chan, note, vel].postln; "quneo".postln;}, nil, nil, 23048651);


)
(
j = (1: 5);
j.includes(5).postln;
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

chordMap.value(activeChord, 5);

)

(
Set[1,2,3] == Set[2-1, 3-1, 4-1]
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