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
    A['rho','Z[%s]'%(j)] = 1
    for u in feasSolution['Node']:
        A['pie[%s]'%(u),'Z[%s]'%(j)] = 0
        [district_u] = feasSolution.loc[feasSolution['Node']==u, 'District']
        if district_u == j:
            A['pie[%s]'%(u),'Z[%s]'%(j)] = 1
       
gerry= {}
for i in range(numDistricts):        
    gerry[i] = md.gerryscoreLP(G.subgraph(district[i]))
    #print('###',i,gerry[i])

c = {}
for j in range(numDistricts):
    c['Z[%s]'%j] = gerry[j]
    #print(j,c['Z[%s]'%j])
    
b = {}
b['rho'] = numDistricts
for i in nodes['Node']:
    b['pie[%s]'%i] = 1

numColumns = numDistricts    

optimality = False    
while optimality == False:
    print()

    master = md.restrictedMasterNew(c,A,numColumns,numDistricts,nodes,b)
    
    print('###',numColumns,master.objVal)
    
    dual = {}
    rho0 = {}
    for constraint in master.getConstrs():
        dual[constraint.ConstrName] = constraint.Pi
        if constraint.ConstrName == 'rho':
            rho0 = constraint.Pi
    
    largeRhoName = 'rho'
    largeRhoVal = rho0
    subproblem = md.solveSubproblem(dual,G,lower,upper)
    
    newDistrict = []
    for v in subproblem.getVars():
        if v.varname[0] == 'X':
            if v.x > 1 - 0.1:
                #print(v.varname, '=', v.x)
                varName = v.varname[2:-1].split(',')
                newDistrict += [int(varName[0])]
    print('### new disrict=',largeRhoName,newDistrict)
    
    minRC = subproblem.objVal - largeRhoVal
    print('### reduced cost =',minRC)
    
    if minRC < - 0.000001:
        optimality = False
    else:
        optimality = True
        
    if optimality == False:
        A['rho','Z[%s]'%numColumns] = 1
        
        for i in nodes['Node']:
            A['pie[%s]'%i,'Z[%s]'%numColumns] = 0

        for i in newDistrict:
            A['pie[%s]'%i,'Z[%s]'%numColumns] = 1
            
        c['Z[%s]'%numColumns] = md.gerryscoreLP(G.subgraph(newDistrict))
            
        numColumns += 1
    
intMasterNew = md.intMasterNew(c,A,numColumns,numDistricts,nodes,b)
print('### Complete Column Generation')
print('### Optimality = ',optimality)
print('### Integer Solution =',intMasterNew.objVal)    









