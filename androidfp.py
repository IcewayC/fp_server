#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.template.loader import get_template
from django.template import Context
from django.shortcuts import render_to_response
from django.http import HttpResponse
# from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt

import MySQLdb, csv, json, time, datetime

timeStringFormat = '%Y-%m-%d %H:%M:%S'
quasiIdSet = set(['Kernel_Version', 'Android_Ver', 'Build_Num', 'User_Agent', 'Time_Zone', '12_24', 'Date_Format', 'Auto_Time', 'Auto_Timezone', 'Screen_Timeout', 'WIFI_Notification', 'WIFI_Sleep', 'Access_Loc', 'LockPattern', 'Lock_Pattern_Visible', 'Lock_Pattern_Vibrate', 'Input_Methods', 'Language', 'Root', 'Font_Size', 'Font_Types', 'User_Packages', 'System_Packages', 'Storage_Structure', 'All_Sound', 'Notesound', 'Alarmsound', 'Ringsound', 'Sound_Effect', 'Auto_Bright', 'Auto_Rotate', 'Show_Pwd', 'Wallpaper_md5'])

threshold = 1.2e-09
condProbs = {'Storage_Structure': {0: 0, 1: 0}, 'Notesound': {0: 29654, 1: 262}, 'Build_Num': {0: 29207, 1: 709}, 'Ringsound': {0: 29333, 1: 583}, 'Sound_Effect': {0: 29845, 1: 71}, 'Screen_Timeout': {0: 28914, 1: 1002}, 'Alarmsound': {0: 29597, 1: 319}, 'Auto_Time': {0: 29777, 1: 139}, '12_24': {0: 29832, 1: 84}, 'Font_Size': {0: 29855, 1: 61}, 'Lock_Pattern_Vibrate': {0: 29908, 1: 8}, 'Kernel_Version': {0: 29315, 1: 601}, 'Time_Zone': {0: 29804, 1: 112}, 'User_Agent': {0: 29748, 1: 168}, 'System_Packages': {0: 0, 1: 0}, 'Language': {0: 29827, 1: 89}, 'Show_Pwd': {0: 29864, 1: 52}, 'Access_Loc': {0: 29169, 1: 747}, 'Android_Ver': {0: 29822, 1: 94}, 'WIFI_Sleep': {0: 29868, 1: 48}, 'Wallpaper_md5': {0: 28185, 1: 1731}, 'Font_Types': {0: 0, 1: 0}, 'Root': {0: 29877, 1: 39}, 'Lock_Pattern_Visible': {0: 29812, 1: 104}, 'WIFI_Notification': {0: 29799, 1: 117}, 'Date_Format': {0: 29865, 1: 51}, 'Auto_Rotate': {0: 29179, 1: 737}, 'LockPattern': {0: 29742, 1: 174}, 'Auto_Bright': {0: 28681, 1: 1235}, 'Input_Methods': {0: 29469, 1: 447}, 'All_Sound': {0: 0, 1: 0}, 'User_Packages': {0: 0, 1: 0}, 'Auto_Timezone': {0: 29812, 1: 104}}
distinctFPFields = ['FpID','Date','IMEI','Android_ID','Kernel_Version','Android_Ver','Build_Num','User_Agent','WIFI_ON','WIFI_MAC','Bluetooth_MAC','Device_Model','Device_Manufacturer','Serial','Screen_Density','Screen_Width','Screen_Height','Time_Zone','12_24','Date_Format','Auto_Time','Auto_Timezone','Screen_Timeout','WIFI_Notification','WIFI_Sleep','Access_Loc','LockPattern','Lock_Pattern_Visible','Lock_Pattern_Vibrate','Input_Methods','Language','Root','Font_Size','Font_Types','User_Packages','System_Packages','Int_Storage_A','Int_Storage_T','Ext_Storage_A','Ext_Storage_T','Storage_Structure','Root_Dir_Structure','All_Sound','Notesound','Alarmsound','Ringsound','Sound_Effect','Auto_Bright','Auto_Rotate','Show_Pwd','Wallpaper_md5']
distinctFPFieldsLen = len(distinctFPFields)

def getJarStatus(request):
    jsonData = dict()
    jsonData['res'] = False
    jsonData['hasupdate'] = False
    if 'jarfile' in request.GET:
        jarFileName = request.GET['jarfile']
        try:
            conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
            cur=conn.cursor()
            sqlcmd = 'SELECT hasupdate FROM androidfingerprint.fp_jarstatus where jarfile = "%s";' % (jarFileName)
            cur.execute(sqlcmd)
            alldata = cur.fetchall()
            if alldata[0][0] == 1:
                jsonData['hasupdate'] = True
            cur.close()
            conn.close()
            jsonData['res'] = True
            json_response = json.dumps(jsonData)
            return HttpResponse(json_response, content_type = 'application/json')
        except MySQLdb.Error,e:
            print "Mysql Error %s: %s" % (e.args[0], e.args[1])
    json_response = json.dumps(jsonData)
    return HttpResponse(json_response, content_type = 'application/json')

def getHistory(request):
    jsonData = dict()
    if 'FpID' in request.GET:
        FpID = request.GET['FpID']
        try:
            conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
            cur=conn.cursor()
            sqlcmd = 'SELECT id, Date, Op FROM androidfingerprint.fp_history where FpID = %s ORDER BY id DESC;' % (FpID)
            cur.execute(sqlcmd)
            alldata = cur.fetchall()
            jsonData['history'] = []
            for line in alldata:
                entry = [line[0]]
                entry.append(line[1].strftime(timeStringFormat))
                entry.append(line[2])
                jsonData['history'].append(entry)
            
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
def uploadNewFP(request):
    jsonData = dict()
    postJSON = json.loads(request.body)
    if type(postJSON) is dict and 'uploadFP' in postJSON:
        fp = postJSON['uploadFP']
        for key in distinctFPFields:
            if key not in fp:
                fp[key] = ''
        foundFp, maxProb = NaiveBayes(fp)
        FpID, hisID, date = 0, 0, time.strftime(timeStringFormat)
        if 'appname' in postJSON:
            ops = postJSON['appname']
        else:
            ops = "unknown"
        try:
            conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
            cur=conn.cursor()
            if foundFp != None: # update entry in fp_distinct
                FpID = foundFp['FpID']       
                sqlcmd = 'UPDATE androidfingerprint.fp_distinct set Date = "%s", IMEI = "%s", Android_ID = "%s", Kernel_Version = "%s", Android_Ver = "%s", Build_Num = "%s", User_Agent = "%s", WIFI_ON = %s, WIFI_MAC = "%s", Bluetooth_MAC = "%s", Device_Model = "%s", Device_Manufacturer = "%s", Serial = "%s", Screen_Density = %s, Screen_Width = %s, Screen_Height = %s, Time_Zone = "%s", `12_24` = %s, Date_Format = "%s", Auto_Time = %s, Auto_Timezone = %s, Screen_Timeout = %s, WIFI_Notification = %s, WIFI_Sleep = %s, Access_Loc = %s, LockPattern = %s, Lock_Pattern_Visible = %s, Lock_Pattern_Vibrate = %s, Input_Methods = "%s", `Language` = "%s", Root = %s, Font_Size = %s, Font_Types = "%s", User_Packages = "%s", System_Packages = "%s", Int_Storage_A = "%s", Int_Storage_T = "%s", Ext_Storage_A = "%s", Ext_Storage_T = "%s", Storage_Structure = "%s", Root_Dir_Structure = "%s", All_Sound = "%s", Notesound = "%s", Alarmsound = "%s", Ringsound = "%s", Sound_Effect = %s, Auto_Bright = %s, Auto_Rotate = %s, Show_Pwd = %s, Wallpaper_md5 = %s  WHERE FpID = %s;' % (date, fp['IMEI'], fp['Android_ID'], fp['Kernel_Version'], fp['Android_Ver'], fp['Build_Num'], fp['User_Agent'], fp['WIFI_ON'], fp['WIFI_MAC'], fp['Bluetooth_MAC'], fp['Device_Model'], fp['Device_Manufacturer'], fp['Serial'], fp['Screen_Density'], fp['Screen_Width'], fp['Screen_Height'], fp['Time_Zone'], fp['12_24'], fp['Date_Format'], fp['Auto_Time'], fp['Auto_Timezone'], fp['Screen_Timeout'], fp['WIFI_Notification'], fp['WIFI_Sleep'], fp['Access_Loc'], fp['LockPattern'], fp['Lock_Pattern_Visible'], fp['Lock_Pattern_Vibrate'], fp['Input_Methods'], fp['Language'], fp['Root'], fp['Font_Size'], fp['Font_Types'], fp['User_Packages'], fp['System_Packages'], fp['Int_Storage_A'], fp['Int_Storage_T'], fp['Ext_Storage_A'], fp['Ext_Storage_T'], fp['Storage_Structure'], fp['Root_Dir_Structure'], fp['All_Sound'], fp['Notesound'], fp['Alarmsound'], fp['Ringsound'], fp['Sound_Effect'], fp['Auto_Bright'], fp['Auto_Rotate'], fp['Show_Pwd'], fp['Wallpaper_md5'], FpID)
                cur.execute(sqlcmd)

            else:   # insert new entry in fp_distinct
                sqlcmd = 'INSERT INTO androidfingerprint.fp_distinct(FpID, Date, IMEI, Android_ID, Kernel_Version, Android_Ver, Build_Num, User_Agent, WIFI_ON, WIFI_MAC, Bluetooth_MAC, Device_Model, Device_Manufacturer, Serial, Screen_Density, Screen_Width, Screen_Height, Time_Zone, `12_24`, Date_Format, Auto_Time, Auto_Timezone, Screen_Timeout, WIFI_Notification, WIFI_Sleep, Access_Loc, LockPattern, Lock_Pattern_Visible, Lock_Pattern_Vibrate, Input_Methods, `Language`, Root, Font_Size, Font_Types, User_Packages, System_Packages, Int_Storage_A, Int_Storage_T, Ext_Storage_A, Ext_Storage_T, Storage_Structure, Root_Dir_Structure, All_Sound, Notesound, Alarmsound, Ringsound, Sound_Effect, Auto_Bright, Auto_Rotate, Show_Pwd, Wallpaper_md5) VALUES(0, "%s", "%s", "%s", "%s", "%s", "%s", "%s", %s, "%s", "%s", "%s", "%s", "%s", %s, %s, %s, "%s", %s, "%s", %s, %s, %s, %s, %s, %s, %s, %s, %s, "%s", "%s", %s, %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", %s, %s, %s, %s, %s);' % (date, fp['IMEI'], fp['Android_ID'], fp['Kernel_Version'], fp['Android_Ver'], fp['Build_Num'], fp['User_Agent'], fp['WIFI_ON'], fp['WIFI_MAC'], fp['Bluetooth_MAC'], fp['Device_Model'], fp['Device_Manufacturer'], fp['Serial'], fp['Screen_Density'], fp['Screen_Width'], fp['Screen_Height'], fp['Time_Zone'], fp['12_24'], fp['Date_Format'], fp['Auto_Time'], fp['Auto_Timezone'], fp['Screen_Timeout'], fp['WIFI_Notification'], fp['WIFI_Sleep'], fp['Access_Loc'], fp['LockPattern'], fp['Lock_Pattern_Visible'], fp['Lock_Pattern_Vibrate'], fp['Input_Methods'], fp['Language'], fp['Root'], fp['Font_Size'], fp['Font_Types'], fp['User_Packages'], fp['System_Packages'], fp['Int_Storage_A'], fp['Int_Storage_T'], fp['Ext_Storage_A'], fp['Ext_Storage_T'], fp['Storage_Structure'], fp['Root_Dir_Structure'], fp['All_Sound'], fp['Notesound'], fp['Alarmsound'], fp['Ringsound'], fp['Sound_Effect'], fp['Auto_Bright'], fp['Auto_Rotate'], fp['Show_Pwd'], fp['Wallpaper_md5'])
                cur.execute(sqlcmd)
                FpID = cur.lastrowid

            # insert into fp_all
            sqlcmd = 'INSERT INTO androidfingerprint.fp_all(id, Date, IMEI, Android_ID, Kernel_Version, Android_Ver, Build_Num, User_Agent, WIFI_ON, WIFI_MAC, Bluetooth_MAC, Device_Model, Device_Manufacturer, Serial, Screen_Density, Screen_Width, Screen_Height, Time_Zone, `12_24`, Date_Format, Auto_Time, Auto_Timezone, Screen_Timeout, WIFI_Notification, WIFI_Sleep, Access_Loc, LockPattern, Lock_Pattern_Visible, Lock_Pattern_Vibrate, Input_Methods, `Language`, Root, Font_Size, Font_Types, User_Packages, System_Packages, Int_Storage_A, Int_Storage_T, Ext_Storage_A, Ext_Storage_T, Storage_Structure, Root_Dir_Structure, All_Sound, Notesound, Alarmsound, Ringsound, Sound_Effect, Auto_Bright, Auto_Rotate, Show_Pwd, Wallpaper_md5) VALUES(0, "%s", "%s", "%s", "%s", "%s", "%s", "%s", %s, "%s", "%s", "%s", "%s", "%s", %s, %s, %s, "%s", %s, "%s", %s, %s, %s, %s, %s, %s, %s, %s, %s, "%s", "%s", %s, %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", %s, %s, %s, %s, %s);' % (date, fp['IMEI'], fp['Android_ID'], fp['Kernel_Version'], fp['Android_Ver'], fp['Build_Num'], fp['User_Agent'], fp['WIFI_ON'], fp['WIFI_MAC'], fp['Bluetooth_MAC'], fp['Device_Model'], fp['Device_Manufacturer'], fp['Serial'], fp['Screen_Density'], fp['Screen_Width'], fp['Screen_Height'], fp['Time_Zone'], fp['12_24'], fp['Date_Format'], fp['Auto_Time'], fp['Auto_Timezone'], fp['Screen_Timeout'], fp['WIFI_Notification'], fp['WIFI_Sleep'], fp['Access_Loc'], fp['LockPattern'], fp['Lock_Pattern_Visible'], fp['Lock_Pattern_Vibrate'], fp['Input_Methods'], fp['Language'], fp['Root'], fp['Font_Size'], fp['Font_Types'], fp['User_Packages'], fp['System_Packages'], fp['Int_Storage_A'], fp['Int_Storage_T'], fp['Ext_Storage_A'], fp['Ext_Storage_T'], fp['Storage_Structure'], fp['Root_Dir_Structure'], fp['All_Sound'], fp['Notesound'], fp['Alarmsound'], fp['Ringsound'], fp['Sound_Effect'], fp['Auto_Bright'], fp['Auto_Rotate'], fp['Show_Pwd'], fp['Wallpaper_md5'])
            cur.execute(sqlcmd)
            hisID = cur.lastrowid
            
            # insert into fp_history
            if FpID != 0 and hisID != 0:
                sqlcmd = 'INSERT INTO androidfingerprint.fp_history(FpID, id, Date, Op) VALUES(%s, %s, "%s", "%s");' % (str(FpID), str(hisID), date, ops)
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

def NaiveBayes(fp):
    foundFp = None
    maxProb = 0.0
    
    # remove "\\" in fp[key]
    for key in quasiIdSet:
        fp[key] = unicode(fp[key]).replace(u"\\", u"")
                                           
    try:
        conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
        cur=conn.cursor()
        sqlcmd = 'SELECT count(*) FROM androidfingerprint.fp_distinct;'
        cur.execute(sqlcmd)
        alldata = cur.fetchall()
        size = alldata[0][0]
        start = 0
        while start < size:
            sqlcmd = 'SELECT * FROM androidfingerprint.fp_distinct LIMIT %d, %d;' % (start, 1000)
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

                prob = 1.0
                for key in quasiIdSet:
                    if item[key] == '' or fp[key] == '':
                        continue
                    if key == 'User_Packages' or key == 'System_Packages' or key == 'Storage_Structure' or key == 'Font_Types':
                        preSet = set(item[key].split('##'))
                        curSet = set(fp[key].split('##'))
                        prob = prob * (1.0 - len(preSet-curSet)*1.0/len(preSet)) * (1.0 - len(curSet-preSet)*1.0/len(curSet))
                    elif key == 'All_Sound':
                        preSet = set(item[key].split(','))
                        curSet = set(fp[key].split(','))
                        prob = prob * (1.0 - len(preSet-curSet)*1.0/len(preSet)) * (1.0 - len(curSet-preSet)*1.0/len(curSet))
                    else:
                        if fp[key] == item[key]:
                            prob = prob * (condProbs[key][0]*1.0/(condProbs[key][0]+condProbs[key][1]))
                        else:
                            prob = prob * (condProbs[key][1]*1.0/(condProbs[key][0]+condProbs[key][1]))
                
                if prob > maxProb and prob > threshold:
                    maxProb = prob
                    foundFp = item
        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %s: %s" % (e.args[0], e.args[1])
    
    return foundFp, maxProb

# print len(distinctFPFields) # 51
# fpStr = u'{"uploadFP":{"Device_Manufacturer":"samsung","Int_Storage_T":"2015MB","Access_Loc":"1","Kernel_Version":"Linux version 3.0.36-CM-gd654360 (bajee@bajee-desktop) (gcc version 4.6.x-google 20120106 (prerelease) (GCC) ) #1 SMP PREEMPT Fri Aug 31 14:56:53 EDT 2012\\n","Auto_Time":"1","Sound_Effect":"1","Bluetooth_MAC":"unknown","WIFI_Sleep":"-1","Show_Pwd":"0","Ext_Storage_T":"11781MB","Wallpaper_md5":"2934221907","Input_Methods":"Android 键盘 (AOSP),谷歌拼音输入法,Google 语音输入,","Screen_Timeout":"30","WIFI_Notification":"1","WIFI_ON":"1","Notesound":"默认铃声（Antimony）","LockPattern":"0","System_Packages":"10000:com.android.contacts##10000:com.android.providers.applications##10000:com.android.providers.contacts##10000:com.android.providers.userdictionary##10001:com.android.backupconfirm##10002:com.android.bluetooth##10003:com.android.browser##10004:com.android.calculator2##10005:com.android.calendar##10006:com.android.providers.calendar##10007:com.android.certinstaller##10008:com.android.defcontainer##10009:com.android.deskclock##10010:com.android.providers.downloads##10010:com.android.providers.downloads.ui##10010:com.android.providers.drm##10010:com.android.providers.media##10011:com.android.email##10012:com.android.exchange##10013:com.android.galaxy4##10014:com.android.gallery3d##10015:com.android.htmlviewer##10016:com.android.wallpaper.holospiral##10017:com.android.inputmethod.latin##10018:com.android.launcher##10019:com.android.wallpaper##10020:com.android.wallpaper.livepicker##10021:com.android.magicsmoke##10022:com.android.livewallpaper.microbesgl##10023:com.android.mms##10024:com.android.musicfx##10025:com.android.noisefield##10026:com.teslacoilsw.launcher##10027:com.android.packageinstaller##10028:com.android.phasebeam##10029:com.svox.pico##10030:com.google.android.apps.genie.geniewidget##10031:com.aokp.romcontrol##10032:com.android.sharedstoragebackup##10033:com.android.soundrecorder##10034:eu.chainfire.supersu##10035:com.aokp.swagpapers##10036:com.android.systemui##10037:com.tf.thinkdroid.sg##10038:com.teamhacksung.tvout##10039:com.aokp.unicornporn##10040:com.android.videoeditor##10041:com.android.musicvis##10042:com.android.voicedialer##10043:com.android.vpndialogs##10044:com.android.smspush##10045:com.google.android.gms##10045:com.google.android.gsf##10045:com.google.android.gsf.login##10045:com.google.android.location##10045:com.google.android.syncadapters.bookmarks##10045:com.google.android.syncadapters.contacts##10046:com.google.android.gm##10047:com.google.android.syncadapters.calendar##10048:com.google.android.ears##10049:com.google.android.feedback##10050:com.google.android.partnersetup##10051:com.google.android.tts##10052:com.google.android.inputmethod.latin.dictionarypack##10053:com.google.android.apps.uploader##10054:com.google.android.onetimeinitializer##10055:com.android.vending##10056:com.google.android.googlequicksearchbox##10057:com.google.android.setupwizard##10058:com.google.android.talk##10059:com.google.android.marvin.talkback##10060:com.google.android.voicesearch##10061:com.android.facelock##","Ext_Storage_A":"11572MB","Lock_Pattern_Visible":"0","Screen_Height":"800","User_Agent":"Mozilla\/5.0 (Linux; U; Android 4.1.1; zh-cn; GT-I9100 Build\/JRO03H) AppleWebKit\/534.30 (KHTML, like Gecko) Version\/4.0 Mobile Safari\/534.30","Device_Model":"GT-I9100","Date_Format":"yyyy-MM-dd","Android_ID":"7768b869740d8a7e","User_Packages":"10062:jackpal.androidterm##10063:com.herald.ezherald##10064:com.taobao.taobao##10065:com.sina.weibo##10066:com.kapp.ifont##10067:com.digiplex.game##10068:com.google.android.inputmethod.pinyin##10069:com.happyelements.AndroidAnimal##10070:com.wyhao31.Test##10071:com.qihoo.appstore##10072:com.mobfound.client##10073:com.qihoo360.mobilesafe##10074:com.wyhao31.app2##10075:com.wyhao31.testaccelerometer##","Ringsound":"默认铃声（Scarabaeus）","Build_Num":"samsung\/GT-I9100\/GT-I9100:4.1.1\/JRO03H\/XXLPQ:user\/release-keys","Storage_Structure":"\/cache 98M##\/data 1G##\/dev 414M##\/efs 19M##\/mnt\/asec 414M##\/mnt\/obb 414M##\/preload 503M##\/storage\/sdcard0 11G##\/system 503M##","Screen_Width":"480","12_24":"12","Serial":"unknown","Font_Size":"1.0","Int_Storage_A":"1529MB","Alarmsound":"默认铃声（Scandium）","Android_Ver":"4.1.1","IMEI":"359778044570859","Screen_Density":"240","Font_Types":"AndroidClock.ttf:4824##AndroidClock_Highlight.ttf:4824##AndroidClock_Solid.ttf:4824##AndroidEmoji.ttf:328252##AnjaliNewLipi-light.ttf:47408##Clockopia.ttf:6880##DroidNaskh-Regular-SystemUI.ttf:158148##DroidNaskh-Regular.ttf:91340##DroidSans-Bold.ttf:Roboto-Bold.ttf##DroidSans.ttf:Roboto-Regular.ttf##DroidSansArmenian.ttf:13856##DroidSansDevanagari-Regular.ttf:123372##DroidSansEthiopic-Regular.ttf:227928##DroidSansFallback.ttf:11534336##DroidSansGeorgian.ttf:21096##DroidSansHebrew-Bold.ttf:30280##DroidSansHebrew-Regular.ttf:30024##DroidSansMono.ttf:119380##DroidSansTamil-Bold.ttf:36448##DroidSansTamil-Regular.ttf:36308##DroidSansThai.ttf:35584##DroidSerif-Bold.ttf:185228##DroidSerif-BoldItalic.ttf:190304##DroidSerif-Italic.ttf:177560##DroidSerif-Regular.ttf:172916##Lohit-Bengali.ttf:139296##Lohit-Kannada.ttf:197028##Lohit-Telugu.ttf:174276##MTLmr3m.ttf:2871020##Roboto-Bold.ttf:77408##Roboto-BoldItalic.ttf:159868##Roboto-Italic.ttf:157248##Roboto-Light.ttf:105984##Roboto-LightItalic.ttf:109172##Roboto-Regular.ttf:291464##RobotoCondensed-Bold.ttf:103424##RobotoCondensed-BoldItalic.ttf:106736##RobotoCondensed-Italic.ttf:106160##RobotoCondensed-Regular.ttf:102864##","Root":"0","Auto_Timezone":"1","All_Sound":"Acheron,Adara,Aldebaran,Altair,Andromeda,Antares,Antimony,Aquila,Arcturus,Argo Navis,Argon,Barium,Beryllium,Betelgeuse,Boötes,Canis Major,Canopus,Capella,Carina,Cassiopeia,Castor,Centaurus,Cesium,Ceti Alpha,Cobalt,Copernicium,Curium,Cygnus,Deneb,Draco,Electra,Eridani,Fermium,Fluorine,Fomalhaut,Gallium,Girtab,Hassium,Helium,Hojus,Hydra,Iridium,Iridium,Krypton,Lalande,Lyra,Machina,Merope,Mira,Nasqueron,Neptunium,Nobelium,Orion,Palladium,Pegasus,Perseus,Plutonium,Polaris,Pollux,Procyon,Proxima,Pyxis,Radon,Regulus,Rigel,Rubidium,Scandium,Scarabaeus,Sceptrum,Selenium,Shaula,Sirius,Sirrah,Solarium,Spica,Strontium,Tejat,Testudo,Thallium,Themos,Upsilon,UrsaMinor,Vega,Vespa,Xenon,Zeta,Zirconium,","WIFI_MAC":"14:7d:c5:93:dd:c4\\n","Lock_Pattern_Vibrate":"0","Language":"中文","Auto_Rotate":"1","Time_Zone":"China Standard Time","Root_Dir_Structure":"acct##boot.txt##cache##charger##config##d##data##default.prop##dev##efs##etc##extSdCard##init##init.goldfish.rc##init.rc##init.smdk4210.rc##init.smdk4210.usb.rc##init.trace.rc##init.usb.rc##lpm.rc##mnt##preload##proc##res##sbin##sdcard##storage##sys##system##ueventd.goldfish.rc##ueventd.rc##ueventd.smdk4210.rc##usbdisk0##vendor##","Auto_Bright":"1"}}'
# fp = json.loads(fpStr)['uploadFP']
# NaiveBayes(fp)
