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
    for r in result:
        config[len(config)]={
            'DB-ID': int(r[0]),
            'type': 'fermenter',
            'name': r[1].encode("utf-8"),
            'sensor': [r[3], r[4], r[5]]}

    sql = "SELECT * from sensor"
    result = connection("r", sql)
    for r in result:
        config[len(config)]={
            'DB-ID': int(r[0]),
            'type': 'sensor',
            'name': r[2].encode("utf-8")}

        
    for x in range(len(config)):
        print(config[x])
        
    return config


def read_log_file (filenames):
    data = {}
    level = 0
    for filename in filenames:
        data_raw = []
        with open('./logs/'+filename+'.log') as file:
            csvReader = csv.reader(file)
            for row in csvReader:
                data_raw.append(row)

                try:
                    # Delete doubble entries
                    if data_raw[-1][1] == row[1] and data_raw[-2][1] == row[1] and data_raw[-3][1] == row[1]:
                        #print("!!")
                        #print("-1: "+str(data_raw[-1][1])+"-2: "+str(data_raw[-2][1])+"-3: "+str(data_raw[-3][1]))
                        data_raw.pop(-2)
                        
                    # Delete small changes if not Setpoint file
                    elif level > 0 and abs(float(row[1]) - float(data_raw[-2][1]))<0.5:
                        data_raw.pop(-1)
                except:
                    pass
            #print("========== data_raw ==========")
            #print(data_raw)
            
            for row in data_raw:
                if row[1] != 'None':
                    # Convert the Date to object
                    date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                    value = row[1]

                    try:
                       data[date][level] = float(value)
                    except:
                        data[date] = {}
                        data[date][level] = float(value)
                
                
                
        level = level + 1 
 
    return data
 
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
    
    # Prepare the list of Logfiles to read
    logs_to_read = [str(config[id]['type'])+'_'+str(config[id]['DB-ID'])]
    try:
        for sensor in config[id]['sensor']:
            logs_to_read.append('sensor_'+str(sensor))
    except:
        pass
    
    data = read_log_file(logs_to_read)
    return render_template('chart.html', data = data, config = config, title=config[id]['name'])

@cbpi.initalizer()
def init(cbpi):
    cbpi.app.register_blueprint(BetterChart, url_prefix='/BetterChart')


