"""
Created on June 4th, 2019

The purpose of this script is to operate the ADQ14DC-4A-VG-USB digitizer and
output data to HDF5 files using HDFWriterReader

@author: Dan Hudetz
"""

import numpy as np
import ctypes as ct
from HDFWriteRead import write
import epics
import modules.example_helpers as a
import sys
import os
import configReader
import threading

# Record settings
number_of_records  = 1
sample_skip = 1;
triggerdelay = 0;
channel_mask = 0xF;

# Set trig mode
trig_type = 2

#initializeing variables
ADQAPI=None
adq_cu=None
adq_num=None
number_of_channels=0
average=False
useChannels=""
input_range=None
samples_per_record=0
n_of_ADQ=0
numAverages=0
rollingAverage=[]

pv=configReader.getContents(os.getcwd()+'\PV.config')
config=configReader.getContents(os.getcwd()+'\config.config')

def reloadFolder():
    config=configReader.getContents(os.getcwd()+'\config.config')
    if "Scan Folder" in config:
        defaultFolder=config["Scan Folder"]
        if "\n" in defaultFolder:
            defaultFolder=defaultFolder[0:len(defaultFolder)-1]
    else:
        defaultFolder=os.getcwd()+"\Scans"

reloadFolder()

def writeData(header_list, numChannels, data):
    reloadFolder()
    scanNum=epics.caget(pv['Scan Number'])-1
    scan = write.scan(scanNum)
    
    coordHeader={}
    for i, key in enumerate(pv):
        if i>2:
            coordHeader.update({key:epics.caget(pv[key])})
    coord = write.coordinate(scan, coordHeader)
    for ch in range(numChannels):
        if useChannels[ch]=='1':
            channelHeader={'SerialNumber':header_list[0].SerialNumber,
            'SamplePeriod':header_list[0].SamplePeriod*.125, 'InputRange':input_range[ch]}
            write.channel(coord, ch, data[ch], channelHeader)
    scan.close()

def processAverage(newData, weight):
    global rollingAverage
    rollingAverage*=weight
    rollingAverage=np.average([rollingAverage, newData], axis=0)
    rollingAverage/=(weight+1)

def initialize(samples, pretriggerPercentage):
    global ADQAPI,adq_cu,adq_num,number_of_channels,input_range, samples_per_record, n_of_ADQ, numAverages, config, useChannels, average
    
    #Setting variables
    samples_per_record=samples
    pretrigger = int(pretriggerPercentage*samples*.01)
    config=configReader.getContents(os.getcwd()+'\config.config')
    if 'Num Repeats' in config:
        numAverages=int(config['Num Repeats'])
    else:
        numAverages=1
    if 'Use Channels' in config:
        useChannels=config['Use Channels']
    else:
        useChannels='0000'
    if 'Auto Average' in config:
        if config['Auto Average'] =='1':
            average=True
        else:
            average=False
        
    ADQAPI = a.adqapi_load()
    
    # Create ADQControlUnit
    adq_cu = ct.c_void_p(ADQAPI.CreateADQControlUnit())
    
    # Enable error logging from ADQAPI
    ADQAPI.ADQControlUnit_EnableErrorTrace(adq_cu, 65536, '.')
    
    # Find ADQ devices
    ADQAPI.ADQControlUnit_FindDevices(adq_cu)
    n_of_ADQ  = ADQAPI.ADQControlUnit_NofADQ(adq_cu)
    n_of_failed_ADQ  = ADQAPI.ADQControlUnit_GetFailedDeviceCount(adq_cu)
    if n_of_failed_ADQ > 0:
      print(n_of_failed_ADQ, 'connected devices failed initialization.')
    print('Number of ADQ found:  {}'.format(n_of_ADQ))
    
    # Exit if no devices were found
    if n_of_ADQ < 1:
        print('No ADQ connected.')
        stop()
        sys.exit()
    
    # Select ADQ
    if n_of_ADQ > 1:
        adq_num = int(input('Select ADQ device 1-{:d}: '.format(n_of_ADQ)))
    else:
        adq_num = 1
    
    a.print_adq_device_revisions(ADQAPI, adq_cu, adq_num)
    
    # Set clock source
    ADQ_CLOCK_INT_INTREF = 0
    ADQAPI.ADQ_SetClockSource(adq_cu, adq_num, ADQ_CLOCK_INT_INTREF)
    
    # Setup test pattern
    ADQAPI.ADQ_SetTestPatternMode(adq_cu, adq_num, 0)
    
    success = ADQAPI.ADQ_SetTriggerMode(adq_cu, adq_num, trig_type)
    if (success == 0):
        print('ADQ_SetTriggerMode failed.')
    
    # Setup data processing (should be done before multirecord setup)
    ADQAPI.ADQ_SetSampleSkip(adq_cu, adq_num, sample_skip)
    ADQAPI.ADQ_SetPreTrigSamples(adq_cu, adq_num, pretrigger)
    ADQAPI.ADQ_SetTriggerDelay(adq_cu, adq_num, triggerdelay)
    
    # Setup multirecord
    ADQAPI.ADQ_MultiRecordSetChannelMask(adq_cu, adq_num, channel_mask)
    ADQAPI.ADQ_MultiRecordSetup(adq_cu, adq_num, number_of_records, samples_per_record)
    
    # Get number of channels from device
    number_of_channels = ADQAPI.ADQ_GetNofChannels(adq_cu, adq_num)
    # Get the input range
    input_range=[ct.c_float(), ct.c_float(), ct.c_float(), ct.c_float()]
    for ch in range(number_of_channels):
        ADQAPI.ADQ_GetInputRange(adq_cu, adq_num, ch+1, ct.byref(input_range[ch]))
        input_range[ch]=input_range[ch].value/1000
    
    print("Number of Channels: "+str(number_of_channels))

def newCoordinate():
    global rollingAverage
    counter=0
    rollingAverage=[np.zeros(number_of_records*samples_per_record, dtype=np.float16),
                    np.zeros(number_of_records*samples_per_record, dtype=np.float16),
                    np.zeros(number_of_records*samples_per_record, dtype=np.float16),
                    np.zeros(number_of_records*samples_per_record, dtype=np.float16)]
    while(counter<numAverages):
        # Arm acquisition
        ADQAPI.ADQ_DisarmTrigger(adq_cu, adq_num)
        ADQAPI.ADQ_ArmTrigger(adq_cu, adq_num)
        
        # Allocate target buffers for intermediate data storage
        target_buffers = (ct.POINTER(ct.c_int16*(number_of_records*samples_per_record))*number_of_channels)()
        for bufp in target_buffers:
            bufp.contents = (ct.c_int16*(number_of_records*samples_per_record))()
        
        # Create some buffers for the full records
        newData = [np.zeros(number_of_records*samples_per_record, dtype=np.float16),
                   np.zeros(number_of_records*samples_per_record, dtype=np.float16),
                   np.zeros(number_of_records*samples_per_record, dtype=np.float16),
                   np.zeros(number_of_records*samples_per_record, dtype=np.float16)]
        # Allocate target buffers for headers
        header_list = (a.HEADER*number_of_records)()
        target_headers = ct.POINTER(a.HEADER*number_of_records)()
        target_headers.contents = header_list
        target_headers_vp = ct.cast(ct.pointer(target_headers), ct.POINTER(ct.c_void_p))
        
        print('Waiting for trigger...')
        # Collect data until all requested records have been recieved
        records_completed = 0
        records_available = 0
    
        while (records_completed < number_of_records):
            records_available = ADQAPI.ADQ_GetAcquiredRecords(adq_cu, adq_num)
            new_records = records_available - records_completed
            if new_records > 0:
                # Fetch data and headers into target buffers
                print("Trigger detected!")
                status = ADQAPI.ADQ_GetDataWHTS(adq_cu, adq_num, target_buffers, target_headers,None,number_of_records*samples_per_record,
                                                2,records_completed,new_records,channel_mask,0,samples_per_record,0x00)
                if status == 0:
                    print('GetDataWH failed!')
                    stop()
                for ch in range(0,number_of_channels):
                    if useChannels[ch]=='1':
                        data_buf = np.frombuffer(target_buffers[ch].contents, dtype=np.int16, count=(samples_per_record*new_records))
                        newData[ch] = data_buf
                target_headers_vp.contents.value += new_records*ct.sizeof(a.HEADER)
                if average:
                    if counter == 0:
                        rollingAverage=newData
                    else:
                        averagingThread=threading.Thread(target=lambda:processAverage(newData, counter))
                        averagingThread.start()
                else:
                    individualWriteThread=threading.Thread(target=lambda:writeData(header_list, number_of_channels, newData))
                    individualWriteThread.start()
                    print('Writing individual repeat to HDF5.')
                records_completed += new_records
                counter+=1
    if average:
        averageWriteThread=threading.Thread(target=lambda:writeData(header_list, number_of_channels, rollingAverage))
        averageWriteThread.start()
        print('Coordinate complete, writing average to HDF5.')
    else:
        print('Coordinate complete.')

def stop():
    global n_of_ADQ
    # Close multirecord
    ADQAPI.ADQ_MultiRecordClose(adq_cu, adq_num)
    # Delete ADQControlunit
    ADQAPI.DeleteADQControlUnit(adq_cu)
    
def getNumDevices():
    return n_of_ADQ