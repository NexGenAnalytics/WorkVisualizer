import numpy as np
import os
import itertools

import networkx as nx

from s2_graph_mock_hierarchy import generate_graph

"""
This script (wip) analyzes the NetworkX graph.
"""

def find_largest_repeating_subpattern(numbers):
    n = len(numbers)
    max_repeats = 0
    best_start = -1
    best_len = 0

    # Try every possible length of pattern from 1 to n/2
    for pattern_length in range(1, n // 2 + 1):
        # Try every possible starting point for the pattern
        for start in range(n - pattern_length):
            current_pattern = numbers[start:start + pattern_length]
            count = 0

            # Count repetitions of the pattern starting from the current start
            for i in range(start, n - pattern_length + 1, pattern_length):
                if numbers[i:i + pattern_length] == current_pattern:
                    count += 1
                else:
                    break  # As soon as pattern does not match, stop counting

            # If the number of repetitions with the current pattern is greater than the max found so far, update
            if count > max_repeats:
                max_repeats = count
                best_start = start
                best_len = pattern_length

    if max_repeats > 1:  # Return only if a repeating pattern is found
        return (best_start, max_repeats, best_len)
    else:
        return None  # No repeating pattern found

def find_matching_nodes(G, label, layer):
    edges = []
    node_ids = [node_id for node_id in layer if G.nodes[node_id] == label]
    for i in range(num_instances):
        list(nx.dfs_edges(G, source=node_id))

def analyze_graph(G):
    bs_layers = dict(enumerate(nx.bfs_layers(G, 0)))

    graph_layers = {}

    for layer_id, layer in bs_layers.items():
        graph_layers[layer_id] = []
        for node_id in layer:
            graph_layers[layer_id].append((int(G.nodes[node_id]["label"])))

    print(graph_layers)

    for layer_id, layer in bs_layers.items():
        subpattern = find_largest_repeating_subpattern(graph_layers[layer_id])
        if find_num_matching_nodes(G, graph_layers[layer_id][subpattern[0]], layer) == subpattern[1]:
            return True


def main():
    G = generate_graph()
    analyze_graph(G)

main()
