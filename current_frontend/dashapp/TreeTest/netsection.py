""" Network Section Model

To do some tree based models and other hiearchial analysis, need to define 'network sections'. These are F1/F2/F3 hiearchicaly

"""

import sys
import csv
import os
import re
import logging



#this might need to be a mixin
class NetworkSection:
    """Network Section represetns all network cable
    at a certain hiearchy, for F3 its all cable downstream
    of PON cabinet"""

    def __init__(self):
        self.name = None       
        self.tier = None
        self.f1 = None
        self.f2 = None
        self.f3 = None
        self.netsecfootage = 0.0
        self.netsecpercent = 0.0

        #calculated
        self.connected = False   
        self.completed = False  
        self.upstreamsection = "" #needs to be sortable
        self.downstreamchildren = [] #if we do another mixin, this would move
        self.f1percent = 0.0
        self.f2percent = 0.0
        self.f3percent = 0.0

    @property 
    def children(self):
        return self.downstreamchildren

    @property
    def parent(self):
        return self.upstreamsection


class NetSectTree:
    """Network Section will be modeled as a tree where sections have reference to their
    parents and children or upstream and downstream nodes"""

    def __init__(self, listOfSections):

        self.logger = logging.getLogger(__name__)

        self.listOfSections = listOfSections
        self.organizedSections = []

        f1ParentChildMap = {}
        f2ParentChildMap = {}

        try:

            #first pass, identify all parents
            for sect in self.listOfSections:
                
                if sect.tier == "F3":
                    sect.upstreamsection = sect.f2
                    if sect.f2 not in f2ParentChildMap.keys():
                        f2ParentChildMap[sect.f2] = [sect]
                    else:
                        f2ParentChildMap[sect.f2].append(sect)

                    if not sect.f2 or sect.f2 =="":
                        self.logger.warning("fiberhood has no parent package")

                elif sect.tier == "F2":
                    sect.upstreamsection = sect.f1
                    if sect.f1 not in f1ParentChildMap.keys():
                        f1ParentChildMap[sect.f1] = [sect]
                    else:
                        f1ParentChildMap[sect.f1].append(sect)

                    if not sect.f1 or sect.f1 =="":
                        self.logger.warning("feeder has no parent package")
                         

            #second pass, identify all children
            for sect in self.listOfSections:

                if sect.tier == "F2":

                    if sect.name in f2ParentChildMap.keys():                    
                        #add children from map created earlier
                        for child in f2ParentChildMap[sect.name]:
                            sect.downstreamchildren.append(child)
                
                elif sect.tier == "F1":
                    #add children from map created earlier
                    if sect.name in f1ParentChildMap.keys():
                        for child in f1ParentChildMap[sect.name]:
                            sect.downstreamchildren.append(child) 
                    self.organizedSections.append(sect)

        except Exception as e:
            self.logger.warning("Error Creating Network Section Tree -- " + str(e))
            return None
   

    def calcUpstreamProgress(self, inputSectionList):

        try:

            for section in inputSectionList: 
                node = section.__dict__          

                # if node["tier"] == "F1":
                #     node["f1footage"] = node["netsecfootage"]
                # elif node["tier"] == "F2":
                #     node["f2footage"] = node["netsecfootage"]
                # elif node["tier"] == "F3":
                #     node["f3footage"] = node["netsecfootage"]

                #get the applicable upstream footages
                foundF1 = False
                foundF2 = False

                nodePercent = float(node["netsecpercent"])
                if nodePercent == 1:
                    node["completed"] = True

                #there may be a better way to loop this logic
                if node["tier"] != "F1":
                    for refSection in inputSectionList:
                        if node["tier"] == "F3":
                            #find matching parent F2 section
                            
                            node["f3percent"] = nodePercent 
                           
                            if refSection.name == node["f2"]:
                                #node["f2footage"] = refSection.netsecfootage
                                node["f2percent"] = float(refSection.netsecpercent)
                                foundF2 = True
                            elif refSection.name == node["f1"]:
                                #node["f1footage"] = refSection.netsecfootage
                                node["f1percent"] = float(refSection.netsecpercent)
                                foundF1 = True
                        elif node["tier"] == "F2":
                            node["f2percent"] = nodePercent 
                            foundF2 = True
                            if refSection.name == node["f1"]:
                                #node["f1footage"] = refSection.netsecfootage
                                node["f1percent"] = float(refSection.netsecpercent)
                                foundF1 = True

                        if foundF1 and foundF2:
                            break
                else:
                    node["f1percent"] = nodePercent 


                #once all upstream packages identified
                if node["tier"] == "F3":
                    if node["f1percent"] == 1 and node["f2percent"] == 1:
                        node["connected"] = True
                    else:
                        node["connected"] = False
                elif node["tier"] == "F2":
                    if node["f1percent"] == 1:
                        node["connected"] = True
                    else:
                        node["connected"] = False
                elif node["tier"] == "F1":
                    node["connected"] = True

            return inputSectionList

        except Exception as e:
            self.logger.exception("Error Calculating Upstream Progress -- " + str(e))
            return None










