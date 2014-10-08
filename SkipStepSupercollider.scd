(
var n, beats, oldTap, newTap, tapLim, tempoClocks, oscMetronomeHit, netAd, midiOut, playHandler, tapTempoHandler, tempoChangeHandler, tempoSyncHandler, lastHits;
n = 4; //set n - number of instruments

/*----------------create n tempo clocks (and associated beat variables?)----------------
When tap-tempoing:
1. either adjust the .tempo of the tempoClocks and reschedule them every .25 beats,
2. or leave the tempo of the tempoClocks at 1 and reschedule them every beats[i]*0.25,
    where beats[i] is changed by the tap tempo
*/
tempoClocks = Array.fill(n, TempoClock.new(1)); //currently using option 2


//----------------create old/new time variables for touch tempo -------------------
oldTap = 0;
newTap = 0;
tapLim = 2;
beats = Array.fill(n, {0.7}); //create n beats
lastHits = Array.fill(n, {0});


//------------------set up tempoClocks to send metronome hits via OSC ---------------------
netAd = NetAddr("localhost", 5174);
oscMetronomeHit = {
	|i| lastHits[i-1] = SystemClock.beats;
	netAd.sendMsg("/played-"++i, i);
};
(0..(n-1)).do(
	{|i| tempoClocks[i].sched(0, {
		oscMetronomeHit.value(i+1); //i+1 in .value() is a hack to get around a small unknown bug
		beats[i]*0.25/*0.25*/})}
);


//--------------------------------set up playChord hanlder--------------------------------
MIDIClient.init;
midiOut = MIDIOut.newByName("IAC Driver", "Bus 1");
midiOut.latency = 0;

playHandler = {|msg, time, addr, recvPort|
	if (msg[2] == 'normal',
		{
			Task({
				msg[3..].do({|i| midiOut.noteOn(msg[1], i)});/*hit noteOn messages*/
				(0.25*beats[msg[1]]).wait; /*wait for beat*/
				msg[3..].do({|i| midiOut.noteOff(msg[1], i)}); /*hit noteOff messages*/
			}).play;
		},
		{
			if (msg[2] == 'on',
				{msg[3..].do({|i| midiOut.noteOn(msg[1], i)}); /*noteon messages*/},
				{msg[3..].do({|i| midiOut.noteOff(msg[1], i)}); /*noteoff messages*/}
			)
		}
	)
};

OSCFunc(playHandler, "/playChord");


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
						("pause" + ((beats[msg[3]]*0.25) - (SystemClock.beats - lastHits[msg[3]]))).postln;
						beats[msg[3]].postln;
					(SystemClock.beats - lastHits[msg[3]]).postln;
						tempoClocks[i].sched((beats[msg[3]]*0.25) - (SystemClock.beats - lastHits[msg[3]]),
							{oscMetronomeHit.value(i+1); beats[i]*0.25/*0.25*/})
				});
			}
		)}
	);
};

OSCFunc(tempoSyncHandler, "/tempoSync");

)


















//------------------- templates and testing - final version above ------------

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


