#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render_to_response
from django.http import HttpResponse
# from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt

import MySQLdb, csv, json, time, datetime, re

timeStringFormat = '%Y-%m-%d %H:%M:%S'
quasiIdSet = set(["accinfo","ua","prod","vend","lan","ce","dnt","platform","cpuclass","plugins","fontlist","sc","tz","sr","html5","css3","noncore","pixelhash","webgl"])

distinctFPFields = ['FpID','Date','cookie',"accinfo","ua","prod","vend","lan","ce","dnt","platform","cpuclass","plugins","fontlist","sc","tz","sr","html5","css3","noncore","pixelhash","webgl"]
distinctFPFieldsLen = len(distinctFPFields)

def displayWebFP(request):
    #t = get_template('webfp.html')
    #html = t.render(Context({}))
    #return HttpResponse(html)
    return render_to_response('webfp.html')

def displayWebFPHistory(request):
    return render_to_response('webfp_history.html')

def getWebFPHistory(request):
    jsonData = dict()
    if 'FpID' in request.GET:
        FpID = request.GET['FpID']
        try:
            conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
            cur=conn.cursor()
            sqlcmd = 'SELECT id, Date FROM androidfingerprint.webfp_history where FpID = %s ORDER BY id DESC;' % (FpID)
            cur.execute(sqlcmd)
            alldata = cur.fetchall()
            jsonData['history'] = []
            cnt = 1
            for line in alldata:
                entry = [cnt]
                entry.append(line[1].strftime(timeStringFormat))
                jsonData['history'].append(entry)
                cnt += 1
            
            jsonData['res'] = True
            cur.close()
            conn.close()
            json_response = json.dumps(jsonData)
            return HttpResponse(json_response, content_type = 'application/json')
        except MySQLdb.Error,e:
            print "Mysql Error %s: %s" % (e.args[0], e.args[1])

    jsonData['res'] = False
    json_response = json.dumps(jsonData)
    return HttpResponse(json_response, content_type = 'application/json')

@csrf_exempt
def uploadNewWebFP(request):
    jsonData = dict()
    postJSON = json.loads(request.body)
    if type(postJSON) is dict and 'uploadFP' in postJSON:
        fp = postJSON['uploadFP']
        fp['accinfo'] = u'';
        foundFp, maxProb = Classify(fp)
        FpID, hisID, date = 0, 0, time.strftime(timeStringFormat)
        try:
            conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
            cur=conn.cursor()
            if foundFp != None: # update entry in fp_distinct
                FpID = foundFp['FpID']       
                sqlcmd = 'UPDATE androidfingerprint.webfp_distinct set Date = "%s", cookie = "%s", accinfo = "%s", ua = "%s", prod = "%s", vend = "%s", lan = "%s", ce = "%s", dnt = "%s", platform = "%s", cpuclass = "%s", plugins = \'%s\', fontlist = "%s", sc = "%s", tz = %s, sr = "%s", html5 = "%s", css3 = "%s", noncore = "%s", pixelhash = "%s", webgl = "%s" WHERE FpID = %s;' % (date, fp['cookie'], fp['accinfo'], fp['ua'], fp['prod'], fp['vend'], fp['lan'], fp['ce'], fp['dnt'], fp['platform'], fp['cpuclass'], fp['plugins'], fp['fontlist'], fp['sc'], fp['tz'], fp['sr'], fp['html5'], fp['css3'], fp['noncore'], fp['pixelhash'], fp['webgl'], FpID)
                cur.execute(sqlcmd)
                
            else:   # insert new entry in fp_distinct
                sqlcmd = 'INSERT INTO androidfingerprint.webfp_distinct(FpID, Date, cookie, accinfo, ua, prod, vend, lan, ce, dnt, platform, cpuclass, plugins, fontlist, sc, tz, sr, html5, css3, noncore, pixelhash, webgl) VALUES(0, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", \'%s\', "%s", "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s");' % (date, fp['cookie'], fp['accinfo'], fp['ua'], fp['prod'], fp['vend'], fp['lan'], fp['ce'], fp['dnt'], fp['platform'], fp['cpuclass'], fp['plugins'], fp['fontlist'], fp['sc'], fp['tz'], fp['sr'], fp['html5'], fp['css3'], fp['noncore'], fp['pixelhash'], fp['webgl'])
                cur.execute(sqlcmd)
                FpID = cur.lastrowid
            
            # insert into fp_all
            sqlcmd = 'INSERT INTO androidfingerprint.webfp_all(id, Date, cookie, accinfo, ua, prod, vend, lan, ce, dnt, platform, cpuclass, plugins, fontlist, sc, tz, sr, html5, css3, noncore, pixelhash, webgl) VALUES(0, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", \'%s\', "%s", "%s", %s, "%s", "%s", "%s", "%s", "%s", "%s");' % (date, fp['cookie'], fp['accinfo'], fp['ua'], fp['prod'], fp['vend'], fp['lan'], fp['ce'], fp['dnt'], fp['platform'], fp['cpuclass'], fp['plugins'], fp['fontlist'], fp['sc'], fp['tz'], fp['sr'], fp['html5'], fp['css3'], fp['noncore'], fp['pixelhash'], fp['webgl'])
            cur.execute(sqlcmd)
            hisID = cur.lastrowid
            
            # insert into fp_history
            if FpID != 0 and hisID != 0:
                sqlcmd = 'INSERT INTO androidfingerprint.webfp_history(FpID, id, Date) VALUES(%s, %s, "%s");' % (str(FpID), str(hisID), date)
                cur.execute(sqlcmd)
                
                conn.commit()
                
                jsonData['res'] = True
                jsonData['FpID'] = FpID
                jsonData['MaxProb'] = maxProb
                jsonData['date'] = date
                json_response = json.dumps(jsonData)
                return HttpResponse(json_response, content_type = 'application/json')
        
        except MySQLdb.Error,e:
            print "Mysql Error %s: %s" % (e.args[0], e.args[1])
                
    jsonData['res'] = False
    json_response = json.dumps(jsonData)
    return HttpResponse(json_response, content_type = 'application/json')

def Classify(fp):
    foundFp = None
    maxProb = 0.0
    
    # remove "\\" in fp[key]
    for key in quasiIdSet:
        fp[key] = unicode(fp[key]).replace(u"\\", u"")
                                           
    try:
        conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
        cur=conn.cursor()
        sqlcmd = 'SELECT count(*) FROM androidfingerprint.webfp_distinct;'
        cur.execute(sqlcmd)
        alldata = cur.fetchall()
        size = alldata[0][0]
        start = 0
        candidates = []
        while start < size:
            sqlcmd = 'SELECT * FROM androidfingerprint.webfp_distinct LIMIT %d, %d;' % (start, 1000)
            start += 1000
            cur.execute(sqlcmd)
            alldata = cur.fetchall()
            for line in alldata:
                item = {}
                for i in xrange(distinctFPFieldsLen):
                    if isinstance(line[i], datetime.datetime):
                        item[distinctFPFields[i]] = line[i].strftime(timeStringFormat)
                    else:
                        item[distinctFPFields[i]] = unicode(line[i])

                flag = True
                for key in quasiIdSet:
                    if fp[key] != item[key]:
                        flag = False
                        break
                if flag:
                    candidates.append(item)
                
                """
                prob = 1.0
                for key in quasiIdSet:
                    if key == 'html5' or key == 'css3':
                        preSet = set(item[key].split(';'))
                        curSet = set(fp[key].split(';'))
                        prob = prob * (1.0 - len(preSet-curSet)*1.0/len(preSet)) * (1.0 - len(curSet-preSet)*1.0/len(curSet))
                    elif key == 'plugins' or key == 'fontlist' or key == 'pixelhash':
                        preSet = set(item[key].split('##'))
                        curSet = set(fp[key].split('##'))
                        prob = prob * (1.0 - len(preSet-curSet)*1.0/len(preSet)) * (1.0 - len(curSet-preSet)*1.0/len(curSet))
                    elif key == 'noncore':
                        t, l = 0, len(fp[key])
                        for i in xrange(0, l):
                            if item[key][i] == fp[key][i]:
                                t += 1
                        prob = prob * (t*1.0 / l)
                        
                    #elif key == 'ua':
                    #   prob = prob * difflib.SequenceMatcher(None, item[key], fp[key]).ratio()
                    
                    else:	
                    #if key != 'plugins' and key != 'html5' and key != 'css3' and key != 'noncore' and key != 'fontlist' and key != 'ua' and key != 'pixelhash':
                        if fp[key] == item[key]:
                            prob = prob * (condProbs[key][0]*1.0/(condProbs[key][0]+condProbs[key][1]))
                        else:
                            prob = prob * (condProbs[key][1]*1.0/(condProbs[key][0]+condProbs[key][1]))
                
                if prob > maxProb and prob > threshold:
                    maxProb = prob
                    foundFp = item
                """
        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %s: %s" % (e.args[0], e.args[1])
    
    if len(candidates) == 1:
        foundFp = candidates[0]
        maxProb = 1.0
    
    return foundFp, maxProb


#print len(distinctFPFields)
#fpStr = u'{"uploadFP":{"cookie":"4430078748296613","ua":"Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:23.0) Gecko/20100101 Firefox/23.0","prod":"Gecko,20100101","vend":",","lan":"en-US;undefined","ce":true,"dnt":"unspecified","platform":"Linux i686","plugins":"6##iTunes Application Detector;This plug-in detects the presence of iTunes when opening iTunes Store URLs in a web page with Firefox.;librhythmbox-itms-detection-plugin.so;(;application/itunes-plugin;;)##Shockwave Flash;Shockwave Flash 11.2 r202;libflashplayer.so;(Shockwave Flash;application/x-shockwave-flash;swf;)(FutureSplash Player;application/futuresplash;spl;)##VLC Multimedia Plugin (compatible Totem 3.0.1);The <a href=\"http://www.gnome.org/projects/totem/\">Totem</a> 3.0.1 plugin handles video and audio streams.;libtotem-cone-plugin.so;(VLC Multimedia Plugin;application/x-vlc-plugin;;)(VLC Multimedia Plugin;application/vlc;;)(VLC Multimedia Plugin;video/x-google-vlc-plugin;;)(Ogg multimedia file;application/x-ogg;ogg;)(Ogg multimedia file;application/ogg;ogg;)(Ogg Audio;audio/ogg;oga;)(Ogg Audio;audio/x-ogg;ogg;)(Ogg Video;video/ogg;ogv;)(Ogg Video;video/x-ogg;ogg;)(Annodex exchange format;application/annodex;anx;)(Annodex Audio;audio/annodex;axa;)(Annodex Video;video/annodex;axv;)(MPEG video;video/mpeg;mpg, mpeg, mpe;)(WAV audio;audio/wav;wav;)(WAV audio;audio/x-wav;wav;)(MP3 audio;audio/mpeg;mp3;)(NullSoft video;application/x-nsv-vp3-mp3;nsv;)(Flash video;video/flv;flv;)(WebM video;video/webm;webm;)(Totem Multimedia plugin;application/x-totem-plugin;;)(MIDI audio;audio/midi;mid, midi;)##DivX® Web Player;DivX Web Player version 1.4.0.233;libtotem-mully-plugin.so;(AVI video;video/divx;divx;)##QuickTime Plug-in 7.6.6;The <a href=\"http://www.gnome.org/projects/totem/\">Totem</a> 3.0.1 plugin handles video and audio streams.;libtotem-narrowspace-plugin.so;(QuickTime video;video/quicktime;mov;)(MPEG-4 video;video/mp4;mp4;)(MacPaint Bitmap image;image/x-macpaint;pntg;)(Macintosh Quickdraw/PICT drawing;image/x-quicktime;pict, pict1, pict2;)(MPEG-4 video;video/x-m4v;m4v;)##Windows Media Player Plug-in 10 (compatible; Totem);The <a href=\"http://www.gnome.org/projects/totem/\">Totem</a> 3.0.1 plugin handles video and audio streams.;libtotem-gmp-plugin.so;(AVI video;application/x-mplayer2;avi, wma, wmv;)(ASF video;video/x-ms-asf-plugin;asf, wmv;)(AVI video;video/x-msvideo;asf, wmv;)(ASF video;video/x-ms-asf;asf;)(Windows Media video;video/x-ms-wmv;wmv;)(Windows Media video;video/x-wmv;wmv;)(Windows Media video;video/x-ms-wvx;wmv;)(Windows Media video;video/x-ms-wm;wmv;)(Windows Media video;video/x-ms-wmp;wmv;)(Windows Media video;application/x-ms-wms;wms;)(Windows Media video;application/x-ms-wmp;wmp;)(Microsoft ASX playlist;application/asx;asx;)(Windows Media audio;audio/x-ms-wma;wma;)##","fontlist":"1021X113##1003X113##1003X113##1003X113##1003X113##1003X113##1003X113##1003X113##754X113##1003X113","sc":"110","tz":-480,"sr":"1080X1920X24","html5":"application_Cache:true;Canvas:true;Canvas_Text:true;Drag_Drop:true;hashchange:true;History:true;HTML5_Audio:true;HTML5_Video:true;IndexedDB:true;Input_Attributes:autocomplete,autofocus,list,placeholder,max,min,multiple,pattern,required,step,;Input_Types:search,tel,url,email,datetime,date,month,week,time,datetime-local,number,range,color,;localStorage:true;postMessage:true;sessionStorage:true;Web_Sockets:true;Web_SQL_Database:false;Web_Workers:true;Geolocation_API:true;Inline_SVG:true;SMIL:true;SVG:true;SVG_Clip_Paths:true;Touch_events:false;WebGl:true","css3":"font_face:true;background_size:true;border_image:true;border_radius:true;box_shadow:true;Flexible_Box_Model:false;HSLA:true;Multiple_Backgrounds:true;Opacity:true;RGBA:true;text_shadow:true;CSS_Animations:true;CSS_Columns:true;Generated_Contenttrue;CSS_Gradients:true;CSS_Reflections:false;CSS_2D_Transforms:true;CSS_3D_Transforms:true;CSS_Transitions:true","noncore":"110101110101111000111101011010100101010010111111111011100000011010110110101000011101101101111110010100","pixelhash":"2517090254##23753297##23753297##23753297##23753297##23753297##23753297##23753297##1059419812##23753297","webgl":2319812595}}'
#fp = json.loads(fpStr)['uploadFP']
# print fp
# NaiveBayes(fp)