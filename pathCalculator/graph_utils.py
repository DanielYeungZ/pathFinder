import networkx as nx
import math
from services import path_logs


def create_graph(binary_image):

    graph = nx.Graph()
    path_logs(f"init graph=====> ")
    rows, cols = binary_image.shape

    for row in range(rows):
        for col in range(cols):
            if binary_image[row, col] == 255:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    neighbor_row, neighbor_col = row + dx, col + dy
                    if 0 <= neighbor_row < rows and 0 <= neighbor_col < cols:
                        if binary_image[neighbor_row, neighbor_col] == 255:
                            path_logs(f"add_edge graph=====> ")
                            graph.add_edge(
                                (row, col), (neighbor_row, neighbor_col), weight=1
                            )
    path_logs(f"graph=====> {len(graph.nodes())}")
    return graph


def shortest_path(graph, start, end):
    def euclidean_distance(a, b):
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    path = nx.astar_path(
        graph, source=start, target=end, heuristic=euclidean_distance, weight="weight"
    )
    return path


# Function to find the shortest path
def shortest_path1(graph, start, end):
    # Calculate the shortest path using Dijkstra's algorithm
    path = nx.shortest_path(graph, source=start, target=end, weight="weight")
    return path
