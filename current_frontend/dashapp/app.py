from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output, State
import dash
import flask
from flask_caching import Cache
import logging
import os
import sys
import datetime


#i dont like this but needed for now
# Adds higher directory to python modules path, needed to point correctly to assets
currentFilePath = os.path.dirname(os.path.realpath(__file__))
#parentPath = os.path.dirname(currentFilePath)    
sys.path.append(currentFilePath) #this will be 2 folders down
# Adds higher directory to python modules path, needed to point correctly to assets   

#loads internal configuration, e.g. folders, environment variables, etc.
import config #note this is different in pole detector

#Get environment variable to check whether dev or production
webinst = os.getenv('WEBSITE_INSTANCE_ID')
webDeployID = os.getenv('WEBSITE_DEPLOYMENT_ID') #'func-lit-steering-dev01', 

#if production, library should have been installed with pip  
if not webinst and not webDeployID: #if neither webinst nor webdeploy, set to local   
   env = "Test"
else:
   env = "Production"

config.setupEnv(env)

#config should have loaded proper modules to find datahandler
from datahandler.datahandler import DataHandler
from style import getStyle

#create a root logger, all sub loggers will inherit from this unless overriden
rootLogger = logging.getLogger()     
rootLogger.setLevel(logging.INFO) 
logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#second handler with info to console while running
consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO) 
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

rootLogger.info("Web instance: " + str(webinst) + "  Web Deploy " + str(webDeployID))

def buildNavigation(selected):

    try:

        nav =  dbc.Nav(
                    [                       
                        dbc.NavItem(dbc.NavLink("Network Tree", href="/NetworkTree")),
                        dbc.NavItem(dbc.NavLink("Map", href="/ProgressMap")),                      
                    ],                 
                    pills=True)

        for item in nav.children:
            link = item.children
            if link.children == selected:
                link.active=True
            else:
                link.active=False

        return nav

    except Exception as e:
        rootLogger.warning("Error building navigation -- " + str(e))
        return None
 
try:   

    parentPath = os.path.dirname(currentFilePath)
    grandParentPath = os.path.dirname(parentPath)
    dataDirectory = os.path.join(grandParentPath, "data")
    dHandler = DataHandler(persistenceType="local directory", dataDirectory=dataDirectory)

    styleData = getStyle()

    # js lib used for colors
    chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
    externalScripts = [chroma]

    dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
    externalStyleSheets =[dbc.themes.YETI, dbc_css]

    #setup dash/wsgi server - note we need to override the assetts folder     
    assetFolder = os.environ["ASSETT_FOLDER"] 

    #need to expose flask server for authentication
    server = flask.Flask(__name__) 
    dash_app = dash.Dash(__name__, server=server,
        assets_folder=assetFolder,
        prevent_initial_callbacks=True,
        external_scripts=externalScripts,
        external_stylesheets=externalStyleSheets)

    CACHE_CONFIG = {
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR': 'cache-directory'
        }
    cache = Cache()
    cache.init_app(dash_app.server, config=CACHE_CONFIG)

except Exception as e:
    rootLogger.exception("Error Setting up basic config -- " + str(e))
       

try:

    from dashapp.progressmap import progressmap

    #Initialize progress map and setup callbacks
    pMap = progressmap.ProgressMap(dHandler)    
    pMap.registerCallbacks(dash_app, cache)     

    #Network Tree Progress Map
    from dashapp.TreeTest import nettreepage
    nTreePage = nettreepage.NetTreePage(dHandler)
    nTreePage.registerCallbacks(dash_app, cache)

    

except Exception as e:
    rootLogger.exception("Error Setting up layouts -- " + str(e))

try:

   
    navigation = buildNavigation("Main")

    #first build of layouts - when server is started
    progressMapLayout = pMap.createProgressMapLayout()
    netTreeLayout = nTreePage.createNetTreePageLayout()
   
    def getMainLayout():   
   
        ###This triggers when loaded page first time and when user hits refresh button, unique for each session

        timeStamp = datetime.datetime.now().strftime("%m/%d/%y %H:%M")
        mainStoreData = {'refreshTime': timeStamp}
  
         
        return html.Div([
        # represents the browser address bar and doesn't render anything
        dcc.Location(id='url', refresh=False),
        dcc.Location(id='redirect', refresh=True),
        # content will be rendered in this element
        html.Div(children=[
            html.Div([html.Div(html.H1("Lit Steering Dash (LSD v0.5)"), className="three columns"),                 
                html.Div(html.Div(navigation, id="navigation"),className="six columns"), 
                ],className="row") ,            
            html.Div(id='page-content'),
            dcc.Store(id="main-session", data=mainStoreData)
            ]),            
        ],className="dbc")      


    #note this is a reference to the function, so each page load it gets reloaded
    dash_app.layout = getMainLayout

   
    @dash_app.callback(Output('page-content', 'children'),Output('navigation', 'children'),
                Input('url', 'pathname'),State('main-session', 'data'))   
    def display_page(pathname, mainStoreData):   

        #this will run whenever they clck a link
        #intervals are per session. we need to somehow just refresh data once a session
        #lets do the timestamp check!?        
      
 
        view = None
        nav = None
        

        if pathname == '/':
            nav = buildNavigation("Progress Map")
            view = pMap.layout
        elif pathname == '/ProgressMap':
            nav = buildNavigation("Map")
            view = pMap.layout
        elif pathname == '/NetworkTree':
            nav = buildNavigation("Network Tree")
            view = nTreePage.layout
     
        else:
            view = "404"
        
       
        return view, nav

 


except Exception as e:
    rootLogger.exception("Error Setting up main page -- " + str(e))   
         


if __name__ == '__main__':
    #for this to run directly, right now callbacks in file 
    #and the assetts folder must be under "dashapps" or same folder as this file.
    #using the "assign" may just not work with my deployment style
   
    dash_app.run_server()


    

    
