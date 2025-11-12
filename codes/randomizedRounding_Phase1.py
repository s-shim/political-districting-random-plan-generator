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

halfX = {}    
for u in G.nodes():
    for g in range(numDistricts):
        halfX[u,g] = 0.5

ptbX = md.PTBX(halfX,numDistricts,G)

RMSD = md.RMSD(halfX,numDistricts,G)

district = md.ROUND(ptbX,numDistricts,G)

# =============================================================================
# for i in range(numDistricts):
#     print(i,district[i])
#     
# zeroX = {}
# for i in range(numDistricts):
#     for u in G.nodes():
#         zeroX[u,i] = 0
#         
# intX=copy.deepcopy(zeroX)
# for i in range(numDistricts):
#     for u in district[i]:
#         zeroX[u,i] = 1
# 
# int_district = md.ROUND(intX,numDistricts,G)
# =============================================================================

totalPopulation = 0
for i in range(numDistricts):
    for u in district[i]:
        totalPopulation += G.nodes[u]['population']
        
averagePopulation = totalPopulation / numDistricts
lower = averagePopulation - (averagePopulation * tolerance)
upper = averagePopulation + (averagePopulation * tolerance)

totalError = md.EQERROR(district,lower,upper,numDistricts,G)

bestDistrict = copy.deepcopy(district)
bestTrial = 0
bestError = totalError    
trial = 0
print(trial,totalError)


seed = copy.deepcopy(halfX)
nLocal = 0
move = True
for trial in range(1,totalTrials):
    ptbX = md.PTBX(seed,numDistricts,G)    
    RMSD = md.RMSD(seed,numDistricts,G)    
    district = md.ROUND(ptbX,numDistricts,G)
    totalError = md.EQERROR(district,lower,upper,numDistricts,G)          

    same = True
    for g in range(numDistricts):
        if same == False:
            break
        for u in bestDistrict[g]:
            if u not in district[g]:
                same = False
                break

    if same == True:
        nLocal += 1
        move = True
        if random.random() < min(1, nLocal/20) * RMSD:
            seed = copy.deepcopy(halfX)
            nLocal = 0
            move = False
    else:
        nLocal = 0
        move = True
        if bestError > totalError:
            bestError = totalError
            bestTrial = trial
            bestDistrict = copy.deepcopy(district)
            print(bestTrial,bestError)
            if abs(bestError - 0) < 1e-6:
                districtArray = []
                nodeArray = []
                for g in range(numDistricts):
                    for u in bestDistrict[g]:
                        districtArray += [g]
                        nodeArray += [u]
                feasSolution = pd.DataFrame(list(zip(districtArray, nodeArray)),columns =['District', 'Node'])
                feasSolution.to_csv(r'feas_MD_sophisticatedFinal.csv', index = False)#Check


    if move == True:
        alpha = 1 / (1 + math.exp(4 * RMSD))
        for g in range(numDistricts):
            for u in G.nodes():
                seed[u,g] = (1 - alpha) * seed[u,g]

        for g in range(numDistricts):
            for u in bestDistrict[g]:
                seed[u,g] += alpha * 1






