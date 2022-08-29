import argparse
from collections import defaultdict
import json
import os
import time

import networkx as nx
from pyvis.network import Network

from mediawiki import MediaWiki
from mediawiki.exceptions import DisambiguationError

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

parser = argparse.ArgumentParser()
parser.add_argument('--filter', action='store_true')
parser.add_argument('--threshold', type=float, default=0.75)

args = parser.parse_args()

value = []
memory = defaultdict(str)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
wikipedia = MediaWiki()
net = Network("1750px", "1250px")


def disambiguation_node(node, topics):
    print(f"{node} is Disambiguation.")
    print(f"{node} may refer to: ")
    topics = list(filter(lambda x: 'disambiguation' not in x, topics))
    for i, topic in enumerate(topics):
        print(i, topic)
    choice = int(input("Enter a choice: "))
    assert choice in range(len(topics))
    temp_summary = wikipedia.summary(topics[choice])

    return temp_summary


def filter_cosine_sim(keyword_embedding, pivot_embedding, node_embedding):
    A = cosine_similarity(keyword_embedding, pivot_embedding)[0][0]
    B = cosine_similarity(pivot_embedding, node_embedding)[0][0]
    if B == 0:
        return 0
    if A > 0:
        value.append(A/abs(B))
        if A/abs(B) >= args.threshold:
            return 1
    return 0


def load_summary(node):
    if memory[node]:
        node_summary = memory[node]
    else:
        try:
            node_summary = wikipedia.summary(node)
        except DisambiguationError as e:
            node_summary = disambiguation_node(node, e.options)
        finally:
            memory[node] = node_summary
    node_embedding = model.encode(node_summary).reshape(1, -1)

    return node_summary, node_embedding


def make_graph_filter(graph, pivot_node, data, weight, summary, keyword_embedding):
    global memory
    pivot_embedding = model.encode(summary).reshape(1, -1)
    pivot_data = data[pivot_node]
    if pivot_data and pivot_data.get('parent-categories'):
        for node in pivot_data['parent-categories'].keys():
            node_summary, node_embedding = load_summary(node)

            if filter_cosine_sim(keyword_embedding, pivot_embedding, node_embedding):
                if not (node in graph.nodes()):
                    graph.add_node(node, size=weight)
                graph.add_edge(pivot_node, node)
                make_graph_filter(
                    graph, node, pivot_data['parent-categories'], weight//2, node_summary, keyword_embedding)
    if pivot_data and pivot_data.get('sub-categories'):
        for node in pivot_data['sub-categories'].keys():
            if not (node in graph.nodes()):
                graph.add_node(node, size=weight)
            graph.add_edge(node, pivot_node)
            make_graph_filter(graph, node, pivot_data
                              ['sub-categories'], weight//2, summary, keyword_embedding)


def make_graph(graph, pivot_node, data, weight):
    pivot_data = data[pivot_node]
    if pivot_data and pivot_data.get('parent-categories'):
        for node in pivot_data['parent-categories'].keys():
            if not (node in graph.nodes()):
                graph.add_node(node, size=weight)
            graph.add_edge(pivot_node, node)
            make_graph(
                graph, node, pivot_data['parent-categories'], weight//2)
    if pivot_data and pivot_data.get('sub-categories'):
        for node in pivot_data['sub-categories'].keys():
            if not (node in graph.nodes()):
                graph.add_node(node, size=weight)
            graph.add_edge(node, pivot_node)
            make_graph(graph, node, pivot_data
                       ['sub-categories'], weight//2)


def main():
    keyword = input("Enter keyword: ")
    keyword = "_".join(keyword.split(' '))
    start_time = time.time()
    try:
        with open('./results/{}.json'.format(keyword), 'r') as inFile:
            strings = inFile.read()
            data = json.loads(strings)
    except:
        ValueError("You need to generate category tree first.")

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    wikipedia = MediaWiki()
    net = Network("1750px", "1250px")

    graph = nx.DiGraph()

    init_weight = 64
    first_node = list(data.keys())[0]
    graph.add_node(first_node, size=init_weight)
    summary = wikipedia.summary(first_node)
    keyword_embedding = model.encode(summary).reshape(1, -1)

    pivot_node = first_node

    if args.filter:
        make_graph_filter(graph, pivot_node, data,
                          init_weight//2, summary, keyword_embedding)
        keyword+='_filter'
    else:
        make_graph(graph, pivot_node, data, init_weight//2)

    net.from_nx(graph)
    # if set graph other setting using show_buttons
    # net.show_buttons(filter_=['nodes'])
    options = open("option.txt", 'r').read()
    net.set_options(options)
    if not os.path.exists('./graph_results'):
        os.mkdir('./graph_results')
    net.show('./graph_results/{}.html'.format(keyword))
    print("[Total time] {}".format(time.time()-start_time))


if __name__ == '__main__':
    main()
