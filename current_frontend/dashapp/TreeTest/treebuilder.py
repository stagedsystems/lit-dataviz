import sys
import csv
import os
import re

import pandas as pd
#from igraph import Graph, EdgeSeq
import logging


#Adds higher directory to python modules path, needed to point correctly to assets
currentFilePath = os.path.dirname(os.path.realpath(__file__))
parentPath = os.path.dirname(currentFilePath)    
sys.path.append(currentFilePath) 
sys.path.append(parentPath)    
grandParentPath = os.path.dirname(parentPath)    
sys.path.append(grandParentPath)    
ggParentPath = os.path.dirname(grandParentPath)
sys.path.append(ggParentPath)    


import netsection, netsectgraph


class TreeBuilder():

    def __init__(self):
       

        self.logger = logging.getLogger(__name__)  
        self.netSectionList = []

    def buildGraph(self, packageData, attributesToMap=None):

        try:

            networkTree = self.buildTreeWithStatus(packageData)
            if networkTree:

                nGraph = netsectgraph.NetSectGraph(networkTree)                
                graph = nGraph.loadDataToTree(self.netSectionList, attributesToMap)
                return graph

        except Exception as e:
            self.logger.warning("Error Building Network Graph -- " + str(e))
            return None


    def buildTreeModel(self, packageData):
        """Take a list of 'packages' with hiearchy information and convert to a tree"""
        try:         
            netSections = self.convertPackagesToNetSections(packageData)

            if netSections:
                self.netSectionList = netSections
                treeModel = netsection.NetSectTree(self.netSectionList)
                return treeModel

        except Exception as e:
            self.logger.warning("Error Building Network Tree -- " + str(e))
            return None

    def buildTreeWithStatus(self, packageData):
        """Take a list of 'packages' with hiearchy information and convert to a tree"""

        try:                     
            treeModel = self.buildTreeModel(packageData)
            treeWithProgress = treeModel.calcUpstreamProgress(treeModel.listOfSections)

            return treeWithProgress

        except Exception as e:
            self.logger.warning("Error Building Network Status Tree -- " + str(e))
            return None

    def convertPackagesToNetSections(self, packageData):
        """Take a list of network packages and convert them to our "network section" model """

        try:           

            netSectionObjectList = []
       
            for package in packageData:
                newNetSect = netsection.NetworkSection()

                #rename keys to match netsection schema, maybe better to do mixin later
                package["name"] = package.pop("package")
                package["tier"] = package.pop("hiearchy")
                package["netsecpercent"] = package.pop("packagepercentcomplete")
                package["f1"] = package.pop("ring")
                package["f2"] = package.pop("feeder")
                if package["tier"] == "F3":
                    package["f3"] = package["name"]
                else:
                    package["f3"] = ""

                #add all other attributes that were there originally
                for key, value in package.items():
                    try:
                        cleanKey = re.sub('\s+','',key).lower()
                        if cleanKey in package.keys():
                            setattr(newNetSect, cleanKey, value)
                    except:
                        pass      
            
                netSectionObjectList.append(newNetSect)

            return netSectionObjectList

        except Exception as e:
            self.logger.warning("Error Initializing Network Tree -- " + str(e))
            return None
