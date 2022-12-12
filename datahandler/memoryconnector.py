"""Memory Data Connector

This persists data by table name/key in a simple dictionary, so all data is stored in memory
and retrieved as needed by user. Fast but not scalable and not persisted between sessions.

"""

import logging

class MemoryConnector():
    """Simple class to persist storage using in memory dictionary"""

    def __init__(self,dataDirectory=None):

        self.logger = logging.getLogger(__name__) 

        #data store will be key and data stored in a list of dictionaries
        self.dataStore = {}

    def addDataToStore(self, dataToSave, key):
        """Adds data to the dictioanry"""
        
        try:            
            
            self.dataStore[key] = dataToSave
       
        except Exception as e:
            self.logger.warning("Error saving data to in memory store - " + str(e))

    def getDataFromStore(self, key):
        """Retrieves data from the dictionary"""

        try:
            if key in self.dataStore.keys():
                return self.dataStore[key]
            else:
                return None
        except Exception as e:
            self.logger.warning("Error retrieving data from store - " + str(e))