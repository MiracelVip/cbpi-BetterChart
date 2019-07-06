# -*- coding: utf-8 -*-
import os
from subprocess import Popen, PIPE, call

from modules import cbpi
import json
from flask import Blueprint, render_template, jsonify, request, url_for
import sqlite3
from os import listdir
import csv
from datetime import datetime

v = "1.1"

def connection (task, sql): 

    try:
        connection = sqlite3.connect(os.getcwd()+'/craftbeerpi.db')
        cursor = connection.cursor()
        cursor.execute(sql)
        
    except sqlite3.Error as e:
        print ("Database error: %s" % e)
    except Exception as e:
        print("Exception in _query: %s" % e)
 
    if task == "r":
        rows = cursor.fetchall()
        cursor.close()
        return rows
    else:
        connection.commit()
        cursor.close()
        return None

def read_config():
    config = {}

    sql = "SELECT * from kettle"
    result = connection("r", sql)
    for r in result:
        config[len(config)]={
            'DB-ID': int(r[0]),
            'type': 'kettle',
            'name': r[1].encode("utf-8"),
            'sensor': [r[2]]}
    
    sql = "SELECT * from fermenter"
    result = connection("r", sql)
    # Dont add empty sensor!
    for r in result:
        sensor = []
        for s in [r[3], r[4], r[5]]:
            if s != '':
                sensor.append(s)
                
        config[len(config)]={
            'DB-ID': int(r[0]),
            'type': 'fermenter',
            'name': r[1].encode("utf-8"),
            'sensor': sensor}

    sql = "SELECT * from sensor"
    result = connection("r", sql)
    for r in result:
        config[len(config)]={
            'DB-ID': int(r[0]),
            'type': 'sensor',
            'name': r[2].encode("utf-8")}

        
    for x in range(len(config)):
        print(config[x])
    print ("____________________________________")    
    return config


def read_log_file (id):
    data = {}
    ids_to_read = []
    config = read_config()
    level = 0

    #What do I have to read?    
    ids_to_read.append([config[id]['type'], config[id]['DB-ID'], config[id]['name']])

    if config[id]['type'] != 'sensor':
        for s in config[id]['sensor']:
            sql = "SELECT * from sensor WHERE id ="+str(s)
            result = connection("r", sql)
            for r in result:
                ids_to_read.append(['sensor', int(r[0]), r[2].encode("utf-8")])

    #print ("ID's to read")
    #print (ids_to_read)
    #print ('##########')
    
    #Read all files one by one
    for i in ids_to_read:
        
        data_raw = []
        path = './logs/'+i[0]+"_"+str(i[1])+'.log'
        # Open CSV file
        with open(path, 'r') as csvFile:
            reader = csv.reader(csvFile)
            try:
                for row in reader:
                    data_raw.append(row)
                    
                    try:
                        # Delete doubble entries
                        if data_raw[-1][1] == row[1] and data_raw[-2][1] == row[1] and data_raw[-3][1] == row[1]:
                            #print("!!")
                            #print("-1: "+str(data_raw[-1][1])+"-2: "+str(data_raw[-2][1])+"-3: "+str(data_raw[-3][1]))
                            data_raw.pop(-2)
                            
                        # Delete small changes if not Setpoint file
                        elif i[0] == 'sensor' and abs(float(row[1]) - float(data_raw[-2][1]))<0.5:
                            data_raw.pop(-1)
                    except:
                        pass
                    
            except:
                print ("cant read "+path)
        csvFile.close()
        
        for row in data_raw:
            if row[1] != 'None':
                # Convert the Date to object
                date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                value = float(row[1])

            try:
                data[date][level] = value
            except:
                data[date] = {}
                data[date][level] = value
    
        #update level
        level += 1
    return ({'data': data,'ids_to_read': ids_to_read})
 
BetterChart = Blueprint('BetterChart', 
               __name__, 
               static_url_path = '/modules/plugins/cbpi-BetterChart/static',
               static_folder = './static',
               template_folder = './template')

@BetterChart.route('/', methods=['GET'])
def start():
    return render_template('index.html', config = read_config(), title="Dashboard")

@BetterChart.route('/chart/<int:id>', methods=['GET'])
def chart(id):
    config = read_config()
    data = read_log_file(id)

    return render_template('chart.html', data = data, config = config, title=config[id]['name'])
    
@BetterChart.route('/settings', methods=['GET'])
def settings():
    config = read_config()
    
    return render_template('settings.html', config = config, title="Settings")

@cbpi.initalizer()
def init(cbpi):
    cbpi.app.register_blueprint(BetterChart, url_prefix='/BetterChart')

