"""
Helper functions

Author: Huey Han <huilong.han@gmail.com>
"""

import os
import json
import re

import pandas as pd
import geopandas as gpd
import numpy as np
from fuzzywuzzy import fuzz, process
from weighted_levenshtein import lev


class PJMSystemMap:
    # class attributes
    SYSTEM_MAP_DATA_DIRECTORY = "/Users/hanhuilong/Desktop/power_simulation/pjm_system_map/helper_functions/pjm_system_map_export"
    OTHER_DATA_DIRECTORY = "/Users/hanhuilong/Desktop/power_simulation/pjm_system_map/helper_functions/pjm_other_data"
    CACHE_DATA_DIRECTORY = "/Users/hanhuilong/Desktop/power_simulation/pjm_system_map/helper_functions/cache_data"
    FILE_NAME = {
        "pjm_backbone_lines": ["pjm_backbone_lines"],
        "all_substations": ["pjm_substations", "non_pjm_substations"],
        "all_substation_labels": ["pjm_substation_labels", "non_pjm_substation_labels"],
        "pjm_zones": ["pjm_zones"],
        # "all_pjm_lines": ["pjm_backbone_lines", "pjm_non_backbone_lines_120_138_161_230_kv","pjm_non_backbone_lines_69_115_kv"]
        "planning_queue": ["planning_queue"],
        "pjm_states": ["pjm_states"]
    }


    def __init__(self):
        """
        Initialize class instance.
        When initializing. Automatically load the following GeoDataFrames:
        """
        self.pjm_backbone_lines = self.loadPJMBackboneLines()
        self.pjm_zones = self.loadPJMZones()
        self.all_substations = self.loadAllSubstations()
        self.all_substation_labels = self.loadAllSubstationLabels()
        self.planning_queue = self.loadPlanningQueue()
        self.pjm_states = self.loadPJMStates()
        self.pnode_list = self.loadPnodeList()


    def makeGeoDataFrame(self, outputFileName, inputFiles):
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
            with open(os.path.join(self.SYSTEM_MAP_DATA_DIRECTORY, inputFileName)) as f:
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
        filePath = os.path.join(self.SYSTEM_MAP_DATA_DIRECTORY, outputFileName)
        output = open(filePath, "w")
        json.dump(geojson, output)
        output.close()

        # load as a GeoDataFrame and do basic cleaning
        df = gpd.read_file(os.path.join(self.SYSTEM_MAP_DATA_DIRECTORY, outputFileName))
        df = df.replace({"Null": np.nan, None: np.nan, "":np.nan})
        df = df.drop_duplicates()

        # remove the geojson file on disk
        os.remove(filePath)

        # return dataframe
        return df


    def loadPJMBackboneLines(self):
        """
        load PJM backbone line data as a GeoDataFrame
        """
        name = "pjm_backbone_lines"
        # make GeoJSON based on raw JSON export from PJM system map
        lines = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        # convert various columns to float
        lines.LENGTH_KM = lines.LENGTH_KM.astype(float)
        lines.MILES = lines.MILES.astype(float)
        lines.VOLTAGE = lines.VOLTAGE.astype(float)
        # return file
        return lines


    def loadPJMZones(self):
        """
        load PJM transmission zone.
        """
        name = "pjm_zones"
        # make GeoJSON based on raw JSON export from PJM system map
        pjm_zones = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        # return file
        return pjm_zones


    def loadAllSubstations(self):
        """
        load all substations, whether inside PJM or not.
        """
        name = "all_substations"
        # make GeoJSON based on raw JSON export from PJM system map
        substations = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        # convert various columns to float
        substations.VOLTAGE = substations.VOLTAGE.astype(float)
        # get get match zone
        self.geoMatchZones(substations)
        # return file
        return substations


    def loadAllSubstationLabels(self):
        """
        load all substation labels data, whether inside PJM or not.
        """
        name = "all_substations"
        # make GeoJSON based on raw JSON export from PJM system map
        substation_labels = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        # convert various columns to float
        substation_labels.VOLTAGE = substation_labels.VOLTAGE.astype(float)
        # get get match zone
        self.geoMatchZones(substation_labels)
        # return file
        return substation_labels


    def loadPlanningQueue(self):
        """
        load PJM planning queue
        """
        name = "planning_queue"
        # make GeoJSON based on raw JSON export from PJM system map
        queue = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        # modify dtype
        queue.VOLTAGE = queue.VOLTAGE.apply(lambda x: x.replace("kV", "") if x is not np.nan else np.nan)
        queue.VOLTAGE = queue.VOLTAGE.astype(float)
        # load queue information exported from PJM as excel
        filePath = os.path.join(self.OTHER_DATA_DIRECTORY, "PlanningQueues.xlsx")
        queue_info = pd.read_excel(filePath)
        columns = ["Queue Number", "Name", "MFO", "MW Energy", "MW Capacity",
                    "MW In Service", "Project Type", "Fuel", "Status", "Revised In Service Date",
                    "Actual In Service Date"]
        queue_info = queue_info[columns]
        queue_merged = pd.merge(queue, queue_info, how="left", left_on="QUEUE_ID", right_on="Queue Number")
        queue_merged["Revised In Service Date"] = pd.to_datetime(queue_merged["Revised In Service Date"])
        queue_merged["Actual In Service Date"] = pd.to_datetime(queue_merged["Actual In Service Date"])
        # return file
        return queue_merged


    def loadPJMStates(self):
        """
        load PJM states
        """
        name = "pjm_states"
        # make GeoJSON based on raw JSON export from PJM system map
        states = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        # add binary for whether PJM zones or not
        states["IN_PJM"] = states.ABBREVIATION.isin(["DE", "IL", "IN", "KY", "MD", "MI", "NJ", "NC", "OH", "PA", "TN", "VA", "WV", "DC"])
        # return file
        return states


    def loadPnodeList(self, use_cache=True, only_match_high_confidence=True):
        """
        load PJM pnode list
        """
        # load pnode_list
        filePath = os.path.join(self.OTHER_DATA_DIRECTORY, "lmp-bus-model.xlsx")
        node_list = pd.read_excel(filePath, skiprows=2)
        node_list.Voltage = node_list.Voltage.apply(lambda x: float(x.replace("KV", "")))
        node_list.columns = ["pnode_id", "zone", "substation", "voltage", "equipment", "type"]
        node_list.pnode_id = node_list.pnode_id.astype(str)
        node_list.substation = node_list.substation.astype(str)
        # replace zonal name to accomodate matching with equiplist
        zonalMap = {'AECO': "AEC", 'AEP': "AEP", 'APS': "APS", 'ATSI': "ATSI", 'BGE': "BGE",
                    'COMED': "ComEd", 'DAY': "Dayton", 'DEOK': "DEOK", 'DOM': "Dominion",
                    'DPL': "DPL", 'DUQ': "DL", 'EKPC': "EKPC", 'JCPL': "JCPL", 'METED': "ME",
                    'OVEC': "OVEC HQ", 'PECO': "PECO", 'PENELEC': "PENELEC", 'PEPCO': "PEPCO",
                    'PPL': "PPL", 'PSEG': "PSEG", 'RECO': "RE"}
        node_list.zone = node_list.zone.replace(zonalMap)
        # match pnode with system substations
        node_list = self.matchPnodeWithMapSubstations(node_list, use_cache=use_cache,
                        only_match_high_confidence=only_match_high_confidence)
        # return file
        return node_list



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
    def getPlanningQueue(self):
        "return pjm planning queue"
        return self.planning_queue
    def getPJMStates(self):
        "return pjm state boundaries"
        return self.pjm_states
    def getPnodeList(self):
        "return pjm node list"
        return self.pnode_list


    def fillMissingSubstations(self, lines, dedupe_lines=False):
        """
        Certain lines don't have corresponding substations.
        Fill these missing substations using distance based matching.
        """

        # first, do matching for those with only 1 substation missing
        for index, row in lines[lines.SUBSTATION_A_GLOBALID.isnull() ^ lines.SUBSTATION_B_GLOBALID.isnull()].iterrows():
            matched_subs = self.substations[self.substations.geometry.apply(lambda x: x.distance(lines.geometry.loc[index])) == 0]
            matched_subs = matched_subs["SUBSTATION_GLOBALID"].to_list()
            
            for sub in matched_subs:
                if sub == row["SUBSTATION_A_GLOBALID"] or sub == row["SUBSTATION_B_GLOBALID"]:
                    continue
                elif row["SUBSTATION_A_GLOBALID"] is np.nan:
                    lines.loc[index, "SUBSTATION_A_GLOBALID"] = sub
                elif row["SUBSTATION_B_GLOBALID"] is np.nan:
                    lines.loc[index, "SUBSTATION_B_GLOBALID"] = sub
                else:
                    print("Hmm, there's a problem here. Line index:", index)


        # second, do matching for those with both substations missing
        for index, row in lines[lines.SUBSTATION_A_GLOBALID.isnull() & lines.SUBSTATION_B_GLOBALID.isnull()].iterrows():
            matched_subs = substations[substations.geometry.apply(lambda x: x.distance(lines.geometry.loc[index])) == 0]
            matched_subs = matched_subs["SUBSTATION_GLOBALID"].to_list()
            
            # insert match information into dataframe
            if len(matched_subs) > 0:
                lines.loc[index, "SUBSTATION_A_GLOBALID"] = matched_subs[0]
            
            if len(matched_subs) > 1:
                lines.loc[index, "SUBSTATION_B_GLOBALID"] = matched_subs[1]
            
            if len(matched_subs) > 2:
                print("Hmm, there's a problem here. Line index:", index)


        # # dedupe lines if dedupe_lines is set to true
        # # TODO: this section is untested and unstable currently
        # if dedupe_lines:
        #     # TODO: for duplicated lines (same substation set) that somehow become fragmented, reconnect
        #     index_to_be_dropped = []

        #     lines_dict = lines.to_dict(orient="index")

        #     for index, row in lines_dict.items():
        #         subA = row["SUBSTATION_A_GLOBALID"]
        #         subB = row["SUBSTATION_B_GLOBALID"]
                
        #         tmp = lines[(lines["SUBSTATION_A_GLOBALID"] == subA) & (lines["SUBSTATION_B_GLOBALID"] == subB)]
        #         start_pts = set(x.coords[0] for x in tmp.geometry.to_list())
        #         end_pts = set(x.coords[-1] for x in tmp.geometry.to_list())
                
        #         if tmp.shape[0] > 1 and len(line_names) == 1 and (len(start_pts) > 1 or len(end_pts) > 1) and start_pts != end_pts:
        #             lines_dict[index]["geometry"] = linemerge(tmp.geometry.to_list()) #TODO: need to QA on whether this actually merges the line
        #             #TODO: seems to also create MultiLineString that's problematic
        #             index_to_be_dropped += [x for x in tmp.index if x != index]
        #             continue
                    
        #         tmp = lines[(lines["SUBSTATION_A_GLOBALID"] == subB) & (lines["SUBSTATION_B_GLOBALID"] == subA)]
        #         start_pts = set(x.coords[0] for x in tmp.geometry.to_list())
        #         end_pts = set(x.coords[-1] for x in tmp.geometry.to_list())

        #         if tmp.shape[0] > 0 and len(line_names) == 1 and (len(start_pts) > 1 or len(end_pts) > 1) and start_pts != end_pts:
        #             lines_dict[index]["geometry"] = linemerge(tmp.geometry.to_list()) #TODO: need to QA on whether this actually merges the line
        #             #TODO: seems to also create MultiLineString that's problematic
        #             index_to_be_dropped += [x for x in tmp.index if x != index]
        #             linemerge(tmp.geometry.to_list())
        #             continue

        #     lines = gpd.GeoDataFrame(lines_dict).T
        #     lines = lines.drop(index_to_be_dropped, axis=0)
        


    def geoMatchZones(self, df):
        """
        Match substations with PJM planning zone based on geometry
        """
        # matched substation to zone based on geoemtry
        zoneGeometryMap = dict(zip(self.pjm_zones["PLANNING_ZONE_NAME"], self.pjm_zones.geometry))

        # set up a new column for geo-match zone
        df["geo_matched_zone"] = np.nan

        # iterate over rows to geo match
        for index, row in df.iterrows():
            for zone, geometry in zoneGeometryMap.items():
                if row["geometry"].within(geometry):
                    df.loc[index, "geo_matched_zone"] = zone


    def matchPnodeWithMapSubstations(self, pnode_list, use_cache=True, only_match_high_confidence=True):
        """
        Match PJM Pnode list with substations from PJM system map.
        Matching is mostly based on levenshtein distance of names.
        Weighted levenshtein distance and same-zone check are also used to ensure high match confidence.

        If use_cache is set to true, function will look for and load previous calculated data.
        If only_match_high_confidence is set to true, function will only return matches that it has
            high confidence are true matches.
        """

        # set up weighted levenshtein score
        insert_costs = np.full((128,), 1, dtype=np.float64)
        delete_costs = np.full((128,), 5, dtype=np.float64)
        substitute_costs = np.full((128, 128), 99999, dtype=np.float64)

        def weighted_lev(word1, word2):
            return lev(word1, word2,
                       insert_costs=insert_costs,
                       delete_costs=delete_costs,
                       substitute_costs=substitute_costs)

        def find_match(word1, choices):
            tmp_word1 = word1.lower()
            tmp_choices = list(map(lambda x: x.lower(), choices))
            scores = list(map(lambda x: weighted_lev(tmp_word1, x), tmp_choices))
            min_index = scores.index(min(scores))
            return (choices[min_index], scores[min_index])


        # set up file path to cache data
        cacheDataPath = os.path.join(self.CACHE_DATA_DIRECTORY, "pnode_substation_match.pkl")
        
        # get match dataframe
        if use_cache and os.path.exists(cacheDataPath):
            match = pd.read_pickle(cacheDataPath)
        
        else:
            # modify substation_labels if needed
            substation_labels = self.all_substation_labels[self.all_substation_labels["MEMBER"] == "1"].copy(deep=True)
            substation_labels["NAME"] = substation_labels["NAME"].astype(str).apply(lambda x: re.sub(r'[^\w]', '', x))

            # initialize dictionaries and lists
            yet_to_be_matched_sublabels = substation_labels.SUBSTATION_GLOBALID.to_list()
            yet_to_be_matched_nodes = pnode_list.groupby("substation")["zone"].unique().to_dict()
            mapping = {}


            matching_iterations = {
                1: {"threshold": 100, "zone_check": True, "weighted_levenshtein": False, "description": "exact match in same zone"},
                2: {"threshold": 90, "zone_check": True, "weighted_levenshtein": False, "description": "high match in same zone"},
                3: {"threshold": 95, "zone_check": False, "weighted_levenshtein": False, "description": "high match in all zones"},
                4: {"threshold": 5, "zone_check": True, "weighted_levenshtein": True, "description": "medium match in same zone with weighted levenshtein"},
                5: {"threshold": 5, "zone_check": False, "weighted_levenshtein": True, "description": "medium match in same zone with weighted levenshtein"},
                6: {"threshold": 10, "zone_check": True, "weighted_levenshtein": True, "description": "low match in same zone with weighted levenshtein"},
                7: {"threshold": np.inf, "zone_check": False, "weighted_levenshtein": True, "description": "remaining same zone with weighted levenshtein"}
            }

            for index, params in matching_iterations.items():
                threshold = params["threshold"]

                for name in list(yet_to_be_matched_nodes):
                    # TODO: need to add condition to skip substations that do not have >= 69 voltages

                    zone = yet_to_be_matched_nodes[name]
                    
                    tmp_sub_labels = substation_labels[substation_labels.SUBSTATION_GLOBALID.isin(yet_to_be_matched_sublabels)]

                    # zone check
                    if params["zone_check"]:
                        tmp_sub_labels = tmp_sub_labels[(tmp_sub_labels["PLANNING_ZONE_NAME"].isin(zone)) | (tmp_sub_labels["geo_matched_zone"].isin(zone))]

                    # TODO: the fix below is temporary to avoid exception
                    if tmp_sub_labels.shape[0] == 0:
                        continue
                    
                    # preprocessing
                    if ("ComEd" in zone) and bool(re.match(r"^\d+\s+(\w+)$", name)):
                        # COMED's naming convention makes it difficult, and need to be handled separately
                        tmp_name = re.search(r"^\d+\s+(\w+)$", name).group(1)        
                    elif (("ATSI" in zone) or ("DEOK" in zone) or ("Dayton" in zone)) and bool(re.match(r"^\d+(\w+)$", name)):
                         # ATSI, DEOK, and Dayton have naming convention that starts with digits, which make matching difficult
                        tmp_name = re.search(r"^\d+(\w+)$", name).group(1)
                    else:
                        tmp_name = name

                    choices = tmp_sub_labels["NAME"].dropna().to_list() # TODO: currently dropping nan, considering replacing with "", i.e. empty string
                    
                    if params["weighted_levenshtein"]:
                        tmp_name = tmp_name.replace("_", "")
                        match = find_match(tmp_name, choices)
                    else:
                        match = process.extractOne(tmp_name, choices)
                        

                    if not params["weighted_levenshtein"] and match[1] < threshold:
                        continue
                    
                    if params["weighted_levenshtein"] and match[1] > threshold:
                        continue
                    
                    # get substation id and name from substation_labels
                    sub_id = tmp_sub_labels[tmp_sub_labels.NAME == match[0]]["SUBSTATION_GLOBALID"].values[0]
                    sub_name = tmp_sub_labels[tmp_sub_labels.NAME == match[0]]["NAME"].values[0]

                    # add to dictionary
                    mapping[name] = (sub_name, zone, sub_id, match[1], index)

                    # remove from list and dicionaries
                    yet_to_be_matched_sublabels.remove(sub_id)
                    del yet_to_be_matched_nodes[name]

            # get result
            match = pd.DataFrame(mapping).T
            match = match.reset_index()
            match.columns = ["pnode_substation_name", "system_map_substation_name", "pnode_zone",
                                "system_map_substation_id", "match_score", "match_round"]

            # select subset
            if only_match_high_confidence:
                match = match[match["match_round"] <= 4] # TODO: 4 hardcoded now

            # select relevant columns
            match = match[["pnode_substation_name", "system_map_substation_name", "system_map_substation_id"]]

            # save cache
            if not os.path.exists(self.CACHE_DATA_DIRECTORY):
                os.makedirs(self.CACHE_DATA_DIRECTORY)
            match.to_pickle(cacheDataPath)

        
        # merge and select columns
        pnode_list = pd.merge(pnode_list, match, left_on="substation", right_on="pnode_substation_name", how="left")
        pnode_list = pnode_list.drop(columns=["pnode_substation_name"])

        # return file
        return pnode_list



        def matchMapLinesWithRatings(self, lines, use_cache=True, only_match_high_confidence=True):
            """
            """
            pass

