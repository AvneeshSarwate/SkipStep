OscRecv recv;
6449 => recv.port;
recv.listen();
recv.event("/touch, s") @=> OscEvent touchEv;
49 @=> int ASCII_1;
now => time newT;
    now => time oldT;
    dur tempo;

dur measure;

string s;
while(true) {
    <<< "     before touch event">>>;
    touchEv => now;
    <<< "     after touch event">>>;
    if(touchEv.nextMsg() != 0) {
        touchEv.getString() @=> string channel_vec;
        <<< " channel vec " , channel_vec >>>;
        newT => oldT;
        now => newT;
        <<< " newT " , newT >>>;
        <<< " old " , oldT >>>;
        if((newT - oldT) < 2::second){
            newT - oldT => tempo;
            <<< "jamba time juice!">>>;
            for (0 => int i;i!=4;++i)
            {
                if (channel_vec.charAt(i) == ASCII_1){
                    modifyTempo(i,tempo);
                }
            } 

        }
        
    }
}

fun void modifyTempo(int channel, dur tempo)
{
    //tempo @=> measure;
    <<< tempo >>>;
}