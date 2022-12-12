import os
import sys
import csv
import json

def convertCSVToJSON(inputCSV, latField, lonField, outJSON):
    """takes an input CSV file with point features and converts to geoJSON"""

    #read the .csv as list of dicts
    with open(inputCSV, "r") as f:
        reader = csv.DictReader(f)
        csvData = list(reader)

    dataAsJSON = convertListToJSON(csvData,latField,lonField)
    
       
    #save the output JSON
    with open(outJSON, "w") as outfile:
        json.dump(dataAsJSON, outfile)

def convertListToJSON(inputData, latField, lonField):
    
    skeletonJSON = {"type" : "FeatureCollection", "features" : []}

    for row in inputData:

        #build a placeholder object in JSON
        rowAsJSON = {"type" : "Feature", "properties" : {}}

        #placeholder in case we want to extend later beyond points
        point=True
        if point:
            rowAsJSON["geometry"] = {"type" : "Point", "coordinates" : [] }
            lonValue = row[lonField]
            latValue = row[latField]            
            rowAsJSON["geometry"]["coordinates"].extend([float(lonValue), float(latValue)])

        #map the dict values to JSON feature properties
        for key, value in row.items():
            if key != latField and key!= lonField:
                rowAsJSON["properties"][key] = value

        skeletonJSON["features"].append(rowAsJSON)

    return skeletonJSON

def addToolTips(jsonPath):

     #fhJSON= json.load(jsonPath)
    with open(jsonPath) as f:
        jsonData=json.load(f)

    for feature in jsonData["features"]:
        feature["properties"]["tooltip"] = "Take Rate: " + feature["properties"]["take rate"]



    with open(jsonPath, "w") as outfile:
        json.dump(jsonData, outfile)


def customizeJSONTooltips():

    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    parentPath = os.path.dirname(currentFilePath)

    jsonPath = os.path.join(parentPath, "assets", "zonedata.json")

    #fhJSON= json.load(jsonPath)
    with open(jsonPath) as f:
        fhJSON=json.load(f)

    for feature in fhJSON["features"]:
        displayTakeRate = '{:.2%}'.format(feature["properties"]["Take Rate"])
        feature["properties"]["tooltip"] = "Take Rate: " + str(displayTakeRate) + "<br> Status: " + feature["properties"]["Status"] 

 
    with open(jsonPath, "w") as outfile:
        json.dump(fhJSON, outfile)

def addAttributesToJSON():



    currentFilePath = os.path.dirname(os.path.realpath(__file__))
    parentPath = os.path.dirname(currentFilePath)

    csvName = os.path.join(parentPath, "assets", "odcmetricdata.csv" )

    with open(csvName, "r") as f:
        reader = csv.DictReader(f)
        odcData = list(reader)

    jsonPath = os.path.join(parentPath, "assets", "zonedata.json")

    #fhJSON= json.load(jsonPath)
    with open(jsonPath) as f:
        fhJSON=json.load(f)

    for feature in fhJSON["features"]:
        matchFound = False
        for odc in odcData:
            if feature["properties"]["Name"] == odc["Fiberhood Name"]:
                matchFound=True
                # try:
                #     pComplete = odc["Percent Complete"].strip('%')
                #     feature["properties"]["Percent Complete"] = float(int(pComplete)/100)                    
                # except Exception as e:
                #     feature["properties"]["Percent Complete"] = 0
                try:                    
                    tRate = odc["Combined Take Rate"].strip('%')
                    feature["properties"]["Take Rate"] = float(float(tRate)/100)
                except Exception as e:
                     feature["properties"]["Take Rate"]  = 0
                # try: 
                #     feature["properties"]["MRC"]= float(odc["Combined Projects Gross Revenue (MRC)"].replace(',', '').replace('$', ''))                   
                # except Exception as e:
                #     feature["properties"]["MRC"]  = 0
                # try:                    
                #     feature["properties"]["Cost To Build"]= float(odc["Cost to Build"].replace(',', '').replace('$', ''))                  
                # except Exception as e:
                #     feature["properties"]["Cost To Build"]  = 0
         
                # feature["properties"]["Status"] = odc["Network Status"]            
                #feature["properties"]["tooltip"] = "Take Rate: " + odc["Combined Take Rate"]

                break
        if not matchFound:
            pass
        #     feature["properties"]["Percent Complete"] = 0.0
        #     feature["properties"]["Status"] = "Unknown"
        #     feature["properties"]["Take Rate"] = 0.0
        #     feature["properties"]["MRC"] = 0.0
        #     feature["properties"]["Cost To Build"] = 0.0
        #     feature["properties"]["tooltip"] = "Take Rate: 0.0"


    with open("zonedata_out.json", "w") as outfile:
        json.dump(fhJSON, outfile)


def createStraightEdges():             

    try:

        currentFilePath = os.path.dirname(os.path.realpath(__file__))
        parentPath = os.path.dirname(currentFilePath)

        csvName = os.path.join(parentPath, "assets", "meb05.csv" )

        with open(csvName, "r") as f:
            reader = csv.DictReader(f)
            odcData = list(reader)

        
        #now lets try to make edges

        #{"name" : "genericname",
        # "distance" : 2217,
        # "source" : "MEB05",
        # "target" : "MS08"}

        edgeData = []
                       

        for node in odcData:
            edgeToParent = {"name" : node["Fiberhood Name"] + "->" + node["Parent"],
                            "distance" : node["DistToParent"],
                            "source" : node["Parent"],
                            "target" : node["Fiberhood Name"],
                            "child lat" : node["lat"],
                            "child lon" : node["lon"]}
            edgeData.append(edgeToParent)             

        for edge in edgeData:
            #find parent in odc list
            for node in odcData:
                if node["Fiberhood Name"] == edge["source"]:
                    edge["parent lat"] = node["lat"]
                    edge["parent lon"] = node["lon"]
                    edge["parent status"] = node["Network Status"]
                    break

        #by now edges should have all sorts of lat longs
        skeletonJSON = {"type" : "FeatureCollection", "features" : []}

        for edge in edgeData:

            rowAsJSON = {"type" : "Feature", "properties" : {}}
            
            rowAsJSON["geometry"] = {"type" : "LineString", "coordinates" : [] }
            try:
                childlon = edge["child lon"]
                childlat = edge["child lat"]
                parentlon = edge["parent lon"]
                parentlat = edge["parent lat"]     
                rowAsJSON["geometry"]["coordinates"].extend([[float(childlon ), float(childlat)],[float(parentlon ), float(parentlat)]])
            except:
                rowAsJSON["geometry"]["coordinates"] = []
            for key, value in edge.items():                    
                rowAsJSON["properties"][key] = value

            skeletonJSON["features"].append(rowAsJSON)

        
        with open("meb05edges.json", "w") as outfile:
            json.dump(skeletonJSON, outfile)

    except Exception as e:
        print("Exception - " + str(e))
    


if __name__ == "__main__":
    customizeJSONTooltips()
    #createStraightEdges()
    #addAttributesToJSON()
    # currentFilePath = os.path.dirname(os.path.realpath(__file__))
    # parentPath = os.path.dirname(currentFilePath)
    # grandparentPath = os.path.dirname(parentPath)
    # csvName = os.path.join(parentPath, "assets", "odcs.csv" )
    # jsonPath = os.path.join(currentFilePath, "assets", "out.json")
    # #convertCSVToJSON(csvName, "lat","lon", jsonPath)

    # jsonPath = os.path.join(parentPath, "assets", "odcpoints.json")
    # addToolTips(jsonPath)



