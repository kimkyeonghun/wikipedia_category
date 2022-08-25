import json

import networkx as nx
from pyvis.network import Network

def make_graph(graph, pivot_node, data, weight):
    if data[pivot_node]:
        for node in data[pivot_node]['parent-categories'].keys():
            graph.add_node(node, size = weight)
            graph.add_edge(pivot_node, node)
            make_graph(graph, node, data[pivot_node]['parent-categories'], weight//2)

keyword = input("Enter keyword: ")
keyword = "_".join(keyword.split(' '))
try:
    with open('./results/{}.json'.format(keyword), 'r') as inFile:
        strings =inFile.read()
        data = json.loads(strings)
except:
    ValueError("You need to generate category tree first.")
    
net = Network("1750px", "1250px")

graph = nx.DiGraph()

init_weight = 32
first_node = list(data.keys())[0]
graph.add_node(first_node, size = init_weight)

pivot_node = first_node

make_graph(graph, pivot_node, data, init_weight)

net.from_nx(graph)
#if set graph other setting using show_buttons
#net.show_buttons(filter_=['nodes'])
net.set_options("""
const options = {
  "nodes": {
    "borderWidth": 3,
    "borderWidthSelected": 4,
    "opacity": null,
    "color": {
        "border": "rgba(165,0,26,0.5)",
        "background": "rgba(165,0,26,1)",
        "highlight": {
            "border": "rgba(165,0,26,1)"
        }
    },
    "font": {
      "size": 20,
      "strokeWidth": 2
    },
    "shapeProperties": {
      "borderRadius": 4
    }
  }
}
""")
net.show('{}.html'.format(keyword))