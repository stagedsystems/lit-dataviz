"""Network Section Graph

A list or tree model of network sections - modeled as a graph using the igraph library. This helps
with visulaizing in tools like plotly and dash

"""

import sys
import csv
import os
import re

import pandas as pd
from igraph import Graph
import logging



#this might need to be a mixin
class NetSectGraph:
  
    def __init__(self, listOfNetSections):  


        self.logger = logging.getLogger(__name__)
        self.listOfSections = listOfNetSections

        self.nodeMap = {} #will link nodes to index number for edge->node loading  

        
    def loadDataToTree(self, inputSectionList, attributesToMap=None):

        try:
            edgeData = []                


            inputSectionList.sort(key=lambda x: x.upstreamsection)               

            for section in inputSectionList:
                node = section.__dict__
                edgeToParent = {"name" : node["name"] + "->" + node["upstreamsection"],
                                 #"distance" : node["footagetoparent"],
                                 "source" : node["upstreamsection"],
                                 "target" : node["name"],
                                 "connected" : node["connected"]}  #connected to upstreamparent
                #topmost nodes don't need edges 
                if edgeToParent["source"] and edgeToParent["source"] != "":      
                    edgeData.append(edgeToParent)             
                self.nodeMap[node["name"]] = -1   

             
            treeNodeDF = pd.DataFrame([vars(s) for s in inputSectionList])
            #try to improve data types
            treeNodeDF.convert_dtypes().dtypes

            nodeNames = treeNodeDF["name"]

            i=0            
            for node in nodeNames:
                self.nodeMap[node] = i
                i+=1

            graphEdgeList = []
            #go through each edge and get indexes for source and target
            for edge in edgeData:

                #topmost nodes will not need edges created
                if edge["source"]:

                    edge["sourceIndex"] = self.nodeMap[edge["source"]] #lookup parentID and get index
                    edge["targetIndex"] = self.nodeMap[edge["target"]] #lookup fhid and get index
                    graphEdgeList.append((edge["targetIndex"],edge["sourceIndex"])) #convert edge to tuple
            
            #build our initial graph          
            # edgeDF = pd.DataFrame(edgeData)
            # df = edgeDF.source.value_counts()
            # maxChildren = df.max()
            # g = Graph.Tree(len(treeNodeDF), maxChildren)

            g = Graph()
            

            #add vertices for each node
            g.add_vertices(len(treeNodeDF))
            g.add_edges(graphEdgeList)
                    
            g.vs["Name"] = treeNodeDF["name"].tolist()      
            g.vs["name"] = treeNodeDF["name"].tolist()    
            #g.vs["Distance To Parent"] = treeNodeDF["footagetoparent"].tolist()
            g.vs["Tier"] = treeNodeDF["tier"].tolist()
            g.vs["F1"] = treeNodeDF["f1"].tolist()
            g.vs["F2"] = treeNodeDF["f2"].tolist()
            g.vs["F3"] = treeNodeDF["f3"].tolist()
            g.vs["UpstreamSect"] = treeNodeDF["upstreamsection"].tolist()
            #g.vs["F1 Footage"] = treeNodeDF["f1footage"]
            #g.vs["F2 Footage"] = treeNodeDF["f2footage"]
            #g.vs["F3 Footage"] = treeNodeDF["f3footage"]
            g.vs["F1 Percent"] = treeNodeDF["f1percent"].tolist()
            g.vs["F2 Percent"] = treeNodeDF["f2percent"].tolist()
            g.vs["F3 Percent"] = treeNodeDF["f3percent"].tolist()
            g.vs["Connected"] = treeNodeDF["connected"].tolist()
            g.vs["Completed"] = treeNodeDF["completed"].tolist()

            if attributesToMap:
                for att in attributesToMap:
                    g.vs[att] = treeNodeDF[att].tolist()


            edgeDF = pd.DataFrame(edgeData)
            g.es["Name"] = edgeDF["name"].tolist()
            g.es["Connected"] = edgeDF["connected"].tolist()

            return g           


        except Exception as e:
            self.logger.exception("Error Loading Data To Tree -- " + str(e))
            return None

 