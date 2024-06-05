import matplotlib.pyplot as plt
import numpy as np
import json
import networkx as nx
import os
import pydot
from networkx.drawing.nx_pydot import graphviz_layout


def build_graph(data, graph, node_sizes, parent=None, node_counter=[0]):
    # Define node id and increase counter for next node
    node_id = node_counter[0]
    node_counter[0] += 1

    # Define node label from path and name
    node_label = f"{data['path']} / {data['name']}"

    if "fence" in node_label.lower():
        return

    node_sizes.append(float(data["duration"]) * 10e4)

    # Add node to the graph
    graph.add_node(node_id, label=node_label)

    # Connect node to its parent
    if parent is not None:
        graph.add_edge(parent, node_id)

    # Recurse for children
    for child in data.get('children', []):
        build_graph(child, graph, node_sizes, parent=node_id, node_counter=node_counter)


def main():
    os.chdir("../")

    with open("data/testapp_0r_100s_pruned.json") as file:
        data = json.load(file)

    G = nx.DiGraph()

    root_id = 0
    G.add_node(root_id, label="Root Node")
    node_counter = [1]
    node_sizes = [2000]

    # Build the graph starting from the root node
    for block in data:
        build_graph(block, G, node_sizes, parent=root_id, node_counter=node_counter)

    pos = nx.spring_layout(G)
    labels = nx.get_node_attributes(G, 'label')
    nx.draw(G, pos, labels=labels, with_labels=True, node_size=node_sizes, node_color='lightblue')
    plt.show()

    pos = graphviz_layout(G, prog="dot")
    nx.draw(G, pos, labels=labels, with_labels=True, node_size=node_sizes, node_color='lightblue')
    plt.show()


if __name__ == "__main__":
    main()
