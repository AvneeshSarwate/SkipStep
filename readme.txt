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

MORE FEATURES to implement
- back button
- reverse looping
----------------------------------------------
FIXED
- transition between normal and collumn subset looping
_________________________________________________

variable noise implemented

save/load grids implemented

--------
SHOULD PIANO GRID BE EDITABLE AND SHOULD CHANGES PUSH TO MAIN GRID
	option to toggle updating on/off?
	For now - "going to piano mode" sends main grid to piano screen
		but piano screen not pushed to main grid (can have button to do that)

writen, but with no UI and not tested: 
	refresh mode
	piano mode
------------------------------------------------------
refresh implemented

seemingly fixed bug with jumping, but broke subsets
------------------------------------------------------
implemented save/load of main grid (no UI, no testing)

BUGS
- SUBSET BROKEN
- still some issues with UI being thrown out of sync w/ internal grid
	double check threading
- noise being applied on 14th column, not first (sort of fixed)
- optimize as much as possible 
-------
TODO:
- save/Load of main grid (coded but no ui or teting)
- piano mode (coded not tested):
	replace step position selectors with buttons
	create playOn and playOff code modeling phrase.play and LooperBackend
- comparison view - have one grid under another, bottom grid is same as current playing
	grid and uneditable, editable grid goes on top 
- optimize UI updating so OSC messages only sent for grid elements that are diff
	(precalculate diff grid: each element is -1 if same, or value of new grid if no
