(
var ccP, ccX, ccY, padX, padXY, ccToInd, ccToXY, noteToInd, noteToXY, activeChord, pianoOn, pianoOff, padOn, padOff, midiOut, channel;
ccP = {|x| (x%3) == 2};
ccX = {|x| (x%3) == 0};
ccY = {|x| (x%3) == 1};
noteToInd = {|x| x - 37};
noteToXY = {|x| [noteToInd.value(x)%4, floor(noteToInd.value(x)/4)]};
ccToInd = {|x| floor((x-23)/3)};
ccToXY = {|x| [(ccToInd.value(x)%4), floor(ccToInd.value(x)/4)]};
activeChord = SortedList.new();

channel = 3;

MIDIIn.connectAll;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

pianoOn = MIDIFunc.noteOn({|vel, note, chan, port| activeChord.add(note); activeChord.postln}, nil, nil, 23048651);
pianoOff = MIDIFunc.noteOff({|vel, note, chan, port| activeChord.remove(note); activeChord.postln}, nil, nil, 23048651);
a = {|vel, note, chan, port|
	var newChord = activeChord; //replace this with mapping functoin
	newChord.do({|i| midiOut.noteOn(channel, i, vel)});
	vel.postln;
};
padOn = MIDIFunc.noteOn(a, nil, nil, 536587261);
b = {|vel, note, chan, port|
	var newChord = activeChord; //replace this with mapping function
	newChord.do({|i| midiOut.noteOff(channel, i, vel)});
};
padOff = MIDIFunc.noteOff(b, nil, nil, 536587261);


// MIDIClient.init;
// MIDIIn.connect(0, MIDIClient.sources[1]);
// MIDIIn.noteOn = { |port, chan, note, vel| a = vel; [port, chan, note, vel].postln };
// MIDIIn.control = { |port, chan, note, vel|
// 	if (ccX.value(note),
// 		{[port, chan, note, a, vel].postln;
// 		ccToXY.value(note).postln};
// )};
)

(
a = SortedList.new();
a.add(30);
a.add(5);
a[1].postln;
a.postln;
a.remove(30);
a.postln;
)

(
j = [1, 2, 3];
j.do({|i| (2+i).postln});
nil;
)


(
MIDIIn.connectAll;
a = MIDIFunc.noteOn({|port, chan, note, vel| [port, chan, note, vel].postln; "quneo".postln;}, nil, nil, 23048651);


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