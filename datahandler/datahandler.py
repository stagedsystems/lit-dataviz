"""Data Handler

So our web api calls and scripts can be generic, setup a seperate library to handle i/o
similar to the repository pattern. Data can be persisted in database, memory, .csv file
or any other generic way. This class makes it seamless to end user

"""

import os
import sys
import logging
import json
import shutil
import tempfile
from datetime import datetime

from integrations.azblobconnector import AZBlobConnector

#maybe data handler has 3 reference classes. one for db, once for csv, one for memory. it handles i/o

#this is going to make data look like in memory to all users

# Adds higher directory to python modules path.
currentFilePath = os.path.dirname(os.path.realpath(__file__))
parentPath = os.path.dirname(currentFilePath)
sys.path.append(parentPath)

from .csvconnector import CSVConnector
from .memoryconnector import MemoryConnector


class DataHandler():
    """Handles input/output of persisted data using named key for table"""

    def __init__(self,dataDirectory=None,persistenceType="local directory", env="Development"):

        try:

            self.logger = logging.getLogger("Data Handler")  

            self.environment=env 

            self.dataLocation = dataDirectory

            #choose the appropriate connector       
            if persistenceType=="local directory" or persistenceType=="temporary files":
                self.connector = CSVConnector(dataDirectory,persistenceType)


            #get geodata local
            try:
        
                zoneFile = os.path.join(self.dataLocation, "geodata","zonedata.json" )
                cabinetFile = os.path.join(self.dataLocation, "geodata", "cabinetpoints.json" )

                with open( zoneFile ) as f:
                    self.geoZoneData = json.load(f)
                with open(cabinetFile) as f:
                    self.geoCabinetData = json.load(f)                     

            except Exception as e:
                self.logger.exception("Error fetching Geo Data -- " + str(e))
                return None  
                    
            
            self.persistenceType=persistenceType   


        except Exception as e:
            self.logger.exception("Unable to initiate data handler -- " + str(e))
            return None

        


    def getDataFromStore(self, key):

        #this may not be good, but lets try the in memory store first, if not attempt to load from disk

        dataRetrieved = None

        try:

            #geo data is stored directly in the class
            if key == "ZoneGeoData":
                return self.geoZoneData
            elif key == "CabinetGeoData":                
                return self.geoCabinetData

            if self.connector:                

                if isinstance(self.connector, MemoryConnector):
                    dataRetrieved = self.connector.getDataFromStore(key)
                elif isinstance(self.connector, CSVConnector):
                    dataRetrieved = self.connector.getDataFromDisk(key)
              
            else:
                self.logger.warning("Unable to get data from store, connector not set")
                return None

        except Exception as e:                      
            self.logger.warning("Error fetching data from store - " + str(e)) 
            return None


        return dataRetrieved

    
