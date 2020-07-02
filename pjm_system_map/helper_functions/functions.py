"""
Helper functions

Author: Huey Han <huilong.han@gmail.com>

TODO:
1) change to return dataframe rather than changing in place
2) add sufficient comments
"""

import os
import json
import re
import uuid

import pandas as pd
import geopandas as gpd
import numpy as np
from fuzzywuzzy import fuzz, process
from weighted_levenshtein import lev
from shapely.ops import nearest_points, linemerge
from shapely.geometry import Point, LineString


class PJMSystemMap:
    # class attributes
    SYSTEM_MAP_DATA_DIRECTORY = "/Users/hanhuilong/Desktop/power_simulation/pjm_system_map/helper_functions/pjm_system_map_export"
    OTHER_DATA_DIRECTORY = "/Users/hanhuilong/Desktop/power_simulation/pjm_system_map/helper_functions/pjm_other_data"
    CACHE_DATA_DIRECTORY = "/Users/hanhuilong/Desktop/power_simulation/pjm_system_map/helper_functions/cache_data"
    FILE_NAME = {
        "pjm_backbone_lines": ["pjm_backbone_lines"],
        "all_substations": ["pjm_substations", "non_pjm_substations"],
        "taps": ["taps"],
        "all_substation_labels": ["pjm_substation_labels", "non_pjm_substation_labels"],
        "pjm_zones": ["pjm_zones"],
        # "all_pjm_lines": ["pjm_backbone_lines", "pjm_non_backbone_lines_120_138_161_230_kv","pjm_non_backbone_lines_69_115_kv"],
        # "non_pjm_backbone_lines": [],
        # "all_non_pjm_lines": [],
        # "all_lines",
        "planning_queue": ["planning_queue"],
        "pjm_states": ["pjm_states"]
    }


    def __init__(self):
        """
        Initialize class instance.
        When initializing. Automatically load the following GeoDataFrames:
        """
        self.pjm_zones = self.loadPJMZones()
        self.all_substations_and_taps = self.loadAllSubstationsAndTaps()
        self.all_substation_labels = self.loadAllSubstationLabels()
        self.pjm_backbone_lines = self.loadPJMBackboneLines()
        self.planning_queue = self.loadPlanningQueue()
        self.pjm_states = self.loadPJMStates()
        self.pnode_list = self.loadPnodeList()
        self.eia_plant = self.loadEIAPlantData()


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
        # remove problematic substations that are not in line
        self.geoCheckLineSubstations(lines)
        # fill missing substations
        self.fillMissingSubstations(lines)
        # connect broken lines
        lines = self.connectBrokenLines(lines)
        # handle special cases
        lines = self.fixLineSpecialCases(lines)

        return lines


    def loadPJMZones(self):
        """
        load PJM transmission zone.
        """
        name = "pjm_zones"
        # make GeoJSON based on raw JSON export from PJM system map
        pjm_zones = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        return pjm_zones


    def loadAllSubstationsAndTaps(self):
        """
        load all substations, whether inside PJM or not.
        """
        name = "all_substations"
        substations = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        name = "taps"
        taps = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        # concat
        substations = pd.concat([substations, taps])
        # TODO: dropping duplicates currently, not sure if it's the most optimal
        substations = substations.drop_duplicates(subset=["geometry"], keep="first")
        # add missing substations and taps
        substations = self.addToSubstationsAndTaps(substations)
        # convert various columns to float
        substations.VOLTAGE = substations.VOLTAGE.astype(float)
        # get get match zone
        self.geoMatchZones(substations)
        return substations


    def loadAllSubstationLabels(self):
        """
        load all substation labels data, whether inside PJM or not.
        """
        name = "all_substation_labels"
        # make GeoJSON based on raw JSON export from PJM system map
        substation_labels = self.makeGeoDataFrame(name, self.FILE_NAME[name])
        # convert various columns to float
        substation_labels.VOLTAGE = substation_labels.VOLTAGE.astype(float)
        # get get match zone
        self.geoMatchZones(substation_labels)
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
        return node_list


    def loadEIAPlantData(self, year="2018"):
        """
        load EIA 860 data.

        Default to load EIA 860 data from 2018.
        """
        # set up file path to EIA 860 data
        filePath = os.path.join(self.OTHER_DATA_DIRECTORY, "eia860{}".format(year))

        # load data
        eia_860_plant = pd.read_excel(os.path.join(filePath, "2___Plant_Y{}.xlsx".format(year)), skiprows=1)
        eia_860_gens = pd.read_excel(os.path.join(filePath, "3_1_Generator_Y{}.xlsx".format(year)), skiprows=1).iloc[:-1, :]
        eia_860_plant["Plant Code"] = eia_860_plant["Plant Code"].astype(int)
        eia_860_gens["Plant Code"] = eia_860_gens["Plant Code"].astype(int)

        # concat voltages to list
        eia_860_plant["Voltages"] = np.empty((len(eia_860_plant), 0)).tolist()
        for index, row in eia_860_plant.iterrows():
            for x in [row['Grid Voltage (kV)'], row['Grid Voltage 2 (kV)'], row['Grid Voltage 3 (kV)']]:
                 if x != " ":
                        row["Voltages"].append(x)

        # select relevant columns
        eia_860_plant = eia_860_plant[["Plant Code", "Plant Name", "Street Address", "City", "County", "State",
                                       "Latitude", "Longitude", "Voltages", "Balancing Authority Name",
                                       "Transmission or Distribution System Owner"]]
        eia_860_gens = eia_860_gens[["Plant Code", "Generator ID", "Unit Code", "Technology", "Prime Mover",
                                     "Nameplate Capacity (MW)", "Nameplate Power Factor",
                                     "Summer Capacity (MW)", "Winter Capacity (MW)", "Minimum Load (MW)",
                                     "RTO/ISO LMP Node Designation",
                                     "RTO/ISO Location Designation for Reporting Wholesale Sales Data to FERC"]]

        # convert relevant columsn to float
        eia_860_gens["Nameplate Capacity (MW)"] = eia_860_gens["Nameplate Capacity (MW)"].astype(float)
        eia_860_gens["Nameplate Power Factor"] = eia_860_gens["Nameplate Power Factor"].replace({" ": np.nan}).astype(float)
        eia_860_gens["Summer Capacity (MW)"] = eia_860_gens["Summer Capacity (MW)"].replace({" ": np.nan}).astype(float)
        eia_860_gens["Winter Capacity (MW)"] = eia_860_gens["Winter Capacity (MW)"].replace({" ": np.nan}).astype(float)
        eia_860_gens["Minimum Load (MW)"] = eia_860_gens["Minimum Load (MW)"].replace({" ": np.nan}).astype(float)

        # merge dataframe and select PJM
        plants = pd.merge(eia_860_plant, eia_860_gens, on="Plant Code", how="outer")
        plants["Plant Code"] = plants["Plant Code"].astype(str)
        plants = plants[plants["Balancing Authority Name"] == "PJM Interconnection, LLC"]

        # eliminate rows that do not have coordinates - necessary if not limiting balancing authority to PJM
        # TODO: figure out if there is some way to get coordinates
        # plants = plants[(plants.Longitude != " ") & (plants.Latitude != " ")]

        # construct geodataframe
        plants = gpd.GeoDataFrame(plants, geometry=gpd.points_from_xy(plants.Longitude, plants.Latitude))

        # convert projection
        plants.crs = 4326
        plants = plants.to_crs(epsg = 3857)

        # drop original coordinates
        plants = plants.drop(columns=["Latitude", "Longitude"])

        # drop rows that we have no capacity info
        # TODO: leave this as something to improve as not sure if it's the most optimal currently
        plants = plants.dropna(subset=["Nameplate Capacity (MW)"], axis=0)

        return plants



    def getPJMBackboneLines(self):
        "return pjm backbone line data"
        return self.pjm_backbone_lines
    def getAllSubstationsAndTaps(self):
        "return all substations and taps data"
        return self.all_substations_and_taps
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
    def getEIAPlantData(self):
        "return EIA 860 plant data"
        return self.eia_plant


    def addToSubstationsAndTaps(self, substations_and_taps):
        """
        add to substation_and_taps for missing taps.

        Currently this is done after extensive manual reviews.
        TODO: figure out an algorithm way to do this.
        """

        substations_and_taps = substations_and_taps.append(
                                    {"NAME": "TAP",
                                    "SUBSTATION_GLOBALID": str(uuid.uuid1()),
                                    "SUBSTATION_TYPE": "1",
                                    "SYM_CODE": "TAP",
                                    "SHAPE": "Point",
                                    "SUBSTATION_KEY": "missing_substation_1",
                                    "geometry": Point(-9819520.7577, 5136039.221299998)
                                    }, ignore_index=True, verify_integrity=True)

        return substations_and_taps


    def geoCheckLineSubstations(self, lines):
        """
        check substations in the line to see if they are part of the line based on
            shapely geo distance. remove if it's not part of the line.
        """
        locations = dict(zip(self.all_substations_and_taps["SUBSTATION_GLOBALID"],
                            self.all_substations_and_taps["geometry"]))

        # iterate over lines to get rid of substations not contained in the line
        for index, row in lines.iterrows():
            line = row["geometry"]

            for column in ["SUBSTATION_A_GLOBALID", "SUBSTATION_B_GLOBALID"]:
                if row[column] is np.nan:
                    # skip is substation is nan
                    continue
                elif row[column] not in locations.keys():
                    # replace sub to nan if sub doesn't exist in sub table
                    lines.loc[index, column] = np.nan
                    continue
                else:
                    sub_geo = locations[row[column]]

                # replace substation with nan if not contained in line
                if line.distance(sub_geo) != 0:
                    lines.loc[index, column] = np.nan


    def fillMissingSubstations(self, lines):
        """
        Certain lines don't have corresponding substations.
        Fill these missing substations using distance based matching.
        """
        # first, do matching for those with only 1 substation missing
        for index, row in lines[lines.SUBSTATION_A_GLOBALID.isnull() ^ lines.SUBSTATION_B_GLOBALID.isnull()].iterrows():
            matched_subs = self.all_substations_and_taps[self.all_substations_and_taps.geometry.apply(lambda x: x.distance(lines.geometry.loc[index])) == 0]
            matched_subs = matched_subs["SUBSTATION_GLOBALID"].to_list()

            for sub in matched_subs:
                if sub == row["SUBSTATION_A_GLOBALID"] or sub == row["SUBSTATION_B_GLOBALID"]:
                    continue
                elif row["SUBSTATION_A_GLOBALID"] is np.nan:
                    lines.loc[index, "SUBSTATION_A_GLOBALID"] = sub
                elif row["SUBSTATION_B_GLOBALID"] is np.nan:
                    lines.loc[index, "SUBSTATION_B_GLOBALID"] = sub
                else: # TODO: might not be necessary
                    print(sub)
                    print(matched_subs)
                    raise(ValueError("There are too many matches. Line index: {}".format(index)))

        # second, do matching for those with both substations missing
        for index, row in lines[lines.SUBSTATION_A_GLOBALID.isnull() & lines.SUBSTATION_B_GLOBALID.isnull()].iterrows():
            matched_subs = self.all_substations_and_taps[self.all_substations_and_taps.geometry.apply(lambda x: x.distance(lines.geometry.loc[index])) == 0]
            matched_subs = matched_subs["SUBSTATION_GLOBALID"].to_list()

            # insert match information into dataframe
            if len(matched_subs) > 0:
                lines.loc[index, "SUBSTATION_A_GLOBALID"] = matched_subs[0]

            if len(matched_subs) > 1:
                lines.loc[index, "SUBSTATION_B_GLOBALID"] = matched_subs[1]

            if len(matched_subs) > 2: # TODO: might not be necessary
                print(sub)
                print(matched_subs)
                raise(ValueError("There are too many matches. Line index: {}".format(index)))


    def connectBrokenLines(self, lines):
        """
        Certain lines are broken/disconnected.
        Find these lines and connect them.
        """
        # get lines that are broken/disconnected
        # these are those that don't have corresponding substation based on geomatch
        problematic_lines = lines[lines["SUBSTATION_A_GLOBALID"].isnull() |
                                    lines["SUBSTATION_B_GLOBALID"].isnull()].copy(deep=True)

        # initialize a list to store matching pairs
        pairs = []

        # iterate over the problematic lines to find pairs
        # pairs are those that are very close to each other
        # here, defined as less than 500 meters apart
        for index, row in problematic_lines.iterrows():
            choices = problematic_lines[problematic_lines.index != index]
            choices = dict(zip(choices.index, choices["geometry"]))

            line = row["geometry"]

            min_distance = np.inf
            min_index = None

            for ix, other_line in choices.items():
                distances = [line.boundary[0].distance(other_line.boundary[0]),
                             line.boundary[0].distance(other_line.boundary[1]),
                             line.boundary[1].distance(other_line.boundary[0]),
                             line.boundary[1].distance(other_line.boundary[1])]

                if min(distances) < min_distance:
                    min_distance = min(distances)
                    min_index = ix

            if min_distance < 500:
                pairs.append(tuple(sorted([index, min_index])))

        # dedupe pairs
        pairs = set(pairs)

        # check that there are no duplicates
        pair_list = list(sum(pairs, ()))
        if any(pair_list.count(x) > 1 for x in pair_list):
            raise(ValueError("There are duplicated match, i.e. one line matches to multiple lines"))


        # iterate over the pairs and connect them
        for p in pairs:
            line_pairs = lines.loc[list(p)]
            line_one = lines.loc[list(p)].geometry.to_list()[0]
            line_two = lines.loc[list(p)].geometry.to_list()[1]

            # sanity check whether the two lines have the same voltage
            voltage_one = lines.loc[list(p)].VOLTAGE.to_list()[0]
            voltage_two = lines.loc[list(p)].VOLTAGE.to_list()[1]
            if voltage_one != voltage_two:
                raise(ValueError("Trying to merge two lines with different voltages."))

            # get merged line geometry
            merged_line = linemerge([lines.loc[p[0]].geometry, lines.loc[p[1]].geometry])

            # if not a single line, create a new line segment and weldeverything together
            if not isinstance(merged_line, LineString):
                min_distance = np.inf
                min_bound_pair = None

                for bound_pair in [(0, 0), (0, -1), (-1, 0), (-1, -1)]:
                    pt1 = bound_pair[0]
                    pt2 = bound_pair[1]

                    distance = Point(line_one.coords[pt1]).distance(Point(line_two.coords[pt2]))

                    if distance < min_distance:
                        min_distance = distance
                        min_bound_pair = bound_pair

                missing_line = LineString([line_one.coords[min_bound_pair[0]], line_two.coords[min_bound_pair[1]]])

                merged_line = linemerge([line_one, missing_line, line_two])

            # append new line to dataframe
            lines = lines.append({"LENGTH_KM": line_pairs["LENGTH_KM"].sum(),
                          "MILES": line_pairs["MILES"].sum(),
                          "VOLTAGE": voltage_one,
                          "TRANSMISSION_LINE_GLOBALID": str(uuid.uuid1()),
                          "geometry": merged_line
                         }, ignore_index=True, verify_integrity=True)


        # iterate over pairs and drop old lines
        for p in pairs:
            lines = lines.drop(list(p), axis=0)

        # fill missing substations and return
        self.fillMissingSubstations(lines)
        return lines


    def fixLineSpecialCases(self, lines):
        """
        fix special cases in lines not covered in above
        """

        # this case handles a location deviation
        index = lines[lines.TRANSMISSION_LINE_GLOBALID == "{2DC162CB-03B3-4F1B-8D22-A55111076626}"].index[0]
        if lines.loc[index, "SUBSTATION_B_GLOBALID"] is np.nan:
            lines.loc[index, "SUBSTATION_B_GLOBALID"] = "{DAD21BFC-B3AD-4F0E-9D5E-29DC7769F454}"

        return lines



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

            # set up parameters for iterations
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


    def getLineEquipList(self, use_cache=True):
        """
        get lines in equiplist with rating information.
        """
        # set up file path to cache data
        cacheDataPath = os.path.join(self.CACHE_DATA_DIRECTORY, "line_equiplist_rating_subs.pkl")

        # get line rating match dataframe
        if use_cache and os.path.exists(cacheDataPath):
            return pd.read_pickle(cacheDataPath)
        else:
            # load equipment list
            filePath = os.path.join(self.OTHER_DATA_DIRECTORY, "equiplist.csv")
            line_equiplist = pd.read_csv(filePath, skiprows=1)
            equiplist["VOLTAGE"] = equiplist["VOLTAGE"].apply(lambda x: float(x.replace("KV", "")))

            # load line rating
            filePath = os.path.join(self.OTHER_DATA_DIRECTORY, "line_rating.csv")
            line_rating = pd.read_csv(filePath)

            # merge equiplist with line rating
            # TODO: currently averaging line rating over different conditions, consider improving this in the future
            line_rating = line_rating.groupby(["company", "substation", "voltage", "device", "end", "description"]).mean()
            line_rating = line_rating[["day_normal"]]
            equiplist = pd.merge(equiplist, line_rating, left_on="LONG NAME", right_on="description", how="left")
            line_equiplist = equiplist[equiplist.TYPE == "LINE"].copy()

            # for the lines equipment list, take out extra stuff in LONG NAME, and leave only substation names in the form of subA-subB
            # this is for matching purpose later where we match system map with equiplist based on substation names
            # add column for cleaned long name, subA, subB
            line_equiplist["cleaned_long_name"] = np.nan
            line_equiplist["subA"] = np.nan
            line_equiplist["subB"] = np.nan

            # get unique station names in equiplist
            equiplist_sub_list = list(equiplist.STATION.unique())

            # find subA and subB for line
            # TODO: currently some substations are missing, come back to fix it by adding more logic to parsing
            for index, row in line_equiplist.iterrows():
                subA = row["STATION"]
                longName = row["LONG NAME"]
                longName = re.sub(r'\s+-', '-', longName) # experimenting, eliminating white space before -
                found = False

                # subA-subB somethingsomething
                for subB in equiplist_sub_list:
                    longName_tmp = "-".join([subA, subB]) + " "
                    if longName_tmp in longName:
                        found = True
                        line_equiplist.loc[index, "subA"] = subA.strip()
                        line_equiplist.loc[index, "subB"] = subB.strip()
                        line_equiplist.loc[index, "cleaned_long_name"] = longName_tmp.strip()
                        break

                # subA-subB
                if not found:
                    for subB in equiplist_sub_list:
                        longName_tmp = "-".join([subA, subB])
                        if longName_tmp == longName:
                            found = True
                            line_equiplist.loc[index, "subA"] = subA.strip()
                            line_equiplist.loc[index, "subB"] = subB.strip()
                            line_equiplist.loc[index, "cleaned_long_name"] = longName_tmp.strip()
                            break

                # subB\s or subB
                if not found:
                    for subB in equiplist_sub_list:
                        if (subB + " ") in longName or bool(re.search(r"{}$".format(subB), longName)):
                            found = True
                            line_equiplist.loc[index, "subA"] = subA.strip()
                            line_equiplist.loc[index, "subB"] = subB.strip()
                            longName_tmp = "-".join([subA, subB])
                            line_equiplist.loc[index, "cleaned_long_name"] = longName_tmp.strip()
                            break

                # ends in subB\d
                if not found:
                    for subB in equiplist_sub_list:
                        if bool(re.search(r"{}\d($|\s)".format(subB), longName)):
                            found = True
                            line_equiplist.loc[index, "subA"] = subA.strip()
                            line_equiplist.loc[index, "subB"] = subB.strip()
                            longName_tmp = "-".join([subA, subB])
                            line_equiplist.loc[index, "cleaned_long_name"] = longName_tmp.strip()
                            break

                # all other cases
                longName = re.sub(r'\d+\s?[Kk][Vv]', '', longName) # experimenting, eliminating kv -
                longName = re.sub(r'\s\w+-?\w+?-?\w+?$', '', longName)
                longName = re.sub(r'TIE$', '', longName)
                longName = re.sub(r'TAP$', '', longName)
                longName = longName.strip()
                line_equiplist.loc[index, "cleaned_long_name"] = longName_tmp.strip()

            # save result as a cache
            line_equiplist.to_pickle(cacheDataPath)

            # return dataframe
            return line_equiplist


    def getLineRatings(self, lines, use_cache=True):
        """
        get line ratings for the lines dataframe

        line rating based on joining between equiplist and line rating.
        """

        # get line equiplist with rating and substation information
        line_equiplist = self.getLineEquipList(use_cache)

        # merge lines and substations to produce a new dataframe
        lines_tmp = lines[["TRANSMISSION_LINE_GLOBALID",
                            "SUBSTATION_A_GLOBALID",
                            "SUBSTATION_B_GLOBALID",
                            "VOLTAGE"]]
        sub_tmp = self.all_substation_labels[["NAME", "SUBSTATION_GLOBALID"]] # TODO: should this be all_substation_labels or all_substations_and_taps? which one is better?
        line_sub = pd.merge(lines_tmp, sub_tmp, how="left",
                            left_on="SUBSTATION_A_GLOBALID", right_on="SUBSTATION_GLOBALID",
                            suffixes=("_LINE", "_SUBSTATION_A"))
        line_sub = pd.merge(line_sub, sub_tmp, how="left",
                            left_on="SUBSTATION_B_GLOBALID", right_on="SUBSTATION_GLOBALID",
                            suffixes=("_SUBSTATION_A", "_SUBSTATION_B"))
        line_sub = line_sub.drop(columns=["SUBSTATION_GLOBALID_SUBSTATION_A", "SUBSTATION_GLOBALID_SUBSTATION_B"])

        # match system map with equiplist based on substation names
        # initialize dictionaries and lists
        mapping = {}

        # iterate over voltage level
        for voltage in sorted(list(line_sub["VOLTAGE"].unique()), reverse=True):
            # TODO: skip 1000 kv for now. Maybe another better way to deal with it.
            if voltage == 1000:
                continue

            # TODO: haven't done substation proxy matching yet
            # drop nan for now
            tmp_lines = line_sub[line_sub.VOLTAGE == voltage].dropna()
            tmp_line_equiplist = line_equiplist[line_equiplist["VOLTAGE"] == voltage]

            # initialize lists to track which line has been matched and which has not
            yet_to_be_matched_map_lines = dict(zip(tmp_lines["TRANSMISSION_LINE_GLOBALID"], tmp_lines["NAME_SUBSTATION_A"] + " " + tmp_lines["NAME_SUBSTATION_B"]))
            yet_to_be_matched_equiplist_lines = dict(zip(tmp_line_equiplist["cleaned_long_name"], tmp_line_equiplist["day_normal"]))

            # iterate over different thresholds for fuzzy match
            # the idea is to match high confidence first, then gradually decrease to lower threshold
            # doing so will increase overall matching since there are less choices for lower confidence match
            for threshold in [90, 80, 70, 60, 50, 40, 0]:
                # iterate over lines to be matched
                for line_id in list(yet_to_be_matched_map_lines):
                    line_name = yet_to_be_matched_map_lines[line_id]
                    # TODO: skip if nan
                    if line_name is np.nan:
                        continue
                    # do matching
                    match = process.extractOne(line_name, yet_to_be_matched_equiplist_lines.keys(), scorer=fuzz.WRatio)
                    # if match score passes thresholld, record, if not, continue
                    if match[1] > threshold:
                        # add to dictionary
                        mapping[line_id] = (line_name, match[0], match[1], yet_to_be_matched_equiplist_lines[match[0]])
                        # remove from list and dicionaries
                        del yet_to_be_matched_map_lines[line_id]
                        del yet_to_be_matched_equiplist_lines[match[0]]

        # make dataframe
        line_rating_map = pd.DataFrame(mapping).T
        line_rating_map = line_rating_map.reset_index()
        line_rating_map.columns = ["line_id", "line_sytem_map_name", "line_equiplist_name", "match_confidence", "line_rating"]

        # TODO: currently only choose high confidence match
        line_rating_map = line_rating_map[line_rating_map.match_confidence >= 80]

        # merge line_rating with system map
        lines = pd.merge(lines, line_rating_map,
                        how="left", left_on="TRANSMISSION_LINE_GLOBALID",
                        right_on="line_id")

        # TODO: fill lines that don't have liner ratin for now
        line_rating_fill = {1000: 750, 765:4000, 500:3000, 345:1250}
        for voltage_level, replacement_value in line_rating_fill.items():
            masks = lines[lines.VOLTAGE == voltage_level].index
            lines.loc[masks, "line_rating"] = lines.loc[masks, "line_rating"].fillna(replacement_value)

        # change dtypes to int
        lines["match_confidence"] = lines["match_confidence"].astype(float)
        lines["line_rating"] = lines["line_rating"].astype(float)

        return lines


    def getLineSubstations(self, lines):
        """
        Get substations that are in the lines dataframe.

        Also fill missing substations not found in the lines dataframe.
        """
        # get substations that exist in lines
        substations = self.all_substations_and_taps[
                        self.all_substations_and_taps["SUBSTATION_GLOBALID"].isin(lines["SUBSTATION_A_GLOBALID"]) |
                        self.all_substations_and_taps["SUBSTATION_GLOBALID"].isin(lines["SUBSTATION_B_GLOBALID"])
                        ].copy(deep=True) # TODO: does it need to be a deep copy?

        # append missing substations to list

        return substations


    def matchEIAPlantWithLineSubstations(self, lines):
        """
        match EIA plant to substations in lines. matching is based on distance.

        the reason matching is not with all substations is that many substations
        don't have connecting lines. if plant gets matched to those substations
        without connecting lines, it would be meaningless since power flow analysis
        can't be run on isolated plants/substations.
        """

        # get substations that exist in lines
        substations = self.getLineSubstations(lines)

        # match plants to nearest substations
        # unary union of the gpd2 geomtries
        gpd1 = self.eia_plant
        gpd2 = substations

        pts3 = gpd2.geometry.unary_union
        def near(point, pts=pts3):
            nearest = gpd2.geometry == nearest_points(point, pts)[1]
            return gpd2[nearest]["SUBSTATION_GLOBALID"].values[0]

        gpd1['Nearest_Substations'] = np.nan
        for index, row in gpd1.iterrows():
            gpd1.loc[index, 'Nearest_Substations'] = near(row["geometry"])
