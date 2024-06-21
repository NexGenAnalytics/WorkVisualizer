import matplotlib.pyplot as plt
import numpy as np
import json
import networkx as nx
import os
import pydot
from networkx.drawing.nx_pydot import graphviz_layout

"""
This script constructs and returns the NetworkX graph based on the mock hierarchy.
To use, import generate_graph and pass it the path to your slicing_dir.

The graph itself is visualized and saved as "mock_graph.png".
"""

def build_graph(data, graph, node_sizes, parent=None, node_counter=[0]):
    # Define node id and increase counter for next node
    node_id = node_counter[0]
    node_counter[0] += 1

    # Define node label from path and name, standardize size
    node_label = data["name"]
    node_sizes.append(2000)

    # Add node to the graph
    graph.add_node(node_id, label=node_label)

    # Connect node to its parent
    if parent is not None:
        graph.add_edge(parent, node_id)

    # Recurse for children
    for child in data.get('children', []):
        build_graph(child, graph, node_sizes, parent=node_id, node_counter=node_counter)


def generate_graph(slicing_dir="/home/calebschilly/Develop/WorkVisualizer/WorkVisualizer/analysis/slicing"):
    # Create files
    hierarchy_file = os.path.join(slicing_dir, "mock_hierarchy.json")
    output_file = os.path.join(slicing_dir, "mock_graph.png")

    # Read in the data
    with open(hierarchy_file) as input_file:
        data = json.load(input_file)

    # Initialize and build the graph
    G = nx.DiGraph()
    node_counter = [0]
    node_sizes = []
    build_graph(data, G, node_sizes, node_counter=node_counter)

    # Visualize the graph
    labels = nx.get_node_attributes(G, 'label')
    pos = graphviz_layout(G, prog="dot")
    nx.draw(G, pos, labels=labels, with_labels=True, node_size=node_sizes, node_color='lightblue')
    plt.show()
    plt.savefig(output_file)

    return G

if __name__ == "__main__":
    generate_graph()
