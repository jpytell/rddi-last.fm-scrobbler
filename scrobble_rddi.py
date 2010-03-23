import sys
import time
import calendar
import httplib
import urllib
import hashlib
import random
from elementtree.ElementTree import parse
from elementtree.ElementTree import ElementTree
from urlparse import urlparse
import pickle

USERNAME = "your_username"
PASSWD = "your_password"
FEED_URL = "http://songid.play.it/NowPlayingWeb/SongIDService.asmx/GetNowPlayingEventForStation?stationID=109"
#FEED_URL = "http://localhost:8888/testdata.xml"
PICKLE_FILE = "scrobbledata.dat"
# this is a hack to handle lags from service. set to 0 if not germain
TIME_OFFSET = random.randint(35, 65)
CLIENT_ID = "tst" #for testing -- get a non test client ID from last.fm


def scrobble_playlist(lastfm_username, lastfm_password, feed_url, pickle_path="scrobbles.dat"):
    UNIXTIME = str(calendar.timegm(time.gmtime()))
    httplib.HTTPConnection.debuglevel = 0
    hsval = "true"
    pval = "1.2"
    cval = CLIENT_ID
    vval = "1.0"
    
    def get_latest_song():
        unpicklefile = open(PICKLE_FILE, "r")
        unpickleditems = pickle.load(unpicklefile)
        unpicklefile.close()
        try:
            myxml = parse(urllib.urlopen(feed_url)).getroot()
        except Exception, e:
            print "could not retrieve feed: %s" % str(e)
            myitems["Title"] = 0
            return 0
        myitems = {}
        for element in myxml.findall("{http://wilshiremedia.com/}CurrentEventPackage"):
            tmptime = int(UNIXTIME) - TIME_OFFSET
            #myitems["IsSong"] = element.get("IsSong") #this is no longer accurate predictor
            tempartist = element.findtext("{http://wilshiremedia.com/}Artist")
            # clean up "Ramones, The" situations
            if tempartist.endswith("The"):
                myitems["Artist"] = "The %s" % tempartist.split(",")[0]
            # clean up "DJ Jazzy J (with Puff Wuffy Doodle)" situations
            myitems["Artist"] = tempartist.split("(")[0].strip().encode("utf8")
            myitems["Title"] = element.findtext("{http://wilshiremedia.com/}Title").split("(")[0].strip().encode("utf8")
            myitems["Duration"] = element.findtext("{http://wilshiremedia.com/}Duration")
            myitems["PlayStart"] = str(tmptime)
            print "current song/artist: %s -- %s" % (myitems["Artist"], myitems["Title"])
        if unpickleditems["Title"] == myitems["Title"]:
            myitems["Dupe"] = 1
            if unpickleditems["Title"] == "":
                print "in commercial"
            else:
                print "title the same"
        else:
            myitems["Dupe"] = 0
            print "title not the same -- updating pickle"
            file = open(PICKLE_FILE, "w")
            pickle.dump(myitems, file)
            file.close()
            myitems = unpickleditems
        return    myitems
    
    def scrobble_song(song_dict):
        print "scrobbling previous song: %s ..." % song_dict.get("Title")
        pwd = hashlib.md5(hashlib.md5(PASSWD).hexdigest() + UNIXTIME).hexdigest()
        #get handshake auth
        querystring = "/?hs=%s&p=%s&c=%s&v=%s&u=%s&t=%s&a=%s" % (hsval, pval, cval, vval, USERNAME, UNIXTIME, pwd)
        httpServ = httplib.HTTPConnection("post.audioscrobbler.com", 80)
        httpServ.connect()
        httpServ.request("GET", querystring)
        response = httpServ.getresponse()
        #print response.status, response.reason
        authdata1 = response.read()
        #print authdata1
        data = authdata1.splitlines()
        sessionid = data[1]
        nowplaying_url = urlparse(data[2])
        scrobble_url = urlparse(data[3])
        print "handshake auth attempt: %s" % authdata1
        
        #send now playing and scrobble data if all ok
        if song_dict["Title"] != "" and authdata1 != "BADAUTH":
            t = song_dict.get("Duration")
            headers = {"Content-type" : "application/x-www-form-urlencoded", "Accept" : "text/plain"}
            params = urllib.urlencode({"s" : sessionid, "a" : song_dict.get("Artist"), "t" : song_dict.get("Title"), "b" : "", "l" : t, "n" : "", "m" : ""})
            httpServ = httplib.HTTPConnection(nowplaying_url.netloc)
            httpServ.connect()
            httpServ.request("POST", nowplaying_url.path, params, headers)
            response = httpServ.getresponse()
            #send scrobble with auth
            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            params = urllib.urlencode({"s" : sessionid, "a[0]" : song_dict.get("Artist"), "t[0]" : song_dict.get("Title"), "i[0]" : song_dict.get("PlayStart"), "o[0]" : "P", "r[0]" : "", "l[0]" : t, "b[0]" : "", "n[0]" : "", "m[0]" : ""})
            httpServ = httplib.HTTPConnection(scrobble_url.netloc)
            httpServ.connect()
            httpServ.request("POST", scrobble_url.path, params, headers)
            response = httpServ.getresponse()
            #print response.status, response.reason
            data1 = response.read()
            print "scrobble attempt: %s" % data1
    latest = get_latest_song()
    if latest:
        if latest["Dupe"] != 1 and latest["Artist"] != "":
            scrobble_song(latest)
    else:
        print "no scrobble at: %s" % time.strftime("%a, %d %b %Y %H:%M:%S + 0000", time.localtime())
            
if __name__ == "__main__":
    scrobble_playlist(USERNAME, PASSWD, FEED_URL, PICKLE_FILE)