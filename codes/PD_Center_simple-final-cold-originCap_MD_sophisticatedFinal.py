import numpy as np
from numpy import random
from itertools import *
from gurobipy import *
import pandas as pd
import networkx as nx

#Input: number of districs, tolerance on population
howManyDistricts = 8
populationError = 0.05

#Construct graphs
##G underlying network
##compG complete graph on the nodes of G
##H complete graph on the districts including dummy 0
##Hplus complete graph on the districts 1,2,...,howManyDistricts
##lowerbound (lbPopulation) and uppbound (ubPopulation) of population = tolerable deviation (populationError) from meanPopulation 
G = nx.Graph()
compG = nx.Graph()
H = nx.Graph()
Hplus = nx.Graph()

nodes = pd.read_csv('nodes_MD_sophisticatedFinal.csv')
meanPopulation = nodes['population'].sum()/howManyDistricts
ubPopulation = meanPopulation * (1 + populationError)
lbPopulation = meanPopulation * (1 - populationError)

lines = pd.read_csv('lines_MD_sophisticatedFinal.csv')
for l in lines['Line']:
    [Source_l] = lines.loc[lines['Line'] == l,'Source']
    [Target_l] = lines.loc[lines['Line'] == l,'Target']
    G.add_edge(Source_l,Target_l)
    
compG.add_nodes_from(G.nodes())
compG.add_edges_from(itertools.combinations(compG.nodes(), 2))        

for districtNumber in range(howManyDistricts+1):
    H.add_node(districtNumber)
    if districtNumber != 0:
        Hplus.add_node(districtNumber)
H.add_edges_from(itertools.combinations(H.nodes(), 2))        
Hplus.add_edges_from(itertools.combinations(Hplus.nodes(), 2))        


#set parameters and start developing formulation
print(GRB.VERSION_MAJOR, GRB.VERSION_MINOR, GRB.VERSION_TECHNICAL)
model = Model('Political Districting')
model.setParam('Threads', 80)
model.setParam('Method', 3)
model.setParam('Cuts', 3)
model.setParam('MIPFocus', 3)
model.setParam('SolFiles', "simpleCold_MDsophFinal_mymodel")


#Employ variables############################################################
## Variable 1) node variable X[v,j] indicating node v belongs to district j
X = model.addVars(G.nodes(), H.nodes(), vtype=GRB.BINARY, name='X')
centerX = model.addVars(G.nodes(), H.nodes(), vtype=GRB.BINARY, name='centerX')

## Variable 2) edge variable ZJ[(u,ju),(v,jv)] indicating extended edge [(u,ju),(v,jv)]; u belongs to ju, and v belongs to jv 
zjvars = [((u,ju),(v,jv)) for (u,v), ju, jv in product(G.edges(), H.nodes(), H.nodes())]
zjnames = ['ZJ[(%s,%s),(%s,%s)]'%(u,ju,v,jv) for (u,v), ju, jv in product(G.edges(), H.nodes(), H.nodes())]
ZJ = model.addVars(zjvars, vtype=GRB.BINARY, name=zjnames)

## Variable 3) edge variable compZJ[(u,ju),(v,jv)] between centerX and X on complete graph compG 
compzjvars1 = [((u,ju),(v,jv)) for (u,v), ju, jv in product(compG.edges(), H.nodes(), H.nodes())]
compzjvars2 = [((v,jv),(u,ju)) for (u,v), ju, jv in product(compG.edges(), H.nodes(), H.nodes())]
compzjnames1 = ['compZJ[(%s,%s),(%s,%s)]'%(u,ju,v,jv) for (u,v), ju, jv in product(compG.edges(), H.nodes(), H.nodes())]
compzjnames2 = ['compZJ[(%s,%s),(%s,%s)]'%(v,jv,u,ju) for (u,v), ju, jv in product(compG.edges(), H.nodes(), H.nodes())]
compzjvars = compzjvars1 + compzjvars2
compzjnames = compzjnames1 + compzjnames2
#compZJ = model.addVars(compzjvars, vtype=GRB.BINARY, name=compzjnames)

## Variable 4) path flow variables F[(i1,i2),(u,v)] and F[(i1,i2),(v,u)] on edge uv to connect center node i1 to node i2
fvars1 = [(j,(i1,i2),(u,v)) for (u,v), (i1,i2), j in product(G.edges(), compG.edges(), Hplus.nodes())]
fvars2 = [(j,(i1,i2),(v,u)) for (u,v), (i1,i2), j in product(G.edges(), compG.edges(), Hplus.nodes())]
fvars3 = [(j,(i2,i1),(u,v)) for (u,v), (i1,i2), j in product(G.edges(), compG.edges(), Hplus.nodes())]
fvars4 = [(j,(i2,i1),(v,u)) for (u,v), (i1,i2), j in product(G.edges(), compG.edges(), Hplus.nodes())]
fnames1 = ['F[%s,(%s,%s),(%s,%s)]'%(j,i1,i2,u,v) for (u,v), (i1,i2), j in product(G.edges(), compG.edges(), Hplus.nodes())]
fnames2 = ['F[%s,(%s,%s),(%s,%s)]'%(j,i1,i2,v,u) for (u,v), (i1,i2), j in product(G.edges(), compG.edges(), Hplus.nodes())]
fnames3 = ['F[%s,(%s,%s),(%s,%s)]'%(j,i2,i1,u,v) for (u,v), (i1,i2), j in product(G.edges(), compG.edges(), Hplus.nodes())]
fnames4 = ['F[%s,(%s,%s),(%s,%s)]'%(j,i2,i1,v,u) for (u,v), (i1,i2), j in product(G.edges(), compG.edges(), Hplus.nodes())]
fvars = fvars1 + fvars2 + fvars3 + fvars4
fnames = fnames1 + fnames2 + fnames3 + fnames4
F = model.addVars(fvars, vtype=GRB.BINARY, name=fnames)

## Variable 5) Arborescence (Tree) variable rooted at the center of a district 
lbDiTreeEdge_vars1 = [(j,(u,v)) for j, (u,v) in product(Hplus.nodes(), G.edges())]
lbDiTreeEdge_vars2 = [(j,(v,u)) for j, (u,v) in product(Hplus.nodes(), G.edges())]
lbDiTreeEdge_names1 = ['lbDiTreeEdge[%s,(%s,%s)]'%(j,u,v) for j, (u,v) in product(Hplus.nodes(), G.edges())]
lbDiTreeEdge_names2 = ['lbDiTreeEdge[%s,(%s,%s)]'%(j,v,u) for j, (u,v) in product(Hplus.nodes(), G.edges())]
lbDiTreeEdge_vars = lbDiTreeEdge_vars1 + lbDiTreeEdge_vars2
lbDiTreeEdge_names = lbDiTreeEdge_names1 + lbDiTreeEdge_names2
#lbDiTreeEdge = model.addVars(lbDiTreeEdge_vars, vtype=GRB.BINARY, name=lbDiTreeEdge_names) 

## Variable 6) Cost variable at district j
costV = model.addVars(Hplus.nodes(), vtype=GRB.CONTINUOUS, name='costV')

## Variable Options
X.BranchPriority = 1
centerX.BranchPriority = 2


#Add Constraints####################################################################################
## Essential Constraints 
### Essential Constraints 1) Boundary constraints            
#### Essential Constraints 1-1) Boundary constraints: node cannot belong to dummy district            
for v in G.nodes():
    lexpr = LinExpr([(1, X[v,0])])
    model.addConstr(lexpr==0, name='Eq(BoundaryX)(%s)'%(v))

#### Essential Constraints 1-2) Boundary constraints: a center node must belong to the district            
for v in G.nodes():
    for j in H.nodes():
        if j != 0:
            lexpr = []
            lexpr += [(1, X[v,j])]
            lexpr += [(-1, centerX[v,j])]
            model.addConstr(LinExpr(lexpr)>=0, name='Eq(RelationXcenterX)(%s,%s)'%(v,j))

### Essential Constraints 2) Partition Equations            
#### Essential Constraints 2-1) Partition Equations on centerX: center belongs to one of the districts. If the node is not a center, it will belong to dummy district.             
for v in G.nodes():
    lexpr = LinExpr([(1, centerX[v,jv]) for jv in H.nodes()])
    model.addConstr(lexpr==1, name='Eq(centerPE)(%s)'%(v))

for j in H.nodes():
    if j != 0:
        lexpr = []
        for v in G.nodes():
            lexpr += [(1, centerX[v,j])]
        model.addConstr(LinExpr(lexpr)==1, name='Eq(centerPEtotal)(%s)'%(j))

#### Essential Constraints 2-2) Partition Equations on X: every node belongs to one district  
for v in G.nodes():
    lexpr = LinExpr([(1, X[v,jv]) for jv in H.nodes()])
    model.addConstr(lexpr==1, name='Eq(PE)(%s)'%(v))
    
### Essential Constraints 3) Bundle Equations
#### Essential Constraints 3-1) Bundle Equations on X 
for u,v in G.edges():
  for ju in H.nodes():
    lexpr = LinExpr([(1, X[u,ju])] + [(-1, ZJ[(u,ju),(v,jv)]) for jv in H.nodes()])
    model.addConstr(lexpr==0, name='Eq(BEL)((%s,%s),%s)'%(u,ju,v))
  for jv in H.nodes():
    lexpr = LinExpr([(1, X[v,jv])] + [(-1, ZJ[(u,ju),(v,jv)]) for ju in H.nodes()])
    model.addConstr(lexpr==0, name='Eq(BER)((%s,%s),%s)'%(v,jv,u))
        
#### Essential Constraints 3-2) Bundle Equations between centerX and X on compG ; compZJ[(u,j),(v,j)] = flow value from centerX[u,j] to X[v,j] 
# =============================================================================
# for u,v in compG.edges():
#   for ju in H.nodes():
#     lexpr = LinExpr([(1, centerX[u,ju])] + [(-1, compZJ[(u,ju),(v,jv)]) for jv in H.nodes()])
#     model.addConstr(lexpr==0, name='Eq(compBEO)((%s,%s),%s)'%(u,ju,v))
#   for jv in H.nodes():
#     lexpr = LinExpr([(1, X[v,jv])] + [(-1, compZJ[(u,ju),(v,jv)]) for ju in H.nodes()])
#     model.addConstr(lexpr==0, name='Eq(compBED)((%s,%s),%s)'%(v,jv,u))
# 
#   for ju in H.nodes():
#     lexpr = LinExpr([(1, X[u,ju])] + [(-1, compZJ[(v,jv),(u,ju)]) for jv in H.nodes()])
#     model.addConstr(lexpr==0, name='Eq(compBED)((%s,%s),%s)'%(u,ju,v))
#   for jv in H.nodes():
#     lexpr = LinExpr([(1, centerX[v,jv])] + [(-1, compZJ[(v,jv),(u,ju)]) for ju in H.nodes()])
#     model.addConstr(lexpr==0, name='Eq(compBEO)((%s,%s),%s)'%(v,jv,u))
# =============================================================================
      
### Essential Constraints 4) Path Flow
#### Essential Constraints 4-1) Flow <= ZJ
for j in Hplus.nodes():
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:                    
                for (u,v) in G.edges():
                    lexpr = [(-1,ZJ[(u,j),(v,j)])]
                    lexpr += [(1,F[j,(i1,i2),(v,u)])]
                    lexpr += [(1,F[j,(i1,i2),(u,v)])]
                    model.addConstr(LinExpr(lexpr)<=0, name='Eq(Fcap)(%s,(%s,%s),(%s,%s))'%(j,i1,i2,u,v))
    
# =============================================================================
# #### Essential Constraints 4-2) Out-Flow Value = compZJ[(i1,j),(i2,j)] 
# for j in Hplus.nodes():
#     for i1 in G.nodes():
#         for i2 in G.nodes():
#             if i1 != i2:
#                 lexpr = [(-1,compZJ[(i1,j),(i2,j)])]
#                 for u,v in G.edges():
#                     if u == i1:
#                         lexpr += [(1,F[j,(i1,i2),(u,v)])]
#                     if v == i1:
#                         lexpr += [(1,F[j,(i1,i2),(v,u)])]
#                 
#                 model.addConstr(LinExpr(lexpr)==0, name='Eq(Fout)(%s,%s,%s)'%(j,i1,i2))
#                 
# #### Essential Constraints 4-2) In-Flow Value = compZJ[(i1,j),(i2,j)] 
# for j in Hplus.nodes():
#     for i1 in G.nodes():
#         for i2 in G.nodes():
#             if i1 != i2:
#                 lexpr = [(-1,compZJ[(i1,j),(i2,j)])]
#                 for u,v in G.edges():
#                     if v == i2:
#                         lexpr += [(1,F[j,(i1,i2),(u,v)])]
#                     if u == i2:
#                         lexpr += [(1,F[j,(i1,i2),(v,u)])]
#                 
#                 model.addConstr(LinExpr(lexpr)==0, name='Eq(Fin)(%s,%s,%s)'%(j,i1,i2))
# =============================================================================

#### Essential Constraints 4-2) Simple: outflow = inflow
for j in Hplus.nodes():
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:
                lexpr = []
                for u,v in G.edges():
                    if u == i1:
                        lexpr += [(-1,F[j,(i1,i2),(u,v)])]
                    if v == i1:
                        lexpr += [(-1,F[j,(i1,i2),(v,u)])]
                    if v == i2:
                        lexpr += [(1,F[j,(i1,i2),(u,v)])]
                    if u == i2:
                        lexpr += [(1,F[j,(i1,i2),(v,u)])]
                
                model.addConstr(LinExpr(lexpr)==0, name='Eq(Fout=Fin)(%s,%s,%s)'%(j,i1,i2))
                
#### Essential Constraints 4-2) Simple: inflow
for j in Hplus.nodes():
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:
                lexpr = [(-1,centerX[i1,j]),(-1,X[i2,j])]                
                for u,v in G.edges():
                    if v == i2:
                        lexpr += [(1,F[j,(i1,i2),(u,v)])]
                    if u == i2:
                        lexpr += [(1,F[j,(i1,i2),(v,u)])]
                
                model.addConstr(LinExpr(lexpr)>=-1, name='Eq(Fval)(%s,%s,%s)'%(j,i1,i2))

#### Essential Constraints 4-3) Kirchhoff law of F
for j in Hplus.nodes():
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:
                for v in G.nodes():
                    if v != i1:
                        if v != i2:
                            lexpr = []
                            for u,w in G.edges():
                                if u == v:
                                    lexpr += [(-1,F[j,(i1,i2),(u,w)])]
                                    lexpr += [(+1,F[j,(i1,i2),(w,u)])]
                                if w == v:
                                    lexpr += [(+1,F[j,(i1,i2),(u,w)])]
                                    lexpr += [(-1,F[j,(i1,i2),(w,u)])]
                            
                            model.addConstr(LinExpr(lexpr)==0, name='Eq(Kir)(%s,(%s,%s),%s)'%(j,i1,i2,v))

#### Essential Constraints 4-4) no inflow F into origin i1
for j in Hplus.nodes():
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:
                for u,v in G.edges():
                    if u == i1:
                        lexpr = [(1,F[j,(i1,i2),(v,u)])]
                        model.addConstr(LinExpr(lexpr)==0, name='Eq(antiOut)(%s,(%s,%s),(%s,%s))'%(j,i1,i2,v,u))
                    if v == i1:
                        lexpr = [(1,F[j,(i1,i2),(u,v)])]
                        model.addConstr(LinExpr(lexpr)==0, name='Eq(antiOut)(%s,(%s,%s),(%s,%s))'%(j,i1,i2,u,v))

            
#### Essential Constraints 4-5) no outflow F from destination i2
for j in Hplus.nodes():
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:
                for u,v in G.edges():
                    if v == i2:
                        lexpr = [(1,F[j,(i1,i2),(v,u)])]
                        model.addConstr(LinExpr(lexpr)==0, name='Eq(antiIn)(%s,(%s,%s),(%s,%s))'%(j,i1,i2,v,u))
                    if u == i2:
                        lexpr = [(1,F[j,(i1,i2),(u,v)])]
                        model.addConstr(LinExpr(lexpr)==0, name='Eq(antiIn)(%s,(%s,%s),(%s,%s))'%(j,i1,i2,u,v))
                        
### Essential Constraints 5) Population Capacity
for j in Hplus.nodes():
    lexpr = []
    for v in G.nodes():
        [population_vj] = nodes.loc[nodes['Node'] == v,'population']
        lexpr += [(population_vj,X[v,j])]
        
    model.addConstr(LinExpr(lexpr)<=ubPopulation, name='Eq(ubPop)(%s)'%(j))
    model.addConstr(LinExpr(lexpr)>=lbPopulation, name='Eq(lbPop)(%s)'%(j))
                        
# =============================================================================
# ### Essential Constraints 6) Arborescence (Tree rooted at center) Constraints: lbDiTreeEdge 
# #### Essential Constraints 6-1) Arborescence Constraints: lbDiTreeEdge >= F
# for j in Hplus.nodes():
#     for u,v in G.edges():
#         for i1 in G.nodes():
#             for i2 in G.nodes():
#                 if i1 != i2:
#                     lexpr_uv = [(-1,lbDiTreeEdge[j,(u,v)])]
#                     lexpr_vu = [(-1,lbDiTreeEdge[j,(v,u)])]
#                     lexpr_uv += [(1,F[j,(i1,i2),(u,v)])]
#                     lexpr_vu += [(1,F[j,(i1,i2),(v,u)])]
#                     model.addConstr(LinExpr(lexpr_uv)<=0, name='Eq(lbDiTreeEdgeCapacity)(%s,(%s,%s),(%s,%s))'%(j,u,v,i1,i2))
#                     model.addConstr(LinExpr(lexpr_vu)<=0, name='Eq(lbDiTreeEdgeCapacity)(%s,(%s,%s),(%s,%s))'%(j,v,u,i1,i2))
# 
# #### Essential Constraints 6-2) Arborescence Constraints: lbDiTreeEdge <= ZJ
# for j in Hplus.nodes():
#     for (u,v) in G.edges():
#         LHS = [(-1,lbDiTreeEdge[j,(u,v)])]
#         LHS += [(-1,lbDiTreeEdge[j,(v,u)])]
#         LHS += [(1,ZJ[(u,j),(v,j)])]
#         model.addConstr(LinExpr(LHS)>=0, name='Eq(lbDiTreeEdge<=ZJ)(%s,(%s,%s))'%(j,u,v))
#     
# #### Essential Constraints 6-3) Arborescence Constraints: sum of lbDiTreeEdge (tree edges sum) = sum of X - 1 (tree node sum - 1)
# for j in Hplus.nodes():
#     lexpr = []
#     for u,v in G.edges():
#         lexpr += [(-1,lbDiTreeEdge[j,(u,v)])]
#         lexpr += [(-1,lbDiTreeEdge[j,(v,u)])]
#         
#     for v in G.nodes():
#         lexpr += [(1,X[v,j])]
# 
#     model.addConstr(LinExpr(lexpr)==1, name='Eq(lbDiTreeEdgeAndX)(%s)'%(j))
#     
# #### Essential Constraints 6-4) Arborescence Constraints: every non-root node receive one arborescence arc    
# for j in Hplus.nodes():
#     for v in G.nodes():
#         lexpr = [(1,centerX[v,j])]
#         lexpr += [(-1,X[v,j])]
#         for (u,w) in G.edges():
#             if u == v:
#                 lexpr += [(1,lbDiTreeEdge[j,(w,u)])]
#             if w == v:
#                 lexpr += [(1,lbDiTreeEdge[j,(u,w)])]
#                     
#         model.addConstr(LinExpr(lexpr)==0, name='Eq(lbDiTreeEdgeIn)(%s,%s)'%(j,v))
# =============================================================================

## Enhancing Constraints 
# =============================================================================
# ### Enhancing Constraints 1) flow value sum from root = tree node sum - 1 
# for j in Hplus.nodes():
#     lexpr = []
#     for v in G.nodes():
#         lexpr += [(-1,X[v,j])]
#     for i1 in G.nodes():
#         for i2 in G.nodes():
#             if i1 != i2:
#                 for u,v in G.edges():
#                     if v == i2:
#                         lexpr += [(1,F[j,(i1,i2),(u,v)])]
#                     if u == i2:
#                         lexpr += [(1,F[j,(i1,i2),(v,u)])]
#                 
#     model.addConstr(LinExpr(lexpr)==-1, name='Eq(FvalueSum)(%s)'%(j))
# =============================================================================
    
### Enhancing Constraints 1-Alternative) flow value sum from root = tree node sum - 1 
for j in Hplus.nodes():
    for i2 in G.nodes():
        lexpr = [(-1,X[i2,j])]
        lexpr += [(1,centerX[i2,j])]
        for i1 in G.nodes():
            if i1 != i2:
                for (u,v) in G.edges():
                    if v == i2:
                        lexpr += [(1,F[j,(i1,i2),(u,v)])]
                    if u == i2:
                        lexpr += [(1,F[j,(i1,i2),(v,u)])]
        model.addConstr(LinExpr(lexpr)==0, name='Eq(FvalueSum)(%s,%s)'%(j,i2))

### Enhancing Constraints 2) Kirchhoff Node Capacity
for j in Hplus.nodes():
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:
                for v in G.nodes():
                    if v != i1:
                        if v != i2:
                            lexpr = [(1,X[v,j])]
                            for u,w in G.edges():
                                if u == v:
                                    lexpr += [(-1,F[j,(i1,i2),(u,w)])]
                                if w == v:
                                    lexpr += [(-1,F[j,(i1,i2),(w,u)])]
                            
                            model.addConstr(LinExpr(lexpr)>=0, name='Eq(KirNodeCapacity)(%s,(%s,%s),%s)'%(j,i1,i2,v))

### Enhancing Constraints 2-2) Origin Node Capacity
for j in Hplus.nodes():
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:
                lexpr = [(1,centerX[i1,j])]
                for (u,v) in G.edges():
                    if u == i1:
                        lexpr += [(-1,F[j,(i1,i2),(u,v)])]
                    if v == i1:
                        lexpr += [(-1,F[j,(i1,i2),(v,u)])]
                model.addConstr(LinExpr(lexpr)>=0, name='Eq(OriginCap)(%s,%s,%s)'%(j,i1,i2))
              
# =============================================================================
# ### Enhancing Constraints 3-1) Symmetry breaking A
# for j in Hplus.nodes():
#     if j > 1:
#         for v in G.nodes():
#             if v > 1:
#                 lexpr = [(1,centerX[v,j])]
#                 for u in range(1,v):
#                     lexpr += [(-1,centerX[u,j-1])]
#                 
#                 model.addConstr(LinExpr(lexpr)<=0, name='Eq(symmetryBreakingA)(%s,%s)'%(j,v))
# 
# ### Enhancing Constraints 3-2) Symmetry breaking B
# for j in Hplus.nodes():
#     if j < len(Hplus.nodes()):
#         for v in G.nodes():
#             if v < len(G.nodes()):
#                 lexpr = [(1,centerX[v,j])]
#                 for u in range(v+1,len(G.nodes)+1):
#                     lexpr += [(-1,centerX[u,j+1])]
#                 
#                 model.addConstr(LinExpr(lexpr)<=0, name='Eq(symmetryBreakingB)(%s,%s)'%(j,v))
# =============================================================================

### Enhancing Constraints 3-3) Other Symmetry breaking 
for j in range(1,howManyDistricts):
    LHS = []
    for u in G.nodes():
        LHS += [(u,centerX[u,j+1])]
        LHS += [(-u,centerX[u,j])]
    model.addConstr(LinExpr(LHS)>=0, name='Eq(otherSB)(%s)'%(j))
    
    
#Must Link
##Must Link: Read Data
mustLinkData = pd.read_csv('mustLink_MD_sophisticatedFinal.csv')
    
##Must Link: Employ Must Link Variables
zMust_vars = []
zMust_names = []
for l in mustLinkData['LinkMust']:
    [Source_l] = mustLinkData.loc[mustLinkData['LinkMust'] == l,'Source_Link']
    [Target_l] = mustLinkData.loc[mustLinkData['LinkMust'] == l,'Target_Link']
    for (district1, district2) in product(Hplus.nodes(),Hplus.nodes()):
        zMust_vars += [((Source_l,district1),(Target_l,district2))]
        zMust_names += ['zMust[(%s,%s),(%s,%s)]'%(Source_l,district1,Target_l,district2)]
zMust = model.addVars(zMust_vars, vtype=GRB.BINARY, name=zMust_names)

##Must Link: Constraints
###Must Link: Constraints: Buldle Equations
for l in mustLinkData['LinkMust']:
    [Source_l] = mustLinkData.loc[mustLinkData['LinkMust'] == l,'Source_Link']
    [Target_l] = mustLinkData.loc[mustLinkData['LinkMust'] == l,'Target_Link']
    for district1 in Hplus.nodes():
        LHS_Source = [(-1,X[Source_l,district1])]
        for districtTemp in Hplus.nodes():
            LHS_Source +=[(1,zMust[(Source_l,district1),(Target_l,districtTemp)])]
        model.addConstr(LinExpr(LHS_Source)==0, name='Eq(mustLinkSource)(%s,%s)'%(l,district1))

    for district2 in Hplus.nodes():
        LHS_Target = [(-1,X[Target_l,district2])]
        for districtTemp in Hplus.nodes():
            LHS_Target +=[(1,zMust[(Source_l,districtTemp),(Target_l,district2)])]
        model.addConstr(LinExpr(LHS_Target)==0, name='Eq(mustLinkTarget)(%s,%s)'%(l,district2))
    
###Must Link: Constraints: Must Link
for l in mustLinkData['LinkMust']:
    [Source_l] = mustLinkData.loc[mustLinkData['LinkMust'] == l,'Source_Link']
    [Target_l] = mustLinkData.loc[mustLinkData['LinkMust'] == l,'Target_Link']
    for (district1, district2) in product(Hplus.nodes(),Hplus.nodes()):
        if district1 != district2:
            model.addConstr(LinExpr([(1,zMust[(Source_l,district1),(Target_l,district2)])])==0, name='Eq(mustLink)(%s,%s,%s)'%(l,district1,district2))
            

#Define Objective Function
# =============================================================================
#         # 4) Objective terms
#     for j in Hplus.nodes():
#         for i1 in G.nodes():
#             for i2 in G.nodes():
#                 if i1 != i2:
#                     lexpr = [(-1,costV[j])]
#                     for u,v in G.edges():
#                         lexpr += [(1,F[j,(i1,i2),(v,u)])]
#                         lexpr += [(1,F[j,(i1,i2),(u,v)])]
#                         
#                     model.addConstr(LinExpr(lexpr)<=0, name='Eq(onjBound)(%s,(%s,%s))'%(j,i1,i2))
# ============================================================================= 

##Define Objective Function####################################################
###Constraints for objective function
for j in Hplus.nodes():
    lexpr = [(-1,costV[j])]
    for i1 in G.nodes():
        for i2 in G.nodes():
            if i1 != i2:
                for u,v in G.edges():
                    lexpr += [(1,F[j,(i1,i2),(v,u)])]
                    lexpr += [(1,F[j,(i1,i2),(u,v)])]
                    
    model.addConstr(LinExpr(lexpr)==0, name='Eq(onjBound)(%s'%(j))
    
###Objective function    
objectiveTerms = []
for j in Hplus.nodes():
    objectiveTerms += [(1,costV[j])]


#Fixing variables (Start)##############################################################
# =============================================================================
# lowerBound = 65
# model.addConstr(LinExpr(objectiveTerms)>=lowerBound, name='Eq(lowerBound)')
# =============================================================================

###END: add constraints###       


# =============================================================================
# nodes_SC_optMJN = pd.read_csv('nodes_SC_optMJN.csv')          
# for i in G.nodes():
#     [district_i] = nodes_SC_optMJN.loc[nodes_SC_optMJN['Node'] == i,'district']
#     model.addConstr(LinExpr([(1,X[i,district_i])])==1, name='Eq(Incumbent)(%s)'%(i))
# =============================================================================


# =============================================================================
# incumbent = pd.read_csv('incumbent.csv')
# for j in incumbent['district']:
#     [i] = incumbent.loc[incumbent['district'] == j,'center']
#     model.addConstr(LinExpr([(1,centerX[i,j])])==1, name='Eq(centerIncumbent)(%s,%s)'%(i,j))
# =============================================================================


# =============================================================================
# incumbent = pd.read_csv('incumbentX.csv')
# for i in incumbent['Node']:
#     [j] = incumbent.loc[incumbent['Node'] == i,'district']
#     model.addConstr(LinExpr([(1,X[i,j])])==1, name='Eq(XIncumbent)(%s,%s)'%(i,j))
# =============================================================================


# =============================================================================
# optPartitionIncumbent = pd.read_csv('optPartitionCenter_ver2-simple-revised_65.csv')
# for j in H.nodes():
#     for i in G.nodes():
#         variableName_X = "X[%s,%s]"%(i,j)
#         if variableName_X in optPartitionIncumbent.values:
#             [variableValue_X] = optPartitionIncumbent.loc[optPartitionIncumbent['varName'] == variableName_X,'varVal']
#             model.addConstr(LinExpr([(1,X[i,j])])==variableValue_X, name='Eq(Incumbent)(%s,%s)'%(i,j))
# =============================================================================
#Fixing variables (End)##############################################################
            
###Set Objective Function    
model.setObjective(LinExpr(objectiveTerms), GRB.MINIMIZE)
model.update()

# =============================================================================
# ### Warm Starting Solution
# optPartitionIncumbent = pd.read_csv('incumbentPlan_MD2012.csv')
# 
# for j in H.nodes():
#     for i in G.nodes():
#         variableName_centerX = "centerX[%s,%s]"%(i,j)
#         variableName_X = "X[%s,%s]"%(i,j)
#         if variableName_centerX in optPartitionIncumbent.values:
#             [variableValue_centerX] = optPartitionIncumbent.loc[optPartitionIncumbent['varName'] == variableName_centerX,'varVal']
#             centerX[i,j].start = variableValue_centerX
# 
#         if variableName_X in optPartitionIncumbent.values:
#             [variableValue_X] = optPartitionIncumbent.loc[optPartitionIncumbent['varName'] == variableName_X,'varVal']
#             X[i,j].start = variableValue_X
# =============================================================================


#Solve the problem#############################################################
#model = model.relax()
model.optimize()


#Output File###################################################################
variableName_SH = []
variableValue_SH = []
for v in model.getVars():
    if v.x > 0:
        variableName_SH += [v.varname]
        variableValue_SH += [v.x]

optPartitionCenter_ver1 = pd.DataFrame(list(zip(variableName_SH, variableValue_SH)),columns =['varName', 'varVal'])
optPartitionCenter_ver1.to_csv(r'opt_simple-cold-MDsophFinal.csv', index = False)
