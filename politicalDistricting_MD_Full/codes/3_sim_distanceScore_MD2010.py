import pandas as pd
import networkx as nx
# from gurobipy import *
import math
import os
import glob
import copy

numDistricts = 8 
tolerance = 0.05
lines = pd.read_csv('../precinct2010_lines_revised.csv')
nodes = pd.read_csv('precinct2010_distanceScore.csv')       

planIDArray = []
for name in glob.glob('sim*feas*.csv'):
    planID = int(name[3:7])
    planIDArray += [planID]
    
planIDArray = sorted(planIDArray)

simIDArray = []
for planID in planIDArray:
    if str(planID) in nodes.columns:
        print('exists',planID)
    else:
        simIDArray += [planID]

print('len(simIDArray) =',len(simIDArray))        

G = nx.Graph()

#Using networkx to create the graph
for l in lines['Line']:
    [Source] = lines.loc[lines['Line'] == l, 'Source']
    [Target] = lines.loc[lines['Line'] == l, 'Target']
    G.add_edge(Source,Target)    

for simID in simIDArray:
    print()
    print('### simID =',simID)    
    randomPlan = pd.read_csv('sim%s_feas_MD_sophisticatedFinal_core0_sol0.csv'%simID)
    
    district = {}
    for districtID in range(8):
        district[districtID] = []
        
    districtFunction = {}
    for precinctID in randomPlan['Node']:
        [district_precinct] = randomPlan.loc[randomPlan['Node']==precinctID,'District']
        district_precinct = int(district_precinct)
        district[district_precinct] += [precinctID]
        districtFunction[precinctID] = district_precinct
            
    subG = {}
    grandFunction = {}
    for districtID in range(8):
        subG[districtID] = nx.Graph(G.subgraph(district[districtID]))
        
        # calculate gerry score and normalized gerry score
        best_gerry = -1
        gerryFunction = {}        
        for c in subG[districtID].nodes():
            gerry_c = 0
            gerryFunction[c] = 0
            for d in subG[districtID].nodes():
                if c != d:
                    distance_c_d = nx.shortest_path_length(subG[districtID], source=c, target=d)
                    gerry_c += distance_c_d
                    gerryFunction[d] = distance_c_d
            if best_gerry < 0:
                best_gerry = gerry_c
                best_c = c
                bestFunction = copy.deepcopy(gerryFunction)
                
            if best_gerry > gerry_c:
                best_gerry = gerry_c
                best_c = c
                bestFunction = copy.deepcopy(gerryFunction)

        for prec in subG[districtID].nodes():
            grandFunction[prec] = bestFunction[prec]

        print()    
        print('planID =',simID)
        print('districtID =',districtID)
        print('gerry score =',best_gerry)
        
    distanceScore = []
    for prec in nodes['Node']:
        distanceScore += [grandFunction[prec]]
        
    nodes['%s'%simID] = distanceScore
    nodes.to_csv(r'precinct2010_distanceScore.csv', index = False)#Check
    
    


