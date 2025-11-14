import pandas as pd
import networkx as nx
# from gurobipy import *
import math
import os
import glob

numDistricts = 2 
tolerance = 0.05
lines = pd.read_csv('../gerrymandered_dist_mass_1812_lines_3.csv')
nodes = pd.read_csv('../gerrymandered_dist_mass_1812_nodes_3.csv')
existingPlan = pd.read_csv('../gerrymandered_dist_mass_1812_nodes_3.csv')
analysis_avg = pd.read_csv('gerry_mass.csv')

districtID = 1

theDistrict = []
for index, row in existingPlan.iterrows():
    if row['District'] == districtID:
        theDistrict += [row['Node']]
        

G = nx.Graph()

#Using networkx to create the graph
for l in lines['Line']:
    [Source] = lines.loc[lines['Line'] == l, 'Source']
    [Target] = lines.loc[lines['Line'] == l, 'Target']
    G.add_edge(Source,Target)

subG = nx.Graph(G.subgraph(theDistrict))

print('District %s is contiguous ='%districtID,nx.is_connected(subG))
print('number of precincts in District %s ='%districtID,len(subG))

best_gerry = -1
for c in subG.nodes():
    gerry_c = 0
    for d in subG.nodes():
        if c != d:
            gerry_c += nx.shortest_path_length(subG, source=c, target=d)
    if best_gerry < 0:
        best_gerry = gerry_c
        best_c = c
        
    if best_gerry > gerry_c:
        best_gerry = gerry_c
        best_c = c

print('center =',best_c)
print('gerry score =',best_gerry)
print('normalized gerry score =',best_gerry/pow(len(subG),1))

# =============================================================================
# total_AVG_GS = 0.0
# for prec in theDistrict:
#     [avg_norm] = analysis_avg.loc[analysis_avg['Node']==prec,'AVG GS'] # VAR GS
#     total_AVG_GS += float(avg_norm)
# 
# planIDArray = [-1]
# for name in glob.glob('complete_sims/sim*feas*.csv'):
#     planID = int(name[14+3:14+7])
#     planIDArray += [planID]
# 
# distArray = [districtID]
# gerryArray = [best_gerry]
# for planID in planIDArray:
#     if planID >= 0:
#         distArray += [districtID]
#         gerry_dist_plan = 0.0
#         for prec in theDistrict:
#             [avg_norm_prec_plan] = analysis_avg.loc[analysis_avg['Node']==prec,'%s'%(planID)] # VAR GS
#             gerry_dist_plan += float(avg_norm_prec_plan)
#         gerryArray += [gerry_dist_plan]
#         print(districtID, planID, gerry_dist_plan)    
#     
# analysisTable = pd.DataFrame(list(zip(distArray,planIDArray,gerryArray)),columns =['district 2010','planID','gerry'])
# analysisTable.to_csv(r'analysis_2010_district%s.csv'%(districtID), index = False)#Check
# =============================================================================



