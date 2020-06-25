import unittest
from functions import * # TODO: why not from ._function import *
import geopandas as gpd

class PJMSystemMapTest(unittest.TestCase):

    def testConstructor(self):
        dataLoader = PJMSystemMap()
        self.assertIsNotNone(dataLoader)


    def testBackboneLinesGetter(self):
        dataLoader = PJMSystemMap()
        backbone_lines = dataLoader.getPJMBackboneLines()
        self.assertEqual(backbone_lines.shape, (732, 16))
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


    def testAllSubstationsGetter(self):
        dataLoader = PJMSystemMap()
        substations = dataLoader.getAllSubstations()
        self.assertEqual(substations.shape, (12870, 16))
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
        dataLoader = PJMSystemMap()
        substations = dataLoader.getAllSubstationLabels()
        self.assertEqual(substations.shape, (12870, 16))
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
        dataLoader = PJMSystemMap()
        pjm_zones = dataLoader.getPJMZones()
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
        dataLoader = PJMSystemMap()
        queue = dataLoader.getPlanningQueue()
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
        dataLoader = PJMSystemMap()
        states = dataLoader.getPJMStates()
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
        dataLoader = PJMSystemMap()
        node_list = dataLoader.getPnodeList()
        self.assertEqual(node_list.shape, (12310, 8))
        columns = ['pnode_id', 'zone', 'substation', 'voltage', 'equipment', 'type',
                    'system_map_substation_name', 'system_map_substation_id']

        for i, x in enumerate(columns):
            self.assertEqual(node_list.columns[i], x)

        dtypes = ['object', 'object', 'object', 'float64', 'object', 'object',
                    'object', 'object']

        for i, x in enumerate(node_list.dtypes):
            self.assertEqual(dtypes[i], x)


if __name__ == '__main__':
    unittest.main()
