"""
Python3 program to do DFS on a grph and get connected subgraphs.

Source: https://www.geeksforgeeks.org/depth-first-search-or-dfs-for-a-graph/

Certain revisions are done on the original to accomodate the current purposes, namely:
    change from directed to undirected graph
    return disconnected vertices
    use set instead of list to rid of duplicates
    add get connected subgraphs: source https://www.geeksforgeeks.org/connected-components-in-an-undirected-graph/

Author: Huey Han <huilong.han@gmail.com>
"""



from collections import defaultdict

# This class represents a undirected graph using
# adjacency list representation
class DFSGraph:

    # Constructor
    def __init__(self):

        # default dictionary to store graph
        # TODO: why default dictionary?
        self.graph = defaultdict(set)

    # function to add an edge to graph
    def addEdge(self, u, v):
        self.graph[u].add(v)
        self.graph[v].add(u)


    def DFSUtil(self, temp, v, visited):

        # Mark the current vertex as visited
        visited[v] = True

        # Store the vertex to list
        temp.append(v)

        # Repeat for all vertices adjacent
        # to this vertex v
        for i in self.graph[v]:
            if visited[i] == False:
                temp = self.DFSUtil(temp, i, visited)
        return temp


    # The function to do DFS traversal. It uses recursive DFSUtil()
    # The function returns the list of vertices unconnected to the current
    # component
    def DFS(self, v):

        # Mark all the vertices as not visited
        visited = {k: False for k in self.graph.keys()}

        # Call the recursive helper function
        # to print DFS traversal
        self.DFSUtil([], v, visited)

        return [k for k, v in visited.items() if not v]

    # return graph
    def getGraph(self):

        return self.graph


    # get connnected components in graph
    def getConnectedComponents(self):
        visited = {k: False for k in self.graph.keys()}
        cc = []
        for v in self.graph.keys():
            if visited[v] == False:
                temp = []
                cc.append(self.DFSUtil(temp, v, visited))
        return cc
