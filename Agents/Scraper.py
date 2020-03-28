'''
 * The MIT License (MIT)
 * Copyright (c) Arturo Rodriguez All rights reserved.
 * Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 '''
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
    # This section gets executed by the Agent according to the cron-job definition below
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
    "0 0 * ? * *", #Cron Schedule
    qae.Utils.SetFunction("Job", qae.Job(Job))
    )