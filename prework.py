#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv, math, MySQLdb

def writeDistinctFPtoDB(sourceFileName):
    """
        write distinct device fingerprint to database
    """
    
    csvReadFile = open(sourceFileName, 'rb')
    reader = csv.reader(csvReadFile)
    fpDict = {}
    count = 0
    colList = []
    for entry in reader:
        if count == 0:
            colList = entry
            count += 1
            continue
        imei = entry[2]
        fpDict[imei] = entry

    csvReadFile.close()
    
    try:
        conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
        cur=conn.cursor()
        for imei in fpDict:
            fp = fpDict[imei]
            sqlcmd = 'INSERT INTO androidfingerprint.fp_distinct(FpID, Date, IMEI, Android_ID, Kernel_Version, Android_Ver, Build_Num, User_Agent, WIFI_ON, WIFI_MAC, Bluetooth_MAC, Device_Model, Device_Manufacturer, Serial, Screen_Density, Screen_Width, Screen_Height, Time_Zone, `12_24`, Date_Format, Auto_Time, Auto_Timezone, Screen_Timeout, WIFI_Notification, WIFI_Sleep, Access_Loc, LockPattern, Lock_Pattern_Visible, Lock_Pattern_Vibrate, Input_Methods, `Language`, Root, Font_Size, Font_Types, User_Packages, System_Packages, Int_Storage_A, Int_Storage_T, Ext_Storage_A, Ext_Storage_T, Storage_Structure, Root_Dir_Structure, All_Sound, Notesound, Alarmsound, Ringsound, Sound_Effect, Auto_Bright, Auto_Rotate, Show_Pwd, Wallpaper_md5) VALUES(0, "%s", "%s", "%s", "%s", "%s", "%s", "%s", %s, "%s", "%s", "%s", "%s", "%s", %s, %s, %s, "%s", %s, "%s", %s, %s, %s, %s, %s, %s, %s, %s, %s, "%s", "%s", %s, %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", %s, %s, %s, %s, %s);' % (fp[1], fp[2], fp[3], fp[4], fp[5], fp[6], fp[7], fp[8], fp[9], fp[10], fp[11], fp[12], fp[13], fp[14], fp[15], fp[16], fp[17], fp[18], fp[19], fp[20], fp[21], fp[22], fp[23], fp[24], fp[25], fp[26], fp[27], fp[28], fp[29], fp[30], fp[31], fp[32], fp[33], fp[34], fp[35], fp[36], fp[37], fp[38], fp[39], fp[40], fp[41], fp[42], fp[43], fp[44], fp[45], fp[46], fp[47], fp[48], fp[49], fp[50])
            cur.execute(sqlcmd)
        
        conn.commit()    
        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %s: %s" % (e.args[0], e.args[1])

def writeAllFPtoDB(sourceFileName):
    """
        write all device fingerprint to database
    """
    csvReadFile = open(sourceFileName, 'rb')
    reader = csv.reader(csvReadFile)
    count = 0
    colList = []
    
    try:
        conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
        cur=conn.cursor()
        for entry in reader:
            if count == 0:
                colList = entry
                count += 1
                continue
            fp = entry
            sqlcmd = 'INSERT INTO androidfingerprint.fp_all(id, Date, IMEI, Android_ID, Kernel_Version, Android_Ver, Build_Num, User_Agent, WIFI_ON, WIFI_MAC, Bluetooth_MAC, Device_Model, Device_Manufacturer, Serial, Screen_Density, Screen_Width, Screen_Height, Time_Zone, `12_24`, Date_Format, Auto_Time, Auto_Timezone, Screen_Timeout, WIFI_Notification, WIFI_Sleep, Access_Loc, LockPattern, Lock_Pattern_Visible, Lock_Pattern_Vibrate, Input_Methods, `Language`, Root, Font_Size, Font_Types, User_Packages, System_Packages, Int_Storage_A, Int_Storage_T, Ext_Storage_A, Ext_Storage_T, Storage_Structure, Root_Dir_Structure, All_Sound, Notesound, Alarmsound, Ringsound, Sound_Effect, Auto_Bright, Auto_Rotate, Show_Pwd, Wallpaper_md5) VALUES(0, "%s", "%s", "%s", "%s", "%s", "%s", "%s", %s, "%s", "%s", "%s", "%s", "%s", %s, %s, %s, "%s", %s, "%s", %s, %s, %s, %s, %s, %s, %s, %s, %s, "%s", "%s", %s, %s, "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", %s, %s, %s, %s, %s);' % (fp[1], fp[2], fp[3], fp[4], fp[5], fp[6], fp[7], fp[8], fp[9], fp[10], fp[11], fp[12], fp[13], fp[14], fp[15], fp[16], fp[17], fp[18], fp[19], fp[20], fp[21], fp[22], fp[23], fp[24], fp[25], fp[26], fp[27], fp[28], fp[29], fp[30], fp[31], fp[32], fp[33], fp[34], fp[35], fp[36], fp[37], fp[38], fp[39], fp[40], fp[41], fp[42], fp[43], fp[44], fp[45], fp[46], fp[47], fp[48], fp[49], fp[50])
            cur.execute(sqlcmd)
            count += 1
        
        conn.commit()
        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %s: %s" % (e.args[0], e.args[1])

    csvReadFile.close()

def writeHistoryToDB():
    """
        write all history to database
    """
    try:
        conn=MySQLdb.connect(host = 'localhost', user = 'root', passwd = 'ibmc51', db = 'androidfingerprint', port = 3306, charset="utf8")
        cur=conn.cursor()
        sqlcmd = 'SELECT id, Date, IMEI FROM androidfingerprint.fp_all;'
        cur.execute(sqlcmd)
        alldata = cur.fetchall()
        allfp = {}
        for line in alldata:
            if line[2] not in allfp:
                allfp[line[2]] = [];
            allfp[line[2]].append(line[:2])

        sqlcmd = 'SELECT FpID, IMEI FROM androidfingerprint.fp_distinct;'
        cur.execute(sqlcmd)
        alldata = cur.fetchall()
        for line in alldata:
            FpID = line[0]
            imei = line[1]
            for item in allfp[imei]:
                sqlcmd = 'INSERT INTO androidfingerprint.fp_history(FpID, id, Date) VALUES(%s, %s, "%s");' % (FpID, item[0], item[1])
                cur.execute(sqlcmd)
            conn.commit()

        cur.close()
        conn.close()
    except MySQLdb.Error,e:
        print "Mysql Error %s: %s" % (e.args[0], e.args[1])


quasiIdSet = set(['Kernel_Version', 'Android_Ver', 'Build_Num', 'User_Agent', 'Time_Zone', '12_24', 'Date_Format', 'Auto_Time', 'Auto_Timezone', 'Screen_Timeout', 'WIFI_Notification', 'WIFI_Sleep', 'Access_Loc', 'LockPattern', 'Lock_Pattern_Visible', 'Lock_Pattern_Vibrate', 'Input_Methods', 'Language', 'Root', 'Font_Size', 'Font_Types', 'User_Packages', 'System_Packages', 'Storage_Structure', 'All_Sound', 'Notesound', 'Alarmsound', 'Ringsound', 'Sound_Effect', 'Auto_Bright', 'Auto_Rotate', 'Show_Pwd', 'Wallpaper_md5'])
condProbs = {}

def getCondProbs(sourceFileName):
    csvReadFile = open(sourceFileName, 'rb')
    reader = csv.reader(csvReadFile)
    fpDict = {}
    count = 0
    colList = []
    colLen = 0

    for key in quasiIdSet:
        condProbs[key] = {0: 0, 1: 0}
        
    for entry in reader:
        if count == 0:
            colList = entry
            colLen = len(colList)
            count += 1
            continue
        fp = {}
        for i in xrange(colLen):
            fp[colList[i]] = entry[i]
            
        if fp['IMEI'] in fpDict:
            oldfp = fpDict[fp['IMEI']]
            for key in quasiIdSet:
                if key != 'Font_Types' and key != 'User_Packages' and key != 'System_Packages' and key != 'All_Sound' and key != 'Storage_Structure':
                    if oldfp[key] != fp[key]:
                        condProbs[key][1] += 1
                    else:
                        condProbs[key][0] += 1
        
        fpDict[fp['IMEI']] = fp
        count += 1
    csvReadFile.close()
    print count-1
    print condProbs


if __name__ == "__main__":
    #writeDistinctFPtoDB('fp_data_20141227_new.csv')
    #writeAllFPtoDB('fp_data_20141227_new.csv')
    writeHistoryToDB()
    #getCondProbs('/var/www/android/fp_data_20141227_new.csv')
    #print len(quasiIdSet)
