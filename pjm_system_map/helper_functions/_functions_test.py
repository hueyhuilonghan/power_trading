import unittest
from _functions import * # TODO: why not from ._function import *
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
        self.assertEqual(substations.shape, (12870, 15))
        columns = ['FAC_ID', 'MEMBER', 'NAME', 'STATE', 'SUBSTATION_GLOBALID',
                    'SUBSTATION_TYPE', 'SYM_CODE', 'VOLTAGE', 'COMMERCIAL_ZONE',
                    'PLANNING_ZONE_NAME', 'PJM_ZONE_GLOBALID', 'SHAPE', 'SUBSTATION_KEY',
                    'ESRI_OID', 'geometry']
        for i, x in enumerate(columns):
            self.assertEqual(substations.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'object',
                    'object', 'object', 'float64', 'object',
                    'object', 'object', 'object', 'object',
                    'object', 'geometry']

        for i, x in enumerate(substations.dtypes):
            self.assertEqual(dtypes[i], x)


    def testAllSubstationLabelsGetter(self):
        dataLoader = PJMSystemMap()
        substations = dataLoader.getAllSubstationLabels()
        self.assertEqual(substations.shape, (12870, 15))
        columns = ['FAC_ID', 'MEMBER', 'NAME', 'STATE', 'SUBSTATION_GLOBALID',
                    'SUBSTATION_TYPE', 'SYM_CODE', 'VOLTAGE', 'COMMERCIAL_ZONE',
                    'PLANNING_ZONE_NAME', 'PJM_ZONE_GLOBALID', 'SHAPE', 'SUBSTATION_KEY',
                    'ESRI_OID', 'geometry']
        for i, x in enumerate(columns):
            self.assertEqual(substations.columns[i], x)

        dtypes = ['object', 'object', 'object', 'object', 'object',
                    'object', 'object', 'float64', 'object',
                    'object', 'object', 'object', 'object',
                    'object', 'geometry']

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




if __name__ == '__main__':
    unittest.main()
