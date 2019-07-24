"""
Created on July 11th, 2019

The purpose of this script is to quickly convert HDF5 DAQ files to a viewScopeData readable binary file type.

@author: Dan Hudetz
"""

from HDFWriteRead import read
import os
import configReader

config=configReader.getContents(os.getcwd()+"\config.txt")
if "Scan Folder" in config:
    defaultFolder=config["Scan Folder"]
    if "\n" in defaultFolder:
        defaultFolder=defaultFolder[0:len(defaultFolder)-1]
else:
    defaultFolder=os.getcwd()+"\Scans"

scanNum=575
newFilePath=defaultFolder+'\\'+str(scanNum)+'.dat'
timeStep=2.0E-9

oldFile=read.scan(scanNum)
newFile=open(newFilePath, 'w')

scanHeader=read.scanHeader(oldFile)

for i in range(len(read.coordinateNames(scanNum))):
    coord=read.coordinate(oldFile, i)
    coordHeader=read.coordinateHeader(coord)
    numberOfChannels=0
    for c in str(scanHeader["Use Channels"]):
        if c=='1':
            numberOfChannels+=1
    coordLine="FileType=DataGrabberBinary X="+str(coordHeader["X"])+" Y="+str(coordHeader["Y"])+" Theta="+str(coordHeader["Theta"])+" NumberOfChannels="+str(numberOfChannels)
    coordLine+=" TimeStamp="+scanHeader["Date"]+"_"+scanHeader["Time"]
    for key in coordHeader:
        if key!="X" and key!="Y" and key!="Theta":
            coordLine+=" "+key+"="+str(coordHeader[key])
    coordLine+="\n"
    newFile.write(coordLine)
    for i in range(len(read.channelNames(scanNum, i))):
        channel=read.channel(coord, i)
        channelHeader=read.channelHeader(channel)
        channelLine="Channel="+str(i)+" UserDescription=PINDiode DAQDevice="+scanHeader["Digitizer Name"]
        channelLine+=" NumAverages=16 RecordLength="+str(scanHeader["Number of Samples"])+" FirstPointTime=0.0 TimeStep="+str(channelHeader["SamplePeriod"])+" DynamicRangeBits=16 BinaryDataType=short Volts=Scale*ADCValue+Offset Scale=6.25E-6 Offset=0.0"
        for key in channelHeader:
            if key!="SamplePeriod":
                channelLine+=" "+key+"="+str(channelHeader[key])
        channelLine+="\n"
        newFile.write(channelLine)
        
oldFile.close()
newFile.close()