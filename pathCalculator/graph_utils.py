import networkx as nx
import math

import numpy as np
from services import path_logs
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from numba import njit, prange

# def create_graph(binary_image):

#     graph = nx.Graph()
#     path_logs(f"init graph=====> ")
#     rows, cols = binary_image.shape

#     for row in range(rows):
#         for col in range(cols):
#             if binary_image[row, col] == 255:
#                 for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
#                     neighbor_row, neighbor_col = row + dx, col + dy
#                     if 0 <= neighbor_row < rows and 0 <= neighbor_col < cols:
#                         if binary_image[neighbor_row, neighbor_col] == 255:
#                             path_logs(f"add_edge graph=====> ")
#                             graph.add_edge(
#                                 (row, col), (neighbor_row, neighbor_col), weight=1
#                             )
#     path_logs(f"graph=====> {len(graph.nodes())}")
#     return graph


def get_edges_for_row(row, binary_image, rows, cols):
    edges = []
    for col in range(cols):
        if binary_image[row, col] == 255:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor_row, neighbor_col = row + dx, col + dy
                if 0 <= neighbor_row < rows and 0 <= neighbor_col < cols:
                    if binary_image[neighbor_row, neighbor_col] == 255:
                        edges.append(((row, col), (neighbor_row, neighbor_col)))
    return edges


def create_graph_fast(binary_image):
    graph = nx.Graph()
    path_logs("init graph=====>")

    # Get coordinates of white pixels
    white_pixels = np.argwhere(binary_image == 255)

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    rows, cols = binary_image.shape
    try:
        for dx, dy in directions:
            shifted = white_pixels + np.array([dx, dy])
            valid = (
                (shifted[:, 0] >= 0)
                & (shifted[:, 0] < rows)
                & (shifted[:, 1] >= 0)
                & (shifted[:, 1] < cols)
            )

            original_valid = white_pixels[valid]
            shifted_valid = shifted[valid]

            mask = binary_image[shifted_valid[:, 0], shifted_valid[:, 1]] == 255
            for (r1, c1), (r2, c2) in zip(original_valid[mask], shifted_valid[mask]):
                graph.add_edge((r1, c1), (r2, c2), weight=1)

        path_logs(f"graph=====> {len(graph.nodes())}")
        return graph
    except Exception as e:
        path_logs(f"Error in create_graph: {e}")
        return None


@njit(parallel=True)
def extract_edges(binary_image):
    rows, cols = binary_image.shape
    max_edges = rows * cols * 4
    edges = np.zeros((max_edges, 4), dtype=np.int32)
    count = 0

    for row in prange(rows):
        for col in range(cols):
            if binary_image[row, col] == 255:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = row + dx, col + dy
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and binary_image[nr, nc] == 255
                    ):
                        idx = row * cols + col  # create unique index
                        edges[count] = [row, col, nr, nc]
                        count += 1
    return edges[:count]


def create_graph(binary_image):
    """
    Creates a graph from a binary image using Numba-accelerated edge extraction.

    Args:
        binary_image (numpy.ndarray): A binary image where 255 represents valid nodes.

    Returns:
        networkx.Graph: A graph representing the binary image, or None if an error occurs.
    """
    try:
        import networkx as nx

        graph = nx.Graph()
        path_logs("create_graph_numba=====> Starting graph creation")

        # Extract edges using Numba-accelerated function
        edge_data = extract_edges(binary_image)
        path_logs(f"create_graph_numba=====> Extracted {len(edge_data)} edges")

        # Add edges to the graph
        for r1, c1, r2, c2 in edge_data:
            graph.add_edge((r1, c1), (r2, c2), weight=1)

        path_logs(
            f"create_graph_numba=====> Graph created with {len(graph.nodes())} nodes and {len(graph.edges())} edges"
        )
        return graph

    except Exception as e:
        path_logs(f"Error in create_graph_numba: {str(e)}")
        return None


def create_graph_v1(binary_image):
    try:
        graph = nx.Graph()
        path_logs("init graph=====>")
        rows, cols = binary_image.shape

        # Use multiprocessing to parallelize per row
        with ProcessPoolExecutor() as executor:
            futures = [
                executor.submit(get_edges_for_row, row, binary_image, rows, cols)
                for row in range(rows)
            ]

            for future in as_completed(futures):
                row_edges = future.result()
                for u, v in row_edges:
                    path_logs("add_edge graph=====>")
                    graph.add_edge(u, v, weight=1)

        path_logs(f"graph=====> {len(graph.nodes())}")
        return graph
    except Exception as e:
        path_logs(f"Error in create_graph: {e}")
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
