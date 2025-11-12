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
    for u in feasSolution['Node']:
        A['pie[%s]'%u,'Z[%s]'%j] = 0
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
for u in feasSolution['Node']:
    b['pie[%s]'%u] = 1



numColumns = numDistricts
lastDistrict = numDistricts - 1

optimality = False
while optimality == False:
    master = Model('Master Problem')
    master.setParam("OutputFlag", 0)
    
    z_vars = []
    z_names = []
    for j in range(numColumns):
        z_vars += [(j)]
        z_names += ['Z[%s]'%j]
    Z = master.addVars(z_vars, vtype = GRB.CONTINUOUS, name = z_names)
    
    
    for i in range(numDistricts):
        LHS = []
        for j in range(numColumns):
            LHS += [(A['rho[%s]'%i,'Z[%s]'%j],Z[j])]
        master.addConstr(LinExpr(LHS) == b['rho[%s]'%i], name='rho[%s]'%i)
        
    for i in nodes['Node']:
        LHS = []
        for j in range(numColumns):
            LHS += [(A['pie[%s]'%i,'Z[%s]'%j],Z[j])]
        master.addConstr(LinExpr(LHS) == b['pie[%s]'%i], name='pie[%s]'%i)
            
    objTerms = []
    for j in range(numColumns):
        objTerms += [(c['Z[%s]'%j],Z[j])]
    master.setObjective(LinExpr(objTerms), GRB.MINIMIZE)
    
    master.update()
    master.optimize()
    
    print()
    print('###')
    print('numColumns=',numColumns)
    print('master.objVal=',master.objVal)    
    
    dual = {}
    for constraint in master.getConstrs():
        dual[constraint.ConstrName] = constraint.Pi
    
    subproblem = md.subProblem(dual,lower,upper,G)
    
    newDistrict = []
    for v in subproblem.getVars():
        if v.varname[0] == 'X':
            if v.x > 1 - 0.000001:
                varName = v.varname[2:-1].split(',')
                newDistrict += [int(varName[0])]
    
    optimality = True
    for i in range(numDistricts):
        if subproblem.objVal - dual['rho[%s]'%((lastDistrict + i + 1) % numDistricts)] < - 0.000001:
            optimality = False
            newDistrictID = (lastDistrict + i + 1) % numDistricts
            minReducedCost = subproblem.objVal - dual['rho[%s]'%((lastDistrict + i + 1) % numDistricts)]
            optimality == False
            lastDistrict = newDistrictID
            break
    
    if optimality == False:
        for i in range(numDistricts):
            A['rho[%s]'%i,'Z[%s]'%numColumns] = 0
            if i == newDistrictID:
                A['rho[%s]'%i,'Z[%s]'%numColumns] = 1
        for i in nodes['Node']:
            A['pie[%s]'%i,'Z[%s]'%numColumns] = 0        
        for i in newDistrict:
            A['pie[%s]'%i,'Z[%s]'%numColumns] = 1
               
        gerry_newDistrict = md.gerryScoreLP(G.subgraph(newDistrict))
        c['Z[%s]'%numColumns] = gerry_newDistrict
        print('minReducedCost=',minReducedCost)
        print('newDistrictID=',newDistrictID)
        print('gerry_newDistrict=',gerry_newDistrict)
        print('newDistrict=',newDistrict)
        
        numColumns += 1
        
        
    
