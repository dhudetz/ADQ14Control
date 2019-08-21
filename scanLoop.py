"""
Created on Wed Jun 19 15:10:30 2019

This is the loop that initializes and runs the  ADQ14DC-4A-VG-USB digitizer
while communicating to EPICS. This is the script you would run to aquire data
using the digitizer.

@author: Dan Hudetz
"""
import epics
import ADQ14
import threading
import configReader
import os

scanStatus=0
run=False
initializing=False
pv=configReader.getContents(os.getcwd()+'\PV.config')

# the main scan loop
def scanLoop():
    global scanStatus, run
    while(run):
        #check for new scan
        busy=epics.caget(pv["Busy Button"])
        if busy==1:
            print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
            #tell EPICS that ADQ is no longer busy
            try:
                ADQ14.newCoordinate()
                epics.caput(pv["Busy Button"], 0)
            except Exception as e:
                print(e)
                print("Scan loop failed while attempting to take new coordinate.")
                stop()
                break
            print("Waiting for motors...")
            #tell EPICS coordinate is done
            scanStatus=epics.caget(pv["Scan Button"])
            #check if scan is ended
            if scanStatus==0:
                print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
                print("End of scan.\n")

# initilize the digitizer and start the scan loop
def initialize(numSamples, pretriggerPercentage):
    global scanStatus, run, initializing
    initializing=True
    run=True
    print("Starting scan loop.")
    epics.caput(pv["Busy Button"], 0)
    ADQ14.initialize(numSamples, pretriggerPercentage)
    initializing=False
    t1=threading.Thread(target=scanLoop)
    t1.start()

# check if the initilization ongoing
def getInitializeStatus():
    return initializing

#check if the scan loop is in progress
def getRunStatus():
    return run

# properly shut down the scan loop
def stop():
    global run
    if run and not initializing:
        print('Shutting down scan loop')
        ADQ14.stop()
        run=False
    
# start a new scan
def scan():
    global scanStatus
    if run and not initializing:
        epics.caput(pv["Scan Button"],1)

# pass on the number of devices (0 or 1)
def getNumDevices():
    return ADQ14.getNumDevices()