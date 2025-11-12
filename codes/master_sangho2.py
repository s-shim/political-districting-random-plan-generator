import pandas as pd
import networkx as nx
import myDictionary as md
import copy
import random
import math
from gurobipy import *

numDistricts = 8 
tolerance = 0.05
lines = pd.read_csv('lines_MD_sophisticatedFinal.csv')
nodes = pd.read_csv('nodes_MD_sophisticatedFinal.csv')
feasSolution = pd.read_csv('feas_MD_sophisticatedFinal.csv')



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

for u in feasSolution['Node']:
    [district_u] = feasSolution.loc[feasSolution['Node']==u,'District'] 
    district[district_u] += [u]     

totalPopulation = 0
for i in range(numDistricts):
    for u in district[i]:
        totalPopulation += G.nodes[u]['population']
        
averagePopulation = totalPopulation / numDistricts
lower = averagePopulation - (averagePopulation * tolerance)
upper = averagePopulation + (averagePopulation * tolerance)



A = {}
for j in range(numDistricts):
    for i in range(numDistricts):
        A['rho[%s]'%i,'Z[%s]'%j] = 0
        if i == j:
            A['rho[%s]'%i,'Z[%s]'%j] = 1
    for u in nodes['Node']:
        A['pie[%s]'%u,'Z[%s]'%j] = 0
    for u in feasSolution['Node']:
        [district_u] = feasSolution.loc[feasSolution['Node']==u,'District']
        if district_u == j:
            A['pie[%s]'%u,'Z[%s]'%j] = 1
            
gerry = {}            
for i in range(numDistricts):            
    gerry[i] = md.gerryScoreLP(G.subgraph(district[i]))

c = {}
for j in range(numDistricts):
    c['Z[%s]'%j] = gerry[j]
    

#########
b = {}
for i in range(numDistricts):
    b['rho[%s]'%i] = 1
for u in nodes['Node']:
    b['pie[%s]'%u] = 1



numColumns = numDistricts
lastDistrict = numDistricts - 1
i_minReducedCost_OLD = -2
minReducedCost_OLD = -2
oldDistrict = [-1]

cycling = False
optimality = False
while optimality == False and cycling == False:
    master = Model('Master Problem')
    master.setParam("OutputFlag", 0)
    master = md.solveMaster(master,A,c,b,numDistricts,numColumns,nodes)
    
    print()
    print('###')
    print('numColumns=',numColumns)
    print('master.objVal=',master.objVal)    
    
    dual = {}
    for constraint in master.getConstrs():
        dual[constraint.ConstrName] = constraint.Pi
        #print(constraint.ConstrName,constraint.Pi)
    
    subproblem = md.subProblem(dual,lower,upper,G)    
    newDistrict = []
    for v in subproblem.getVars():
        if v.varname[0] == 'X':
            if v.x > 1 - 0.1:
                print(v.varname, '=', v.x)
                varName = v.varname[2:-1].split(',')
                newDistrict += [int(varName[0])]
    print('newDistrict=',newDistrict)
    newPopulation = 0
    for i in newDistrict:
        newPopulation += G.nodes[i]['population']
    print(lower,newPopulation,upper)
    
    i_minReducedCost = -1
    minReducedCost = 0
    reducedCost = {}
    for i in range(numDistricts):
        reducedCost[i] = subproblem.objVal - dual['rho[%s]'%i]
        if minReducedCost > reducedCost[i]:
            minReducedCost = reducedCost[i]
            i_minReducedCost = i
            
    if minReducedCost > - 0.0000001:
        optimality = True
        break
    else:
        optimality = False

# =============================================================================
#     randomDistricts = list(range(numDistricts))
#     random.shuffle(randomDistricts)
#     for i in randomDistricts:
#         districtID = i
#         if reducedCost[districtID] < -0.000001:
#             print('reducedCost[%s]='%districtID, reducedCost[districtID])
#             for k in range(numDistricts):
#                 A['rho[%s]'%k,'Z[%s]'%numColumns] = 0
#             A['rho[%s]'%districtID,'Z[%s]'%numDistricts] = 1
#             for u in nodes['Node']:
#                 A['pie[%s]'%u,'Z[%s]'%numColumns] = 0
#             for u in newDistrict:
#                 A['pie[%s]'%u,'Z[%s]'%numColumns] = 1
#             c['Z[%s]'%numColumns] = md.gerryScoreLP(G.subgraph(newDistrict))
#             numColumns += 1
#             break
# =============================================================================

    same = False            
    if i_minReducedCost_OLD == i_minReducedCost:
        if int(minReducedCost_OLD * 10 ** 6 + 0.5) == int(minReducedCost * 10 ** 6 + 0.5):
            if len(newDistrict) == len(oldDistrict):
                same == True
                for u in newDistrict:
                    if u not in oldDistrict:
                        same == False
                        break
            
    print('same=',same)
    print('optimality=',optimality)
    
    if same == False and optimality == False:
        districtID = i_minReducedCost
        print('reducedCost[%s]='%districtID, reducedCost[districtID])
        for k in range(numDistricts):
            A['rho[%s]'%k,'Z[%s]'%numColumns] = 0
        A['rho[%s]'%districtID,'Z[%s]'%numDistricts] = 1
        for u in nodes['Node']:
            A['pie[%s]'%u,'Z[%s]'%numColumns] = 0
        for u in newDistrict:
            A['pie[%s]'%u,'Z[%s]'%numColumns] = 1
        c['Z[%s]'%numColumns] = md.gerryScoreLP(G.subgraph(newDistrict))
        numColumns += 1
        i_minReducedCost_OLD = i_minReducedCost
        minReducedCost_OLD = minReducedCost
        oldDistrict = copy.deepcopy(newDistrict)

    if same == True and optimality == False:
        cycling = True

        randomDistricts = list(range(numDistricts))
        randomDistricts.remove(i_minReducedCost)
        random.shuffle(randomDistricts)

        for i in randomDistricts:
            districtID = i
            if reducedCost[districtID] < -0.000001:
                cycling = False                    
                print('reducedCost[%s]='%districtID, reducedCost[districtID])
                for k in range(numDistricts):
                    A['rho[%s]'%k,'Z[%s]'%numColumns] = 0
                A['rho[%s]'%districtID,'Z[%s]'%numDistricts] = 1
                for u in nodes['Node']:
                    A['pie[%s]'%u,'Z[%s]'%numColumns] = 0
                for u in newDistrict:
                    A['pie[%s]'%u,'Z[%s]'%numColumns] = 1
                c['Z[%s]'%numColumns] = md.gerryScoreLP(G.subgraph(newDistrict))
                numColumns += 1
                i_minReducedCost_OLD = districtID
                minReducedCost_OLD = reducedCost[districtID]
                oldDistrict = copy.deepcopy(newDistrict)
                break
            
print('optimality=',optimality)
            
            
