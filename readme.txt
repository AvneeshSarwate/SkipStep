---------------------------------------------------
MORE DOCS AND INSTALLATION INSTRUCTIONS COMING SOON
---------------------------------------------------


SkipStep is a step sequencer influenced musical tool for algorithmic composition and live performance. 

A quick video showing SkipStep in action: 
	https://www.dropbox.com/s/a365qh0hxx4nbhh/SkipStep_Live_Clips.m4v?dl=0 

The ICMC paper about SkipStep is saved as the file SkipStep_ICMC.pdf 
- NOTE: this paper does not document the newly added “scene” and “offline-edit” features




 
A brief overview of the code structure (more documentation coming soon):

I. Software Components
 
	The iPad interface for SkipStep was built using TouchOSC, an app for the iPad that allows you to build UIs in a graphical editor by dragging and dropping UI widgets onto a screen. The logic is run on a laptop, and the iPad and the iPad and laptop communicate via Wi-Fi using the OSC protocol. The logic was written in Python, and ChucK was used to control timing and to send MIDI messages to a DAW, which was used to synthesize the sound. Python and ChucK communicated via OSC, using the pyOSC library. 
	SkipStep has a multi-user mode where users can send melodies to each other. LANdini, a networking utility by Jascha Narveson, was used when multiple SkipStep instances were run coordinated in multi-play mode. LANdini simplifies the sending of OSC messages between multiple users on the same Wi-Fi network. LANdini instances also communicate via OSC. Diagrams of the information flow for single-user (Single_User_Data_Flow.png) and multi-user setups (Multi_User_Data_Flow.png) are included in this repository. 

II. Main code areas
 
	The “Looper” class defines an object that represents all the data for a single “instrument” in SkipStep, while the “MultiLoop” class defines a single instance of SkipStep. The setup of the SkipStep instance occurs in the “__init__” function in the MultiLoop class. 
	The ChucK backend acts, among other things, as a metronome for SkipStep. ChucK sends and OSC message to the Python script, where a handler function called “realPlay” handles the logic for what occurs at each step. If, after the initial setup, no UI elements are touched, realPlay() is the only function in the Python script that is ever called. After reading the comments in the Looper class and in MultiLoop.__init__(), this is the place to start reading the code. 
	The “phrase.play” function is used to to send information from Python to ChucK, where it is converted to MIDI and forwarded to the MIDI instrument. 
	Most of the functions in the MultiLoop class are handlers for UI controls. Whether a function is a handler or not will be indicated in the function comments. 



LANdini can be found here: http://jaschanarveson.com/pages/code.html






