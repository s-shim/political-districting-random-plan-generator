import pandas as pd
import networkx as nx
import myDictionary as md
import copy

numDistricts = 8 
tolerance = 0.05
lines = pd.read_csv('lines_MD_sophisticatedFinal.csv')
nodes = pd.read_csv('nodes_MD_sophisticatedFinal.csv')
fracXTable = pd.read_csv('fracFile.csv')

G = nx.Graph()

#Using networkx to create the graph
for l in lines['Line']:
    [Source] = lines.loc[lines['Line'] == l, 'Source']
    [Target] = lines.loc[lines['Line'] == l, 'Target']
    G.add_edge(Source,Target)

for u in nodes['Node']:
    [population] = nodes.loc[nodes['Node']==u,'population']
    G.nodes[u]['population'] = population 
    
fracX = {}
for i in fracXTable.index:
    fracX[fracXTable['Node'][i],fracXTable['District'][i]] = fracXTable['fracX'][i]

district = md.ROUND(fracX,numDistricts,G)                        
                
for i in range(numDistricts):
    print(i,district[i])
    
zeroX = {}
for i in range(numDistricts):
    for u in G.nodes():
        zeroX[u,i] = 0
        
intX = copy.deepcopy(zeroX)        
for i in range(numDistricts):
    for u in district[i]:
        intX[u,i] = 1
        
int_district = md.ROUND(intX,numDistricts,G)                        
for i in range(numDistricts):
    print(i,int_district[i])        
        
        
        
        
