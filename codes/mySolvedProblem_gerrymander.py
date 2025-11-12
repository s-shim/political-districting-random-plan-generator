import pandas as pd
import networkx as nx
from gurobipy import *

numDistricts = 8 
tolerance = 0.05
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
    
model = Model('Gerrymander')

#creating variables to check for connectivity
x_vars = []
x_names = []
for u in G.nodes():
    for g in G.nodes():
        x_vars += [(u,g)]
        x_names += ['X[%s,%s]'%(u,g)]
X = model.addVars(x_vars, vtype = GRB.BINARY, name = x_names)

y_vars = []
y_names = []
for (u, v) in G.edges():
    for g in G.nodes():
        y_vars += [(u,v,g)]
        y_names += ['Y[%s,%s,%s]' %(u,v,g)]
Y = model.addVars(y_vars, vtype = GRB.BINARY, name = y_names)

f_vars = []
f_names = []
for (u, v) in G.edges():
    for g in G.nodes():
        f_vars += [(u,v,g)]
        f_names += ['F[%s,%s,%s]'%(u,v,g)]
        
        f_vars += [(v,u,g)]
        f_names += ['F[%s,%s,%s]'%(v,u,g)]
F = model.addVars(f_vars, vtype = GRB.INTEGER, name = f_names)

#constraints
#Partition
for u in G.nodes():
    LHS = []
    for g in G.nodes:
        LHS += [(1,X[u,g])]
    model.addConstr(LinExpr(LHS)==1, name='Eq.partition(%s)'%u)
    
#Number of Districts
LHS = []
for g in G.nodes():
    LHS += [(1,X[g,g])]
model.addConstr(LinExpr(LHS)==numDistricts, name='Eq.numDistricts')

# X[u,g] <= X[g,g]
for g in G.nodes():
    for u in G.nodes():
        LHS = [(1,X[u,g]),(-1,X[g,g])]
        model.addConstr(LinExpr(LHS)<=0, name='Eq.X[u,g]<=X[g,g](%s,%s)'%(u,g))
  
#y <= x
for (u,v) in G.edges():
    for g in G.nodes():
        LHS1 = [(1,Y[u,v,g]),(-1,X[u,g])]
        LHS2 = [(1,Y[u,v,g]),(-1,X[v,g])]
        model.addConstr(LinExpr(LHS1)<=0, name='Eq.Y<=X1(%s,%s,%s)'%(u,v,g))
        model.addConstr(LinExpr(LHS2)<=0, name='Eq.Y<=X2(%s,%s,%s)'%(u,v,g))
        
# Y >= F
for (u,v) in G.edges():
    for g in G.nodes():
        LHS = [(1,F[u,v,g]),(1,F[v,u,g]),(-len(G.nodes)+numDistricts,Y[u,v,g])]
        model.addConstr(LinExpr(LHS)<=0, name='Eq.F<=Y(%s,%s,%s)'%(u,v,g))
        
# F[u,g,g] = 0
for (u,v) in G.edges():
    for g in G.nodes():
        if v == g:
            LHS = [(1,F[u,v,g])]
            model.addConstr(LinExpr(LHS)==0, name='Eq.F[u,g,g] = 0(%s,%s,%s)'%(u,v,g))
        if u == g:
            LHS = [(1,F[v,u,g])]
            model.addConstr(LinExpr(LHS)==0, name='Eq.F[v,g,g] = 0(%s,%s,%s)'%(u,v,g))

# sum_v F[g,v,g] = sum_(u!=g) X[u,g]
for g in G.nodes():
    LHS = []
    for (u,v) in G.edges():
        if u == g:
            LHS += [(1,F[u,v,g])]
        if v == g:
            LHS += [(1,F[v,u,g])]
    for u in G.nodes():
        if u != g:
            LHS += [(-1,X[u,g])]
    model.addConstr(LinExpr(LHS)==0, name='Eq.SUM F[g,v,g](%s)'%(g))
            
# Flow Conservative
for g in G.nodes():
    for u in G.nodes():
        if u != g:
            LHS = [(-1,X[u,g])]
            for (i,j) in G.edges():
                if i == u:
                    LHS += [(1,F[j,i,g])]
                    LHS += [(-1,F[i,j,g])]
                if j == u:
                    LHS += [(-1,F[j,i,g])]
                    LHS += [(1,F[i,j,g])]
            model.addConstr(LinExpr(LHS)==0, name='Eq.FlowConservative(%s,%s)'%(g,u))
                
# Equal Population Constraint: 
## Calculate Average Population
totalPopulation = 0
for node in G.nodes():
    population = G.nodes[node]['population']
    totalPopulation += population            
avgPopulation = totalPopulation / numDistricts

## Upper Bound Population: sum_u population_u X[u,g] <= avgPopulation * (1 + tolerance) X[g,g]
for g in G.nodes():
    LHS = [(-avgPopulation * (1 + tolerance),X[g,g])]
    for u in G.nodes():
        LHS += [(G.nodes[u]['population'],X[u,g])]
    model.addConstr(LinExpr(LHS)<=0, name='Eq.UpperBoundPopulation(%s)'%(g))

## Lower Bound Population: sum_u population_u X[u,g] >= avgPopulation * (1 - tolerance) X[g,g]
for g in G.nodes():
    LHS = [(-avgPopulation * (1 - tolerance),X[g,g])]
    for u in G.nodes():
        LHS += [(G.nodes[u]['population'],X[u,g])]
    model.addConstr(LinExpr(LHS)>=0, name='Eq.LowerBoundPopulation(%s)'%(g))    
           
# =============================================================================
# ## Must Link
# mustlink = pd.read_csv('mustLink_MD_sophisticatedFinal.csv')    
# for ml in mustlink['LinkMust']:
#     [Source_Link] = mustlink.loc[mustlink['LinkMust']==ml,'Source_Link']
#     [Target_Link] = mustlink.loc[mustlink['LinkMust']==ml,'Target_Link']
#     for g in G.nodes():
#         LHS = [(1,X[Source_Link,g]),(-1,X[Target_Link,g])]
#         model.addConstr(LinExpr(LHS)==0, name='Eq.MustLink(%s,%s,%s)'%(Source_Link,Target_Link,g))    
# =============================================================================
    
#Objective: Gerrymander Score
objTerms = []
for (u,v) in G.edges():
    for g in G.nodes():
        objTerms += [(1,F[u,v,g])]
        objTerms += [(1,F[v,u,g])]
model.setObjective(LinExpr(objTerms), GRB.MINIMIZE)

model.update()
model.optimize()

# read the optimal solution
variableName = []
variableValue = []
district = {}
for g in range(numDistricts):
    district[g] = []
    
for v in model.getVars():
    variableName += [v.varname]
    variableValue += [v.x]
    if v.x > 0.9 and v.varname[0] == 'X':
        pair = v.varname[2:-1].split(',')
        print(pair[0],pair[1])
        district[pair[1]] += [pair[0]]


optSolution = pd.DataFrame(list(zip(variableName, variableValue)),columns =['varName', 'varVal'])
optSolution.to_csv(r'opt_MD_sophisticatedFinal.csv', index = False)#Check

        
totalGerry = 0
for g in range(numDistricts):
    subG = G.subgraph(district[g])
    gerry_g = len(G.nodes) * len(G.edges)
    for c in subG.nodes():
        distance = 0
        for d in subG.nodes():
            if d != c:
                distance += nx.shortest_path_length(subG, source = c, target = d)
        if gerry_g > distance:
         gerry_g = distance
    totalGerry += gerry_g
print(totalGerry)
