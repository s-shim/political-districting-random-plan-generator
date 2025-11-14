#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 25 19:28:55 2025

@author: noahlee
"""

import pandas as pd
import networkx as nx
import myDictionary as md
import copy
import random
import math
#import multiprocessing as mp
import os
import glob

numDistricts = 2;
tolerance = 0.05
lines = pd.read_csv('../gerrymandered_dist_mass_1812_lines_3.csv')
nodes = pd.read_csv('../gerrymandered_dist_mass_1812_nodes_3.csv')


G = nx.Graph()

#Using networkx to create the graph

for l in lines['Line']:
    [Source] = lines.loc[lines['Line'] == l, 'Source']
    [Target] = lines.loc[lines['Line'] == l, 'Target']
    G.add_edge(Source,Target)

for u in nodes['Node']:
    [population] = nodes.loc[nodes['Node']==u,'population']
    G.nodes[u]['population'] = population 
    
def create_district_from_csv(filepath):
    df = pd.read_csv(filepath)
    district = {}
    for _, row in df.iterrows():
        d = row['District']
        node = row['Node']
        if d not in district:
            district[d] = []
        district[d].append(node)
    return district


# =============================================================================
# def gerryEx(district,G,numDistricts,nx):
#     gerry = {}  
#     for g in range(1,numDistricts+1):
#         gerry_district = -1
#         subG = G.subgraph(district[g])
#         for c in subG.nodes():
#             sumDistance_c = 0
#             for d in subG.nodes():
#                 if c != d:
#                     sumDistance_c += nx.shortest_path_length(subG, source = c, target = d)
#             if gerry_district == -1:
#                 gerry_district = sumDistance_c
#             else:
#                 if gerry_district > sumDistance_c:
#                     gerry_district = sumDistance_c
#         print(g,gerry_district,len(district[g]),gerry_district / len(district[g]))
#         gerry[g] = gerry_district / pow(len(district[g]),1)
#     return gerry
# 
# # gerryscore existing plan
# district = create_district_from_csv(f'gerrymandereded_dist_mass_1812_nodes.csv')
# currentScore = gerryEx(district,G,numDistricts,nx)
# =============================================================================


idArray = []
districtArray = []
gerryArray = []
totalScore = 0
# =============================================================================
# for i in range(1, 501):
#     print()
#     print(i)
# =============================================================================
for name in glob.glob('feas*.csv'):
    planID = int(name[17:-4])
    district = create_district_from_csv(name)
    currentScore = md.gerry(district, G, numDistricts)
 
    idArray += [planID]
    districtArray += [0]
    gerryArray += [currentScore[0]]

    idArray += [planID]
    districtArray += [1]
    gerryArray += [currentScore[1]]


gerryTable = pd.DataFrame(list(zip(idArray,districtArray,gerryArray)),columns =['ID','District','Normal Gerry'])
gerryTable.to_csv('gerry_mass.csv', index=False)

    