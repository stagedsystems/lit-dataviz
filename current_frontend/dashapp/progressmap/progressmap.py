"""Progress Map - 

Dash layout using leaflet that shows boundaries and fiberhood statistics

This is built as a class and methods create the callbacks and layout

"""

import logging
import os
import sys
from this import d
import datetime
import json
#https://stackoverflow.com/questions/43214204/how-do-i-tell-if-a-column-in-a-pandas-dataframe-is-of-type-datetime-how-do-i-te
from pandas.api.types import is_datetime64_any_dtype as is_datetime

import dash
from dash import dcc,html, dash_table
from dash import Output, Input, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import dash_leaflet as dl

#may be terrible idea
from dash.development.base_component import Component

from dash_extensions.javascript import Namespace,arrow_function
from dash_extensions.enrich import html
from dash.exceptions import PreventUpdate



#Adds higher directory to python modules path, needed to point correctly to assets
currentFilePath = os.path.dirname(os.path.realpath(__file__))
parentPath = os.path.dirname(currentFilePath)    
sys.path.append(currentFilePath) 
sys.path.append(parentPath)    

import utils as ut
from style import getStyle


class ProgressMap():

    def __init__(self, dataHandler):

        self.logger = logging.getLogger(__name__)  
        self.dHandler = dataHandler

        self.styleData = getStyle()

        self.zoneColorbar = None     
        self.litColorMap = {}
        self.litColorScale = []
        self.litNetCategories= []

        self.pointColorPropOptions = []     
        self.pointColorScaleOptions = []
        self.polyColorPropOptions =  [] 
        self.polyColorScaleOptions = []                                        

        self.initializeNetColors()

        #layout should be static!
        self.layout = None
                       

    def mergeTabAndGeoData(self,tabularData, geoData, geoIDField):
        """The map needs geojson data to display correctly, so will start with geojson and add 
        updated attributes from the database"""

        try:

      
            #organize zone tabular data into dictionary for merging
            zoneData = {}
            for zone in tabularData:
                zoneData[zone["fiberhood"]] = {}
                for key, value in zone.items():
                    zoneData[zone["fiberhood"]][key] = value

            #go through each geojson polygon, clear existing properties
            for feature in geoData["features"]:

                geoID = feature["properties"][geoIDField]
                #split name if it contains leg and FH, don't split if Seville/WestField
                if "-" in geoID and "-FH" not in geoID:
                    split = geoID.split("-")

                    fhName = split[-1]
                else:
                    fhName = feature["properties"][geoIDField]

                feature["properties"].clear()
                feature["properties"][geoIDField] = fhName

                #get the matching tabular zone record, and update geojson with new attributes
                if fhName in zoneData.keys():
                    #get attribute data from tabular zone dictionary
                    for key, value in zoneData[fhName].items():
                        feature["properties"][key] = value

            
            return geoData
            

        except Exception as e:
            self.logger.warning("Error attempting to merge zone geo and table data - " + str(e))
            return None


    def getData(self):
        """Data will need to be accessible by multiple components and callbacks"""

        try:

            self.logger.info("getting zone data for progress map....")
            zoneData = {}

            zoneData = self.dHandler.getDataFromStore("FiberhoodData")

            #datetimes need to be converted for serialization
            zoneDF = pd.DataFrame(zoneData)    
            for col in zoneDF.columns:
                if zoneDF[col].dtype == 'datetime64[ns]':
                    zoneDF[col] = zoneDF[col].dt.strftime('%Y-%m-%d')            
                                       
            zoneDF = zoneDF[["fiberhood", "networkstatus", "totalhhp", "coszonestatus","combinedtakerate", "totalsubscribers", "scheduledinstalls","costperhhp", "fhpercentcomplete","specialprojectsmduhoaother", "totalsurveys"]]
            
            refreshTime = datetime.datetime.now().strftime("%m/%d/%y %H:%M")

            datasets = {
                    "zoneDF" : zoneDF.to_json(orient='split', date_format='iso'),  
                    "refreshTime" : refreshTime
            }  

            #datasets = self.initializeNetColors(datasets)

            return json.dumps(datasets)

        except Exception as e:
            self.logger.exception("Error retrieving zone data -- " + str(e))
            return None

    def initializeNetColors(self):
        """Tag zone data with color code numbers corresponding to network status"""

        self.litColorMap = {
                    "Planning" : "gray",
                    "Detailed Design" : "gold" ,               
                    "Construction Package" : "orange",
                    "Permitting" : "tomato",
                    "Permits Approved Ready For Construction" : "darkorchid",
                    "Active Construction" : "cornflowerblue",
                    "Construction Complete" : "lightseagreen",                
                    "LIT" : "limegreen"
                    }       


        self.litColorScale = []
        self.litNetCategories = []

        try:


            for litStatus, litColor in self.litColorMap.items():
    
                self.litColorScale.append(litColor)    
                self.litNetCategories.append(litStatus)

            return True

        except Exception as e:
            self.logger.exception("Error intializing network colors -- " + str(e))
            return False



    def setColorScale(self, colorName):

        #https://colorbrewer2.org/#type=sequential&scheme=BuGn&n=3
        #built in - https://github.com/gka/chroma.js/blob/main/src/colors/colorbrewer.js

        #         Diverging
        #     BrBG, PiYG, PRGn, PuOr, RdBu, RdGy, RdYlBu, RdYlGn, Spectral
        # Qualitative
        #     Accent, Dark2, Paired, Pastel1, Pastel2, Set1, Set2, Set3
        # Sequential
        #     Blues, BuGn, BuPu, GnBu, Greens, Greys, Oranges, OrRd, PuBu, PuBuGn, PuRd, Purples, RdPu, Reds, YlGn, YlGnBu, YlOrBr, YlOrRd

        #note - the classes may be important to better spread the scale out

        try:

            if colorName == "BuGn":
                #colorscale = ['#f7fcfd', '#e5f5f9', '#ccece6', '#99d8c9', '#66c2a4', '#41ae76', '#238b45', '#006d2c', '#00441b'] #bugn
                colorScale = ['#f7fcfd', '#e5f5f9', '#ccece6', '#99d8c9', '#66c2a4', '#41ae76', '#238b45', '#006d2c'] #bugn
            elif colorName == "Rainbow":
                #colorscale = ['purple','blue','green','yellow','orange','red']
                colorScale = ['red', 'yellow', 'green', 'blue', 'purple']
            elif colorName == "OrRd":
                colorScale = ['#fff7ec', '#fee8c8', '#fdd49e', '#fdbb84', '#fc8d59', '#ef6548', '#d7301f', '#b30000', '#7f0000']
            elif colorName == "Lit Status":
                colorScale = self.litColorScale
                           
                    
            else:
                colorScale = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026']
         

            return colorScale



        except Exception as e:
            self.logger.exception("Error setting color scale -- " + str(e))
            return None


    def calcPropertyMinMax(self, propertyName):

        try:

            if propertyName == "statuscolorcode":

                cabinetColorMin = 0
                cabinetColorMax = len(self.litColorScale)-1                         
                                                                                        

            elif propertyName == "combinedtakerate":
                #rebuild the color bar
                cabinetColorMin = 0
                cabinetColorMax = .5

            elif propertyName == "surveymrc":
                cabinetColorMin = 0
                cabinetColorMax = 5000

            elif propertyName == "totalsurveys":
                cabinetColorMin = 0
                cabinetColorMax = 50

            elif propertyName == "costperhhp":
                cabinetColorMin = 0
                cabinetColorMax = 5000

            elif propertyName == "totalsubscribers":
                cabinetColorMin = 0
                cabinetColorMax = 50

            elif propertyName == "fhpercentcomplete":
                cabinetColorMin = 0
                cabinetColorMax = 1

            else:
                cabinetColorMin = 0
                cabinetColorMax = 1

            return cabinetColorMin, cabinetColorMax

        except Exception as e:
            self.logger.exception("Error calculating property min/max -- " + str(e))
            return None

            
    def customizeZoneGeometry(self, ns,colorProp,colorScale, mergedZoneData):

        try:

            colorMin = 0
            colorMax = 1

            colorBar = self.createColorBar(colorProp, colorScale, colorMin, colorMax, position="bottomright", id="zonecolorbar")                                    
               
            for feature in mergedZoneData["features"]:
                try:
                    takeRateText = '{:.2%}'.format(feature["properties"]["combinedtakerate"])
                    feature["properties"]["tooltip"] = "Take Rate: " + str(takeRateText)
                except:
                    feature["properties"]["tooltip"] = "Take Rate: " 
                               
            
            zoneColorScale = self.setColorScale(colorScale)         

            zoneStyle = dict(weight=2, opacity=.5, color='gray', dashArray='3', fillOpacity=0.5)

      
            zoneHide = {"colorscale" :zoneColorScale, 
                "style": zoneStyle, 
                "colorProp":colorProp, 
                "selectedZones" :[],
                "min" : colorMin, 
                "max" : colorMax
                }

            #note the assetss may be under the root folder not "dashapps"
            zoneGeoJSON =  dl.GeoJSON(data=mergedZoneData, 
                            options=dict(style=ns("zoneStyle")),  # how to style each polygon
                            #zoomToBounds=True,  # when true, zooms to bounds when data changes (e.g. on load)
                            zoomToBoundsOnClick=True,  # when true, zooms to bounds of feature (e.g. polygon) on click
                            hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
                            #hideout=dict(colorscale=zoneColorscale, classes=classes, style=style, colorProp="fhpercentcomplete"),
                            hideout=zoneHide,
                            id="zones")

            return zoneGeoJSON, colorBar
    
        except Exception as e:
            self.logger.exception("Error customizing zone geometry -- " + str(e))
            return None

    def createColorBar(self, colorProp, colorCode, colorMin, colorMax, position, id):

        try:

            cabinetColorbar = dl.Colorbar(width=20, 
                                    height=150,                                        
                                    min=colorMin, 
                                    max=colorMax,               
                                    position=position,                                       
                                    id=id)

            colorScale = self.setColorScale(colorCode)
     
            if colorProp == "statuscolorcode":  
                indices = list(range(len(self.litNetCategories) + 1))                   
      
                cabinetColorbar.max = colorMax + 1
                cabinetColorbar.colorscale = self.litColorScale
                cabinetColorbar.classes = indices
                cabinetColorbar.tickValues = [item + 0.5 for item in indices[:-1]]
                cabinetColorbar.tickText = self.litNetCategories

                            
            else:         
                cabinetColorbar.colorscale  = colorScale  
                cabinetColorbar.classes  = None #default is continuous
                cabinetColorbar.tickValues = None
                cabinetColorbar.tickText = None
                        
            return cabinetColorbar

        except Exception as e:
            self.logger.exception("Error customizing cabinet color coding -- " + str(e))
            return None


    def customizeCabinetPoints(self, ns, colorProp,colorScale, mergedCabinetData):

        try:
          
            colorMin = 0
            colorMax = len(self.litColorScale)-1
                   
            colorBar =  self.createColorBar(colorProp, colorScale, colorMin, colorMax, position="bottomleft", id="cabinetcolorbar")                                                        

            cabinetHide = {"colorProp" : colorProp,
                           "circleOptions" : {"fillOpacity" : 1, "stroke" : False, "radius" : 5},
                           "min" : colorMin,
                           "max" : colorMax,
                           "colorscale" : self.litColorScale
            }
  
            cabinetGeoJSON =  dl.GeoJSON(data=mergedCabinetData,
                            zoomToBounds=True,  # when true, zooms to bounds when data changes (e.g. on load)
                            options=dict(pointToLayer=ns("cabinetPointToLayer")),
                            superClusterOptions=dict(radius=50), #adjust cluster size
                            zoomToBoundsOnClick=True,  
                            hideout=cabinetHide,
                            id="cabinets")

            return cabinetGeoJSON, colorBar
            
        except Exception as e:
            self.logger.exception("Error customizing cabinet points -- " + str(e))
            return None

    def buildLeafletLayout(self, zoneDF):

        try:

            #more data gathering
            zoneData = zoneDF.to_dict("records")

            #load source data
            zoneGeoData = self.dHandler.getDataFromStore("ZoneGeoData")
            mergedZoneData = self.mergeTabAndGeoData(zoneData, zoneGeoData, "Name")
            cabinetGeoData = self.dHandler.getDataFromStore("CabinetGeoData")      
            mergedCabinetData = self.mergeTabAndGeoData(zoneData, cabinetGeoData, "name") 

             #add color properties to geo data
            i = 0           
            for litStatus in self.litColorMap.keys():
  
                for zone in mergedCabinetData["features"]:
                    if "networkstatus" in zone["properties"].keys() and zone["properties"]["networkstatus"] == litStatus:
                        zone["properties"]["statuscolorcode"] = i

                for zone in mergedZoneData["features"]:
                    if "networkstatus" in zone["properties"].keys() and zone["properties"]["networkstatus"] == litStatus:
                        zone["properties"]["statuscolorcode"] = i
                i += 1


            #TILE LAYER FIRST
            attribution='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors'
            tileLayer = dl.TileLayer(url='https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png', attribution=attribution, maxZoom=20)

              #this is a re-work to use a seperate file for the style function instead of using "assign"
            #functions part of the namespace can be used as component property
            ns = Namespace("dashExtensions", "default") #matches naming in .js file - probably need better name 
            

            defaultPolyColorProp = self.polyColorPropOptions[0]["value"]
            defaultPolyColorScale = self.polyColorScaleOptions[0]["value"]   
            zoneGeoJSON, zoneColorbar = self.customizeZoneGeometry(ns,defaultPolyColorProp,defaultPolyColorScale, mergedZoneData)      

            #customize the polygon and point map features    
            defaultPointColorProp = self.pointColorPropOptions[0]["value"]
            defaultPointColorScale = self.pointColorScaleOptions[0]["value"]
            cabinetGeoJSON, cabinetColorbar= self.customizeCabinetPoints(ns, defaultPointColorProp, defaultPointColorScale, mergedCabinetData)     


            # Create info control.
            info = html.Div(children=self.getZoneInfo(), id="info", className="info",
                        style={"position": "absolute", "top": "10px", "right": "10px", "zIndex": "1000"})
                         

            #surprised this works but it does - passing the styles with a dict is interesting
            crowFlyEdgeGeoJSON =  dl.GeoJSON(url="/assets/meb05edges.json",
                                    #options=dict(style=dict(weight=2, opacity=.8, color='black',  fillOpacity=1)),
                                    options=dict(style=ns("edgeColorByStatus")),
                                    hideout=dict(style=dict(weight=2, opacity=.8, color='black', fillOpacity=1), colorProp="parent status"),
                                    id="edges")

            leafletLayout = html.Div([
                dl.Map(center=[39, -98], zoom=4, children=[
            # dl.Pane( [tileLayer], style={"zIndex":151}),                        
            # dl.Pane( [cabinetGeoJSON], style={"zIndex":1000}),  
            # #dl.Pane( [zoneGeoJSON], style={"zIndex": 999}), #attempt to wwrap in pane to force z    
            tileLayer,
            zoneGeoJSON,
            cabinetGeoJSON,                   
            dl.Pane([cabinetColorbar, zoneColorbar], id="colorbarpane"),
            #crowFlyEdgeGeoJSON,
            info  # geobuf resource (fastest option)
            ], 
            style={'width': '100%', 'height': '50vh', 'margin': "auto", "display": "block"}, id="map")          
            ])

            return leafletLayout



        except Exception as e:
            self.logger.exception("Error building leaflet layout -- " + str(e))
            return None

    def createProgressMapLayout(self):

        try:

            self.logger.info("Initializing Progress Map...")

            #Dynamic Data - even worth loading?
            dccStoreData = self.getData()   
            dataSets = json.loads(dccStoreData)
            zoneDF = pd.read_json(dataSets['zoneDF'], orient='split')
            #zoneGeoData = pd.read_json(dataSets['zoneGeoData'], orient='split')
          
         
            #static stuff          
            #Cabinet Color Property Drodpwon
            self.pointColorPropOptions = [ {"label" : "Network Status", "value" : "statuscolorcode"},
                                {"label" : "Percent Complete", "value" : "fhpercentcomplete"},   
                                {"label" : "Take rate", "value" : "combinedtakerate"},
                                {"label" : "MRC", "value" : "surveymrc"},
                                {"label" : "Cost Per HHP", "value" : "costperhhp"},
                                {"label" : "Surveys", "value" : "totalsurveys"},
                                {"label" : "Subs", "value" : "totalsubscribers"}                                
                                ]                     

            #Cabinet Coloring Scale Dropdon
            self.pointColorScaleOptions = [ {"label" : "Rainbow", "value" : "Rainbow"},
                                {"label" : "Blue->Green", "value" : "BuGn"},                           
                                {"label" : "Orange->Red", "value" : "OrRd"}]
                    
            #Zone Polygon Color Property Dropdown
            self.polyColorPropOptions =  [{"label" : "Percent Complete", "value" : "fhpercentcomplete"},
                                    {"label" : "Network Status", "value" : "statuscolorcode"},
                                    {"label" : "Take Rate", "value" : "combinedtakerate"},                          
                                    {"label" : "MRC", "value" : "surveymrc"},
                                    {"label" : "Cost Per HHP", "value" : "costperhhp"},
                                    {"label" : "Surveys", "value" : "totalsurveys"},
                                    {"label" : "Subs", "value" : "totalsubscribers"}                                  
                                ]
            

            #Zone Polygon Coloring Scale Dropdown           
            self.polyColorScaleOptions = [  {"label" : "Blue->Green", "value" : "BuGn"},  
                                    {"label" : "Rainbow", "value" : "Rainbow"},                                                        
                                {"label" : "Orange->Red", "value" : "OrRd"}]
                

            leafletLayout = self.buildLeafletLayout(zoneDF)

            dataStyleConditions = [
                {
                    'if': {
                    'filter_query': '{networkstatus} = "LIT"', # comparing columns to each other
                    'column_id': 'networkstatus'
                    },
                    'backgroundColor': '#3D9970'
                }
            ]
            
            #zoneDF = pd.read_json(dataSets['zoneDF'], orient='split')
            #zoneDFData  = dataSets["zoneDFData"]
            zoneDFData =  zoneDF.to_dict('records')

            netstats = zoneDF.networkstatus.unique().tolist()
                                       
    
            columns = [{"name": i, "id": i} for i in zoneDF.columns]
            dataLayout = html.Div(                    
                    dash_table.DataTable(id='datatable-interactivity',
                    data=zoneDFData, 
                    columns=columns, 
                    row_selectable="multi",
                    selected_rows=[],
                    page_size=20, 
                    style_as_list_view=True, 
                    filter_action="native",
                    sort_action="native",
                    style_data_conditional=dataStyleConditions)
                    )      


            dataCollapse = html.Div(
                [
                    dbc.Button(
                        "Expand Fiberhood Data Table",
                        id="collapse-button",
                        className="mb-3",
                        color="primary",
                        n_clicks=0,
                    ),                    
                    dbc.Collapse(
                        html.Div([
                            html.Div(children='''Source data is below, can be sorted/filtered and should synch to map. Selecting rows at the left will highlight zones in map.'''),
                            dataLayout
                            ]),
                            id="collapse",
                            is_open=False,                      
                    ),
                ]
            )

            #dropdown defaults   
            defaultPointColorProp = self.pointColorPropOptions[0]["value"]
            defaultPointColorScale = self.pointColorScaleOptions[0]["value"]        
            defaultPolyColorProp = self.polyColorPropOptions[0]["value"]
            defaultPolyColorScale = self.polyColorScaleOptions[0]["value"]   

        
            layout = dbc.Card(        
            children=[
                    dbc.CardHeader(html.H3("Progress / Take Rate Map")),                        
                    dbc.CardBody([       
                        html.Div([   
                            html.Div([
                                html.H5(children='''Color Coding Options'''),
                                html.Div(children='''Select the attribute and color scale and the map will change colors for either the cabinet points or zone polygons'''),
                                html.Br(),
                                html.B(children='''Cabinet Point'''),
                                dcc.Dropdown(id="cabinetpropdropdown",
                                options=self.pointColorPropOptions,                                       
                                value= defaultPointColorProp,   
                                clearable=False),           
                                dcc.Dropdown(id="cabinetcolordropdown",
                                options=self.pointColorScaleOptions,        
                                value= defaultPointColorScale,   
                                clearable=False),          
                                html.Br(),
                                html.B(children='''Fiberhood Poly'''),
                                dcc.Dropdown(id="polypropdropdown",
                                options=self.polyColorPropOptions,        
                                value= defaultPolyColorProp,   
                                clearable=False),
                                dcc.Dropdown(id="polycolordropdown",
                                options=self.polyColorScaleOptions,        
                                value= defaultPolyColorScale,   
                                clearable=False),                              
                                html.Br(),html.Br(),
                                html.Br(),html.Br(),
                                html.Div(children='''Network Status Filter'''),
                                dcc.Dropdown(id="filter_dropdown",
                                    options=[{'label':ns, 'value':ns} for ns in netstats],          
                                    placeholder="-Select a Status-",
                                    multi=True
                                    ),
                            ],style={'width': '15%'}),
                            html.Div(leafletLayout,id="leaflet-progressmap",style={'width': '85%'})
                        ],className="row"),                 
                        dataCollapse,
                        dcc.Store(id='progressmap-filecache', data=dccStoreData), #added to trigger a callback that only fires first time page loads          
                        dcc.Interval(
                                id='progressmap-interval',
                                interval=1, # in milliseconds
                                n_intervals=0,
                                max_intervals=1
                            )  
                    ])
                ]         
 
            ,color=self.styleData["cardcolor"])  #card

            self.layout = layout

            return layout

            
        except Exception as e:
            self.logger.exception("Error Loading Leaflet Example -- " + str(e))
            self.logger.warning(str(sys.path))

    

    #hover callback function, when user hovers over a polygon
    def getZoneInfo(self,feature=None):
        header = [html.H4("Zone Info")]
        if not feature:
            return header + [html.P("Hover over a Fiberhood")]

        try:
            displayTakeRate = '{:.2%}'.format(feature["properties"]["combinedtakerate"])
        except:
            displayTakeRate = ""
        try:
            displayPercentComplete = '{:.2%}'.format(feature["properties"]["fhpercentcomplete"])
        except:
            displayPercentComplete = ""
        try:
            displayMRC = '${:,.2f}'.format(feature["properties"]["surveymrc"] )
        except:
            displayMRC = ""
        try:
            displayCostToBuild = '${:,.2f}'.format(feature["properties"]["estcosttobuild"] )
        except:
            displayCostToBuild = ""
        try:
            displayStatus = feature["properties"]["networkstatus"]
        except:    
            displayStatus = ""
        try:
            displayHHP = feature["properties"]["totalhhp"]
        except:
            displayHHP = ""
        
        return header + [html.B(feature["properties"]["Name"]), 
                        html.Br(),
                        "HHP: " + str(displayHHP),
                        html.Br(),
                        "Status: ",
                        html.Br(), 
                        displayStatus,
                        html.Br(),
                        "Percent Complete: " + displayPercentComplete,
                        html.Br(),
                        "Take Rate: " + displayTakeRate,
                        html.Br(),
                        "MRC: " + displayMRC,
                        html.Br(),
                        "Cost To Build: " + displayCostToBuild ]     



    def registerCallbacks(self, app, cache):
        """Helper function to register all callbacks with dash server"""

        @app.callback(Output("info", "children"), [Input("zones", "hover_feature")])
        def zoneHover(feature):
            """Fill basic zone data into info popup on top of map"""
            return self.getZoneInfo(feature)

                 
        @app.callback(Output("colorbarpane", "children"), [Input("cabinetcolordropdown", "value"), Input("cabinetpropdropdown", "value"),Input("polycolordropdown", "value"), Input("polypropdropdown", "value"),Input("colorbarpane", "children")])
        def refreshColorBar(selectedCabColorScaleName, selectedCabColorProp,selectedPolyColorScaleName, selectedPolyColorProp,mapChildren) :
            """Will change the cabinet color options based on selected scale"""

            try:
                                                              

                ctx = callback_context
                if ctx.triggered:

                    trigger = (ctx.triggered[0]['prop_id'].split('.')[0])

                    #first check, see if they changed the cabinet property
                    if trigger == "cabinetpropdropdown" or trigger =="cabinetcolordropdown":   

                        selectedColorProp = selectedCabColorProp
                        selectedColorScaleName = selectedCabColorScaleName                     

                        mapChildren = [chart for chart in mapChildren if "cabinetcolorbar" not in str(chart)]                   
                                     
                    
                        cabinetColorMin, cabinetColorMax = self.calcPropertyMinMax(selectedColorProp)             
                                                         
                    
                        newColorBar = self.createColorBar(selectedColorProp, 
                                                        selectedColorScaleName, 
                                                        cabinetColorMin, 
                                                        cabinetColorMax,
                                                        position="bottomleft", 
                                                        id="cabinetcolorbar")

                        mapChildren.append(newColorBar)  

                    elif trigger == "polypropdropdown" or trigger =="polycolordropdown": 
                        
                        selectedColorProp = selectedPolyColorProp
                        selectedColorScaleName = selectedPolyColorScaleName 
                        
                        mapChildren = [chart for chart in mapChildren if "zonecolorbar" not in str(chart)]                   
                                     
                    
                        cabinetColorMin, cabinetColorMax = self.calcPropertyMinMax(selectedColorProp)             
                                                         
                    
                        newColorBar = self.createColorBar(selectedColorProp, 
                                                        selectedColorScaleName, 
                                                        cabinetColorMin, 
                                                        cabinetColorMax,
                                                        position="bottomright", 
                                                        id="zonecolorbar")                         
                                 
                     
                        mapChildren.append(newColorBar)   

                    return mapChildren     

                
            except Exception as e:
                self.logger.warning(str(e))
            
            
        @app.callback([Output("cabinets", "hideout"),
            Output("cabinetcolordropdown", "disabled")], 
            [Input("cabinetcolordropdown", "value"), 
            Input("cabinetpropdropdown", "value")],
            State("cabinets", "hideout"), )
        def updateCabinetColor(selectedColorScaleName, selectedColorProp,originalHideout) :
            """Will change the cabinet color options based on selected scale"""

            try:

                cabinetHide = originalHideout    
                colorDropDownDisabled = False                                                    

                ctx = callback_context
                if ctx.triggered:

                    trigger = (ctx.triggered[0]['prop_id'].split('.')[0])

                    #first check, see if they changed the cabinet property
                    if trigger == "cabinetpropdropdown":                        
                    
                                     
                        if selectedColorProp == "statuscolorcode":                  
                                                                                
                            cabinetHide["colorscale"] = self.litColorScale
                   
                            colorDropDownDisabled = True
                                                                                           

                        else:                                  
                     
                            cabinetHide["colorscale"] = self.setColorScale(selectedColorScaleName)

                        cabinetColorMin, cabinetColorMax = self.calcPropertyMinMax(selectedColorProp)                
                     
                        cabinetHide["colorProp"] = selectedColorProp
                        cabinetHide["min"] = cabinetColorMin
                        cabinetHide["max"] = cabinetColorMax  
                 

                    elif trigger == "cabinetcolordropdown":   

                        if selectedColorProp != "statuscolorcode":

                            cabinetHide["colorscale"] = self.setColorScale(selectedColorScaleName)
                        #cabinetHide["colorscale"] = "BuGn"
                           
                    return cabinetHide,colorDropDownDisabled 
       
                
            except Exception as e:
                self.logger.warning(str(e))


        @app.callback([Output("zones", "hideout"),Output("polycolordropdown", "disabled")], [Input("datatable-interactivity", "selected_rows"),
                                                    Input("datatable-interactivity", "data"), 
                                                    Input("polycolordropdown", "value"),
                                                    Input("polypropdropdown", "value")],
                                                    State("zones", "hideout")) 
        def updateZoneAppearance(selected_rows, zoneData, selectedColorScaleName, selectedColorProp,originalHideOut):
            """Will highlight the leaflet zone boundary for fiberhood selected in databable"""

            zoneHide = originalHideOut
            if selectedColorProp == "statuscolorcode":
                colorDropDownDisabled = True 
            else:
                colorDropDownDisabled = False

            ctx = callback_context
            if ctx.triggered:

                trigger = (ctx.triggered[0]['prop_id'].split('.')[0])

                #first check, see if they changed the cabinet property
                if trigger == "datatable-interactivity":
                  
                    if selected_rows:
                        fhList = []
                        #this isn't the best "pandas way", but seems to work
                        for i in selected_rows:
                            fhList.append(zoneData[i]["fiberhood"])

                        selectedZones = fhList

                        zoneHide["selectedZones"] = selectedZones
                    else:
                        #if it was triggered, but no change in selection stop update
                        #bcause it will mess up the point/poly overlay
                        if zoneHide["selectedZones"] == []:
                            raise PreventUpdate
                        else:
                            zoneHide["selectedZones"] = []

                elif trigger=="polypropdropdown":

                    if selectedColorProp == "statuscolorcode":  

                        zoneHide["colorscale"] = self.litColorScale                    
                      
                    else:                                  
                     
                        zoneHide["colorscale"] = self.setColorScale(selectedColorScaleName)

                    cabinetColorMin, cabinetColorMax = self.calcPropertyMinMax(selectedColorProp)  

                    zoneHide["colorProp"] = selectedColorProp
                    zoneHide["min"] = cabinetColorMin
                    zoneHide["max"] = cabinetColorMax  

                
                elif trigger=="polycolordropdown":

                    if selectedColorProp != "statuscolorcode":

                        zoneHide["colorscale"] = self.setColorScale(selectedColorScaleName)

                 
                
            #returns the hideout, updated with a list of fiberhoods
            return zoneHide, colorDropDownDisabled



        @app.callback([Output('datatable-interactivity', 'data'),
            Output('datatable-interactivity', 'selected_rows')],
            [Input('filter_dropdown', 'value'), 
            Input("zones", "click_feature"),
            Input("progressmap-filecache", 'data')] )
        def filterDataTable(netstatus, feature, dccStore):
            """Update datatable, can be filtered by either map click or dropdown filter"""

            try:

                dataSets = json.loads(dccStore)

                df = pd.read_json(dataSets['zoneDF'], orient='split')

                if (not netstatus and not feature):
                    return df.to_dict('records'), []

                #attempt to see what triggered it
                ctx = callback_context
                if ctx.triggered:
                    trigger = (ctx.triggered[0]['prop_id'].split('.')[0])
                    if trigger == "zones":

                        if feature:
                            dff = df[df.fiberhood == feature["properties"]["fiberhood"]]

                            #rowListTry1 = dff.loc[df.fiberhood == feature["properties"]["fiberhood"]]
                            rowListTry2 = dff.index.values.tolist()

                            #need new index?
                            newRowIDs = [[i for i in range(len(dff))]]                        

                            return dff.to_dict('records'), [0]

                    #was triggered by dropdown, not by map
                    if netstatus and netstatus is not None:
                        
                        dff = df[df.networkstatus.isin(netstatus)]
                    #selectedRow = dff.loc[dffiber.isin(some_values)]

                        newRowIDs = [i for i in range(len(dff))]

                        return dff.to_dict('records'), newRowIDs
                        
                    else:
                        return df.to_dict('records'), []


            except Exception as e:
                self.logger.warning(str(e))

        @app.callback(
            Output('leaflet-progressmap', 'children'),         
            [Input('progressmap-filecache', 'modified_timestamp'),
            Input("progressmap-filecache", 'data')]
        )
        def updateLeafletLayout(refreshTime, dccStore):     
            #if the page has just loaded and no data, wait for a callback
            #from the dcc store itself
            if not dccStore:
                raise PreventUpdate
            else:         
                dataSets = json.loads(dccStore)

                zoneDF = pd.read_json(dataSets['zoneDF'], orient='split')                
                return self.buildLeafletLayout(zoneDF)

        @app.callback(
               Output("progressmap-filecache", 'data'),
               Input('progressmap-interval', 'n_intervals'),
               [State('progressmap-filecache', 'modified_timestamp'),
                State("progressmap-filecache", 'data'),
                State("main-session", 'data')]
              )

        #only refresh when page loads!
        def refreshData(n, refreshTime, pMapStore, mainStore): 

            self.logger.info("Progress Map page loaded -- checking data..." + str(n))

            #check if store not initialized, should not happen currently
            if not pMapStore:
                self.logger.info("progress map store empty, loading...")
                jsonData = self.getData()
                return jsonData

            #if data is in there, check if need a refresh
            if pMapStore and mainStore: #note sure why, but having the mainstore seems critical
                self.logger.info("ops store has data, checking for refresh...")

                refreshNeeded = False
                mainRefreshTime= datetime.datetime.strptime(mainStore["refreshTime"], "%m/%d/%y %H:%M")
                ###THIS IS NOT WORMING RIGHT< SOMETIMES NO MAIN STORE DATA, do db check here?
                if not refreshTime: #fires if we get here from page other than main       
                    #the ops store doesn't have a modified timestamp. not sure what would cause this.
                    #first check if the refresh was noted on the store data

                    dataSets = json.loads(pMapStore)
                    if "refreshTime" in dataSets:
                        refreshTime = datetime.datetime.strptime(dataSets["refreshTime"], "%m/%d/%y %H:%M")
                        if refreshTime < mainRefreshTime:
                            refreshNeeded = True
                    else:


                        refreshNeeded = True #refresh just to be safe
                else:
                    #check timestamps before more expensive checks
                    #mainRefreshTime = datetime.datetime.fromtimestamp( mainStoreTimeStamp/1000) #milliseconds need to be div
                    pMapsRefreshTime = datetime.datetime.fromtimestamp(refreshTime/1000) #milliseconds need to be div

                    if pMapsRefreshTime < mainRefreshTime:
                        refreshNeeded = True
                    else:
                        refreshNeeded = False
                if refreshNeeded:
                    self.logger.info("Stale progress map data -- refreshing...")
                     # compute value and send a signal when done
                    global_store(pMapStore)
                    return pMapStore

                else:
                    return pMapStore

            else:
                x=123

         # perform expensive computations in this "global store"
        # these computations are cached in a globally available
        # redis memory store which is available across processes
        # and for all time.
        @cache.memoize()
        def global_store(value):
            self.logger.info("Getting progress map data for store...")
            #note this just gets the data, it 
            #doesn't refresh the figures - they will be triggered
            jsonData = self.getData()
            return jsonData

        

        @app.callback(
            Output("collapse", "is_open"),
            [Input("collapse-button", "n_clicks")],
            [State("collapse", "is_open")],
        )
        def toggle_collapse(n, is_open):
            if n:
                return not is_open
            return is_open



                        


            # within layout
           
    # # callback
    # @app.callback(
    #     Output(component_id="c-store", component_property="data"),
    #     Input(component_id="load_interval", component_property="n_intervals"),
    # )
    # def load_dbdata(n_intervals:int):

    # def update_spanner(n_intervals:int):
    #     return datetime.now()


    # @app.callback(Output("odc", "children"), [Input("cabinets", "hover_feature")])
    # def odc_hover(feature):
    #     if feature is not None:
    #         return f"ODC:{feature['properties']['name']} Take Rate:{feature['properties']['take rate']} "



if __name__ == '__main__':

    #only for running locally while testing
    #may need to move to test folder instead

    #only when run directly
    grandParentPath = os.path.dirname(parentPath)    
    sys.path.append(grandParentPath)    
    ggParentPath = os.path.dirname(grandParentPath)
    sys.path.append(ggParentPath)    

  

    #loads internal configuration, e.g. folders, environment variables, etc.
    from dashapp import config
    from flask_caching import Cache
    from datahandler.datahandler import DataHandler
    config.setupEnv()

    assetFolder = os.environ["ASSETT_FOLDER"]
    dataDirectory = os.path.join(ggParentPath, "data")
    dHandler = DataHandler(persistenceType="local directory", dataDirectory=dataDirectory)

     # js lib used for colors
    chroma = "https://cdnjs.cloudflare.com/ajax/libs/chroma-js/2.1.0/chroma.min.js"
    externalScripts = [chroma]

    pMap = ProgressMap(dHandler)

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

    
    pMap.registerCallbacks(app, cache)        
    pMap.Layout = pMap.createProgressMapLayout()

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
       return pMap.layout


    app.run_server(debug=True, use_reloader=False) # Turn off reloader if inside Jupyter
