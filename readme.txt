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

basic grid sending working, need to change "recipient" in sendGrid()
only tested with 1 instance/computer 
______________________________________

Game of life simulator written but not tested
blend function written but not tested (and no UI)
_________________________________________________

multi looping code written, not tested
extra/unused functions need to be removed 
_______________________________

pianoprog variable added to Looper, needs to be added to MultiLoop
cleaned up variable usage for different grid/prog objects
cleaned up usage of self.pullupgrid()
cleaned up usage of assign2

basic grid sending/recieving/"applying" of grid and scale tested on one device 
	send/recieve loop thru landini, sending to "all" - should work for multiple 

____________________________
clear button and save/pullup of grid/scale pairs implemented but not tested
____________________________

clear button, save/pullup if grid/scale pairs, save/load of files for "sets",
and multi-computer grid sending all tested 
*didn't test sending diff scales, but it should work



for multi instrument looping:
	create a gridState class that holds all data for a grid/state
	create a MultiLoop class that contains several gridState instances
	each UI element type will exist on multiple pages (ex "/1/colsub/1/1", "/2colsub/1/1")
	all ui elements/addresses of same type will map to a single callback
	the callback parses which index element it is, and acts on that indexed gridState
	single callback coordinates stepping over all gridStates
	instead of "realPlay", the function finds the chord to play for each gridState
		use multi-object playing functionality of phrase.play to play all at once
	what it looks like in the code:
		callback assignment inside a loop to account for multiple pages
		callback functions act on gridState[index] instead of self
		realPlay returns a deep copy of the chords to be played (other side effects happen as normal)
		
	
Working feature list: 
	- SAVE/LOAD - grid/scale for active and all saved grids
	- make live-grid saving also save scale
	- changing root note via up/down buttons with toggle on
	- GRID SHARING
	- multi scale interface
	- grid blending
	- undo button, undoes single touches, grid changes, scale changes
	- game of life step changing
	- smart randomization
	- MULTI INSTRUMENT LOOPING

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
- save/Load of main grid (coded but no ui or teting)
- slider for tempo control
- comparison view - have one grid under another, bottom grid is same as current playing
	grid and uneditable, editable grid goes on top 
- optimize UI updating so OSC messages only sent for grid elements that are diff
	(precalculate diff grid: each element is -1 if same, or value of new grid if no
	
	
BIG IDEA FOR NATIVE: let users scale up complexity of interface themselves.
Max Flexibility: let users chose what features they want and lay out their
	controls in a maner similar to touchOSC
for simple learning and introduction:	
start them with a simple step sequencers, and keep +/- buttons in the bottom corner
+ adds a random control widget to the screen, - removes the last one added
the app smartly packs them
let users flip between random "pages" of set up controls (could be a handmade set)
users could share their setups 
--this flexibility allows you to create many "non core" widgets/features
	that aren't forced onto the user 
"Non heirarchial structure"