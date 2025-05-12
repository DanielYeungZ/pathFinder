import networkx as nx
import math

import numpy as np
from services import path_logs


def extract_edges_v2(binary_image):
    rows, cols = binary_image.shape
    max_edges = rows * cols * 10  # upper bound

    edges = np.empty((max_edges, 4), dtype=np.int32)
    count = 0

    for row in range(rows):
        for col in range(cols):
            if binary_image[row, col] == 255:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = row + dx, col + dy
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and binary_image[nr, nc] == 255
                    ):
                        edges[count] = (row, col, nr, nc)
                        count += 1

    return edges[:count]


def extract_edges(binary_image):
    rows, cols = binary_image.shape
    max_edges = rows * cols * 4  # maximum 4 neighbors per white pixel

    edges = np.empty((max_edges, 4), dtype=np.int32)
    count = 0

    # Get all white pixel coordinates
    white_rows, white_cols = np.where(binary_image == 255)

    # 4-connected neighbors
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for i in range(len(white_rows)):
        row = white_rows[i]
        col = white_cols[i]

        for dx, dy in directions:
            nr, nc = row + dx, col + dy
            if 0 <= nr < rows and 0 <= nc < cols and binary_image[nr, nc] == 255:
                edges[count] = (row, col, nr, nc)
                count += 1

    return edges[:count]


def create_graph(binary_image):
    try:
        graph = nx.Graph()
        path_logs("init graphssss=====>")

        edges = extract_edges(binary_image)
        path_logs(f"extract_edges=====> {len(edges)} edges")

        graph.add_edges_from(
            ((r1, c1), (r2, c2), {"weight": 1}) for r1, c1, r2, c2 in edges
        )
        # optionally: print("add_edge graph=====>")

        path_logs(f"finish graph=====> {len(graph.nodes())}")
        return graph
    except Exception as e:
        path_logs(f"Error creating graph: {e}")
        return None


def create_graph_origin(binary_image):

    graph = nx.Graph()
    path_logs(f"init graph=====> ")
    rows, cols = binary_image.shape
    try:
        for row in range(rows):
            for col in range(cols):
                if binary_image[row, col] == 255:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        neighbor_row, neighbor_col = row + dx, col + dy
                        if 0 <= neighbor_row < rows and 0 <= neighbor_col < cols:
                            if binary_image[neighbor_row, neighbor_col] == 255:
                                graph.add_edge(
                                    (row, col), (neighbor_row, neighbor_col), weight=1
                                )
        path_logs(f"graph=====> {len(graph.nodes())}")
        return graph
    except Exception as e:
        path_logs(f"Error creating graph: {e}")
        return None


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
