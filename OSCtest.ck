OscSend confLANdini;
confLANdini.setHost( "127.0.0.1", 50506 );

/*
confLANdini.startMsg("/send/GD, s, s, i");
"all" => confLANdini.addString;
"/markovButton" => confLANdini.addString;
1 => confLANdini.addInt;
*/

/*
confLANdini.startMsg("/send/GD, s, s, i, i");
"all" => confLANdini.addString;
"/markovStep" => confLANdini.addString;
0 => confLANdini.addInt;
1 => confLANdini.addInt;
*/


confLANdini.startMsg("/send/GD, s, s, i, s, i");
"all" => confLANdini.addString;
"/pianoButton" => confLANdini.addString;
71 => confLANdini.addInt;
"on"=> confLANdini.addString;
0 => confLANdini.addInt;

.8::second=>now;

confLANdini.startMsg("/send/GD, s, s, i, s, i");
"all" => confLANdini.addString;
"/pianoButton" => confLANdini.addString;
71 => confLANdini.addInt;
"off"=> confLANdini.addString;
0 => confLANdini.addInt;
