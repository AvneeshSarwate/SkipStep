(
var n, beats, oldTap, newTap, tapLim, tempoClocks, oscMetronomeHit, midiOut, playHandler, tapTempoHandler, tempoChangeHandler, tempoSyncHandler, lastHits, indTest, playChordParamNum, chordDur, skipHitCalc, pythonOSCport, loopingOn, lastBeats, metronomeClocks, notesOn, clockFuncGenerator, lastBeatsHandler, holdDownPlay, loop_BUTTON, hold_BUTTON, masterLoopingOn, startMetronomeResponse, padOn, padOff, noteToXY, noteToInd, isPadNote, quneoOut, padIndToGreen, padIndToRed, loopingPads, singlePlayPads, heldDownPads, loop_LIGHT, hold_LIGHT, tampTempo_BUTTON, lastTimeTapped, beatMods, tapTempo_BUTTON, ccHandler, transposeMap, transposePositions, startPositionMap, startPosition, replayList, recordList, replayRecording, replayLoopState, replayedInstrument, record_BUTTON, replay_BUTTON, replayingLoop, replayInd, replayClock, loopStartFunctions, masterClockBeat, masterClockTempoHandler, masterClockOSCport, launchpadOut, launchPad, lastColoredIndPad, color1, color2, channelAndStartIndToPad, launchPadToChanelAndStartInd, selectedPadPerInst, launchPadButtonOn, launchPadOnFunc, launchPadButtonOff, launchpadOffFunc, quneo, instrumentIsHolding, launchpadBankButtonGroupings, launchpadButtonToChanInd;


n = 4; //set n - number of instruments
//MIDIClient.init;
MIDIIn.connectAll;
/*----------------create n tempo clocks (and associated beat variables?)----------------
When tap-tempoing:
1. either adjust the .tempo of the tempoClocks and reschedule them every .25 beats,
2. or leave the tempo of the tempoClocks at 1 and reschedule them every beats[i]*0.25,
    where beats[i] is changed by the tap tempo
*/
tempoClocks = List(); //currently using option 2
(1..n).do({|i| tempoClocks.add(TempoClock.new(1))});


quneoOut = MIDIOut.newByName("QUNEO", "QUNEO");
quneoOut.latency = 0;

padIndToGreen = ((0..15)*2);
padIndToRed = ((0..15)*2 + 1);

//----------------create old/new time variables for touch tempo -------------------
oldTap = 0;
newTap = 0;
tapLim = 2;
beats = Array.fill(n, {1}); //create n beats (default 0.7)
lastHits = Array.fill(n, {0});


//------------------set up tempoClocks to send metronome hits via OSC ---------------------
pythonOSCport = NetAddr("localhost", 5174);
masterClockOSCport = NetAddr("localhost", 57120);
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
quneo = MIDIClient.sources.select({|elem| (elem.name == "QUNEO")
	&& (elem.device == "QUNEO")})[0];

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
hold_BUTTON = 25;
loop_LIGHT = 35;
hold_LIGHT = 34;
tapTempo_BUTTON = 24;
loopingPads = Set.new();
singlePlayPads = Set.new();
heldDownPads = Set.new();
instrumentIsHolding = Array.fill(n, {false});
lastTimeTapped = TempoClock.default.beats;
beatMods = beats = Array.fill(n, {1});
transposeMap = Dictionary.new;
transposePositions = Array.fill(n, {0});
startPositionMap = Dictionary.new;
startPosition = 0;
recordList = List.new; //raw time, midiNote, on/off
replayList = List.new; //wait time, midiNote, on/off
replayRecording = false;
record_BUTTON = 21;
replay_BUTTON = 20;
replayLoopState = [false, false]; //holddown mode and loop mode
replayedInstrument = 0;
replayClock = TempoClock.new(1);
replayingLoop = false;
replayInd = 0;
loopStartFunctions = List.fill(4, {nil});

(0..15).do({|i|
    quneoOut.noteOff(0, padIndToGreen[i], 127);
    quneoOut.noteOff(0, padIndToRed[i], 127);
});
(0..3).do({|i|
    quneoOut.noteOn(0, padIndToRed[i], 127);
});
quneoOut.noteOff(0, loop_LIGHT, 127);
quneoOut.noteOff(0, hold_LIGHT, 127);

(0..8).do({|i|
	(i*14..i*14+10).do({|j| transposeMap.put(j, i)});
});

(0..7).do({|i|
	(i*16..i*14+13).do({|j| startPositionMap.put(j, i)});
});
//------------------end code to handle Quneo triggering ---------------------

//------------------set up code to handle launchPad triggering ---------------------
launchpadOut = MIDIOut.newByName("Launchpad Pro", "Standalone Port");
launchpadOut.latency = 0;
launchPad = MIDIClient.sources.select({|elem| (elem.name == "Standalone Port")
	&& (elem.device == "Launchpad Pro")})[0];
lastColoredIndPad = [11,31,51,71];
color1 = [39, 112, 4, 83];
color2 = [25, 45, 72, 13];
channelAndStartIndToPad = {|chan, ind| 10+(20*chan) + if(ind < 8, ind+1, 11+(ind-8))};
launchpadBankButtonGroupings = [[80,70,89,79],[60,50,69,59],[40,30,49,39],[20,10,29,19]];

//maps round buttons to (instrumentIndex, bankIndex)
launchpadBankButtonToChanInd = Dictionary.new;
(0..3).do{|i|
    (0..3).do{|j|
        launchpadBankButtonToChanInd[launchpadBankButtonGroupings[i][j]] = [i, j]; //channel, bank ind
    }
};

//maps step sequencer pad midi numbers to (instrumentIndex, sequenceIndex)
launchPadToChanelAndStartInd = Dictionary.new;
(1..8).do{|i|
    (1..8).do{|j|
        launchPadToChanelAndStartInd.put((i*10+j), [((i-1)/2).floor, ((i-1)%2)*8 + (j-1)]);
        launchpadOut.noteOn(0, (i*10+j), color1[((i-1)/2).floor]);
    }
};
noteToInd = {|x| (noteToXY.(x)[1]*4) + noteToXY.(x)[0]}; //convert note to pad index
noteToXY = {|x|
    var xVal = ((x-10)/20).floor;
    var yVal = launchpadBankButtonGroupings[xVal].indexOf(x);
    [xVal, yVal]
}; //convert note to pad xy (bottom left 0,0)
isBankNote = {|x| noteToXY.(x)[1].isNil.not};

selectedPadPerInst = Dictionary.new;
(0..3).do({|i| selectedPadPerInst[i] = 0});

launchPadButtonOn = {|vel, note, chan, port|
    var chanAndStartInd = launchPadToChanelAndStartInd[note];
    if(chanAndStartInd.isNil.not, {
        var channel = chanAndStartInd[0];
        var startInd = chanAndStartInd[1];
        var padSlot = selectedPadPerInst[channel];
        var padInd = padSlot*4 + channel; //this gives the padInd
        metronomeClocks[channel].clear;
        if(loopingOn[channel],{
            loopStartFunctions[channel] = {pythonOSCport.sendMsg("/padHit", channel, padSlot, startInd)};
        });
        if(instrumentIsHolding[channel], {
            heldDownPads.add(padInd);
            pythonOSCport.sendMsg("/padHit", channel, padSlot, startInd);
        });
        if(loopingOn[channel].not && instrumentIsHolding[channel].not, {
            pythonOSCport.sendMsg("/padHit", channel, padSlot, startInd);
        });
    })
};
launchPadOnFunc = MIDIFunc.noteOn(launchPadButtonOn, nil, nil, launchPad.uid);

launchPadButtonOff = {|vel, note, chan, port|
    var chanAndStartInd = launchPadToChanelAndStartInd[note];
    if(chanAndStartInd.isNil.not, {
        var channel = chanAndStartInd[0];
        var startInd = chanAndStartInd[1];
        var padSlot = selectedPadPerInst[channel];
        var padInd = padSlot*4 + channel; //this gives the padInd
        ["off hanlder", note, isPadNote.(note), heldDownPads].postln;
        if(heldDownPads.includes(padInd), {
            metronomeClocks[channel].clear;
            notesOn[channel].do({|i| midiOut.noteOff(channel, i)});
            notesOn[channel].clear;
            heldDownPads.remove(padInd);
            ["hold-down OFF", padInd].postln;
        });
    })
};
launchpadOffFunc = MIDIFunc.noteOff(launchPadButtonOff, nil, nil, launchPad.uid);
//------------------end code to handle launchpad triggering ---------------------


/*
 -------------------------------------------------------------------------------------
TODO: - need a way to stop a looping melody without starting a new one
      - can we move to a model where mini state UI hanlders don't access any properties not in minStates?
         - can we remove all state information not related to a miniState from the model?
         - moving close to the design that what is on the ipad only defines "musical closures"
           and all performative state is controlled by the pad


-startInd and multiTranspose working, but need to fine tune the separator space for the sliders
-also need to do lights for the multi transpose
-fix lights for when you stop playing a loop
-need to test pad recording with hold-down mode and looping mode

*/

clockFuncGenerator = {|i|
	{
		var returnVal;
        var j = selectedPadPerInst[i];
		if(loopingOn[i].not && heldDownPads.includes(4*j + i).not && lastBeats[i],
			{
				lastBeats[i] = false;
				returnVal = nil;
				("lastBeat cutoff" + i + " " + j).postln;
			},
			{
				lastHits[i] = SystemClock.beats;
				pythonOSCport.sendMsg("/played-"++i, i, j);
				("beat" + i + " " + beats[i]).postln;
				returnVal = beats[i] * (1/ beatMods[i]) * 0.25;
		});

		returnVal
	}
};

//Quneo noteon
a = {|vel, note, chan, port|
	if(isPadNote.(note), {
		var xVal = noteToXY.(note)[0];
		var yVal = noteToXY.(note)[1];
		var padInd = noteToInd.(note);
		"padOn".postln;
		//reset everything about that instrument
		//turn off all lights on pad

        //TODO Launchpad = check this commented out block
/*		lastBeats[xVal] = false;
		notesOn[xVal].do({|i| midiOut.noteOff(xVal, i)});
		notesOn[xVal].clear;*/
		//clear all lights in column
		((0..3)*4+xVal).do({|i|
			singlePlayPads.remove(i);
			heldDownPads.remove(i);
			quneoOut.noteOff(0, padIndToGreen[i], 127);
			quneoOut.noteOff(0, padIndToRed[i], 127);
            if((padInd == i) && loopingPads.includes(padInd), {}, {loopingPads.remove(i)});
		});


        if(loopingPads.includes(padInd), {
            "STOP LOOP".postln;
            metronomeClocks[xVal].clear;
            quneoOut.noteOn(0, padIndToGreen[padInd], 127);
        });
        selectedPadPerInst[xVal] = yVal;
        if(masterLoopingOn,{
            ((0..3)*4+xVal).do({|i|loopingPads.remove(i)});
            loopingPads.add(padInd);
            quneoOut.noteOn(0, padIndToGreen[padInd], 127);
            ["looping on", padInd].postln;
            loopingOn[xVal] = true;
            instrumentIsHolding[xVal] = false;
        });
        if(holdDownPlay, {
            loopingOn[xVal] = false;
            instrumentIsHolding[xVal] = true;
            quneoOut.noteOn(0, padIndToRed[padInd], 90);
            quneoOut.noteOn(0, padIndToGreen[padInd], 90);
            heldDownPads.add(padInd);
            ["hold-down on", padInd].postln;
            heldDownPads.postln;
        });
        if(masterLoopingOn.not && holdDownPlay.not, {
            loopingOn[xVal] = false;
            instrumentIsHolding[xVal] = false;
            singlePlayPads.add(padInd);
            quneoOut.noteOn(0, padIndToRed[padInd], 127);
            ["single-play on", padInd].postln;
        });

				//TODO: lighting stuff - turn on red if normal, green if loop, orange if holdDown
	});
	["SHOULD BE TAP TEMPO", note, tapTempo_BUTTON].postln;
	[note >= tapTempo_BUTTON, note <= tapTempo_BUTTON, note == tapTempo_BUTTON].postln;
	if(note == tapTempo_BUTTON, {
		var thisHit = TempoClock.default.beats;
		var beatDif = thisHit - lastTimeTapped;
		lastTimeTapped = thisHit;
		["tapTempo", 60*(1/beatDif)].postln;
		//TODO - send tap info to master clock
		if(TempoClock.default.beats2secs(beatDif) < 2, {masterClockOSCport.sendMsg("/uploadTempo", beatDif)});
	});
	//if "record" - clear the replayList, capture the loop-style settings, set replayRecord to true
};

padOn = MIDIFunc.noteOn(a, nil, nil, quneo.uid);

//Quneo noteoff
b = {|vel, note, chan, port|
	if(note == loop_BUTTON, {
		masterLoopingOn = masterLoopingOn.not;
		if(masterLoopingOn,
			{
				holdDownPlay = false;
				quneoOut.noteOff(0, hold_LIGHT, 127);
				quneoOut.noteOn(0, loop_LIGHT, 127);
			},
			{quneoOut.noteOff(0, loop_LIGHT, 127);}
		);
		//toggle lighting
	});
	if(note == hold_BUTTON, {
		holdDownPlay = holdDownPlay.not;
		if(holdDownPlay,
			{
				masterLoopingOn = false;
				quneoOut.noteOff(0, loop_LIGHT, 127);
				quneoOut.noteOn(0, hold_LIGHT, 127);
			},
			{quneoOut.noteOff(0, hold_LIGHT, 127);}
		);
		//toggle lighting
	});
};
padOff = MIDIFunc.noteOff(b, nil, nil, quneo.uid);

//Quneo cc
c = {|vel, note, chan, port|
	if((note < 10) && (note > 5), {
		if((transposeMap[vel]!= nil) && (transposePositions[note-6] != transposeMap[vel]), {
			transposePositions[note-6] = transposeMap[vel];
			pythonOSCport.sendMsg("/padTranspose", note-6, transposePositions[note-6] - 4); //from -4 to 4 tranpose
			quneoOut.control(0, note-5, vel); //todo: why 5 not 6?
		});
	});
	if(note == 10, {
		if((startPositionMap[vel] != nil) && (startPosition != startPositionMap[vel]), {
			startPosition = startPositionMap[vel];
			startPosition.postln;
		});
	});
};

ccHandler = MIDIFunc.cc(c, nil, nil, 2017846184);

//msg[1] is the instrument index for which to start the metronome
//msg[2] is the miniState index that is being played on the metronome
startMetronomeResponse = {|msg, time, addr, recvPort|
	("metronome started for" + msg[1]).postln;
	metronomeClocks[msg[1]].sched(0, clockFuncGenerator.(msg[1], msg[2]));
};
OSCFunc(startMetronomeResponse, "/startMetronome");

//msg[1] is the instrument index
//msg[2] is the miniState index that is being played on the metronome
lastBeatsHandler = {|msg, time, addr, recvPort|
	("lastBeat flag set" + msg[1]).postln;
	lastBeats[msg[1]] = true;
};
OSCFunc(lastBeatsHandler, "/lastBeats");

//msg[1] is the new BEAT DURATION (not tempo)
masterClockBeat = {|msg, time, addr, recvPort|
	(0..3).do({|i|
		if(loopStartFunctions[i] != nil, {
			loopStartFunctions[i].();
			loopStartFunctions[i] = nil;
		})
	});
	//"SKIPSTEP BEAT".postln;
};
OSCFunc(masterClockBeat, "/masterClockBeat");

//msg[1] is the new BEAT DURATION (not tempo)
masterClockTempoHandler = {|msg, time, addr, recvPort|
	(0..3).do({|i| metronomeClocks[i].tempo = 1/msg[1].asFloat})
};
OSCFunc(masterClockTempoHandler, "/masterClockTempo");


//--------------------------------set up playChord hanlder--------------------------------
//msg[1] is an index for which gridState the message is from
//msg[2] is either "normal", "on", or "off" - specifying a piano vs non-piano play
//msg[3] is a int (1 or 0) indicating whether the play is a stepjump play or not
//msg[4] is a int corresopnding to the index this chord is in the sequence
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;
playChordParamNum = 5; //start index of where the chord notes start in the OSC message

playHandler = {|msg, time, addr, recvPort|
	if (msg[2] == 'normal',
		{
            launchpadOut.noteOn(0, lastColoredIndPad[msg[1]], color1[msg[1]]);
            launchpadOut.noteOn(0, channelAndStartIndToPad.(msg[1], msg[4]), color2[msg[1]]);
            lastColoredIndPad[msg[1]] = channelAndStartIndToPad.(msg[1], msg[4]);
			//TODO: set lastHits[i] flag if needed
			if (msg[3] == 1,
				{
					chordDur = beats[msg[1]] - (SystemClock.beats-lastHits[msg[1]]) - 0.005;
					("stepjump duration is" + chordDur).postln;
				},
				{chordDur = 0.25*beats[msg[1]]-0.005}
			);
			Task({
				//TODO: add onNotes tracking
				msg[playChordParamNum..].do({|i|
                    if(i > 0, {
                        midiOut.noteOn(msg[1], i);
                        notesOn[msg[1]].add(i);
                    });
				});/*hit noteOn messages*/
				chordDur.wait; /*wait for beat*/
				msg[playChordParamNum..].do({|i|
                    if(i > 0, {
                        midiOut.noteOff(msg[1], i);
                        notesOn[msg[1]].remove(i);
                    });
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


