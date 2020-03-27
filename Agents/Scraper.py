import System
import QuantApp.Kernel as qak
import QuantApp.Engine as qae

import datetime
import time
import pickle
import json

import covid19.data as cov19


defaultID = "e2750a32-3e92-436a-8078-263b072f0e40"

def Add(id, data):
    pass
    
def Exchange(id, data):
    pass
    
def Remove(id, data):
    pass
    
def Load(data):
    pass
    
def Body(data):
    return data

def Job(timestamp, data):
    print("COVID19 Scraping Job: " + str(timestamp) + " --> " + str(data))
    cov19.Load(True)
    

def pkg():
    return qae.FPKG(
    defaultID, #ID
    "c68ca7c8-c9b6-4ded-b25a-2867f10a150a", #Workspace ID
    "COVID19 Scraper Agent", #Name
    "COVID19 Scraper Agent", #Description
    None, #M ID Listener
    qae.Utils.SetFunction("Load", qae.Load(Load)), 
    qae.Utils.SetFunction("Add", qak.MCallback(Add)), 
    qae.Utils.SetFunction("Exchange", qak.MCallback(Exchange)), 
    qae.Utils.SetFunction("Remove", qak.MCallback(Remove)), 
    qae.Utils.SetFunction("Body", qae.Body(Body)), 
    "0 * * ? * *", #Cron Schedule
    qae.Utils.SetFunction("Job", qae.Job(Job))
    )