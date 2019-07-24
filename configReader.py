"""
Created on July 3rd, 2019

The purpose of this script is to easily read custom formatted config files.

@author: Dan Hudetz
"""
import os

def getContents(path):
    contents={}
    if os.path.exists(path):
        config=open(path,"r")
        configLines=config.readlines()
        for line in configLines:
            if line!="\n":
                split1=line.split(" : ")
                try:
                    contents.update({split1[0]:split1[1]})
                except Exception as e:
                    print(e)
                    print("WARNING: Config file is formatted wrong. Unable to read")
        config.close()
    else:
        print("WARNING: attempting to access nonexistent configuration file")
    return contents
