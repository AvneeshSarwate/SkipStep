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


// create our OSC receiver
OscRecv recv;
// use port 6449
6449 => recv.port;
// start listening (launch thread)
recv.listen();

5 => int maxMultiplay;
OscEvent nums[maxMultiplay];

for(0 => int i; i < maxMultiplay; i++) {
    recv.event("nums" + i + ", i") @=> nums[i];
}

// create an address in the receiver, store in new variable
recv.event( "/print, f" ) @=> OscEvent oe;
recv.event("start, s") @=> OscEvent start;
recv.event("type, s") @=> OscEvent type;
recv.event("objs, i") @=> OscEvent objs;




// host name and port
"127.0.0.1" => string hostname;
5147 => int port;

// get command line
if( me.args() ) me.arg(0) => hostname;
if( me.args() > 1 ) me.arg(1) => Std.atoi => port;

// send object
OscSend conf;

// aim the transmitter
conf.setHost( hostname, port );

60 => int note;

conf.startMsg("/played", "s");
        "0" => conf.addString;
<<<"played 0">>>;











Flute f => dac;

10 => int nInst;
Mandolin m[nInst];
Gain g => dac;
1.0/nInst => g.gain;
for(0 => int i; i < nInst; i++) {
    m[i] => g;
}

1.5::second => dur whole;
.01::second => dur split;

fun void playPhrase(StkInstrument c, int notes[], int times[], dur whole) {
    
    Flute s => dac;
    
    <<<"oi">>>;
    notes.size() => int len;
    
    for(0 => int i; i < len; i++) {
        .8 => s.noteOn;
        //problem comes when OSC messaged doesn't get sent 
        <<<notes[i], times[i]>>>;  //displas 0, 0 on error
        if(notes[i] == 0 || times[i] == 0) {
            <<<"OSC message failure (play)">>>;
            break;
        } 
        if(notes[i] == -1) {
            1 => s.noteOff;
            whole/times[i] => now;
        }
        else{
            Std.mtof(notes[i]) => s.freq;
            whole/times[i] - split => now;
        }
        1 => s.noteOff;
        split=>now;
    }   
    1 => s.noteOff;
    
    s =< dac;
    
    <<<"function played">>>;
}

fun void readOSCPhrase(OscEvent start, OscEvent nums, int n, StkInstrument f, dur whole) {
    <<<n>>>;
    int notes[n];
    int times[n];

    for(0 => int i; i < n; i++) {
        nums => now;
        nums.nextMsg();
        nums.getInt() => notes[i];
        nums => now;
        nums.nextMsg();
        nums.getInt() => times[i];
        if(notes[i] == 0 || times[i] == 0) {
            <<<"OSC message failure (read)">>>;
            break;
        }
    }
    <<<"yo">>>;
    playPhrase(f, notes, times, whole);
}

fun void readOSCProg(OscEvent start, OscEvent nums, int n, Mandolin m[], dur whole) {
    chord c[n];
    int t[n];
    <<<"stared read prog with " + n + " chords">>>; 
    for(0 => int i; i < n; i++){
        nums => now;
        nums.nextMsg();
        nums.getInt() => int cn;
        <<<"cn " + cn>>>;
        int cnotes[cn];
        nums => now;
        nums.nextMsg();
        nums.getInt() => t[i];
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
        playChord(m, c[i], (1.0/t[i])*whole);
    }

}

fun void readOSCChord(OscEvent start, OscEvent nums, int n, Mandolin m[], dur whole) {
    <<<n>>>;
    int notes[n];
    
    for(0 => int i; i < n; i++) {
        nums => now;
        nums.nextMsg();
        nums.getInt() => notes[i];
        if(notes[i] == 0) {
            <<<"OSC message failure (read)">>>;
            break;
        }
    }
    chord c;
    c.setNotes(notes);
    <<<"yo chord">>>;
    playChord(m, c, whole);
}

fun void playChord(Mandolin m[], chord c, dur whole) {
    <<<"oi chord">>>;
    c.size() => int len;
    
    for(0 => int i; i < len; i++) {
        if(c.notes[i] == 0) {
            <<<"OSC message failure (play)">>>;
            break;
        } 
        spork ~ miniPlay(Std.mtof(c.notes[i]), whole, m[i]);
        <<<c.notes[i]>>>;
    }   
    whole => now;
    conf.startMsg("/played", "s");
    "played0" => conf.addString;

    <<<"function played chord">>>;
}

fun void miniPlay(float freq, dur t, Mandolin m) {
    <<<"miniplay">>>;
    Mandolin s => dac;
    freq => s.freq;
    .9 => s.noteOn;
    t => now;
    .9 => s.noteOff;
    s =< dac;
    <<<"chord note played">>>;
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
                <<<"phrase again">>>;
                spork~ readOSCPhrase(start, nums[i], n, f, whole); 
            }
            if(mtype == "chord") {
                spork~ readOSCChord(start, nums[i], n, m, whole);
            }
            if(mtype == "progression") {
                spork~ readOSCProg(start, nums[i], n, m, whole);
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

