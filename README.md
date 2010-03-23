rddi-last.fm-scrobbler
====================
A basic python script for scrobbling a "now playing" playlist from an RDDI radio automation system. Persists one song.

Usage
--------------
Define the constants at top of script:

    USERNAME = ""
    PASSWD = ""
    FEED_URL = ""
    PICKLE_FILE = ""
    TIME_OFFSET = 0
    CLIENT_ID = "tst"
Then run:
    
    python scrobble_rddi.py >> scrobblelog.log
   
Limitations
----------------
This does not handle batching locally so last.fm outages will mean lost data. 

Licence
-----------
Licensed with the WTFPL ( http://sam.zoy.org/wtfpl/ )