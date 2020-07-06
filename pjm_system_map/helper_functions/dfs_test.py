import unittest

from dfs import DFSGraph


class DFSTest(unittest.TestCase):

    def testGraphConstructor(self):
        g = DFSGraph()
        self.assertIsNotNone(g)

    def testaddEdges(self):
        g = DFSGraph()
        g.addEdge("0", "1")
        g.addEdge("0", "2")
        g.addEdge("1", "2")
        g = g.getGraph()
        self.assertEqual(len(g.keys()), 3)
        self.assertEqual(len(g["0"]), 2)
        self.assertEqual(len(g["1"]), 2)
        self.assertEqual(len(g["2"]), 2)

    def testaddDuplicatedEdges(self):
        g = DFSGraph()
        g.addEdge("0", "1")
        g.addEdge("0", "1")
        g.addEdge("1", "0")
        g.addEdge("0", "2")
        g.addEdge("2", "0")
        g.addEdge("1", "2")
        g.addEdge("2", "1")
        g.addEdge("2", "1")
        g = g.getGraph()
        self.assertEqual(len(g.keys()), 3)
        self.assertEqual(len(g["0"]), 2)
        self.assertEqual(len(g["1"]), 2)
        self.assertEqual(len(g["2"]), 2)

    def testDFS(self):
        g = DFSGraph()
        g.addEdge("0", "1")
        g.addEdge("0", "2")
        g.addEdge("1", "2")
        g.addEdge("2", "0")
        g.addEdge("2", "3")
        g.addEdge("3", "3")
        unconnected_vertices = g.DFS("2")
        self.assertEqual(len(unconnected_vertices), 0)

        unconnected_vertices = g.DFS("3")
        self.assertEqual(len(unconnected_vertices), 0)

    def testDFSIsolatedVertices(self):
        g = DFSGraph()
        g.addEdge("0", "1")
        g.addEdge("0", "2")
        g.addEdge("1", "2")
        g.addEdge("2", "0")
        g.addEdge("2", "3")
        g.addEdge("3", "3")
        g.addEdge("4", "5")
        unconnected_vertices = g.DFS("2")
        self.assertEqual(len(unconnected_vertices), 2)

        unconnected_vertices = g.DFS("3")
        self.assertEqual(len(unconnected_vertices), 2)

        unconnected_vertices = g.DFS("4")
        self.assertEqual(len(unconnected_vertices), 4)


    def testGetConnectedComponents(self):
        g = DFSGraph()
        g.addEdge("0", "1")
        g.addEdge("0", "2")
        g.addEdge("1", "2")
        g.addEdge("2", "0")
        g.addEdge("2", "3")
        g.addEdge("3", "3")
        connected_components = g.getConnectedComponents()
        self.assertEqual(len(connected_components), 1)

    def testGetConnectedComponentsTwo(self):
        g = DFSGraph()
        g.addEdge("0", "1")
        g.addEdge("0", "2")
        g.addEdge("1", "2")
        g.addEdge("2", "0")
        g.addEdge("2", "3")
        g.addEdge("3", "3")
        g.addEdge("4", "5")
        connected_components = g.getConnectedComponents()
        self.assertEqual(len(connected_components), 2)


if __name__ == '__main__':
    unittest.main()
