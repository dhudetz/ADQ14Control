"""
Created on Mon Jun 10 11:12:57 2019

This GUI controls and views the attributes and graphs of HDF5 data
aquisition files from the ADQ14DC-4A-VG-USB digitizer.

@author: Dan Hudetz
"""
import tkinter as t
import tkinter.ttk as ttk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from HDFWriteRead import read
from HDFWriteRead import write
from matplotlib.figure import Figure
import os
import numpy as np
import threading
import scanLoop
import configReader
import epics
from random import randrange

def scanChange(event):
    updateCoords()
    readScanAttributes()

def coordChange(event):
    updateChannels()
    readCoordinateAttributes()
    
def channelChange(event):
    readChannelAttributes()

def updateScans():
    scansList=[]
    if os.path.exists(defaultFolder):
        for file in os.listdir(defaultFolder):
            if file.endswith(".h5"):
                split1=file.split('_')
                split2=split1[1].split('.')
                scansList.append(split2[0])
        scans.configure(values=scansList)
        try:
            scans.current(len(scansList)-1) #set the selected item
        except:
            pass
        updateCoords()

def readValidity():
    scanNum=scans.get()
    coordNum=coordinates.get()
    scan=read.scan(scanNum)
    coord=read.coordinate(scan, coordNum)
    attrs=read.coordinateHeader(coord)
    scan.close()
    if attrs['Valid']==1:
        return True
    else:
        return False
    
def updateValidity():
    if readValidity():
        validCheck.configure(bg="#e3ebd5", fg="black", text="Valid Coordinate")
        validCheck.select()
    else:
        validCheck.configure(bg="red", fg="white", text="Invalid Coordinate")
        validCheck.deselect()
    
def flipValidity():
    scanNum=scans.get()
    coordNum=coordinates.get()
    try:
        scan = write.scan(scanNum)
    except:
        write.close()
        scan = write.scan(scanNum)
    coord = write.specificCoordinate(scan, coordNum)
    if readValidity():
        validCheck.configure(bg="red", fg="white", text="Invalid Coordinate")
        write.updateAttribute(coord, 'Valid', 0)
        readCoordinateAttributes()
    else:
        validCheck.configure(bg="#e3ebd5", fg="black", text="Valid Coordinate")
        write.updateAttribute(coord, 'Valid', 1)
        readCoordinateAttributes()
    scan.close()
    
def updateCoords():
    try:
        coordsList=read.coordinateNames(scans.get())
        for i in range(len(coordsList)):
            split1=coordsList[i].split('_')
            coordsList[i]=split1[1]
        coordinates.configure(values=coordsList)
        try:
            coordinates.current(0) #set the selected item
            updateChannels()
        except:
            pass
    except:
        print("No scans in the /Scans")

def updateChannels():
    channelsList=read.channelNames(scans.get(), coordinates.get())
    for i in range(len(channelsList)):
        split1=channelsList[i].split('_')
        channelsList[i]=channelNames[int(split1[1])]
    channels.configure(values=channelsList)
    channels.current(0) #set the selected it
    updateValidity()

def readScanAttributes():
    selectedScan=scans.get()
    scan = read.scan(selectedScan)
    attributes=read.scanHeader(scan)
    message="SCAN "+str(selectedScan)+":\n"
    for k in attributes.keys():
        message=message+str(k)+' = '+str(attributes[k])+'\n'
    attributesMessage.configure(text=message)

def readCoordinateAttributes():
    scanNum=scans.get()
    coordNum=coordinates.get()
    scan=read.scan(scanNum)
    coord=read.coordinate(scan, coordNum)
    attrs=read.coordinateHeader(coord)
    scan.close()
    message="Scan "+str(scanNum)+" at COORDINATE " + str(coordNum) + ":\n"
    for k in attrs.keys():
        message=message+str(k)+' = '+str(attrs[k])+'\n'
    attributesMessage.configure(text=message)

def convertChannelNameToIndex(a):
    for i, name in enumerate(channelNames):
        if name==a:
            return str(i)
    return '0'

def readChannelAttributes():
    selectedScan=scans.get()
    selectedCoordinate=coordinates.get()
    selectedChannel=convertChannelNameToIndex(channels.get())
    scan=read.scan(selectedScan)
    coord=read.coordinate(scan, selectedCoordinate)
    channel = read.channel(coord, selectedChannel)
    attributes=read.channelHeader(channel)
    message="Scan "+str(selectedScan)+" at coord " + str(selectedCoordinate) + " CHANNEL " + selectedChannel + ":\n"
    for k in attributes.keys():
        message=message+str(k)+' = '+str(attributes[k])+'\n'
    attributesMessage.configure(text=message)

def newColors(event):
    colors=[]
    for i in range(4):
        colors.append('#'+str(hex(randrange(16777216))[2:].zfill(6)))
    window.tk_setPalette(background=colors[0], foreground=colors[1], activeBackground=colors[2], activeForeground=colors[3])

def newPlotWindow(xData, yData, xlabel, ylabel, title):
    graphWindow = t.Tk()
    graphWindow.wm_title("ADQ14 Control Graph")
    
    fig = Figure(figsize=(8, 6), dpi=80)
    graph = fig.add_subplot(111)
    graph.plot(xData,yData,'.')
    graph.set_xlabel(xlabel)
    graph.set_ylabel(ylabel)
    graph.set_title(title)
    canvas = FigureCanvasTkAgg(fig, master=graphWindow)  # A tk.DrawingArea.
    canvas.draw()
    canvas.get_tk_widget().pack(side=t.TOP, fill=t.BOTH, expand=1)
    
    toolbar = NavigationToolbar2Tk(canvas, graphWindow)
    toolbar.update()
    canvas.get_tk_widget().pack(side=t.TOP, fill=t.BOTH, expand=1)
    
    def _quit():
        graphWindow.quit()     # stops mainloop
        graphWindow.destroy()  # this is necessary on Windows to prevent
                               # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    
    button = t.Button(master=graphWindow, text="Quit", command=_quit)
    button.pack(side=t.BOTTOM)
    
    t.mainloop()

def rawGraph():
    scanNum=scans.get()
    coordNum=coordinates.get()
    channelNum=convertChannelNameToIndex(channels.get())
    scan=read.scan(scanNum)
    coord=read.coordinate(scan, coordNum)
    channel = read.channel(coord, channelNum)
    attrs=read.channelHeader(channel)
    samplePeriodNano=int(attrs['SamplePeriod'])
    voltage=read.channelData(channel)*((read.channelHeader(channel)['InputRange'])/65536)
    scan.close()
    time=range(0,samplePeriodNano*(len(voltage)),samplePeriodNano)
    newPlotWindow(time, voltage, "Time (ns)", "Voltage (V)", "Raw graph for scan "+scanNum+" coord "+coordNum+" channel "+channelNum)
#
#def processedGraph():
#    scanNum=scans.get()
#    coordNum=coordinates.get()
#    channelNum=convertChannelNameToIndex(channels.get())
#    scan=read.scan(scanNum)
#    coord=read.coordinate(scan, coordNum)
#    channel = read.channel(coord, channelNum)
#    attrs=read.channelHeader(channel)
#    samplePeriodNano=int(attrs['SamplePeriod'])
#    samplePeriod=1e-9*samplePeriodNano
#    voltage=read.channelData(channel)
#    scan.close()
#    time=range(0,int(samplePeriodNano)*(len(voltage)),int(samplePeriodNano))
#    t_bin = 3.625e-6 # seconds for one orbit
#    n_per_bin = int(np.round(t_bin/samplePeriod))
#    NumBins,PointsToRemove = np.divmod(len(voltage),n_per_bin)
#    #get rid of extra points
#    time = time[:-1*PointsToRemove]
#    voltage = voltage[:-1*PointsToRemove]
#    time = np.reshape(time,(NumBins,n_per_bin)).mean(axis=1)
#    voltage = np.reshape(voltage,(NumBins,n_per_bin)).sum(axis=1)
#    newPlotWindow(time, voltage, "Time (ns)", "?", "Processed graph for scan "+scanNum+" coord "+coordNum+" channel "+channelNum)

def onClosing():
    if not scanLoop.getInitializeStatus():
        scanLoop.stop()    
        window.quit()
        window.destroy()
    else:
        result=t.messagebox.askyesno("Exit?", "Are you sure? Closing now could destabilize the digitizer.")
        if result:
            scanLoop.stop()    
            window.quit()
            window.destroy()


def startScanLoop():
    if 'Number of Samples' in config:
        numSamples=int(config['Number of Samples'])
    else:
        print("Config doesn't have number of samples, defaulting to 125000")
        numSamples=125000
    if 'Trig Delay' in config:
        pretriggerPerentage=int(config['Trig Delay'])
    loopThread=threading.Thread(target=lambda:scanLoop.initialize(numSamples, pretriggerPerentage))
    loopThread.setDaemon(True)
    loopThread.start()
    startScanLoopButton.configure(state='disabled')
    stopLoopButton.configure(state='normal')
    scanStatusLabel.configure(fg="green", bg="black", text="Active")
    newScanButton.configure(state='normal')

spamCount=0
def stopScanLoop():
    global spamCount
    if not scanLoop.getInitializeStatus():
        startScanLoopButton.configure(state='normal')
        stopLoopButton.configure(state='disabled')
        scanLoop.stop()
        scanStatusLabel.configure(fg="red", bg="black", text="Disabled")
        newScanButton.configure(state='disabled')
        spamCount=0
    else:
        spamCount+=1
        if spamCount>8:
            scanStatusLabel.configure(fg="white", bg="black", text="BRO, CHILL")

def newScan():
    global spamCount
    if scanLoop.getNumDevices()==0:
        spamCount+=1
        scanStatusLabel.configure(bg="red", fg="white", text="NO ADQ CONNECTION")
        if spamCount>8:
            scanStatusLabel.configure(fg="white", bg="black", text="BRO, CHILL")
    else:
        scanStatusLabel.configure(fg="green", bg="black", text="Active")
        scanLoop.scan()

def showScreen(screenIndex):
    if screenIndex==0:
        updateScans()
    for i in range(len(screens)):
        if i != screenIndex:
            try:
                screens[i].pack_forget()
            except:
                pass
    screens[screenIndex].pack()

def updateConfig():
    file=open(os.getcwd()+"\config.config", 'w')
    file.write('Number of Samples : '+sampleEntry.get()+'\n')
    file.write('Trig Delay : '+str(trigDelay.get())+'\n')
    file.write('Digitizer Name : '+str(nameEntry.get())+'\n')
    file.write('Num Repeats : '+str(averagesEntry.get())+'\n')
    if trigDelay.get()==69:
        configTitle.configure(text="heh. heh heh. nice")
    channelString=''
    for c in channelCheckboxesVar:
        if c.get():
            channelString+='1'
        else:
            channelString+='0'
    file.write('Use Channels : '+channelString+'\n')
    file.write('Scan Folder : '+str(scanFolderEntry.get()))
    if saveAverageCheckVar.get():
        file.write('Auto Average : 1')
    else:
        file.write('Auto Average : 0')
    file.close()
    print('Config file saved.')
    print('Note: for new config, reinitialize digitizer.')

def updatePVs():
    userLines=[]
    pvLines=[]
    pvPath=os.getcwd()+"\pv.config"
    for line in userTextBox.get('1.0', 'end-1c').splitlines():
        userLines.append(line)
    for line in pvTextBox.get('1.0', 'end-1c').splitlines():
        pvLines.append(line+'\n')
    if len(pvLines)==len(userLines):
        file=open(pvPath, "w")
        for i in range(len(pvLines)):
            file.write(userLines[i]+" : "+pvLines[i])
        file.close()
        for i, line in enumerate(pvLines):
            if epics.caget(line)==None:
                connectionLabels[i]=t.Label(screen3, text="  ", bg="red", font=("Courier", 4))
                print("PV in line",i,"is failing to connect to EPICS.")
            else:
                connectionLabels[i]=t.Label(screen3, text="  ", bg="green", font=("Courier", 4))
            connectionLabels[i].grid(column=2, row=i+1)
        print("PVs Updated.")
    else:
        print("User Friendlies and PVs aren't same # of lines")


###############################################################################
config=configReader.getContents(os.getcwd()+"\config.config")
pv=configReader.getContents(os.getcwd()+"\PV.config")
if "Scan Folder" in config:
    defaultFolder=config["Scan Folder"]
    if "\n" in defaultFolder:
        defaultFolder=defaultFolder[0:len(defaultFolder)-1]
else:
    defaultFolder=os.getcwd()+"\Scans"
    
#GUI SETUP below
###############################################################################
window = t.Tk()
window.wm_title("ADQ14 Control")
window.geometry('575x550')
window.tk_setPalette(background='#e3ebd5', foreground='black', activeBackground='#143d0c', activeForeground='white')
screens=[]
###############################################################################
screen0 = t.Frame(window)


topFrame = t.Frame(screen0)
topFrame.pack(side=t.TOP)
bottomFrame = t.Frame(screen0)
bottomFrame.pack(side=t.BOTTOM)

t.Label(topFrame, text="Past Data Attributes View", font=("Courier 14 bold")).grid(row=0, columnspan=3)

scanLabel=t.Label(topFrame, text="SCAN", font=("Courier", 12))
scanLabel.grid(column=0, row=1)
coordLabel=t.Label(topFrame, text="COORDINATE", font=("Courier", 12))
coordLabel.grid(column=0, row=2)
chanLabel=t.Label(topFrame, text="CHANNEL", font=("Courier", 12))
chanLabel.grid(column=0, row=3)

scans = ttk.Combobox(topFrame)
scans.grid(column=1, row=1)
scans.bind("<<ComboboxSelected>>", scanChange)

coordinates = ttk.Combobox(topFrame)
coordinates.grid(column=1, row=2)
coordinates.bind("<<ComboboxSelected>>", coordChange)

channels = ttk.Combobox(topFrame)
channels.grid(column=1, row=3)
channels.bind("<<ComboboxSelected>>", channelChange)

scanAttrsButton = t.Button(topFrame, text='Scan Attributes', command=readScanAttributes, width='25')
scanAttrsButton.grid(column=2, row=1)

coordAttrsButton = t.Button(topFrame, text='Coordinate Attributes', command=readCoordinateAttributes, width='25')
coordAttrsButton.grid(column=2, row=2)

chanAttrsButton = t.Button(topFrame, text='Channel Attributes', command=readChannelAttributes, width='25')
chanAttrsButton.grid(column=2, row=3)

graphButton = t.Button(topFrame, text='Raw Graph', command=rawGraph, width='15')
graphButton.grid(column=0, row=4)

#graphButton2 = t.Button(topFrame, text='Processed Graph', command=processedGraph, width='15')
#graphButton2.grid(column=1, row=4)

validCheck = t.Checkbutton(topFrame, text='Valid Coordinate', command=flipValidity)
validCheck.grid(column=2, row=4)

attributesMessage = t.Message(bottomFrame, font=("Courier", 10), width=500)
attributesMessage.grid(column=2, row=1)

screens.append(screen0)
###############################################################################
screen1 = t.Frame(window)

configTitle=t.Label(screen1, text="Initialization Configuration", font=("Courier 14 bold"))
configTitle.grid(row=0, columnspan=3)

t.Label(screen1, text="Trig Delay").grid(row=1, column=0)
trigDelay = t.Scale(screen1, from_=0, to=100, orient=t.HORIZONTAL, length=250)
trigDelay.grid(row=1, column=1, columnspan=2)

t.Label(screen1, text="Number of Samples").grid(row=2, column=0)
sampleEntry = t.Entry(screen1, width=65, bg="white")
sampleEntry.grid(row=2, column=1, columnspan=2)

t.Label(screen1, text="Number of Repeats").grid(row=3, column=0)
averagesEntry = t.Entry(screen1, width=48, bg="white")
averagesEntry.grid(row=3, column=1)
saveAverageCheckVar=t.IntVar()
averageCheck=t.Checkbutton(screen1, text="Auto Average", var=saveAverageCheckVar)
averageCheck.grid(row=3, column=2)

t.Label(screen1, text="Digitizer Name").grid(row=4, column=0)
nameEntry = t.Entry(screen1, width=65, bg="white")
nameEntry.grid(row=4, column=1, columnspan=2)

t.Label(screen1, text="Scan Folder").grid(row=5, column=0)
scanFolderEntry = t.Entry(screen1, width=65, bg="white")
scanFolderEntry.grid(row=5, column=1, columnspan=2)

if 'Number of Samples' in config:
    sampleEntry.insert(0, config['Number of Samples'])
if 'Digitizer Name' in config:
    nameEntry.insert(0, config['Digitizer Name'])
if 'Scan Folder' in config:
    scanFolderEntry.insert(0, config['Scan Folder'])
if 'Num Repeats' in config:
    averagesEntry.insert(0, config['Num Repeats'])
if 'Trig Delay' in config:
    trigDelay.set(config['Trig Delay'])
if 'Auto Average' in config:
    if config['Auto Average']=='1':
        averageCheck.select()

t.Label(screen1, text="Record Channels").grid(row=6, column=0)
channelCheckboxesVar=[]
channelNames=['A','B','C','D']
if 'Use Channels' in config:
    useChannels=config['Use Channels']
for i, name in enumerate(channelNames):
    channelCheckboxesVar.append(t.IntVar())
    check=t.Checkbutton(screen1, text="Channel "+name, var=channelCheckboxesVar[i])
    check.grid(row=6+i, column=1)
    if 'Use Channels' in config:
        if useChannels[i]=='1':
            check.select()

updateConfigButton=t.Button(screen1, text="Update Configuration", command=updateConfig)
updateConfigButton.grid(row=6+len(channelNames), column=0, columnspan=2)

screens.append(screen1)
###############################################################################
screen2 = t.Frame(window)
screen2.pack()

mainControlLabel=t.Label(screen2, text="Main ADQ14 Control", font=("Courier 14 bold"))
mainControlLabel.grid(row=0)
mainControlLabel.bind('<Button-1>', newColors)

startScanLoopButton=t.Button(screen2, text="Start Loop", command=startScanLoop, width=20, height=2, font=("Courier 12 bold"))
startScanLoopButton.grid(row=1)
stopLoopButton=t.Button(screen2, text="Stop Loop", command=stopScanLoop, state='disabled', width=20, height=2, font=("Courier 12 bold"))
stopLoopButton.grid(row=2)
newScanButton=t.Button(screen2, text="New Scan", command=newScan, state='disabled', width=20, height=2, font=("Courier 12 bold"))
newScanButton.grid(row=3)

scanStatusLabel=t.Label(screen2, text="Disabled", font=("Courier", 30), bg="black", fg="red")
scanStatusLabel.grid(row=4)

screens.append(screen2)
###############################################################################
screen3 = t.Frame(window)

maxPVs=30
titlesLabel=t.Label(screen3, text="USER FRIENDLY", font='Courier 14 bold')
titlesLabel.grid(row=0, column=0)
titlesLabel=t.Label(screen3, text="PV", font='Courier 14 bold')
titlesLabel.grid(row=0, column=1)

userTextBox=t.Text(screen3, height=maxPVs, width=34, bg="white")
userTextBox.grid(row=1, column=0, rowspan=maxPVs)

pvTextBox=t.Text(screen3, height=maxPVs, width=35, bg="white")
pvTextBox.grid(row=1, column=1, rowspan=maxPVs)

connectionLabels=[]

for i, key in enumerate(pv):
    userTextBox.insert(t.END, key+'\n')
    pvTextBox.insert(t.END, pv[key])
    if epics.caget(pv[key])==None:
        connectionLabels.append(t.Label(screen3, text="  ", bg="red", font=("Courier", 4)))
        print("PV in line",i,"is failing to connect to EPICS.")
    else:
        connectionLabels.append(t.Label(screen3, text="  ", bg="green", font=("Courier", 4)))
    connectionLabels[i].grid(column=2, row=i+1)
for i in range(len(connectionLabels)-1, maxPVs):
    connectionLabels.append(t.Label(screen3, text="  ", bg="red", font=("Courier", 4)))
    connectionLabels[i].grid(column=2, row=i+1)
updatePVButton=t.Button(screen3, text="Update PV Variables", command=updatePVs)
updatePVButton.grid(row=maxPVs+1, column=0)

screens.append(screen3)
###############################################################################
menu = t.Menu(window)
 
file = t.Menu(menu, tearoff=0)
edit = t.Menu(menu, tearoff=0)
 
file.add_command(label='Scan Control', command=lambda:showScreen(2)) 
file.add_command(label='View Past Data', command=lambda:showScreen(0))
edit.add_command(label='Initialization Configuration', command=lambda:showScreen(1))
edit.add_command(label='PV Attributes', command=lambda:showScreen(3)) 

menu.add_cascade(label='File', menu=file)
menu.add_cascade(label='Edit', menu=edit)
window.config(menu=menu)

window.protocol("WM_DELETE_WINDOW", onClosing)

if os.path.exists(defaultFolder):
    updateScans()

window.mainloop()