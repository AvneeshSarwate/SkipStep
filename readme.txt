
SkipStep is a step sequencer influenced musical tool for algorithmic composition and live performance. 


--------------------------------------------------
                   PAPER
--------------------------------------------------
The ICMC paper about SkipStep is saved in this repository as the file SkipStep_ICMC.pdf (includes pictures)
It describes the motivation and design principles behind SkipStep
- NOTE: this paper is missing features built since April 2014


---------------------------------------------------
                   VIDEOS
---------------------------------------------------
A quick video showing SkipStep in action (30 sec): 
https://www.dropbox.com/s/a365qh0hxx4nbhh/SkipStep_Live_Clips.m4v?dl=0 

A video demonstrating the algorithms currently available in SkipStep (4:30):
https://www.dropbox.com/s/83q0uiwms04s1dy/SkipStepDemo1.mov?dl=0

An example of how the algorithms can take a static loop and make dynamic (2 min):
https://www.dropbox.com/s/cqe1ah4k9q5gwch/SkipStepDemo2.mov?dl=0

A networked performance using SkipStep, performed by the Princeton Laptop Orchestra (10 min):
http://vimeo.com/99373121

(NEW) - An improvised jam showcasing some new SkipStep features
https://www.dropbox.com/s/a9bts3u4mtg2v73/SkipStep%20Demo%202015%20lite.m4v?dl=0




---------------------------------------------------
MORE DOCS AND INSTALLATION INSTRUCTIONS COMING SOON
---------------------------------------------------

A brief overview of the code structure (more documentation coming soon):

I. Software Components
 
	The iPad interface for SkipStep was built using TouchOSC, an app for the iPad that allows you to build UIs in a graphical editor by dragging and dropping UI widgets onto a screen. The logic is run on a laptop, and the iPad and laptop communicate via Wi-Fi using the OSC protocol. The logic was written in Python, and SuperCollider was used to control timing and to send MIDI messages to a DAW, which was used to synthesize the sound. Python and SuperCollider communicated via OSC, using the pyOSC library. 
	SkipStep has a multi-user mode where users can send melodies to each other. LANdini, a networking utility by Jascha Narveson, was used when multiple SkipStep instances were run coordinated in multi-play mode. LANdini simplifies the sending of OSC messages between multiple users on the same Wi-Fi network. LANdini instances also communicate via OSC. Diagrams of the information flow for single-user (Single_User_Data_Flow.png) and multi-user setups (Multi_User_Data_Flow.png) are included in this repository. 

II. Main code areas
 
	The “Looper” class defines an object that represents all the data for a single “instrument” in SkipStep, while the “MultiLoop” class defines a single instance of SkipStep. The setup of the SkipStep instance occurs in the “__init__” function in the MultiLoop class. 
	The SuperCollider backend acts, among other things, as a metronome for SkipStep. SuperCollider sends a metronome tick via OSC message to the Python script, where a handler function called “realPlay” handles the logic for what occurs at each step. If, after the initial setup, no UI elements are touched, realPlay() is the only function in the Python script that is ever called. After reading the comments in the Looper class and in MultiLoop.__init__(), this is the "entry point" for SkipStep's execution and the best place to start reading the code. 
	Most of the functions in the MultiLoop class are handlers for UI controls. Whether a function is a handler or not will be indicated in the function comments. Most of the functionality of SkipStep occurs through the logic in the UI control handlers and their helper functions. 



LANdini: http://jaschanarveson.com/pages/code.html
pyOSC: https://trac.v2.nl/wiki/pyOSC
SuperCollider: http://supercollider.sourceforge.net/






