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



// create our OSC receiver
OscRecv recv;
// use port 6449
6449 => recv.port;
// start listening (launch thread)
recv.listen();

5 => int maxMultiplay;
OscEvent nums[maxMultiplay];
OscEvent objLen[maxMultiplay];

for(0 => int i; i < maxMultiplay; i++) {
    recv.event("nums" + i + ", i") @=> nums[i];
}
for(0 => int i; i < maxMultiplay; i++) {
    recv.event("objLen" + i + ", i") @=> objLen[i];
}

// create an address in the receiver, store in new variable
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

dur whole[maxMultiplay];
for(0 => int i; i < maxMultiplay; i++) {
    1::second => whole[i];
}
2::second => dur slowest;
.01::second => dur split;



// host name and port

//50506 => int port; //LANDINI
// send object

// aim the transmitter


//conf.startMsg("/send/GD, s, s, s"); LANDINI
//"all" => conf.addString; LANDINI
//"/played" => conf.addString; LANDINI

OscRecv recvTempo;
// use port 6449
5678 => recvTempo.port;
// start listening (launch thread)
recvTempo.listen();

recv.event("/touch, s") @=> OscEvent touchEv;

fun void touchTempo(){
    now => time newT;
    now => time oldT;
    while(true){
        <<<"                  starting thread">>>;
        touchEv => now;
        <<<"                                   got a touch event">>>;
        while(touchEv.nextMsg() != 0) {
            now => newT;
            if((newT - oldT) < slowest){
                newT - oldT => whole[0];
            }
            newT => oldT;
        }
    }   
}


spork~ touchTempo();
<<<"touch tempo sporked">>>;

OscSend confLANdini;
confLANdini.setHost( "127.0.0.1", 50506 );
"all" => confLANdini.addString;
"/played" => confLANdini.addString;
"played0" => confLANdini.addString;
0 => int track; //decide what you want to do with this
now => time old;
now => time nu;
fun void timerLANdini(int n){
    while(true) {
        //1 => m[0].noteOn;
        .25 * whole[n] => now;
        now => nu;
        confLANdini.startMsg("/send/GD, s, s, i");
        "all" => confLANdini.addString;
        "/" + (n+1) + "/played" => confLANdini.addString;
         track => confLANdini.addInt;
        //<<<"                  step", nu-old, track>>>;
        nu => old;
        track++;
        track %16 => track;
        
    }
}


//for multi loop, send over multiple ports
OscSend conf;
"127.0.0.1" => string hostname;
5174 => int port;
conf.setHost( hostname, port );
conf.startMsg("/played, s");
"played0" => conf.addString;

fun void timer(int n){
    while(true) {
        .25 * whole[n] => now;
        conf.startMsg("/" + (n+1) + "/played, i");
        track => conf.addInt;
//        <<<"                  step">>>;
    }
}

0 => int chordNum;
fun void readOSCChord(OscEvent start, OscEvent nums, int n, Mandolin m[], dur whole, int chan) {
    //<<<n>>>;
    //<<<chordNum + "chordNum">>>;
    chordNum++;
    int notes[n];
    0 => int broken;
    for(0 => int i; i < n; i++) {
        nums => now;
        //<<<"readnote", chan>>>;
        nums.nextMsg();
        nums.getInt() => notes[i];
        if(notes[i] == 0) {
            <<<"OSC message failure (read)">>>;
            1 => broken;
            //return; //better than break?
            //break;
        }
    }
    if(broken == 1) return;
    chord c;
    c.setNotes(notes);
    //<<<"yo chord", chan>>>;
    playChord(m, c, whole, chan);
}

fun chord readOSCChord2(OscEvent start, OscEvent nums, int n) {
    //<<<n>>>;
    int notes[n];
    0 => int broken;
    for(0 => int i; i < n; i++) {
        nums => now;
        nums.nextMsg();
        nums.getInt() => notes[i];
        <<<"                   ", notes[i]>>>;
        if(notes[i] == 0) {
            <<<"OSC message failure (read)">>>;
            1 => broken;
            //return; //better than break?
            //break;
        }
    }
    if(broken == 1) return null;
    chord c;
    c.setNotes(notes);
    //<<<"yo chord">>>;
    return c;
}

fun void readAndToggle(OscEvent start, OscEvent nums, int n, int on, int chan){
    <<<"starting to read toggle chord">>>;
    readOSCChord2(start, nums, n) @=> chord c;
    if(c == null) return;
    <<<"len read chord", c.size()>>>;
    for(0 => int i; i < c.size(); i++) {
        //<<<"toggle notes ", c.notes[i]>>>;
    }
    chordToggle(c, on, chan);
}

fun void chordToggle(chord c, int on, int chan) {
    //<<<"oi chord">>>;
    c.size() => int len;
    if(c.notes[0] == -1) {
        /*.25 * whole => now;
        <<<"chord rest">>>;
        conf.startMsg("/played", "s");
        "played0" => conf.addString;*/
        return;
    }
    
    for(0 => int i; i < len; i++) {
        if(c.notes[i] == 0) {
            <<<"OSC message failure (play)">>>;
            return; //better than break?
            break;
        } 
        //spork ~ miniPlay(Std.mtof(c.notes[i]), whole, m[i]);
        if(on == 1){
            midOn(c.notes[i], chan);
            <<<"on", c.notes[i]>>>;
        }
        else{
            midOff(c.notes[i], chan);
            <<<"off", c.notes[i]>>>;
        }
    }   
    /*.25*whole => now;
    for(0 => int i; i < len; i++) {
        midOff(c.notes[i]);
    }
    conf.startMsg("/played", "s");
    "played0" => conf.addString;
    <<<"function played chord">>>;*/
}




fun void playChord(Mandolin m[], chord c, dur whole, int chan) {
    //<<<"oi chord">>>;
    c.size() => int len;
    if(c.notes[0] == -1) {
        .25 * whole => now;
        <<<"chord rest channel", chan >>>;
        //conf.startMsg("/played", "s");
        //"played0" => conf.addString;
        return;
    }
    
    for(0 => int i; i < len; i++) {
        if(c.notes[i] == 0) {
            <<<"OSC message failure (play)">>>;
            return; //better than break?
            break;
        } 
        //spork ~ miniPlay(Std.mtof(c.notes[i]), whole, m[i]);
        midOn(c.notes[i], chan);
        <<<c.notes[i], "chan", chan>>>;
    }   
    .25*whole - split=> now;
    for(0 => int i; i < len; i++) {
        midOff(c.notes[i], chan);
    }
    //conf.startMsg("/played", "s");
    //"played0" => conf.addString;
    //<<<"function played chord">>>;
}

for(0 => int i; i < 3; i++) {
    spork~ timer(i);
}

// infinite event loop
while ( true )
{
    // wait for event to arrive
    //oe => now;
    start => now;
    while(start.nextMsg() != 0) {
        
        
        start.getString() => string a;
        //<<<a>>>;
        objs => now; 
        objs.nextMsg();
        objs.getInt() => int i;//nobj;
        //for(0=>int i; i < nobj; i++){ //for multiloop, nobj is looper index, and instead of for loop, directly index by nobj
            type => now;
            type.nextMsg();
            type.getString() => string mtype;
            //<<<"mtype is", mtype, " channel is ", i>>>;
            if(mtype == "skip") {
                <<<"about to skip">>>;
                continue;
            }
            if(mtype == "skip") {
                <<<"SHOULD NOT SEE THIS">>>;
                continue;
            }
            objLen[i] => now;
            //<<<"got length", i>>>;
            objLen[i].nextMsg();
            objLen[i].getInt() => int n;
            if(mtype == "chord") {
                spork~ readOSCChord(start, nums[i], n, m, whole[n], i);
            }
            //<<<"before problematic conditional">>>;
            if(mtype == "on") {
                <<<"pre read toggle ON">>>;
                readAndToggle(start, nums[i], n, 1, i);
                <<<"             ON">>>;
            }
            if(mtype == "off") {
                <<<"pre read toggle OFF">>>;
                readAndToggle(start, nums[i], n, 0, i);
                <<<"             OFF">>>;
            }
        //}
          
    }
    //now that you have phrase length n, make and play arrays
}


