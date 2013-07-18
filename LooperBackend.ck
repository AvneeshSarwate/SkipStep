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


// host name and port
"127.0.0.1" => string hostname;
5174 => int port;

// get command line
if( me.args() ) me.arg(0) => hostname;
if( me.args() > 1 ) me.arg(1) => Std.atoi => port;
<<<hostname, port>>>;
// send object
OscSend conf;

// aim the transmitter
conf.setHost( hostname, port );

60 => int note;

conf.startMsg("/played", "s");
        "0" => conf.addString;
<<<"played 0">>>;
conf.startMsg("/played", "s");
        "02" => conf.addString;
conf.startMsg("/tester", "i");
5=>conf.addInt;


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

1.2::second => dur whole;
.01::second => dur split;

fun void playPhrase(StkInstrument c, int notes[], float times[], dur whole) {
    
    Flute s => dac;
    
    <<<"oi">>>;
    notes.size() => int len;
    
    for(0 => int i; i < len; i++) {
        //problem comes when OSC messaged doesn't get sent 
        <<<notes[i], times[i]>>>;  //displas 0, 0 on error
        if(notes[i] == 0 || times[i] == 0) {
            <<<"OSC message failure (play)">>>;
            return;
        } 
        if(notes[i] == -1) {
            whole*times[i] => now;
        }
        else{
            midOn(notes[i]);
            whole*times[i] - split => now;
        }
        midOff(notes[i]);
        split=>now;
    }   
    1 => s.noteOff;
    
    s =< dac;
    conf.startMsg("/played", "s");
    "played0" => conf.addString;
    <<<"phrase played">>>;
}

fun void readOSCPhrase(OscEvent start, OscEvent nums, OscEvent nums2, int n, StkInstrument f, dur whole) {
    <<<n, "numnotes">>>;
    int notes[n];
    float times[n];
    
    0 => int broken;
    for(0 => int i; i < n; i++) {
        nums => now;
        nums.nextMsg();
        nums.getInt() => notes[i];
        <<<notes[i], "notes[i]">>>;
        nums2 => now;
        nums2.nextMsg();
        nums2.getFloat() => times[i];
        <<<times[i], "times[i]">>>;
        if(notes[i] == 0 || times[i] == 0) {
            <<<"OSC message failure (read)">>>;
            1 => broken;
            //return;
        }
    }
    if(broken == 1) return;
    <<<"yo">>>;
    playPhrase(f, notes, times, whole);
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

fun void playChord(Mandolin m[], chord c, dur whole) {
    //<<<"oi chord">>>;
    c.size() => int len;
    if(c.notes[0] == -1) {
        .25 * whole => now;
        <<<"chord rest">>>;
        conf.startMsg("/played", "s");
        "played0" => conf.addString;
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
    .25*whole => now;
    for(0 => int i; i < len; i++) {
        midOff(c.notes[i]);
    }
    conf.startMsg("/played", "s");
    "played0" => conf.addString;
    <<<"function played chord">>>;
}


fun void readOSCProg(OscEvent start, OscEvent nums, OscEvent nums2, int n, Mandolin m[], dur whole) {
    chord c[n];
    float t[n];
    <<<"stared read prog with " + n + " chords">>>; 
    for(0 => int i; i < n; i++){
        nums => now;
        nums.nextMsg();
        nums.getInt() => int cn;
        <<<"cn " + cn>>>;
        int cnotes[cn];
        nums2 => now;
        nums2.nextMsg();
        nums2.getFloat() => t[i];
        if(cn * t[i] == 0) {
            <<<"OSC reading error (prog)">>>;
            while(nums.nextMsg() != 0) ;
            return;
        }
        <<<"t[i] " + t[i]>>>;
        for(0 => int k; k < cn; k++) {
            nums => now;
            nums.nextMsg();
            nums.getInt() => cnotes[k];
            <<<cnotes[k]>>>;
            if(cnotes[k] == 0) {
                <<<"OSC reading error (prog)">>>;
                while(nums.nextMsg() != 0) ;
                return;
            }
        }
        c[i].setNotes(cnotes);
        <<<"chord " + i + " done">>>;
    }
    for(0 => int i; i < n; i++){
        playChord(m, c[i], t[i]*whole);
    }
    
}



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
        for(0=>int i; i < nobj; i++){
            type => now;
            type.nextMsg();
            type.getString() => string mtype;
            <<<mtype>>>;
            nums[i] => now;
            nums[i].nextMsg();
            nums[i].getInt() => int n;
            if(mtype == "phrase") {
                spork~ readOSCPhrase(start, nums[i], nums2[i], n, f, whole); 
            }
            if(mtype == "chord") {
                spork~ readOSCChord(start, nums[i], n, m, whole);
            }
            if(mtype == "progression") {
                spork~ readOSCProg(start, nums[i], nums2[i], n, m, whole);
            }
        }
    }
    //now that you have phrase length n, make and play arrays
}



// grab the next message from the queue. 
// while ( oe.nextMsg() != 0 )
//{ 
// getFloat fetches the expected float (as indicated by "f")
//   oe.getFloat() => float got;
// print
//   <<< "got (via OSC):", got >>>;
// set play pointer to beginning
//0 => buf.pos;

//   oe.nextMsg();
//   oe.getFloat() => got;
//   <<<"got again", got >>>;
//}

