"""CSV Data Connector

Deals with persistence using local or remote .csv files as datastore.

"""

import os
import sys
import logging
import csv
import tempfile

class CSVConnector():
    """Handles import and export of data, to user it will look generic or like memory, but is actually in .csv files"""

    def __init__(self,dataDirectory=None,persistenceType = "local directory"):

        self.logger = logging.getLogger(__name__)  

        self.persistenceType = persistenceType

        #keep map of all the csvLinks     
        self.csvLinks = {}

        try:

            if self.persistenceType == "local directory":

                #if given a specific data directory use that, otherwise use default "data" subdirectory
                if dataDirectory:
                    self.DataDirectory = dataDirectory
                else:
                    self.DataDirectory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

                self.outputDirectory = os.path.join(self.DataDirectory, "output")
            
                #build initial links if directory isn't empty
                for file in os.listdir(self.outputDirectory):
                    if ".csv" in file:
                        dataName = file[0:-4]
                        self.csvLinks[dataName] = os.path.join(self.outputDirectory,file)

        except Exception as e:            
            self.logger.exception("Error setting local folder for file input/output -- " + str(e))


              
    def exportDataToCSV(self, listToExport, dataName, fields=None):

        if listToExport:
            if len(listToExport) == 0 or not isinstance(listToExport, list):
                return None
        else:
            self.logger.info(dataName + " data not saved, no data found")
            return None
            
        try:
            if fields==None:
                fields = list(listToExport[0])#.keys?
        
        except Exception as e:
            self.logger.exception("Error getting schema for local data save -- " + str(e))
            return None  
                 

        if self.persistenceType == "local directory":

            try:

                csvName = os.path.join(self.outputDirectory,dataName + ".csv")

                #right now lets use export to csv
                self.exportToCSV(os.path.join(csvName), listToExport)
                self.csvLinks[dataName] = csvName
                return csvName

            except Exception as e:
                self.logger.warning("Error writing to local directory -- " + str(e))
                return None      

        elif self.persistenceType == "temporary files":

            try:

                with tempfile.NamedTemporaryFile(mode='w',suffix='.csv', prefix=dataName,delete=False) as csvFile:
                    writer = csv.DictWriter(csvFile, fieldnames=fields,extrasaction='ignore') #note the extrasaction ignores extra fields
                    writer.writeheader() #the .csv column names / header
                    for data in listToExport:
                        writer.writerow(data)

                    #self.addDataToStore(csvFile, dataName)
                    self.csvLinks[dataName] = csvFile

                    return csvFile

            except Exception as e:
                self.logger.warning("Error writing to temporary file -- " + str(e))
                return None        
        

    def exportToCSV(self,csvName, listToWrite, csvColumns=None):

        #if no columns are specified, use the first item's keys
        if csvColumns==None:
            csvColumns = list(listToWrite[0])

        try:
            with open(csvName, 'w', newline='') as csvFile:
                writer = csv.DictWriter(csvFile, fieldnames=csvColumns,extrasaction='ignore') #note the extrasaction ignores extra fields
                writer.writeheader() #the .csv column names / header
                for data in listToWrite:
                    writer.writerow(data)
            
            exDir = os.path.dirname(csvName)  
            if not exDir or exDir == "":
                exDir = os.getcwd()

            self.logger.info("exported to " + exDir + "\\" + csvName)

        except Exception as e:
            self.logger.warning("Error writing to .csv - ensure file is closed - " + str(e))

    def getDataFromDisk(self, key):
        """not sure i really want this, but working right now for test code"""

        try:
            diskLocation = self.csvLinks[key]

            with open(diskLocation, "r") as f:
                reader = csv.DictReader(f)
                diskData= list(reader)
                return diskData
        except Exception as e:                      
            self.logger.warning("Error fetching data from disk - " + str(e)) 
            return None


        

      



