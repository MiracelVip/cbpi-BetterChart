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
    sql = "SELECT * from kettle"
    kettle = connection("r", sql)
    sql = "SELECT * from fermenter"
    fermenter = connection("r", sql)
    pair=[]
    
    for k in kettle:
        pair.append(['k', str(k[0]), k[1], k[2]])
     
    for f in fermenter:
        pair.append(['f', str(f[0]), f[1], f[3], f[4], f[5]])
        
    #print (pair)
    return pair


def read_log_file (filenames):
    data = {}
    level = 0
    for filename in filenames:
        data_raw = []
        with open('./logs/'+filename) as file:
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
    config = read_config()
    
    return render_template('BetterChart.html', config = config)

@BetterChart.route('/<type>/<id>', methods=['GET'])
def chart2(type, id):
    config = read_config()
    for c in config:
        if c[0] == type and c[1] == id:
            select = c
            break
    
    if select[0] == 'k':
        read = ["kettle_"+select[1]+".log", "sensor_"+select[3]+".log"]
        
        data=read_log_file(read)
        return render_template('chart.html', log = select[2], data = data, config = config)
        
    if select[0] == 'f':
        read = ["fermenter_"+select[1]+".log", "sensor_"+select[3]+".log"]
        
        data=read_log_file(read)
        return render_template('chart.html', log = select[2], data = data, config = config)
        





@cbpi.initalizer()
def init(cbpi):
    cbpi.app.register_blueprint(BetterChart, url_prefix='/BetterChart')


