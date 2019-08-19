"""
Created on Fri Jun 14 11:13:50 2019

The purpose of this script is to read and write DAQ files in HDF5 with 
attributes for each coordinate scanned and each channel of that coordinate.

Hierarchy:
Scan_xxx.h5
    Coordinate_xxx
        Channel_x
            Data

@author: Dan Hudetz
"""
import os
import h5py as hdf
import numpy as np
import datetime
import gc
import configReader

config=configReader.getContents(os.getcwd()+"\config.config")
if "Scan Folder" in config:
    defaultFolder=config["Scan Folder"]
    if "\n" in defaultFolder:
        defaultFolder=defaultFolder[0:len(defaultFolder)-1]
else:
    defaultFolder=os.getcwd()+"\Scans"

class write:
    def scan(scanNum):
        write.close()
        if not os.path.exists(defaultFolder):
            os.mkdir(defaultFolder)
        scanString=str(scanNum)
        while(len(scanString)<3):
            scanString='0'+scanString
        newFile=False
        if not os.path.exists(defaultFolder+ '\Scan_' + scanString + '.h5'):
            newFile=True
        file = hdf.File(defaultFolder+ '\Scan_' + scanString + '.h5', 'a') #a for general access
        if newFile:
            file.attrs.create("# Coords", 0)
            file.attrs.create("TimeStamp", datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), dtype="S20")
            config=configReader.getContents(os.getcwd()+"\config.config")
            for key in config:
                file.attrs.create(key, config[key], dtype="S60")
        return file
    
    def specificCoordinate(file, coordNum):
        coordString=str(coordNum)
        while(len(coordString)<3):
            coordString='0'+coordString
        coordString='Coordinate_' + coordString
        try:
            coord = file.get(list(file.items())[int(coordNum)][0]) #second index of items is just the name
        except:
            file.close()
            pass
        return coord
    
    def coordinate(file, coordHeader={}):
        coordNum=file.attrs.get("# Coords")
        file.attrs.modify("# Coords", coordNum+1)
        coordString=str(coordNum)
        while(len(coordString)<3):
            coordString='0'+coordString
        coordString='Coordinate_' + coordString
        if len(coordHeader)==0:
            try:
                coord = file.get(list(file.items())[int(coordNum)][0]) #second index of items is just the name
            except:
                file.close()
                raise IndexError("Coordinate does not exist")
            return coord
        else:
            try:
                coord = file.create_group(coordString)
            except:
                file.close()
                raise RuntimeError("Attempted to write a coordinate which already exists")
            for key in coordHeader:
                coord.attrs.create(key, coordHeader[key])
            coord.attrs.create('Valid', 1)
            return coord
        
    def channel(coordinate, channelNum, dat, channelHeader={}):   
        try:
            channel = coordinate.create_dataset('Channel_' + str(channelNum), data=dat, dtype='float16')
        except:
            write.close()
            raise RuntimeError("Attempted to write channel data which already exists")
        for key in channelHeader:
            channel.attrs.create(key, channelHeader[key])
        return channel
    
    def updateAttribute(target, key, value):
        target.attrs.modify(key, value)

    def close():
        for obj in gc.get_objects():   # Browse through ALL objects
            if isinstance(obj, hdf.File):   # Just HDF5 files
                try:
                    obj.close()
                except:
                    pass
class read:
    def scan(scanNum):
        scanString=str(scanNum)
        while len(scanString)<3:
            scanString="0"+scanString   
        file = hdf.File(defaultFolder+'\Scan_' + scanString + '.h5', 'r') #r for write access
        return file
    
    def scanHeader(file):
        rawAttrs=file.attrs.items()
        attrs={}
        for attr in rawAttrs:
            attrs.update({attr[0]:attr[1]})
        attrs=read.filterStrings(attrs)
        return attrs
    
    def coordinate(file, coordNum): #the coord number must start at 0 and move up by 1
        try:
            coord = file.get(list(file.items())[int(coordNum)][0]) #second index of items is just the name
        except:
            raise IndexError("Coordinate does not exist")
        return coord
    
    def coordinateHeader(coordinate):
        rawAttrs=coordinate.attrs.items()
        attrs={}
        for attr in rawAttrs:
            attrs.update({attr[0]:attr[1]})
        attrs=read.filterStrings(attrs)
        return attrs
    
    def channel(coordinate, channelNum):
        channels=coordinate.items()
        for i in range(len(channels)):
            if i == int(channelNum):
                return coordinate.get(list(channels)[i][0]) #the second index is just the name of the channel
        raise RuntimeError("Channel does not exist.")
    
    def channelData(channel):
        return np.array(channel)
    
    def channelHeader(channel):
        rawAttrs=channel.attrs.items()
        attrs={}
        for attr in rawAttrs:
            attrs.update({attr[0]:attr[1]})
        attrs=read.filterStrings(attrs)
        return attrs
    
    def coordinateNames(scanNum):
        file=read.scan(scanNum)
        names=[]
        for i in file.items():
            names.append(i[0])
        file.close()
        return names
    
    def channelNames(scanNum, coordNum):
        file=read.scan(scanNum)
        coord=read.coordinate(file, coordNum)
        names=[]
        for i in coord.items():
            names.append(i[0])
        file.close()
        return names

    def filterStrings(header):
        for key in header.keys():
            try:
                header[key] = header[key].decode()
                if "\n" in header[key]:
                    header[key]=header[key][0:len(header[key])-1]
            except AttributeError:
                pass
        return header
                