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

fun void midOn(int note){
    144 => msg.data1;
    note => msg.data2;
    100 => msg.data3;
    mout.send( msg );
}

fun void midOff(int note){
    128 => msg.data1;
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
OscEvent nums2[maxMultiplay];

for(0 => int i; i < maxMultiplay; i++) {
    recv.event("nums" + i + ", i") @=> nums[i];
}
for(0 => int i; i < maxMultiplay; i++) {
    recv.event("nums2" + i + ", f") @=> nums2[i];
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

1::second => dur whole;
.01::second => dur split;



// host name and port

//50506 => int port; //LANDINI
// send object

// aim the transmitter


//conf.startMsg("/send/GD, s, s, s"); LANDINI
//"all" => conf.addString; LANDINI
//"/played" => conf.addString; LANDINI


OscSend confLANdini;
confLANdini.setHost( "127.0.0.1", 50506 );
"all" => confLANdini.addString;
"/played" => confLANdini.addString;
"played0" => confLANdini.addString;

fun void timerLANdini(){
    while(true) {
        .25 * whole => now;
        confLANdini.startMsg("/send/GD, s, s, s");
        "all" => confLANdini.addString;
        "/played" => confLANdini.addString;
        "played0" => confLANdini.addString;
        <<<"                  step">>>;
    }
}


//for multi loop, send over multiple ports
OscSend conf;
"127.0.0.1" => string hostname;
5174 => int port;
conf.setHost( hostname, port );
conf.startMsg("/played, s");
"played0" => conf.addString;

fun void timer(){
    while(true) {
        .25 * whole => now;
        conf.startMsg("/played, s");
        "played0" => conf.addString;
        <<<"                  step">>>;
    }
}

0 => int chordNum;
fun void readOSCChord(OscEvent start, OscEvent nums, int n, Mandolin m[], dur whole) {
    <<<n>>>;
    <<<chordNum + "chordNum">>>;
    chordNum++;
    int notes[n];
    0 => int broken;
    for(0 => int i; i < n; i++) {
        nums => now;
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
    //<<<"yo chord">>>;
    playChord(m, c, whole);
}

fun chord readOSCChord2(OscEvent start, OscEvent nums, int n) {
    <<<n>>>;
    int notes[n];
    0 => int broken;
    for(0 => int i; i < n; i++) {
        nums => now;
        nums.nextMsg();
        nums.getInt() => notes[i];
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

fun void readAndToggle(OscEvent start, OscEvent nums, int n, int on){
    readOSCChord2(start, nums, n) @=> chord c;
    chordToggle(c, on);
}

fun void chordToggle(chord c, int on) {
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
        if(on == 1)
            midOn(c.notes[i]);
        else
            midOff(c.notes[i]);
        <<<c.notes[i]>>>;
    }   
    /*.25*whole => now;
    for(0 => int i; i < len; i++) {
        midOff(c.notes[i]);
    }
    conf.startMsg("/played", "s");
    "played0" => conf.addString;
    <<<"function played chord">>>;*/
}




fun void playChord(Mandolin m[], chord c, dur whole) {
    //<<<"oi chord">>>;
    c.size() => int len;
    if(c.notes[0] == -1) {
        .25 * whole => now;
        <<<"chord rest">>>;
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
        midOn(c.notes[i]);
        <<<c.notes[i]>>>;
    }   
    .25*whole - split=> now;
    for(0 => int i; i < len; i++) {
        midOff(c.notes[i]);
    }
    //conf.startMsg("/played", "s");
    //"played0" => conf.addString;
    <<<"function played chord">>>;
}

spork~ timerLANdini();

// infinite event loop
while ( true )
{
    // wait for event to arrive
    //oe => now;
    start => now;
    while(start.nextMsg() != 0) {
        
        
        start.getString() => string a;
        <<<a>>>;
        objs => now;
        objs.nextMsg();
        objs.getInt() => int nobj;
        for(0=>int i; i < nobj; i++){ //for multiloop, nobj is looper index, and instead of for loop, directly index by nobj
            type => now;
            type.nextMsg();
            type.getString() => string mtype;
            <<<mtype>>>;
            nums[i] => now;
            nums[i].nextMsg();
            nums[i].getInt() => int n;
            if(mtype == "chord") {
                spork~ readOSCChord(start, nums[i], n, m, whole);
            }
            if(mtype == "on") {
                readAndToggle(start, nums[i], n, 1);
                <<<"             ON">>>;
            }
            if(mtype == "off") {
                readAndToggle(start, nums[i], n, 0);
                <<<"             OFF">>>;
            }
        }
          
    }
    //now that you have phrase length n, make and play arrays
}


