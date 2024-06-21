from collections import defaultdict, deque

from s2_graph_mock_hierarchy import generate_graph

class GraphNode:
    def __init__(self, value):
        self.value = value
        self.children = []

def serialize_subgraph(G, root, depth):
    if depth == 0:
        return ""
    subgraph_str = f"{root}"
    if depth > 0:
        for neighbor in G.successors(root):
            subgraph_str += f"({serialize_subgraph(G, neighbor, depth - 1)})"

    print(subgraph_str)
    return subgraph_str

def is_similar(subgraph1, subgraph2, similarity_threshold):
    """
    Checks if two subgraphs are similar based on a similarity threshold.

    Args:
        subgraph1 (str): Serialized representation of the first subgraph.
        subgraph2 (str): Serialized representation of the second subgraph.
        similarity_threshold (float): Threshold for determining similarity (0 to 1).

    Returns:
        bool: True if the subgraphs are similar above the threshold, False otherwise.
    """
    # Use SequenceMatcher to find the similarity ratio
    matcher = difflib.SequenceMatcher(None, subgraph1, subgraph2)
    similarity_ratio = matcher.ratio()

    return similarity_ratio >= similarity_threshold

def find_repeating_subgraphs(G, max_depth, similarity_threshold):
    subgraph_frequency = defaultdict(int)
    stack = deque([(0, 0)])  # Assuming the root node is labeled 0

    while stack:
        current_node, current_depth = stack.pop()
        if current_depth < max_depth:
            serialized_subgraph = serialize_subgraph(G, current_node, max_depth - current_depth)
            subgraph_frequency[serialized_subgraph] += 1

            for neighbor in G.successors(current_node):
                stack.append((neighbor, current_depth + 1))

    # Filter subgraphs based on similarity threshold
    repeating_subgraphs = {sg: freq for sg, freq in subgraph_frequency.items() if freq > 1}
    return repeating_subgraphs

# Example usage
G = generate_graph()

# Define parameters
max_depth = 3
similarity_threshold = 0.1

# Find repeating subgraphs
repeating_subgraphs = find_repeating_subgraphs(G, max_depth, similarity_threshold)
for sg, freq in repeating_subgraphs.items():
    print(f"Subgraph: {sg}, Frequency: {freq}")