(var midiOut, rhythmList, pitchSeqList, tempoClocks, noteToInd, noteToXY, padPlay, indDictList, art, degrees, rhythms, scales, scale, speed, buildMelody, root, roots, ordinals, sliderInd, padOn, padOff;

MIDIIn.connectAll;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

n = 16;
art = 0.01; //articulation

tempoClocks = List(); //currently using option 2
(1..n).do({|i| tempoClocks.add(TempoClock.new(1))});

noteToInd = {|x| x - 36}; //convert note to pad index
noteToXY = {|x| [noteToInd.(x)%4, floor(noteToInd.(x)/4)]}; //convert note to pad xy (bottom left 0,0)

speed = 1;
sliderInd = 0;

//ordinal values of a scale - 1 indexed
ordinals = List();
ordinals.add([1, 3, 4, 3, 2, 6, 9, 3, 4]);
ordinals.add([2, 3, 2, 5, 2, 4, 3]);
ordinals.add([5, 6, 7, 9, 5, 6, 9, 7]);
ordinals.add([2, 1, 2, 2, 1, 3, 3, 1, 2, 4, 1]);

//rhythms
rhythms = List();
rhythms.add([0.25, 0.25, 0.5, 0.5, 1, 0.5, 0.5, 0.25, 0.25]);
rhythms.add([0.25, 0.25, 0.5]);
rhythms.add([(1/3), 0.25, (2/3), 0.75]);
rhythms.add([0.5, 0.2, 0.4, 0.4, 0.5]);

//scales
scales = List();
scales.add([0, 2, 4, 5, 7, 9, 11]); //major scale

scale = scales[0];

//roots - changing root via the UI triggers rebuilding of pad/melody map
roots = (55..65);

root = 60;

//build melody from root, ordinals, scale
buildMelody = {|root, ord, scale|
	var mel, ln;
	mel = List();
	ln = scale.size;
	ord.do({|ordVal|
		mel.add( root + scale[(ordVal-1)%ln] + (12*floor(ordVal/ln) ) );
	});
	mel;
};

//assign melodies to map object
//CHANGING ROOT OR SCALE TRIGGERS REMAPPING
indDictList = List(); //map index to dictionary with keys "mel" and "rhy"

(0..15).do({|i|
	var dic = Dictionary();
	dic.put("mel", buildMelody.value(root, ordinals[i%4], scale));
	dic.put("rhy", rhythms[floor(i/4)]);
	indDictList.add(dic);
});





//when the pad is hit, this function is called with that pad's padInd and ind = sliderInd (from horizontal slider)
padPlay = {|padInd, ind|
	var pd = indDictList[padInd];
	Task({
		midiOut.noteOn(0, pd["mel"][ind%pd["mel"].size]);

		//(pd["mel"][ind%pd["mel"].size] + " " + ((speed * pd["rhy"][ ind%pd["rhy"].size ]) - art)).postln;

		((speed * pd["rhy"][ ind%pd["rhy"].size ]) - art).wait;

		midiOut.noteOff(0, pd["mel"][ind%pd["mel"].size]);
	}).play;

	tempoClocks[padInd].sched((speed * pd["rhy"][ ind%pd["rhy"].size ]), {padPlay.value(padInd, ind+1)});
};


a = {|vel, note, chan, port|
	//insted of sliderInd directly - should scale it to some value between 0 and LCM of melody and rhtyhm lenghts
	padPlay.value(noteToInd.value(note), sliderInd);
	("played pad" + noteToInd.value(note)).postln;
};
padOn = MIDIFunc.noteOn(a, nil, nil, 2017846184);

padOff = MIDIFunc.noteOff({|vel, note, chan, port|
	tempoClocks[noteToInd.value(note)].clear();
	},
	nil, nil, 2017846184);

)

(
MIDIClient.init;
MIDIClient.sources[1].uid;
)

(
t = TempoClock();
j = {|i| i.postln;};
v = 5;
a = {j.value(v)};
v = 6;
b = {j.value(v)};
a.value();
b.value();


)

floor(5/3)

(
var //build melody from root, ordinals, scale
buildMelody = {|root, ord, scale|
	var mel, ln;
	mel = List();
	ln = scale.size;
	ord.do({|ordVal|
		mel.add( root + scale[ordVal%ln] + (12*floor(ordVal/ln) ) );
	});
	mel;
};

buildMelody.value(60, [8, 9, 10, 0, 1], [0, 2, 4, 5, 7, 9, 11]);
)

(
1.postln;
Task({
	j = Dictionary();
	j.put("aba", "daba");
	2.wait;
	j["aba"].postln;
}).play;
2.postln;
)







