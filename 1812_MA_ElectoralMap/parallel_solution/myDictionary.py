import pandas as pd
import networkx as nx
import random
import math
from gurobipy import *

def gerryscoreLP(G):
    numDistricts = 1
    model = Model('Gerrymander')
    model.setParam("OutputFlag", 0)
    
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
                
    #Objective: Gerrymander Score
    objTerms = []
    for (u,v) in G.edges():
        for g in G.nodes():
            objTerms += [(1,F[u,v,g])]
            objTerms += [(1,F[v,u,g])]
    model.setObjective(LinExpr(objTerms), GRB.MINIMIZE)
    
    model.update()
    model.optimize()
    return model.objVal
    

def ROUND(fracX,numDistricts,G):
    district = {}
    for d in range(numDistricts):
        district[d] = []
    
    done = []
    notDone = list(G.nodes)
    
    while len(notDone) > 0:
        bestFrac = 0.0
        best_u = -1
        bestDistrict =  -1
        for d in range(numDistricts):
            if len(district[d]) == 0:
                for u in notDone:
                    if bestFrac < fracX[u,d]:
                        bestFrac = fracX[u,d]
                        best_u = u
                        bestDistrict =  d
            else:
                for v in district[d]:
                    for u in G.neighbors(v):
                        if u in notDone:
                            if bestFrac < fracX[u,d]:
                                bestFrac = fracX[u,d]
                                best_u = u
                                bestDistrict =  d
        
        notDone.remove(best_u)
        done.append(best_u)
        district[bestDistrict].append(best_u)
        
    return district


def PTBX(halfX,numDistricts,G):
    ptbX = {}
    for u in G.nodes():
        for g in range(numDistricts):
            ptbX[u,g] = halfX[u,g] * random.random()
    return ptbX


def RMSD(ptbX,numDistricts,G):     
    RMSD = 0.0
    for u in G.nodes():
        for g in range(numDistricts):
            RMSD += (ptbX[u,g] - 0.5) ** 2
    RMSD = RMSD/len(G.nodes()) / numDistricts
    RMSD = math.sqrt(RMSD)
    return RMSD


def EQERROR(district,lower,upper,numDistricts,G):
    totalError = 0
    for i in range(numDistricts):
        population_i = 0
        for u in district[i]:
            population_i += G.nodes[u]['population']
        lower_error = lower - population_i
        upper_error = population_i - upper
        totalError += max(0,lower_error,upper_error)
    return totalError

def GERRYSCORE(numDistricts, G, district, nx):
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
    return totalGerry


def gerry(district,G,numDistricts):
    gerry = {}  
    for g in range(numDistricts):
        gerry_district = -1
        subG = G.subgraph(district[g])
        for c in subG.nodes():
            sumDistance_c = 0
            for d in subG.nodes():
                if c != d:
                    sumDistance_c += nx.shortest_path_length(subG, source = c, target = d)
            if gerry_district == -1:
                gerry_district = sumDistance_c
            else:
                if gerry_district > sumDistance_c:
                    gerry_district = sumDistance_c
        # print(g,gerry_district / len(district[g]))
        # gerry[g] = gerry_district / pow(len(district[g]),1)
        gerry[g] = gerry_district / len(district[g])
    return gerry




def solveSubProblem(dual,G,lower,upper):
    numDistricts = 1
    model = Model('subproblem')
    model.setParam("OutputFlag", 0)
    
    
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
    
    #lower : lower * X[g,g] <= sum_u pop[u] * X[u,g]
    
    for g in G.nodes():
        LHS = [(-lower,X[g,g])]
        for u in G.nodes():
            LHS += [(G.nodes[u]['population'],X[u,g])]
        model.addConstr(LinExpr(LHS)>=0, name='Eq.Lower(%s)'%(g))
        
    #upper : upper * X[g,g] >= sum_u pop[u] * X[u,g]
    for g in G.nodes():
         LHS = [(-upper,X[g,g])]
         for u in G.nodes():
             LHS += [(G.nodes[u]['population'],X[u,g])]
         model.addConstr(LinExpr(LHS)<=0, name='Eq.Upper(%s)'%(g))
        
        
                
    #Objective: Gerrymander Score
    objTerms = []
    for (u,v) in G.edges():
        for g in G.nodes():
            objTerms += [(1,F[u,v,g])]
            objTerms += [(1,F[v,u,g])]
            
    for u in G.nodes():
        for g in G.nodes():
            objTerms += [(-dual['pie[%s]'%u],X[u,g])]
    model.setObjective(LinExpr(objTerms), GRB.MINIMIZE)
    
    model.update()
    model.optimize()
    
    return model
    