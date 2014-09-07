/*the “chord” class that encapsulates the information
of a chord/SkipStep-column coming on osc and being sent out by python
*/
public class chord{
    int notes[];
    public void setNotes(int a[]) {
        int temp[a.size()];
        for(0 => int i; i < a.size(); i++) {
            a[i] => temp[i];
        }
        temp @=> notes;
    }
    public int size() {
        return notes.size();
    }    
}


MidiOut mout;
MidiMsg msg;
// check if port is open
if( !mout.open( 0 ) ) me.exit();

// fill the message with data
144 => msg.data1;
52 => msg.data2;
100 => msg.data3;
// bugs after this point can be sent
// to the manufacturer of your synth

fun void midOn(int note, int chan){
    144 + chan => msg.data1;
    note => msg.data2;
    100 => msg.data3;
    mout.send( msg );
}

fun void midOff(int note, int chan){
    128 + chan => msg.data1;
    note => msg.data2;
    100 => msg.data3;
    mout.send( msg );
}


60 => int note;


/*
this block sets up the OSC reciever that recieves the chord data
*/
// create our OSC receiver
OscRecv recv;
// use port 6449
6449 => recv.port;
// start listening (launch thread)
recv.listen();
//sets up the data structures fro
4 => int numInstruments;
OscEvent nums[numInstruments];
OscEvent objLen[numInstruments];

/*
sets up the data structures for recieving chord data 
item on the ith channel sends infomration to address
“objLeni” and “numsi” 
*/
for(0 => int i; i < numInstruments; i++) {
    recv.event("nums" + i + ", i") @=> nums[i];
}
for(0 => int i; i < numInstruments; i++) {
    recv.event("objLen" + i + ", i") @=> objLen[i];
}
// create an addresses in the receiver, store in new variable
recv.event( "/print, f" ) @=> OscEvent oe;
recv.event("start, s") @=> OscEvent start;
recv.event("type, s") @=> OscEvent type;
recv.event("objs, i") @=> OscEvent objs;

Flute f => dac;

10 => int nInst;
Mandolin m[nInst];
Gain g => dac;
1.0/nInst => g.gain;
for(0 => int i; i < nInst; i++) {
    m[i] => g;
}


//time constants: slowest time possible and cutoff length
2::second => dur slowest;
.01::second => dur split;
//duration of a measure
dur measure[numInstruments];
for(0 => int i; i < numInstruments; i++) {
    3::second => measure[i]; }




// IGNORE
//50506 => int port; //LANDINI
//conf.startMsg("/send/GD, s, s, s"); LANDINI
//"all" => conf.addString; LANDINI
//"/played" => conf.addString; LANDINI

/*
this block sets up the tap tempo listener  
*/

recv.event("/touch, s") @=> OscEvent touchEv;

    
fun void modifyTempo(int channel, dur tempo)
 {
     tempo @=> measure[channel];
     <<< tempo >>>;
 }
 
 48 @=> int ASCII_0;
 49 @=> int ASCII_1;
 
 fun void touchTempo(){
     now => time newT;
     now => time oldT;
     dur tempo;
     while(true){
         <<<"                  starting touch thread">>>;
         touchEv => now;
         <<< now, newT, oldT>>>;
         <<<"                                   got a touch event">>>;
         if(touchEv.nextMsg() != 0) {
             touchEv.getString() @=> string channel_vec;
             <<< channel_vec >>>; 
             now => newT;
             <<< now, newT, oldT>>>;
             if((newT - oldT) < slowest){
                 newT - oldT => tempo;
                 //<<< 555, tempo >>>; 
                 for (0 => int i;i!=numInstruments;++i)
                 {
                     if (channel_vec.charAt(i) == ASCII_1){
                         modifyTempo(i,tempo);
                     }
                 }
             }
             newT => oldT;
             
             
             
         }
     }   
 }
 
 spork~ touchTempo();
 //<<<"touch tempo sporked">>>;
 
 fun void sporkTest() {
     while(true) {
         1::second => now;
         //<<< 5555 >>>; 
     }
 }
 
 
 /*
 this block sets up the metronome that sends messages to python 
 */
 OscSend conf;
 "127.0.0.1" => string hostname;
 5174 => int port;
 conf.setHost( hostname, port );
 conf.startMsg("/played, s");
 "played0" => conf.addString;
 
 fun void timer(int i){
     while(true) {
         .25 * measure[i] => now;
         conf.startMsg("/played-" + (i+1) + ", s");
         "  " => conf.addString;
         //<<< "          " , "/played-" + (i+1)  >>>;
     }
 }
 
 //starts all the metronomes
 for(0 => int i; i < numInstruments; i++) {
     spork~ timer(i); }
     
     
     //reads in the chord info for a chord to be played (non piano)
     0 => int chordNum;
     fun void readOSCChord(OscEvent start, OscEvent nums, int n, Mandolin m[], dur measure, int chan) {
         ////<<<n>>>;
         ////<<<chordNum + "chordNum">>>;
         chordNum++;
         int notes[n];
         0 => int broken;
         for(0 => int i; i < n; i++) {
             nums => now;
             ////<<<"readnote", chan>>>;
             nums.nextMsg();
             nums.getInt() => notes[i];
             ////<<< notes[i] >>>;
             if(notes[i] == 0) {
                 //<<<"OSC message failure (read)">>>;
                 1 => broken;
                 //return; //better than break?
                 //break;
             }
         }
         if(broken == 1) return;
         chord c;
         c.setNotes(notes);
         ////<<<"yo chord", chan>>>;
         playChord(m, c, measure, chan);
     }
     
     
     //chord reading function used by readAndToggle()  (this is bad design)
     fun chord readOSCChord2(OscEvent start, OscEvent nums, int n) {
         ////<<<n>>>;
         int notes[n];
         0 => int broken;
         for(0 => int i; i < n; i++) {
             nums => now;
             nums.nextMsg();
             nums.getInt() => notes[i];
             //<<<"                   ", notes[i]>>>;
             if(notes[i] == 0) {
                 //<<<"OSC message failure (read)">>>;
                 1 => broken;
                 //return; //better than break?
                 //break;
             }
         }
         if(broken == 1) return null;
         chord c;
         c.setNotes(notes);
         ////<<<"yo chord">>>;
         return c;
     }
     
     //read the incoming chord data from a piano key event 
     fun void readAndToggle(OscEvent start, OscEvent nums, int n, int on, int chan){
         //<<<"starting to read toggle chord">>>;
         readOSCChord2(start, nums, n) @=> chord c;
         if(c == null) return;
         //<<<"len read chord", c.size()>>>;
         for(0 => int i; i < c.size(); i++) {
             ////<<<"toggle notes ", c.notes[i]>>>;
         }
         chordToggle(c, on, chan);
     }
     
     // function that plays/stops a chord based on piano key input
     fun void chordToggle(chord c, int on, int chan) {
         ////<<<"oi chord">>>;
         c.size() => int len;
         if(c.notes[0] == -1) {
             return;
         }
         
         for(0 => int i; i < len; i++) {
             if(c.notes[i] == 0) {
                 //<<<"OSC message failure (play)">>>;
                 return; //better than break?
                 break;
             } 
             //spork ~ miniPlay(Std.mtof(c.notes[i]), measure, m[i]);
             if(on == 1){
                 midOn(c.notes[i], chan);
                 //<<<"on", c.notes[i]>>>;
             }
             else{
                 midOff(c.notes[i], chan);
                 //<<<"off", c.notes[i]>>>;
             }
         }   
     }
     
     //plays a chord (sends midi information to the DAW
     fun void playChord(Mandolin m[], chord c, dur measure, int chan) {
         ////<<<"oi chord">>>;
         c.size() => int len;
         if(c.notes[0] == -1) {
             .25 * measure => now;
             ////<<<"chord rest channel", chan >>>;
             //conf.startMsg("/played", "s");
             //"played0" => conf.addString;
             return;
         }
         
         for(0 => int i; i < len; i++) {
             if(c.notes[i] == 0) {
                 //<<<"OSC message failure (play)">>>;
                 return; //better than break?
                 break;
             } 
             //spork ~ miniPlay(Std.mtof(c.notes[i]), measure, m[i]);
             midOn(c.notes[i], chan);
             ////<<<c.notes[i], "chan ", chan>>>;
         }   
         .25*measure - split=> now;
         for(0 => int i; i < len; i++) {
             midOff(c.notes[i], chan);
         }
         //conf.startMsg("/played", "s");
         //"played0" => conf.addString;
         ////<<<"function played chord">>>;
     }
     
     // infinite event loop that listenes for incoming chord data 
     while ( true )
     {
         // wait for the start event to arrive
         //oe => now;
         start => now;
         while(start.nextMsg() != 0) {
             
             
             start.getString() => string a;
             ////<<<a>>>;
             objs => now; 
             objs.nextMsg();
             objs.getInt() => int i;//get the channel to play the chord on 
             
             //get the type of the 
             type => now;
             type.nextMsg();
             type.getString() => string mtype;
             ////<<<"mtype is", mtype, " channel is ", i>>>;
             if(mtype == "skip") {
                 //<<<"about to skip">>>;
                 continue;
             }
             objLen[i] => now;
             ////<<<"got length", i>>>;
             objLen[i].nextMsg();
             objLen[i].getInt() => int n;
             
             //if the chord is a normal chord, read and play
             if(mtype == "chord") {
                 spork~ readOSCChord(start, nums[i], n, m, measure[i], i);
                 ////<<< i >>>;
             }
             
             //if the chord is from a piano key press, read and toggle it
             if(mtype == "on") {
                 //<<<"pre read toggle ON">>>;
                 readAndToggle(start, nums[i], n, 1, i);
                 //<<<"             ON">>>;
             }
             if(mtype == "off") {
                 //<<<"pre read toggle OFF">>>;
                 readAndToggle(start, nums[i], n, 0, i);
                 //<<<"             OFF">>>;
        }
    }
}
