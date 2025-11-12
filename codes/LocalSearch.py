import pandas as pd
import networkx as nx
import myDictionary as md
import copy
import random
import math

numDistricts = 8 
tolerance = 0.05
lines = pd.read_csv('lines_MD_sophisticatedFinal.csv')
nodes = pd.read_csv('nodes_MD_sophisticatedFinal.csv')
feasSolution = pd.read_csv('feas_MD_sophisticatedFinal.csv')
totalTrials = 1000000


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
for g in range(numDistricts):
    district[g] = []
    
for i, row in feasSolution.iterrows():
    district[row[0]] += [row[1]]


gerry = md.gerry(district,G,numDistricts,nx)

for g in range(numDistricts):
    print(g,gerry[g])
             
                    
                
                
                
                
                
                
                
                
                
                
                
                