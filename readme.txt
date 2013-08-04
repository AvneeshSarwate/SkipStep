basic looping mechanism working - start chuck, then python
chord/prog play properly with MIDI
python handles callbacks for grid correctly 
BASIC STEP SEQUENCER WORKS (maybe latency/timing issues regarding locks?)


Next steps
test stopping
test morph function



BUG (FIXED WITH MINIAUDICLE UPDATE) - 
after certain amount of loop iterations, 
playing a phrase no longer plays audio on ableton
even though ableton registers midi coming in, no audio.
restarting chuck VM temporarily fixes this. 
not sure if ableton or chuck problem. 

----------------------------------------------------

basic grid "noise" function working
on every loop iteration, grid flips on average k squares.

----------------------------------------------------
step indicator and "step jumping" working

noise on/off button, clear grid button working

added grid copy function

column subset looping working (with small bug)

modularity improvements (wrapper for cleanliness):
	create play(i) function - plays ith chord/column
	method to translate touchOSC indicies into grid indicies
	
for "column subset looping" - maintin list of selected column indicies
	iterate over that list (no need for new progression)

BUGS 
- still some issues with UI being thrown out of sync w/ internal grid
	double check threading
- when switching from subset to full looping, not going to correct column on transition

MORE FEATURES to implement
- back button
- reverse looping
----------------------------------------------
FIXED
- transition between normal and collumn subset looping

BUG
- when jumping between columns on collumn subset mode, doesn't exactly work right