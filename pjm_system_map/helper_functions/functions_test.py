import unittest
from functions import *
import geopandas as gpd

class PJMSystemMapTest(unittest.TestCase):
    dataLoader = PJMSystemMap()

    def testConstructor(self):
        self.assertIsNotNone(self.dataLoader)


    def testBackboneLinesGetter(self):
        backbone_lines = self.dataLoader.getPJMBackboneLines()
        self.assertEqual(backbone_lines.shape, (726, 16))
        columns = ['COMPANY_ID', 'LENGTH_KM', 'LINE_ID', 'MEMBER', 'MILES', 'NAME',
                    'SUBSTATION_A_GLOBALID', 'SUBSTATION_B_GLOBALID', 'SYM_CODE',
                    'TO_LINE_NAME', 'TRANSMISSION_LINE_GLOBALID', 'VOLTAGE', 'SHAPE',
                    'TRANSMISSION_LINE_KEY', 'ESRI_OID', 'geometry']
        for i, x in enumerate(columns):
            self.assertEqual(backbone_lines.columns[i], x)

        dtypes = ['object', 'float64', 'object', 'object', 'float64', 'object',
                    'object', 'object', 'object',
                    'object', 'object', 'float64', 'object',
                    'object', 'object', 'geometry']

        for i, x in enumerate(backbone_lines.dtypes):
            self.assertEqual(dtypes[i], x)

        # check if missing lines are filled
        self.assertEqual(backbone_lines["SUBSTATION_A_GLOBALID"].isnull().sum(), 0)
        self.assertEqual(backbone_lines["SUBSTATION_B_GLOBALID"].isnull().sum(), 0)


    def testGetLineEquipList(self):
        line_equiplist = self.dataLoader.getLineEquipList()
        self.assertEqual(line_equiplist.shape, (24986, 11))
        columns = ['TYPE', 'COMPANY', 'ZONE', 'STATION', 'VOLTAGE', 'NAME', 'LONG NAME',
                    'day_normal', 'cleaned_long_name', 'subA', 'subB']
        for i, x in enumerate(columns):
            self.assertEqual(line_equiplist.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'float64', 'object', 'object',
                    'float64', 'object', 'object', 'object']

        for i, x in enumerate(line_equiplist.dtypes):
            self.assertEqual(dtypes[i], x)


    def testGetLineRatings(self):
        # check before calling getLineRatings()
        backbone_lines = self.dataLoader.getPJMBackboneLines()
        self.assertEqual(backbone_lines.shape, (726, 16))
        columns = ['COMPANY_ID', 'LENGTH_KM', 'LINE_ID', 'MEMBER', 'MILES', 'NAME',
                    'SUBSTATION_A_GLOBALID', 'SUBSTATION_B_GLOBALID', 'SYM_CODE',
                    'TO_LINE_NAME', 'TRANSMISSION_LINE_GLOBALID', 'VOLTAGE', 'SHAPE',
                    'TRANSMISSION_LINE_KEY', 'ESRI_OID', 'geometry']
        for i, x in enumerate(columns):
            self.assertEqual(backbone_lines.columns[i], x)

        dtypes = ['object', 'float64', 'object', 'object', 'float64', 'object',
                    'object', 'object', 'object',
                    'object', 'object', 'float64', 'object',
                    'object', 'object', 'geometry']

        for i, x in enumerate(backbone_lines.dtypes):
            self.assertEqual(dtypes[i], x)

        backbone_lines = self.dataLoader.getLineRatings(backbone_lines)

        # check after calling getLineRatings()
        self.assertEqual(backbone_lines.shape, (726, 21))
        columns = ['COMPANY_ID', 'LENGTH_KM', 'LINE_ID', 'MEMBER', 'MILES', 'NAME',
                    'SUBSTATION_A_GLOBALID', 'SUBSTATION_B_GLOBALID', 'SYM_CODE',
                    'TO_LINE_NAME', 'TRANSMISSION_LINE_GLOBALID', 'VOLTAGE', 'SHAPE',
                    'TRANSMISSION_LINE_KEY', 'ESRI_OID', 'geometry',
                    'line_id', 'line_sytem_map_name', 'line_equiplist_name',
                    'match_confidence', 'line_rating']
        for i, x in enumerate(columns):
            self.assertEqual(backbone_lines.columns[i], x)

        dtypes = ['object', 'float64', 'object', 'object', 'float64', 'object',
                    'object', 'object', 'object',
                    'object', 'object', 'float64', 'object',
                    'object', 'object', 'geometry',
                    'object', 'object', 'object',
                    'float64', 'float64']

        for i, x in enumerate(backbone_lines.dtypes):
            self.assertEqual(dtypes[i], x)

        # check that all lines have a corresponding line rating
        self.assertEqual(backbone_lines["line_rating"].isnull().sum(), 0)

    def testAllSubstationsAndTapsGetter(self):
        substations = self.dataLoader.getAllSubstationsAndTaps()
        self.assertEqual(substations.shape, (15367, 16))
        columns = ['FAC_ID', 'MEMBER', 'NAME', 'STATE', 'SUBSTATION_GLOBALID',
                    'SUBSTATION_TYPE', 'SYM_CODE', 'VOLTAGE', 'COMMERCIAL_ZONE',
                    'PLANNING_ZONE_NAME', 'PJM_ZONE_GLOBALID', 'SHAPE', 'SUBSTATION_KEY',
                    'ESRI_OID', 'geometry', 'geo_matched_zone']
        for i, x in enumerate(columns):
            self.assertEqual(substations.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'object',
                    'object', 'object', 'float64', 'object',
                    'object', 'object', 'object', 'object',
                    'object', 'geometry', 'object']

        for i, x in enumerate(substations.dtypes):
            self.assertEqual(dtypes[i], x)


    def testAllSubstationLabelsGetter(self):
        substations = self.dataLoader.getAllSubstationLabels()
        self.assertEqual(substations.shape, (12872, 16))
        columns = ['FAC_ID', 'MEMBER', 'NAME', 'STATE', 'SUBSTATION_GLOBALID',
                    'SUBSTATION_TYPE', 'SYM_CODE', 'VOLTAGE', 'COMMERCIAL_ZONE',
                    'PLANNING_ZONE_NAME', 'PJM_ZONE_GLOBALID', 'SHAPE', 'SUBSTATION_KEY',
                    'ESRI_OID', 'geometry', 'geo_matched_zone']
        for i, x in enumerate(columns):
            self.assertEqual(substations.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'object',
                    'object', 'object', 'float64', 'object',
                    'object', 'object', 'object', 'object',
                    'object', 'geometry', 'object']

        for i, x in enumerate(substations.dtypes):
            self.assertEqual(dtypes[i], x)


    def testPJMZonesGetter(self):
        pjm_zones = self.dataLoader.getPJMZones()
        self.assertEqual(pjm_zones.shape, (21, 7))
        columns = ['ZONE_PLANNING_KEY', 'COMMERCIAL_ZONE', 'PLANNING_ZONE_NAME', 'ZONE_ID',
                    'PJM_ZONE_GLOBALID', 'SHAPE', 'geometry']
        for i, x in enumerate(columns):
            self.assertEqual(pjm_zones.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object',
                    'object', 'object', 'geometry']

        for i, x in enumerate(pjm_zones.dtypes):
            self.assertEqual(dtypes[i], x)


    def testPlanningQueueGetter(self):
        queue = self.dataLoader.getPlanningQueue()
        self.assertEqual(queue.shape, (4883, 20))
        columns = ['QUEUE KEY', 'FAC_ID', 'MERCHANT_FLAG', 'PJM_ZONE_GLOBALID',
                    'QUEUE_GLOBALID', 'QUEUE_ID', 'VOLTAGE', 'Shape', 'geometry',
                    'Queue Number', 'Name', 'MFO', 'MW Energy', 'MW Capacity',
                    'MW In Service', 'Project Type', 'Fuel', 'Status',
                    'Revised In Service Date', 'Actual In Service Date']
        for i, x in enumerate(columns):
            self.assertEqual(queue.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object',
                    'object', 'object', 'float64', 'object', 'geometry',
                    'object', 'object', 'float64', 'float64', 'float64',
                    'float64', 'object', 'object', 'object',
                    'datetime64[ns]', 'datetime64[ns]']

        for i, x in enumerate(queue.dtypes):
            self.assertEqual(dtypes[i], x)


    def testPJMStatesGetter(self):
        states = self.dataLoader.getPJMStates()
        self.assertEqual(states.shape, (70, 11))
        columns = ['STATE PROVINCE KEY', 'ABBREVIATION', 'CNT_STATE', 'COUNTRY', 'STATE',
                    'STATE_PROVINCE_GLOBALID', 'Shape', 'Shape.STArea()',
                    'Shape.STLength()', 'geometry', 'IN_PJM']

        for i, x in enumerate(columns):
            self.assertEqual(states.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'object',
                    'object', 'object', 'object',
                    'object', 'geometry', 'bool']

        for i, x in enumerate(states.dtypes):
            self.assertEqual(dtypes[i], x)


    def testPJMPnodeListGetter(self):
        node_list = self.dataLoader.getPnodeList()
        self.assertEqual(node_list.shape, (12310, 8))
        columns = ['pnode_id', 'zone', 'substation', 'voltage', 'equipment', 'type',
                    'system_map_substation_name', 'system_map_substation_id']

        for i, x in enumerate(columns):
            self.assertEqual(node_list.columns[i], x)

        dtypes = ['object', 'object', 'object', 'float64', 'object', 'object',
                    'object', 'object']

        for i, x in enumerate(node_list.dtypes):
            self.assertEqual(dtypes[i], x)


    def testGetLineSubstationsTaps(self):
        lines = self.dataLoader.getPJMBackboneLines()
        substations = self.dataLoader.getLineSubstationsTaps(lines)
        self.assertEqual(substations.shape, (478, 16))
        columns = ['FAC_ID', 'MEMBER', 'NAME', 'STATE', 'SUBSTATION_GLOBALID',
                    'SUBSTATION_TYPE', 'SYM_CODE', 'VOLTAGE', 'COMMERCIAL_ZONE',
                    'PLANNING_ZONE_NAME', 'PJM_ZONE_GLOBALID', 'SHAPE', 'SUBSTATION_KEY',
                    'ESRI_OID', 'geometry', 'geo_matched_zone']
        for i, x in enumerate(columns):
            self.assertEqual(substations.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'object',
                    'object', 'object', 'float64', 'object',
                    'object', 'object', 'object', 'object',
                    'object', 'geometry', 'object']

        for i, x in enumerate(substations.dtypes):
            self.assertEqual(dtypes[i], x)


    def testEIAPlantDataGetter(self):
        plant = self.dataLoader.getEIAPlantData()
        self.assertEqual(plant.shape, (3373, 21))
        columns = ['Plant Code', 'Plant Name', 'Street Address', 'City', 'County', 'State',
                    'Voltages', 'Balancing Authority Name',
                    'Transmission or Distribution System Owner', 'Generator ID',
                    'Unit Code', 'Technology', 'Prime Mover', 'Nameplate Capacity (MW)',
                    'Nameplate Power Factor', 'Summer Capacity (MW)',
                    'Winter Capacity (MW)', 'Minimum Load (MW)',
                    'RTO/ISO LMP Node Designation',
                    'RTO/ISO Location Designation for Reporting Wholesale Sales Data to FERC',
                    'geometry']

        for i, x in enumerate(columns):
            self.assertEqual(plant.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'object', 'object',
                    'object', 'object',
                    'object', 'object',
                    'object', 'object', 'object', 'float64',
                    'float64', 'float64',
                    'float64', 'float64',
                    'object',
                    'object',
                    'geometry']

        for i, x in enumerate(plant.dtypes):
            self.assertEqual(dtypes[i], x)


    def testMatchEIAPlantWithLineSubstationsTaps(self):
        plant = self.dataLoader.getEIAPlantData()
        lines = self.dataLoader.getPJMBackboneLines()
        self.dataLoader.matchEIAPlantWithLineSubstationsTaps(lines)

        self.assertEqual(plant.shape, (3373, 22))
        columns = ['Plant Code', 'Plant Name', 'Street Address', 'City', 'County', 'State',
                    'Voltages', 'Balancing Authority Name',
                    'Transmission or Distribution System Owner', 'Generator ID',
                    'Unit Code', 'Technology', 'Prime Mover', 'Nameplate Capacity (MW)',
                    'Nameplate Power Factor', 'Summer Capacity (MW)',
                    'Winter Capacity (MW)', 'Minimum Load (MW)',
                    'RTO/ISO LMP Node Designation',
                    'RTO/ISO Location Designation for Reporting Wholesale Sales Data to FERC',
                    'geometry', 'Nearest_Substations']

        for i, x in enumerate(columns):
            self.assertEqual(plant.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'object', 'object',
                    'object', 'object',
                    'object', 'object',
                    'object', 'object', 'object', 'float64',
                    'float64', 'float64',
                    'float64', 'float64',
                    'object',
                    'object',
                    'geometry', 'object']

        for i, x in enumerate(plant.dtypes):
            self.assertEqual(dtypes[i], x)

        # check that all plant has a corresponding nearest substations
        self.assertEqual(plant["Nearest_Substations"].isnull().sum(), 0)


if __name__ == '__main__':
    unittest.main()
