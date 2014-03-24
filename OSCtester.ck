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


fun void listener(int i) {
    while(true){
        objLen[i] => now;
        <<<"got length", i>>>;
        objLen[i].nextMsg();
        objLen[i].getInt() => int n;   
    }
}

OscSend conf;
"127.0.0.1" => string hostname;
5174 => int port;
conf.setHost( hostname, port );
conf.startMsg("/played, s");
"played0" => conf.addString;

1::second => dur whole;

fun void timer(){
    while(true) {
        .25 * whole => now;
        conf.startMsg("/played, s");
        "played0" => conf.addString;
        //        <<<"                  step">>>;
    }
}

spork~ listener(0);

spork~ listener(1);

spork~ listener(2);

//spork~ timer();


while(true) 1::second => now;