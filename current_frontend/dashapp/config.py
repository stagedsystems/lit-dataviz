"""Helper file to do some basic configuration for dash when it starts"""
import os
import sys
import logging
import json



def setupEnv(env="Development"):
    logger = logging.getLogger(__name__)


    # Adds higher directory to python modules path.
    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    parentPath = os.path.dirname(currentFilePath)
    sys.path.append(parentPath)

   
     #Get environment variable to check whether dev or production
    webInst = os.getenv('WEBSITE_INSTANCE_ID')
    webDeployID = os.getenv('WEBSITE_DEPLOYMENT_ID') #'func-lit-steering-dev01', 
    if not webInst and not webDeployID: #if neither webinst nor webdeploy, set to local
        #dev, go two folders up to get library
        grandParentPath = os.path.dirname(parentPath)
        sys.path.append(grandParentPath)

        if "CONFIGDIR" not in os.environ:
            configDir = os.path.join(grandParentPath, "cfg") 
            os.environ["CONFIGDIR"] = configDir

    else:
        #production, folders should be copied 
        if "CONFIGDIR" not in os.environ:
            configDir = os.path.join(parentPath, "cfg") 
            os.environ["CONFIGDIR"] = configDir 
  

    #setup some dash variables, these will always be in "frontend" directory
    os.environ["ASSETT_FOLDER"] = os.path.join(parentPath, "assets")
