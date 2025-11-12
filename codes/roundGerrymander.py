import pandas as pd
import networkx as nx
import random 

numDistricts = 8 
lines = pd.read_csv('lines_MD_sophisticatedFinal.csv')
nodes = pd.read_csv('nodes_MD_sophisticatedFinal.csv')

G = nx.Graph()

#Using networkx to create the graph
for l in lines['Line']:
    [Source] = lines.loc[lines['Line'] == l, 'Source']
    [Target] = lines.loc[lines['Line'] == l, 'Target']
    G.add_edge(Source,Target)

for u in nodes['Node']:
    [population] = nodes.loc[nodes['Node']==u,'population']
    G.nodes[u]['population'] = population 
    
district = {}
for i in range(numDistricts):
    district[i] = []
    
fracX = {}
for u in G.nodes():
    for i in range(numDistricts):
        fracX[u,i] = random.random()

uArray = []
iArray = []
fracXArray = []
for u in G.nodes():
    for i in range(numDistricts):
        uArray += [u]
        iArray += [i]
        fracXArray += [fracX[u,i]]

inputTable = pd.DataFrame(list(zip(uArray,iArray,fracXArray)),columns =['Node', 'District', 'fracX'])
inputTable.to_csv(r'fracFile.csv', index = False)




