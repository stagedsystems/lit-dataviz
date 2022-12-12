"""Network Tree - 

Dash layout to depict network build as a hierarchial tree
"""

import logging
import os
import sys

import dash
import dash_bootstrap_components as dbc
from dash import dcc,html, dash_table
from dash import Output, Input, State, callback_context
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from igraph import Graph

import pandas as pd
import numpy as np
import json
import datetime

#Adds higher directory to python modules path, needed to point correctly to assets
currentFilePath = os.path.dirname(os.path.realpath(__file__))
parentPath = os.path.dirname(currentFilePath)    
sys.path.append(currentFilePath) 
sys.path.append(parentPath)    

import treebuilder

from style import getStyle

class NetTreeVisual():
    """Small class to save properties required to visualize the tree node/edge properties"""

    def __init__(self):
         #vertex list data for tree
        self.vHoverLabels = []
        self.vLabels = []
        self.nodeColors = []
        self.nodeOpacity = []
        self.nodeBorderColors = []
        self.nodeBorderWeights = []

        #edge list data for tree
        self.eHoverLabels = []
        self.eLabels = []

        self.graphLayoutLength = 0
        self.nodeXCoords = []
        self.nodeYCoords = []


class NetTreePage():

    def __init__(self, dataHandler):       

        self.logger = logging.getLogger(__name__)  
        self.dHandler = dataHandler

        self.styleData = getStyle()

        self.f3Attributes = {"totalsubscribers" : int,
                "scheduledinstalls" : int,
                "subtakerate" : float}

        #layout should be static!
        self.layout = None
        

    def getData(self):
        """Expensive Data Gathering task, will be calculated and saved in dcc.store"""

        try:
            self.logger.info("tree expensive data gathering....")

            #load source data
            packageData = self.dHandler.getDataFromStore("NetPackageData")
            zoneData = self.dHandler.getDataFromStore("FiberhoodData")

            packageDF = pd.DataFrame(packageData)
            #make sure theres no duplicate rings before building packages
            packageDF =packageDF.drop_duplicates(subset='package', keep="first")
            packageDF.sort_values(by=["hiearchy"])
            packageDF.convert_dtypes().dtypes

            #if we want to filter out columns
            #zoneDF = zoneDF[["fiberhood", "networkstatus", "totalhhp", "coszonestatus","combinedtakerate", "totalsubscribers", "scheduledinstalls","costperhhp", "fhpercentcomplete","mduhoaorgreenfield"]]
                   
            #get unique ring names
            ringList = packageDF.ring.unique().tolist()

            #get additional F3/zone data
            zoneDF = pd.DataFrame(zoneData)
            zoneDFCols = ["fiberhood"]
            zoneDFCols.extend(self.f3Attributes.keys())
            zoneDF = zoneDF[zoneDFCols]  
            
            #replace all empty strings
            preppedZoneDF = zoneDF.replace(r'^\s*$', np.nan, regex=True)
            #replace nas with the appropriate type
            for col, colType in self.f3Attributes.items():
                if colType == int or colType == float:
                    preppedZoneDF.fillna({col:0}, inplace=True)  
                    if colType == int:
                        #in case decimals came across with the input, we want to convert to int
                        preppedZoneDF[col] = preppedZoneDF[col].astype(float).astype(int)
                else:
                    preppedZoneDF.fillna({col:""}, inplace=True)     

            preppedZoneDF = preppedZoneDF.astype(self.f3Attributes)

            #we want to add zone data
            packageAndZoneDF = packageDF.merge(preppedZoneDF, left_on="package", right_on="fiberhood", how="left")

            refreshTime = datetime.datetime.now().strftime("%m/%d/%y %H:%M")

            datasets = {
                'packageDF': packageAndZoneDF.to_json(orient='split', date_format='iso'),
                'ringList' : json.dumps(ringList),
                "refreshTime" : refreshTime

            }

            return json.dumps(datasets)

        except Exception as e:
            self.logger.exception("Error retrieving tree Data-- " + str(e))
            return None


    def buildDataTable(self, packageData :list):

        columnList = ["package",
                      "ring",
                      "feeder",
                      "hiearchy",
                      "packagestatus",
                      "packagepercentcomplete",
                      "totalhhp",
                      "odc",
                      "fibertestingcompletedate",
                      "packagehomesearned",
                      "rolluphomesearned",
                      "downstreamhomes"
                      ]

        #columns = [{"name": i, "id": i} for i in packageDF.columns]
        columns = [{"name": i, "id" : i} for i in columnList]

        dataTable =  dash_table.DataTable(id='datatable-tree',
            data=packageData, 
            columns=columns, 
            row_selectable="multi",
            selected_rows=[],
            page_size=20, 
            style_as_list_view=True, 
            filter_action="native",
            sort_action="native")            
           
        return dataTable
   
        
    def buildNetGraph(self, packageData : list, ringName:str):
        """Build the Network Graph Model for use in the output / dash, builds for specific ring"""

        try:

            tb = treebuilder.TreeBuilder()

            demoPackages = []

            for package in packageData:
                #for demo purposes only
                if ringName == package["ring"]:
                    demoPackages.append(package)                          

            #turn the list of packages into a network graph using igraph
            extraAttributesToMap = ["packagestatus", "totalhhp", "targetactivationdate","packagehomesearned", "rolluphomesearned", "downstreamhomes","totalsubscribers", "scheduledinstalls", "subtakerate"]
            nGraph = tb.buildGraph(demoPackages, extraAttributesToMap)
       
            return nGraph

        except Exception as e:
            self.logger.exception("Error Building Network Graph -- " + str(e))
            return None



    def customizeNodeProperties(self, graph :Graph, treeVisual:NetTreeVisual):
        """Add labels and other attributes to the graph vertexes"""

        try:

            #reset hover labels in case they were left over
            treeVisual.vHoverLabels = []
                
            #go through each vertex, at this point they should have attribute data
            for vertex in graph.vs:

                vAtts = vertex.attribute_names()

                #labels = ["Connected", "F1 Percent", "F2 Percent", "Status"]
                vLabel = str(vertex["Name"]) + "  (" + vertex["Tier"] + ")"

                # vLabel = "Name: " +str( vertex["Name"])      
                # vLabel += "<br>Connected: " + str(vertex["Connected"])                
                # vLabel += "<br>F1 Percent: " + str(vertex["F1 Percent"])
                # vLabel += "<br>F2 Percent: " + str(vertex["F2 Percent"])
                # vLabel += "<br>Status: " + str(vertex["Status"])
                #vLabel += "<br>Distance To Parent: " + str(vertex["Distance To Parent"])


                if vertex["Tier"] == "F1" and vertex["Completed"]:
                    vertex["Color"] = "green"
                elif vertex["Tier"] == "F1":
                    vertex["Color"] = "lightgreen"
                elif vertex["Tier"] == "F2" and vertex["Completed"]:
                    vertex["Color"] = "blue"
                elif vertex["Tier"] == "F2":
                    vertex["Color"] = "lightskyblue"
                elif vertex["Tier"] == "F3" and vertex["Completed"]:
                    vertex["Color"] = "red"
                else:
                    vertex["Color"] = "lightpink"                   

                #if vertex["Connected"]:
                    #vertex["Opacity"] = 1
                #else:
                    #vertex["Opacity"] = .75
                vertex["Opacity"] = 1

                if vertex["Completed"] and vertex["Connected"]:
                    vertex["BorderColor"] = "green"
                    vertex["BorderWeight"] = 2
                elif vertex["packagestatus"] == "Active Construction":
                    vertex["BorderColor"] = "orange"
                    vertex["BorderWeight"] = 2
                elif vertex["packagestatus"] == "Construction Complete":
                    vertex["BorderColor"] = "black"
                    vertex["BorderWeight"] = 2
                else:
                    vertex["BorderColor"] = "rgb(210,210,210)"
                    vertex["BorderWeight"] = 1

                labelsToExclude = ["Name", "name", "Tier","BorderWeight", "BorderColor", "Color", "Opacity","F1 Percent","F2 Percent","F3 Percent"]
                
                #add F1/F2/F3
                vertex["F1"] = vertex["F1"] + " - " + format(vertex["F1 Percent"], '.2%')
                vertex["F2"] = vertex["F2"] + " - " + format(vertex["F1 Percent"], '.2%')
                vertex["F3"] = vertex["F3"] + " - " + format(vertex["F3 Percent"], '.2%')

                #add all attributes
                for label in vAtts:
                    if label not in labelsToExclude:

                        #only add F3 labels where needed
                        if label in self.f3Attributes and vertex["Tier"] != "F3":
                            continue
                        else:

                            #first check if is a custom attribute and fix the type
                            if label in self.f3Attributes.keys():
                                if self.f3Attributes[label] == int:
                                    labelText = str(int(vertex[label]))
                                elif self.f3Attributes[label] == float:
                                    labelText = format(vertex[label], '.2%')
                                else:
                                    labelText = str(vertex[label])
                            else:          
                                                   
                                if isinstance(vertex[label], float):
                                    labelText = format(vertex[label], '.2%')
            
                                else:
                                    labelText = str(vertex[label])                                

                            vLabel += "<br>" + label + ": " + labelText                       
                        
                treeVisual.vHoverLabels.append(vLabel)

            treeVisual.vLabels=list(graph.vs['Name'])
            treeVisual.nodeColors = list(graph.vs['Color'])
            treeVisual.nodeOpacity = list(graph.vs["Opacity"])
            treeVisual.nodeBorderColors = list(graph.vs['BorderColor'])
            treeVisual.nodeBorderWeights = list(graph.vs['BorderWeight'])
               
            return treeVisual
                
        except Exception as e:
            self.logger.exception("Error Customizing Node Properties -- " + str(e))
            return None

    def customizeEdgeProperties(self, graph :Graph, treeVisual:NetTreeVisual):
        """Add labels and other attributes to the graph edges"""

        try:

            treeVisual.eHoverLabels = []

            #go through each edge, they have some basic properties
            for edge in graph.es:
                if edge["Connected"]:
                    edge["Color"] = "black"
                else:
                    edge["Color"] = "blue"
                eLabel = "Name: " +str(edge["Name"])      
                eLabel += "<br>Connected: " + str(edge["Connected"])    

                treeVisual.eHoverLabels.append(eLabel)           

            treeVisual.eLabels=list(graph.es['Name'])
            #edgeColors = list(g.es['Color'])
            return treeVisual    

        except Exception as e:
            self.logger.warning("Error Customizing Edge Properties -- " + str(e))
            return None

    def makeAnnotations(self,treeVisual:NetTreeVisual,font_size=10, font_color='rgb(250,250,250)'):
        
        annotations = []
        for k in range(treeVisual.graphLayoutLength):    

            xCenter = treeVisual.nodeXCoords[k]
            yCenter = treeVisual.nodeYCoords[k]
            
            #vertex annotations, these are placed using the same logic as  
            annotations.append(
                dict(
                    text=treeVisual.vLabels[k], # or replace labels with a different list for the text within the circle
                    x=xCenter, y=yCenter,
                    xref='x1', yref='y1',
                    font=dict(color=font_color, size=font_size),
                    showarrow=False)
            )

        return annotations

    def buildTreeFigure(self, graphData :Graph,  layout="kk",xMultiplier=2, yMultiplier=2):
        """X and Y multiplier are used for scaling the graph"""

        try:

            #create a small class to keep up with tree visual properties
            treeViz = NetTreeVisual()

            treeViz = self.customizeNodeProperties(graphData, treeViz)
            treeViz = self.customizeEdgeProperties(graphData, treeViz)
    
            #https://community.plotly.com/t/adding-edges-label-to-tree-plot/50541
            fig = go.Figure()

            g = graphData            
            
            nr_vertices = len(g.vs)
 
            #'kk' kamada-kawait, "rt", "rt_circular"
            lay = g.layout(layout)

            #position is a list of all the coordinates with the proper layout
            #position = {k: lay[k] for k in range(nr_vertices)}
            X = [lay[k][0] for k in range(nr_vertices)]
            #Y = [lay[k][1] for k in range(nr_vertices)]
            M = max(X) #top coordinate of area

            #es = EdgeSeq(g) # sequence of edges            
            E = [e.tuple for e in g.es] # list of edges - maybe replace with line above?

            treeViz.graphLayoutLength  = len(lay)
      
            #double x since the tree is wide
            treeViz.nodeXCoords= [xMultiplier*lay[k][0] for k in range(treeViz.graphLayoutLength)]        
            treeViz.nodeYCoords = [yMultiplier*M-lay[k][1] for k in range(treeViz.graphLayoutLength)]
                
            XLitEdge = []
            YLitEdge = []
            edgeLitLabels = []
            XUnlitEdge = []
            YUnlitEdge = []
            edgeUnlitLabels = []
            #edgeLabelCoord = []
            elabel_pos=[]
       
            for edge in g.es:                

                coord = edge.tuple
              
                edgeXCoords = [xMultiplier*lay[coord[0]][0],xMultiplier*lay[coord[1]][0], None]
                edgeYCoords = [yMultiplier*M-lay[coord[0]][1],yMultiplier*M-lay[coord[1]][1], None]

                if edge["Connected"]:
                    XLitEdge+=edgeXCoords
                    YLitEdge+=edgeYCoords                    
                    edgeLitLabels.append("Lit")                    
                    
                else:
                    XUnlitEdge+=edgeXCoords
                    YUnlitEdge+=edgeYCoords                     
                    edgeUnlitLabels.append("Unlit")                    

                #create a label on the center - take midpoint of edge line
                labelX = (edgeXCoords[0] + edgeXCoords[1]) / 2
                labelY = (edgeYCoords[0] + edgeYCoords[1]) /2
                elabel_pos.append([labelX, labelY])

            elabel_pos=np.asarray(elabel_pos)

            #edge labels, as transparent nodes that can hover
            fig.add_scatter(x=elabel_pos[:, 0], y=elabel_pos[:,1], mode='markers', 
                            marker=go.Marker(
                            opacity=0, size=50),
                            hoverinfo="text", text=treeViz.eHoverLabels)
        
            fig.add_trace(go.Scatter(x=XLitEdge,
                            y=YLitEdge,
                            mode="lines", #this may be imporant
                            name='Path',
                            line=dict(color="green", width=2),
                            hoverinfo='text',
                            text=edgeLitLabels                  
                             ))
            fig.add_trace(go.Scatter(x=XUnlitEdge,
                            y=YUnlitEdge,
                            mode="lines", #this may be imporant
                            name='Path',
                            line=dict(color="rgb(210,210,210)", width=1),
                            hoverinfo='text',
                            text=edgeUnlitLabels                  
                            ))
                                  
            fig.add_trace(go.Scatter(x=treeViz.nodeXCoords,
                            y=treeViz.nodeYCoords,
                            mode='markers',
                            name='Nodes',
                            marker=dict(symbol='circle', #circle-dot
                                            size=50,
                                            color=treeViz.nodeColors,    #'#DB4551',
                                            opacity=treeViz.nodeOpacity,
                                            line = dict(color=treeViz.nodeBorderColors, width=treeViz.nodeBorderWeights)                                         
                                            ),
                            text=treeViz.vHoverLabels,
                            hoverinfo='text',                    
                            ))
           
            axis = dict(showline=False, # hide axis line, grid, ticklabels and  title
                        zeroline=False,
                        showgrid=False,
                        showticklabels=False,
                        )          

            # to rotate tree, just swap x and y
            fig.update_layout(
                        annotations=self.makeAnnotations(treeViz),
                        font_size=12,
                        showlegend=False,         
                        height=800,
                        width=2000,                       
                        xaxis=axis,
                        yaxis=axis,
                        margin=dict(l=40, r=40, b=40, t=40),
                        hovermode='closest',
                        plot_bgcolor='rgb(248,248,248)',
                        paper_bgcolor=self.styleData["paper_bgcolor"]
                        )    

            return fig


        except Exception as e:
            self.logger.exception("Error Creating Graph Layout -- " + str(e))
            return None


    def createFigureData(self, ring :str, packageData :list):

        try:

            #need to make a shallow copy, because the data gets manipulated
            packageCopy = []
            for p in packageData:
                pCopy = {}
                for key, value in p.items():
                    pCopy[key] = value
                packageCopy.append(pCopy)

            #build network graph from source package data
            graphData = self.buildNetGraph(packageCopy, ring)

            return graphData

        except Exception as e:
            self.logger.exception("Error Creating Figure Data -- " + str(e))
            return None

    def createNetTreePageLayout(self):
        """Create the network tree page layout for dash"""

        try:

            self.logger.info("Initializing Tree Layout")    

            #this needs to be all the static data only            
            layoutOptions = [{"label" : "Circular Ring", "value" : "rt_circular"},
                            {"label" : "Tree", "value" : "rt"},
                            {"label" : "Kamada-Kawait", "value" : "kk"}]

            defaultLayout = layoutOptions[2]["value"]

            #Dynamic Data - even worth loading?
            dccStoreData = self.getData()

            treeLayout = dbc.Card(        
            children=[
                    dbc.CardHeader(html.H3("Tree Model of Network Build")),                        
                    dbc.CardBody([                            
                        html.Div(children='''
                    Tree represents F1/F2/F3 network section hiearchy. Light/gray sections are not connected/LIT.  Hover over nodes to see attributes, zoom as needed.
                    '''),
                    html.Div([                       
                    html.Div(dcc.Dropdown(id="ring-dropdown",                                     
                            placeholder="-Select a Ring-",                                              
                            ),className="two columns"),            
                    html.Div(dcc.Dropdown(id="tree-dropdown",
                            options=layoutOptions,          
                            placeholder="-Tree Orientation-",
                            value= defaultLayout                      
                            ), className="two columns")          
                    ],className="row"),
                    dcc.Graph(id="networktree"),
                    html.Button('Clear', id='clearbutton', n_clicks=0),
                    html.Div(id="tree-month-table"), 
                    dcc.Store(id='tree-filecache', data=dccStoreData), #added to trigger a callback that only fires first time page loads                           
                    dcc.Interval(
                        id='tree-interval',
                        interval=1, # in milliseconds
                        n_intervals=0,
                        max_intervals=1
                    )             
                    ])
                ]                   
            ,color=self.styleData["cardcolor"])  

            self.layout = treeLayout

            return treeLayout
            
        except Exception as e:
            self.logger.exception("Error Loading Tree Example -- " + str(e))
            self.logger.warning(str(sys.path))

    def registerCallbacks(self, app, cache):
        """Helper function to register all callbacks with dash server"""


        #first callback will take the dropdown and create a tree and update the graph
        @app.callback(Output("networktree", "figure"), 
        [Input("ring-dropdown", "value"),
        Input("tree-dropdown", "value")],
        State("tree-filecache", 'data'))
        def updateTreeLayout(ringName, layout, dccStore):
            """Redraw the tree if the ring selected or coordinate layout is changed"""
            try:

                #attempt to see what triggered it
                ctx = callback_context
                if ctx.triggered:
                    trigger = (ctx.triggered[0]['prop_id'].split('.')[0])
                    
                    if trigger == "ring-dropdown":
                    #Based on the user selected ring, get data and build network tree
             
                        dataSets = json.loads(dccStore)
                        packageDF = pd.read_json(dataSets['packageDF'], orient='split')
                        packageData =packageDF.to_dict('records')

                        treeData = self.createFigureData(ringName, packageData)
                        treeFigure = self.buildTreeFigure(treeData, layout=layout)
                        return treeFigure

                    elif trigger == "tree-dropdown":        
                        
                        #this can def be optimized, no need to reload the entire thing, but testing statelss right now
                        dataSets = json.loads(dccStore)
                        packageDF = pd.read_json(dataSets['packageDF'], orient='split')
                        packageData =packageDF.to_dict('records')

                        treeData = self.createFigureData(ringName, packageData)

                        return self.buildTreeFigure(treeData, layout=layout)

            except Exception as e:
                self.logger.warning(str(e))

        @app.callback([Output('datatable-tree', 'data'),
        Output('datatable-tree', 'selected_rows')], 
        [Input("networktree", "clickData"), 
        Input('clearbutton', 'n_clicks'),],
        State("tree-filecache", 'data'))
        def filterTable(selectedData, n_clicks, dccStore):

            try:
                 #attempt to see what triggered it
                ctx = callback_context
                if ctx.triggered:
                    trigger = (ctx.triggered[0]['prop_id'].split('.')[0])
                    dataSets = json.loads(dccStore)
                    packageDF = pd.read_json(dataSets['packageDF'], orient='split')
                    if trigger == "networktree":

                        if selectedData:
                            pointLabel = selectedData["points"][0]["text"]
                            pointName = pointLabel.split("<")[0].replace("Name: ", "")
                            dff = packageDF[packageDF.package == pointName]
                            return dff.to_dict('records'), [0]

                    else:                                 
                        return packageDF.to_dict('records'), []

            except Exception as e:
                self.logger.warning(str(e))


        @app.callback(
            Output('ring-dropdown', 'options'),       
            Output('ring-dropdown', 'value'),  
            [Input('tree-filecache', 'modified_timestamp'),
            Input("tree-filecache", 'data')] 
        )
        def updateRingOptions(refreshTime, dccStore):     
            #if the page has just loaded and no data, wait for a callback
            #from the dcc store itself
            if not dccStore:
                raise PreventUpdate
            else:         
                dataSets = json.loads(dccStore)
                ringList = json.loads(dataSets['ringList'])
                options=[{'label':ns, 'value':ns} for ns in ringList]                
                defaultRing = ringList[2]
                return options, defaultRing

        @app.callback(
            Output('tree-month-table', 'children'),         
            [Input('tree-filecache', 'modified_timestamp'),
            Input("tree-filecache", 'data')]
        )
        def updateDataTable(refreshTime, dccStore):     
            #if the page has just loaded and no data, wait for a callback
            #from the dcc store itself
            if not dccStore:
                raise PreventUpdate
            else:         
                dataSets = json.loads(dccStore)
                packageDF = pd.read_json(dataSets['packageDF'], orient='split')
                packageData = packageDF.to_dict('records')
                dataTable = self.buildDataTable(packageData)
                return dataTable

        @app.callback(
               Output("tree-filecache", 'data'),
               Input('tree-interval', 'n_intervals'),
               [State('tree-filecache', 'modified_timestamp'),
                State("tree-filecache", 'data'),
                State("main-session", 'data')]
              )

        #only refresh when page loads!
        def refreshData(n, refreshTime, treeStore, mainStore): 

            self.logger.info("Reports page loaded -- checking data..." + str(n))

            #check if store not initialized, should not happen currently
            if not treeStore:
                self.logger.info("tree store empty, loading...")
                jsonData = self.getData('records')
                return jsonData

            #if data is in there, check if need a refresh
            if treeStore and mainStore: #note sure why, but having the mainstore seems critical
                self.logger.info("tree store has data, checking for refresh...")

                refreshNeeded = False
                mainRefreshTime= datetime.datetime.strptime(mainStore["refreshTime"], "%m/%d/%y %H:%M")
                ###THIS IS NOT WORMING RIGHT< SOMETIMES NO MAIN STORE DATA, do db check here?
                if not refreshTime: #fires if we get here from page other than main       
                    #the ops store doesn't have a modified timestamp. not sure what would cause this.
                    #first check if the refresh was noted on the store data

                    dataSets = json.loads(treeStore)
                    if "refreshTime" in dataSets:
                        refreshTime = datetime.datetime.strptime(dataSets["refreshTime"], "%m/%d/%y %H:%M")
                        if refreshTime < mainRefreshTime:
                            refreshNeeded = True
                    else:
                        refreshNeeded = True #refresh just to be safe
                else:
                    #check timestamps before more expensive checks
                    #mainRefreshTime = datetime.datetime.fromtimestamp( mainStoreTimeStamp/1000) #milliseconds need to be div
                    treeRefreshTime = datetime.datetime.fromtimestamp(refreshTime/1000) #milliseconds need to be div

                    if treeRefreshTime < mainRefreshTime:
                        refreshNeeded = True
                    else:
                        refreshNeeded = False
                if refreshNeeded:
                    self.logger.info("Stale tree data -- refreshing...")
                    # compute value and send a signal when done
                    global_store(treeStore)
                    return treeStore
                else:
                    return treeStore
        
        # perform expensive computations in this "global store"
        # these computations are cached in a globally available
        # redis memory store which is available across processes
        # and for all time.
        @cache.memoize()
        def global_store(value):
            self.logger.info("Getting tree data for store...")
            #note this just gets the data, it 
            #doesn't refresh the figures - they will be triggered
            jsonData = self.getData()
            return jsonData


if __name__ == '__main__':

    #only for running locally while testing
    #may need to move to test folder instead

    #only when run directly
    grandParentPath = os.path.dirname(parentPath)    
    sys.path.append(grandParentPath)    
    ggParentPath = os.path.dirname(grandParentPath)
    sys.path.append(ggParentPath)    

    from flask_caching import Cache

    #loads internal configuration, e.g. folders, environment variables, etc.
    from dashapp import config
    from datahandler.datahandler import DataHandler
    from style import getStyle

    env="Test"
    
    config.setupEnv(env)

    styleData = getStyle()

    assetFolder = os.environ["ASSETT_FOLDER"]
    dataDirectory = os.path.join(ggParentPath, "data")
    dHandler = DataHandler(persistenceType="local directory", dataDirectory=dataDirectory)

     # js lib used for colors
    chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
    externalScripts = [chroma]

    nTreePage = NetTreePage(dHandler)
    
    dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
    externalStyleSheets =[dbc.themes.YETI, dbc_css]

    #app = dash.Dash(__name__,assets_folder=assetFolder,prevent_initial_callbacks=True)
    app = dash.Dash(__name__,
        assets_folder=assetFolder,
        prevent_initial_callbacks=True,
        external_scripts=externalScripts,
        external_stylesheets=externalStyleSheets)
    
    CACHE_CONFIG = {
        'CACHE_TYPE': 'FileSystemCache',
        'CACHE_DIR' : 'cache-directory'
        }
    cache = Cache()
    cache.init_app(app.server, config=CACHE_CONFIG)

    
    
    nTreePage.registerCallbacks(app,cache)

    netTreeLayout = nTreePage.createNetTreePageLayout()

    mainStoreData = {'refreshTime': datetime.datetime.now().strftime("%m/%d/%y %H:%M")}

    #new way of refreshing data on page load
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content'),
        dcc.Store(id="main-session", data=mainStoreData) #so errors dont get thrown
    ])

    #note sure if i am doing this right...
    from dash.dependencies import Input, Output, State
    @app.callback(Output('page-content', 'children'),
             Input('url', 'pathname'))
    def display_page(pathname):
        return nTreePage.layout
 
    #app.layout = pLayout 

    app.run_server(debug=True, use_reloader=False) # Turn off reloader if inside Jupyter