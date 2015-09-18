(
var n, beats, oldTap, newTap, tapLim, tempoClocks, oscMetronomeHit, midiOut, playHandler, tapTempoHandler, tempoChangeHandler, tempoSyncHandler, lastHits, indTest, playChordParamNum, chordDur, skipHitCalc, pythonOSCport, loopingOn, lastBeats, metronomeClocks, notesOn, clockFuncGenerator, lastBeatsHandler, holdDownPlay, loop_BUTTON, hold_BUTTON, masterLoopingOn, startMetronomeResponse, padOn, padOff, noteToXY, noteToInd, isPadNote;


n = 4; //set n - number of instruments
MIDIClient.init;
MIDIIn.connectAll;
/*----------------create n tempo clocks (and associated beat variables?)----------------
When tap-tempoing:
1. either adjust the .tempo of the tempoClocks and reschedule them every .25 beats,
2. or leave the tempo of the tempoClocks at 1 and reschedule them every beats[i]*0.25,
    where beats[i] is changed by the tap tempo
*/
tempoClocks = List(); //currently using option 2
(1..n).do({|i| tempoClocks.add(TempoClock.new(1))});


//----------------create old/new time variables for touch tempo -------------------
oldTap = 0;
newTap = 0;
tapLim = 2;
beats = Array.fill(n, {1.5}); //create n beats (default 0.7)
lastHits = Array.fill(n, {0});


//------------------set up tempoClocks to send metronome hits via OSC ---------------------
pythonOSCport = NetAddr("localhost", 5174);
/*oscMetronomeHit = {
	|i| lastHits[i-1] = SystemClock.beats;
	pythonOSCport.sendMsg("/played-"++i, i);
	//("/played-"++i + "," + i).postln;
};
(0..(n-1)).do(
	{|i| tempoClocks[i].sched(0, {
		oscMetronomeHit.value(i+1); //i+1 in .value() is a hack to get around a small unknown bug
		beats[i]*0.25/*0.25*/})}
);*/


//------------------set up code to handle Quneo triggering ---------------------
noteToInd = {|x| x - 36}; //convert note to pad index
noteToXY = {|x| [noteToInd.(x)%4, floor(noteToInd.(x)/4)]}; //convert note to pad xy (bottom left 0,0)
isPadNote = {|x| (noteToInd.(x) >=0) && (noteToInd.(x) < 16)};

loopingOn = Array.fill(n, {false});
lastBeats = Array.fill(n, {false});
metronomeClocks = Array.fill(n, {TempoClock.new(1)});
notesOn = Array.fill(n, {Set.new()});
holdDownPlay = false;
masterLoopingOn = false;
loop_BUTTON = 26;
hold_BUTTON = 24;

/*
beatHit

vars - loopingOn[i], holdPlayOn (can't be on at same time, buttons toggle them on/off)
       lastBeats[] - array indicating value of lastHit flag for each instrument/metronome
       metronomeClocks[] - column/instrument -> task mapping
       notesOn[] - on notes for each instrument

MetronomeTask - loops and sends metronomeHit while (!loopOn[i] lastBeats[i]) is true, then sets it to false

padDown -
    if another pad in the same column is looping, kill that loop
    if this is not a "turn off loop" scenario
        send padDown message to python, wait on "gridLoaded" message

onGridLoaded
    start MetronomeTask
    add task to metronomeTask[i]

padUp -
    turn off notes for that instrument/column
    destroy/erase/stop task for that column

TODO in Python - create padDown endpoint, add lastHit flag,
check that refresh/auto-alg stuff (stuff in postChordPlay() in python)
all works properly wrt timing after the last chord is played in all use cases

 -------------------------------------------------------------------------------------
TODO: - need a way to stop a looping melody without starting a new one
      - need to rework how saving miniStates works -
         - need to save 4 "reactive" miniStates
      - maybe don't have step tracker move, but be static and act as a "start point" control
      - expand miniState to include: alg parameters (type, intensity, loop), refershMode, "start point" ^
      - need to do lights


*/

clockFuncGenerator = {|i|
	{
		var returnVal;
		if(loopingOn[i].not && holdDownPlay.not && lastBeats[i],
			{
				lastBeats[i] = false;
				returnVal = nil;
				("lastBeat cutoff" + i).postln;
				//turn off red/normal
			},
			{
				lastHits[i] = SystemClock.beats;
				pythonOSCport.sendMsg("/played-"++i, i);
				("beat" + i + " " + beats[i]).postln;
				returnVal = beats[i]*0.25;
		});

		returnVal
	}
};

a = {|vel, note, chan, port|
	if(isPadNote.(note), {
		var xVal = noteToXY.(note)[0];
		var yVal = noteToXY.(note)[1];
		"padOn".postln;
		//reset everything about that instrument
		//turn off all lights on pad
		lastBeats[xVal] = false;
		loopingOn[xVal] = false;
		metronomeClocks[xVal].clear;
		notesOn[xVal].do({|i| midiOut.noteOff(xVal, i)});
		notesOn[xVal].clear;
		pythonOSCport.sendMsg("/padHit", xVal, yVal);

		if(masterLoopingOn, {loopingOn[xVal] = true});
		//TODO: lighting stuff - turn on red if normal, green if loop, orange if holdDown
	});
	//TODO: hanlde looping and holdDownPlay (where it only plays while you're holding it down)
	if(note == loop_BUTTON, {
		masterLoopingOn = masterLoopingOn.not;
		//toggle lighting
	});
	if(note == hold_BUTTON, {
		holdDownPlay = holdDownPlay.not;
		//toggle lighting
	});

};

padOn = MIDIFunc.noteOn(a, nil, nil, 2017846184);


b = {|vel, note, chan, port|
	if(isPadNote.(note) && holdDownPlay, {
		var xVal = noteToXY.(note)[0];
		var yVal = noteToXY.(note)[1];
		metronomeClocks[xVal].clear;
		notesOn[xVal].do({|i| midiOut.noteOff(xVal, i)});
		notesOn[xVal].clear;
		//turn off orange
		/*LIGHTING BUG - if you hold down a pad not in holdMode, turn on hold mode, and let go of the pad,
		it will turn off that pad's despite it not being a holdMode light*/
	});
};
padOff = MIDIFunc.noteOff(b, nil, nil, 2017846184);

//msg[1] is the instrument index for which to start the metronome
startMetronomeResponse = {|msg, time, addr, recvPort|
	("metronome started for" + msg[1]).postln;
	metronomeClocks[msg[1]].sched(0, clockFuncGenerator.(msg[1]));
};
OSCFunc(startMetronomeResponse, "/startMetronome");


lastBeatsHandler = {|msg, time, addr, recvPort|
	("lastBeat flag set" + msg[1]).postln;
	lastBeats[msg[1]] = true;
};
OSCFunc(lastBeatsHandler, "/lastBeats");

//--------------------------------set up playChord hanlder--------------------------------
//msg[1] is an index for which gridState the message is from
//msg[2] is either "normal", "on", or "off" - specifying a piano vs non-piano play
//msg[3] is a int (1 or 0) indicating whether the play is a stepjump play or not
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;
playChordParamNum = 4; //start index of where the chord notes start in the OSC message

playHandler = {|msg, time, addr, recvPort|
	if (msg[2] == 'normal',
		{
			//TODO: set lastHits[i] flag if needed
			if (msg[3] == 1,
				{
					chordDur = beats[msg[1]] - (SystemClock.beats-lastHits[msg[1]]) - 0.005;
					("stepjump duration is" + chordDur).postln;
				},
				{("BEATS VAL" + [beats[msg[1]], msg[1]]).postln; chordDur = 0.25*beats[msg[1]]-0.005}
			);
			Task({
				//TODO: add onNotes tracking
				msg[playChordParamNum..].do({|i|
					midiOut.noteOn(msg[1], i);
					notesOn[msg[1]].add(i);
				});/*hit noteOn messages*/
				chordDur.wait; /*wait for beat*/
				msg[playChordParamNum..].do({|i|
					midiOut.noteOff(msg[1], i);
					notesOn[msg[1]].remove(i);
				}); /*hit noteOff messages*/
				0.005.wait; //articulation
			}).play;

		},
		{
			if (msg[2] == 'on',
				{msg[playChordParamNum..].do({|i| midiOut.noteOn(msg[1], i)}); /*noteon messages*/},
				{msg[playChordParamNum..].do({|i| midiOut.noteOff(msg[1], i)}); /*noteoff messages*/}
			)
		}
	)
};

OSCFunc(playHandler, "/playChord");


//--------------------------------set up stepjump error calculator--------------------------------
//msg[1] is index of gridState
//msg[2] is the index of the stepjump

skipHitCalc = {|msg, time, addr, recvPort|
	//TODO stepjump: turn of the currently playing chord - add a set object that tracks "on" notes
	("flag value is " + ((SystemClock.beats - lastHits[msg[1]]) > ((0.25*beats[msg[1]]) - 0.03))).postln;
	if ((SystemClock.beats - lastHits[msg[1]]) > ((0.25*beats[msg[1]]) - 0.03),
		{pythonOSCport.sendMsg("/stepJumpFlag", msg[1], 1, msg[2])},
		{pythonOSCport.sendMsg("/stepJumpFlag", msg[1], 0, msg[2])},
	)
};

OSCFunc(skipHitCalc, "/skipHitCalc");


//--------------------------------set up tap tempo handler--------------------------------
//make sure time argument is in seconds
//msg[1] is a symbol-type binary vector indicating which instruments to change the beat for
tapTempoHandler = {|msg, time, addr, recvPort|
	//msg[1] is a boolean vector indicating which instruments the tap occured for
	oldTap = newTap;
	newTap = time; //should it be SystemClock.beat instead?
	if(newTap - oldTap < tapLim,
		{
			(0..n-1).do({|i|
				if(msg[1].asString[i] == $1,
					{beats[i] = newTap - oldTap};
				)}
			);
		}
	)
};

OSCFunc(tapTempoHandler, "/touch");


//--------------------------------set up tempo change handler--------------------------------
//msg[1] is a symbol-type binary vector indicating which instruments to change the beat for
//msg[2] is the factor to multiply the beat(s) by
tempoChangeHandler = {|msg, time, addr, recvPort|
	(0..n-1).do({|i|
		if(msg[1].asString[i] == $1,
			{
				beats[i] = beats[i] * msg[2];
			}
		)}
	);
};

OSCFunc(tempoChangeHandler, "/tempoChange");

indTest = 1;
//--------------------------------set up tempo sync handler--------------------------------
//msg[1] is a symbol-type binary vector indicating which instruments to change the beat for
//msg[2] is a symbol-type binary vector indicating whether to sync (1) tempo, and (2) next hit
//msg[3] is the index of the instrument to sync to
tempoSyncHandler = {|msg, time, addr, recvPort|
	(0..n-1).do({|i|
		if(msg[1].asString[i] == $1,
			{
				if(msg[2].asString[0] == $1,
					{
						//tempo sync
						beats[i] = beats[msg[3]];

				});
				if(msg[2].asString[1] == $1,
					{
						//next hit sync
						tempoClocks[i].clear();
						("\n" + msg[3]).postln;
						(i + "time to next beat" + ((beats[msg[3]]*0.25) - (SystemClock.beats - lastHits[msg[3]]))).postln;
						(i + "beat duration" + (beats[msg[3]]*0.25)).postln;
						(i + "time from last beat" + (SystemClock.beats - lastHits[msg[3]]) + "\n").postln;
						tempoClocks[i].sched((beats[msg[3]]*0.25) - (SystemClock.beats - lastHits[msg[3]]),
							{
								oscMetronomeHit.value(i+1);
								//(i + "index check" + indTest).postln;
								indTest = indTest+1;
								beats[i]*0.25/*0.25*/
						});
						("clock queue" + i).postln;
						tempoClocks[i].queue.postln;
				});
			}
		)}
	);
};

OSCFunc(tempoSyncHandler, "/tempoSync");

)
















//------------------- templates and testing - final version above ------------

(
k = 5;
(1..4).do({|i|
	Task({
		{|break|
			var lv = 1;
			{
				if(lv > k, {break.value();});
				i.postln;
				lv.postln;
				k.postln;
				" ".postln;
				lv = lv +1;
				1.wait;
			}.loop;
		}.block;
	}).play;
});
)

(


)

(
var tempoClocks;
n = 4;
tempoClocks = Array.fill(n, TempoClock.new(1));
tempoClocks[1] === tempoClocks[2];
)


//FIRST DATA OF OSC MESSAGE WILL ALWAYS BE INSTRUMENT INDEX (when appropriate)

SystemClock.beats
(
//template for playChord() hanlder
var cf, midiOut, tempClock, beat;

beat = 0.5;

MIDIClient.init;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");

cf = {|msg, time, addr, recvPort|
	if (msg[2] == 'normal',
		{
			Task({
				//msg.postln;
				msg[3..].do({|i| midiOut.noteOn(msg[1], i)});/*hit noteOn messages*/
				//GENERALIZE: beat[msg[1]] or tempClocks[msg[1].tempo
				beat.wait; /*wait for beat*/
				msg[3..].do({|i| midiOut.noteOff(msg[1], i)}); /*hit noteOff messages*/
			}).play;
		},
		{
			//msg[2].postln;
			if (msg[2] == 'on',
				{msg[3..].do({|i| midiOut.noteOn(msg[1], i)}); /*noteon messages*/},
				{msg[3..].do({|i| midiOut.noteOff(msg[1], i)}); /*noteoff messages*/}
			)
		},
	)
};

OSCFunc(cf, "/playChord");

OSCFunc.trace(true);
)

(
//template for tap tempo hanlder
var oldTap, newTap, tapLim, tapFunc, beat;

beat = .5;
tapLim = 2;

//make sure time is in seconds
tapFunc = {|msg, time, addr, recvPort|
	//msg[1] is a boolean vector indicating which instruments the tap occured for
	oldTap = newTap;
	newTap = time; //should it be SystemClock.beat instead?
	("time"+time).postln;
	if(newTap - oldTap < tapLim,
		{
			("duration"+(newTap-oldTap)).postln;
			(0..n-1).do({|i|
				if(msg[1].asString[i] == $1,
					//directly set .tempo of TempoClocks here, recalculate duration to "beat"
					{beats[i] = newTap - oldTap};
				)}
			)
		}; //generalized version
	)
};
)

(
/*start array of tempo clocks like this - beat change by tap tempo should
give the proper behavior */
var temp = TempoClock.new(2.0);
/*assign to each tempoClock as {f1.value(chanVal_i)}*/
var f1 = {|chan| /*repalce with an oscSend*/; .25};
//if using beats array instead of TempoClock tempo, this function would return beats[i]
temp.sched(0, f1);
)


(
var num = 4;
(0..(num-1)).do({|i|
	if('1101'.asString[i] == $1,
		{("yes"+i).postln;"dork".post},
		{("no"+i).postln;}
)});
)

(
var fu, gu;
fu = {|a1| a1*2;};
gu = {fu.value(5);};
gu.class.postln;
)

(
var ar = Array.newClear(4);
ar[1] = 12;
ar[2] = "yp";
ar.postln;
)
a = [1]
(
Task({
	SystemClock.beats.postln;
	1.wait;
	SystemClock.beats.postln;
}).play;
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


