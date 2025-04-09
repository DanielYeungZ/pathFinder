import networkx as nx
import math
from services import path_logs
from concurrent.futures import ThreadPoolExecutor

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


def process_chunk(binary_image, start_row, end_row):
    path_logs(f"process_chunk=====> start_row: {start_row}, end_row: {end_row}")
    try:
        graph = nx.Graph()
        rows, cols = binary_image.shape
        for row in range(start_row, end_row):
            for col in range(cols):
                if binary_image[row, col] == 255:
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        neighbor_row, neighbor_col = row + dx, col + dy
                        if 0 <= neighbor_row < rows and 0 <= neighbor_col < cols:
                            if binary_image[neighbor_row, neighbor_col] == 255:
                                graph.add_edge(
                                    (row, col), (neighbor_row, neighbor_col), weight=1
                                )
    except Exception as e:
        path_logs(f"Error in process_chunk for rows {start_row}-{end_row}: {str(e)}")
    path_logs(
        f"process_chunk graph=====> start_row: {start_row}, end_row: {end_row}, nodes: {len(graph.nodes())}"
    )
    return graph


def create_graph(binary_image):
    try:
        rows, cols = binary_image.shape
        chunk_size = max(
            1, rows // 12
        )  # Divide the image into 8 chunks or more if rows are small
        graphs = []
        futures = []

        path_logs(
            f"create_graph=====> Starting graph creation with {rows} rows and {cols} cols"
        )

        with ThreadPoolExecutor() as executor:
            for i in range(0, rows, chunk_size):
                start_row = i
                end_row = min(i + chunk_size, rows)

                # Add 1 extra row overlap unless it's the last chunk
                if end_row < rows:
                    end_row = min(end_row + 1, rows)

                futures.append(
                    executor.submit(process_chunk, binary_image, start_row, end_row)
                )

            for future in futures:
                graphs.append(future.result())

        path_logs(
            f"create_graph=====> Finished processing all chunks, total graphs: {len(graphs)}"
        )
        # Combine subgraphs
        combined_graph = nx.Graph()
        for g in graphs:
            combined_graph.add_edges_from(g.edges(data=True))

        return combined_graph
    except Exception as e:
        path_logs(f"Error in create_graph: {str(e)}")

    # def create_graph(binary_image):
    rows, cols = binary_image.shape
    chunk_size = rows // 4  # Divide into 4 chunks
    graphs = []

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(process_chunk, binary_image, i, i + chunk_size)
            for i in range(0, rows, chunk_size)
        ]
        for future in futures:
            graphs.append(future.result())

    # Combine all subgraphs
    combined_graph = nx.Graph()
    for g in graphs:
        combined_graph.add_edges_from(g.edges(data=True))

    return combined_graph


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
