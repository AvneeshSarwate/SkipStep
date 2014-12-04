OscSend conf;
"127.0.0.1" => string hostname;
6449 => int port;
conf.setHost( hostname, port );

conf.startMsg("/touch, s");
"1000" => conf.addString;