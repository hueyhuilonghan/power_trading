"""
Helper functions

Author: Huey Han <huilong.han@gmail.com>
"""

import os
import json

import pandas as pd
import geopandas as gpd
import numpy as np


class PJMSystemMap:
    # class attributes
    DIRECTORY = "/Users/hanhuilong/Desktop/power_simulation/pjm_system_map/data/pjm_system_map_export"
    FILE_NAME = {
        "pjm_backbone_lines": ["pjm_backbone_lines"],
        "all_substations": ["pjm_substations", "non_pjm_substations"],
        "all_substation_labels": ["pjm_substation_labels", "non_pjm_substation_labels"],
        "pjm_zones": ["pjm_zones"]
        # "all_pjm_lines": ["pjm_backbone_lines", "pjm_non_backbone_lines_120_138_161_230_kv","pjm_non_backbone_lines_69_115_kv"]
    }


    def __init__(self):
        """
        Initialize class instance.
        When initializing. Automatically load the following GeoDataFrames:
            pjm_backbone_lines
            all_substations
            all_substation_labels
            pjm_zones
        """
        self.pjm_backbone_lines = self.loadPJMBackboneLines()
        self.all_substations = self.loadAllSubstations()
        self.all_substation_labels = self.loadAllSubstationLabels()
        self.pjm_zones = self.loadPJMZones()


    def makeGeoJSON(self, outputFileName, inputFiles):
        """
        Make GeoJSON file based on raw JSON export
        from PJM system map.
        """
        # initialize geojson
        geojson = {
            "type": "FeatureCollection",
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
            "features": []
        }

        # name the output file
        outputFileName = outputFileName + ".geojson"

        for fileName in inputFiles:
            # name the input file
            inputFileName = fileName + ".json"

            # load data
            with open(os.path.join(self.DIRECTORY, inputFileName)) as f:
                data = json.load(f)

            # iterate over the json and format it into geojson to be added
            for x in data["results"]:
                # initialize dictionary to be appended to geojson
                tmp = {"type": "Feature", "properties" : x["attributes"], "geometry":{"type": None, "coordinates": None}}

                # handle lines
                if x["geometryType"] == "esriGeometryPolyline":
                    if len(x["geometry"]["paths"]) == 1:
                        tmp["geometry"]["type"] = "LineString"
                        tmp["geometry"]["coordinates"] = x["geometry"]["paths"][0]
                    else:
                        raise("Unrecognized line geometry type. MultiLineString is detected but LineString is expected.")

                # handle points
                elif x["geometryType"] == "esriGeometryPoint":
                    tmp["geometry"]["type"] = "Point"
                    tmp["geometry"]["coordinates"] = [x["geometry"]["x"], x["geometry"]["y"]]

                # handle polygons
                elif x["geometryType"] == "esriGeometryPolygon":
                    if len(x["geometry"]["rings"]) == 1 or x["value"] == "EKPC": #TODO: hardcoding EKPC for now, which is a donut shape
                        tmp["geometry"]["type"] = "Polygon"
                        tmp["geometry"]["coordinates"] = x["geometry"]["rings"]
                    else:
                        tmp["geometry"]["type"] = "MultiPolygon"
                        tmp["geometry"]["coordinates"] = [[d] for d in x["geometry"]["rings"]]

                # else, unrecognizable geometry shape
                else:
                    raise("Unrecognized geometry type: {}".format(x["geometryType"]))

                # append tmp to geojson
                geojson["features"].append(tmp)


        # write geojson to disk
        output = open(os.path.join(self.DIRECTORY, outputFileName), "w")
        json.dump(geojson, output)
        output.close()


    def loadPJMBackboneLines(self):
        """
        load PJM backbone line data as a GeoDataFrame
        """
        name = "pjm_backbone_lines"
        # make GeoJSON based on raw JSON export from PJM system map
        self.makeGeoJSON(name, self.FILE_NAME[name])
        # load geojson as a geodataframe
        filePath = os.path.join(self.DIRECTORY, name + ".geojson")
        lines = gpd.read_file(filePath)
        # replace NULL and None values with NaN
        lines = lines.replace({"Null": np.nan, None: np.nan, "":np.nan})
        # convert various columns to float
        lines.LENGTH_KM = lines.LENGTH_KM.astype(float)
        lines.MILES = lines.MILES.astype(float)
        lines.VOLTAGE = lines.VOLTAGE.astype(float)
        # dedupe
        lines = lines.drop_duplicates()
        # return file
        return lines


    def loadAllSubstations(self):
        """
        load all substations, whether inside PJM or not.
        """
        name = "all_substations"
        # make GeoJSON based on raw JSON export from PJM system map
        self.makeGeoJSON(name, self.FILE_NAME[name])
        # load geojson as a geodataframe
        filePath = os.path.join(self.DIRECTORY, name + ".geojson")
        substation_labels = gpd.read_file(filePath)
        # replace NULL and None values with NaN
        substation_labels = substation_labels.replace({"Null": np.nan, None: np.nan, "":np.nan})
        # convert various columns to float
        substation_labels.VOLTAGE = substation_labels.VOLTAGE.astype(float)
        # dedupe
        substation_labels = substation_labels.drop_duplicates()
        # return file
        return substation_labels


    def loadAllSubstationLabels(self):
        """
        load all substation labels data, whether inside PJM or not.
        """
        name = "all_substations"
        # make GeoJSON based on raw JSON export from PJM system map
        self.makeGeoJSON(name, self.FILE_NAME[name])
        # load geojson as a geodataframe
        filePath = os.path.join(self.DIRECTORY, name + ".geojson")
        substations = gpd.read_file(filePath)
        # replace NULL and None values with NaN
        substations = substations.replace({"Null": np.nan, None: np.nan, "":np.nan})
        # convert various columns to float
        substations.VOLTAGE = substations.VOLTAGE.astype(float)
        # dedupe
        substations = substations.drop_duplicates()
        # return file
        return substations


    def loadPJMZones(self):
        """
        load PJM transmission zone.
        """
        name = "pjm_zones"
        # make GeoJSON based on raw JSON export from PJM system map
        self.makeGeoJSON(name, self.FILE_NAME[name])
        # load geojson as a geodataframe
        filePath = os.path.join(self.DIRECTORY, name + ".geojson")
        pjm_zones = gpd.read_file(filePath)
        # replace NULL and None values with NaN
        pjm_zones = pjm_zones.replace({"Null": np.nan, None: np.nan, "":np.nan})
        # dedupe
        pjm_zones = pjm_zones.drop_duplicates()
        # return file
        return pjm_zones


    def getPJMBackboneLines(self):
        "return pjm backbone line data"
        return self.pjm_backbone_lines


    def getAllSubstations(self):
        "return all substation data"
        return self.all_substations


    def getAllSubstationLabels(self):
        "return all substation label data"
        return self.all_substation_labels


    def getPJMZones(self):
        "return pjm zones"
        return self.pjm_zones


    def fillMissingSubstations(self):
        """
        Certain lines don't have corresponding substations.
        Fill these missing substations.
        """
        pass
