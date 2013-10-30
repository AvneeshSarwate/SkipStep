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
------------------------------------------------------
got piano mode mostly working (some problems when swiping across keys)

can generally fix problems by removing extra threads hanging around in chuck
------------------------------------------------------
fixed major threading problems for piano mode   
------------------------------------------------------
added (none tested): 
scale definer code, no UI

compare view code, no UI

timer thread added in backend 

----------------------------
added UI for arranger view (including noise and refresh mode)
--no code written
_________________________

fixed timer thread

----------------

added grid shifting and reverse direction looping
LANdini code added to backend but not tested 
grid send/recieve ui roughly put together
______________________________________

LANdini working for stepping with 1 instance/computer
- for sending grids: simple solution:
	create custom toString/from string methods for grid/context and send it
	alternatively, figure out how to serialize objects, or use OSC bundles

BUGS   
- very jumpy stepping, reverse mode not activiting as fast as desired 
- when swiping across keys in piano mode, chuck threading/midi handled badly
	partially fixed by calling instead of sporking on/off readers in chuck
		still latency issues - not sure if code or hardware/network
- piano mode on/off acts weird (ex starting in on position and going to off)
- ?????? - SUBSET BROKEN - hasn't been well replicated
- still some issues with UI being thrown out of sync w/ internal grid
	double check threading
- sometimes UI actions not reaching python 
	problem in python or just UDP messages failing sometimes?
- noise being applied on 14th column, not first (sort of fixed)
- optimize as much as possible 
-------
TODO:
- LANdini for coordinated stepping 
- save/Load of main grid (coded but no ui or teting)
- custom scale definer (partially done) 
- slider for tempo control
- comparison view - have one grid under another, bottom grid is same as current playing
	grid and uneditable, editable grid goes on top 
- optimize UI updating so OSC messages only sent for grid elements that are diff
	(precalculate diff grid: each element is -1 if same, or value of new grid if no
