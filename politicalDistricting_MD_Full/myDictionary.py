import pandas as pd
import networkx as n
import random
import math
from gurobipy import *
import copy

def localSearch(district,G,numDistricts,nx,upper,lower):
    gerryTemp = gerry(district,G,numDistricts,nx)
    gerryScore = 0
    for i in range(numDistricts):
        gerryScore += gerryTemp[i]
    # print(gerryScore)
    gerryScoreImprove = False
    
    improve = True
    while improve == True:
        improve = False
        for i in range(numDistricts):
            if improve == True:
                break
            for j in range(numDistricts):
                if i < j:
                    mergedDistrict = district[i] + district[j]
                    if nx.is_connected(G.subgraph(mergedDistrict)) == True:
                        model = districting(G.subgraph(mergedDistrict),2,upper,lower)
                        if int(gerryTemp[i] + gerryTemp[j] + 0.5) > int(model.objVal + 0.5):
                            gerryScoreImprove = True
                            gerryScore += (- int(gerryTemp[i] + gerryTemp[j] + 0.5) + int(model.objVal + 0.5))
                            variableName_SH = []
                            variableValue_SH = []
                            twoDistricts = []
                            for v in model.getVars():
                                if v.varname[0] == 'X':                            
                                    if v.x > 1.0 - 0.0001:
                                        u_g_pair = v.varname[2:-1].split(',')
                                        twoDistricts += [int(u_g_pair[1])]
                            twoDistricts = list(set(twoDistricts))
                            district[i] = []
                            district[j] = []
                            for v in model.getVars():
                                if v.varname[0] == 'X':                            
                                    if v.x > 1.0 - 0.0001:
                                        u_g_pair = v.varname[2:-1].split(',')                                
                                        if int(u_g_pair[1]) == int(twoDistricts[0]):
                                            district[i] += [int(u_g_pair[0])]
                                        if int(u_g_pair[1]) == int(twoDistricts[1]):
                                            district[j] += [int(u_g_pair[0])]
                            district_i = {}
                            district_i[0] = copy.deepcopy(district[i])
                            gerry_i = gerry(district_i,G.subgraph(district[i]),1,nx)
                            gerryTemp[i] = gerry_i[0]
        
                            district_j = {}
                            district_j[0] = copy.deepcopy(district[j])
                            gerry_j = gerry(district_j,G.subgraph(district[j]),1,nx)
                            gerryTemp[j] = gerry_j[0]
                                            
                            print('###',twoDistricts)                    
                            improve = True
                            break

    return gerry, district, gerryScoreImprove, gerryScore            


def districting(G,numDistricts,upper,lower):    
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
    ## Upper Bound Population: sum_u population_u X[u,g] <= avgPopulation * (1 + tolerance) X[g,g]
    for g in G.nodes():
        LHS = [(-upper,X[g,g])]
        for u in G.nodes():
            LHS += [(G.nodes[u]['population'],X[u,g])]
        model.addConstr(LinExpr(LHS)<=0, name='Eq.UpperBoundPopulation(%s)'%(g))
    
    ## Lower Bound Population: sum_u population_u X[u,g] >= avgPopulation * (1 - tolerance) X[g,g]
    for g in G.nodes():
        LHS = [(-lower,X[g,g])]
        for u in G.nodes():
            LHS += [(G.nodes[u]['population'],X[u,g])]
        model.addConstr(LinExpr(LHS)>=0, name='Eq.LowerBoundPopulation(%s)'%(g))    
                  
    #Objective: Gerrymander Score
    objTerms = []
    for (u,v) in G.edges():
        for g in G.nodes():
            objTerms += [(1,F[u,v,g])]
            objTerms += [(1,F[v,u,g])]
    model.setObjective(LinExpr(objTerms), GRB.MINIMIZE)
    
    model.update()
    model.optimize()

    return model



def intMasterNew(c,A,numColumns,numDistricts,nodes,b):
    master = Model('master')
    master.setParam("OutputFlag", 0)
     
    z_vars = []
    z_names = []
    for j in range(numColumns):
        z_vars += [(j)]
        z_names += ['Z[%s]'%j]
    Z = master.addVars(z_vars, vtype = GRB.BINARY, name = z_names)
                
    # add constraints
    LHS = []
    for j in range(numColumns):
        LHS += [(A['rho','Z[%s]'%j],Z[j])]
    master.addConstr(LinExpr(LHS) == b['rho'], name='rho')
    
    for i in nodes['Node']:
        LHS = []
        for j in range(numColumns):
            LHS += [(A['pie[%s]'%i,'Z[%s]'%j],Z[j])]
        master.addConstr(LinExpr(LHS) == b['pie[%s]'%i], name='pie[%s]'%i)
    
    # set objective
    objTerms = []
    for j in range(numColumns):
        objTerms += [(c['Z[%s]'%j],Z[j])]
    master.setObjective(LinExpr(objTerms), GRB.MINIMIZE)
    
    master.update()
    master.optimize()

    return master



def restrictedMasterNew(c,A,numColumns,numDistricts,nodes,b):
    master = Model('master')
    master.setParam("OutputFlag", 0)
     
    z_vars = []
    z_names = []
    for j in range(numColumns):
        z_vars += [(j)]
        z_names += ['Z[%s]'%j]
    Z = master.addVars(z_vars, vtype = GRB.CONTINUOUS, name = z_names)
                
    # add constraints
    LHS = []
    for j in range(numColumns):
        LHS += [(A['rho','Z[%s]'%j],Z[j])]
    master.addConstr(LinExpr(LHS) == b['rho'], name='rho')
    
    for i in nodes['Node']:
        LHS = []
        for j in range(numColumns):
            LHS += [(A['pie[%s]'%i,'Z[%s]'%j],Z[j])]
        master.addConstr(LinExpr(LHS) == b['pie[%s]'%i], name='pie[%s]'%i)
    
    # set objective
    objTerms = []
    for j in range(numColumns):
        objTerms += [(c['Z[%s]'%j],Z[j])]
    master.setObjective(LinExpr(objTerms), GRB.MINIMIZE)
    
    master.update()
    master.optimize()

    return master
    


def intMaster(c,A,numColumns,numDistricts,nodes,b):
    master = Model('master')
    master.setParam("OutputFlag", 0)
     
    z_vars = []
    z_names = []
    for j in range(numColumns):
        z_vars += [(j)]
        z_names += ['Z[%s]'%j]
    Z = master.addVars(z_vars, vtype = GRB.BINARY, name = z_names)
                
    # add constraints
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
    
    # set objective
    objTerms = []
    for j in range(numColumns):
        objTerms += [(c['Z[%s]'%j],Z[j])]
    master.setObjective(LinExpr(objTerms), GRB.MINIMIZE)
    
    master.update()
    master.optimize()
    
    return master


def restrictedMaster(c,A,workingColumns,numColumns,numDistricts,nodes,b):
    master = Model('master')
    master.setParam("OutputFlag", 0)
     
    z_vars = []
    z_names = []
    for j in workingColumns:
        z_vars += [(j)]
        z_names += ['Z[%s]'%j]
    Z = master.addVars(z_vars, vtype = GRB.CONTINUOUS, name = z_names)
                
    # add constraints
    for i in range(numDistricts):
        LHS = []
        for j in workingColumns:
            LHS += [(A['rho[%s]'%i,'Z[%s]'%j],Z[j])]
        master.addConstr(LinExpr(LHS) == b['rho[%s]'%i], name='rho[%s]'%i)
    
    for i in nodes['Node']:
        LHS = []
        for j in workingColumns:
            LHS += [(A['pie[%s]'%i,'Z[%s]'%j],Z[j])]
        master.addConstr(LinExpr(LHS) == b['pie[%s]'%i], name='pie[%s]'%i)
    
    # set objective
    objTerms = []
    for j in workingColumns:
        objTerms += [(c['Z[%s]'%j],Z[j])]
    master.setObjective(LinExpr(objTerms), GRB.MINIMIZE)
    
    master.update()
    master.optimize()
    
    return master


def solveMasterInteger(master,A,c,b,numDistricts,numColumns,nodes):
    z_vars = []
    z_names = []
    for j in range(numColumns):
        z_vars += [(j)]
        z_names += ['Z[%s]'%j]
    Z = master.addVars(z_vars, vtype = GRB.BINARY, name = z_names)
    
    
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

    return master


def solveSubproblem(dual,G,lower,upper):
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
                                        
    # lower : lower * X[g,g] <= sum_ u pop[u] * X[u,g]
    
    for g in G.nodes():
        LHS = [(-lower,X[g,g])]
        for u in G.nodes():
            LHS += [(G.nodes[u]['population'],X[u,g])]
        model.addConstr(LinExpr(LHS)>=0, name='Eq.lower(%s)'%(g))
                
    # upper : upper * X[g,g] >= sum_ u pop[u] * X[u,g]
    
    for g in G.nodes():
        LHS = [(-upper,X[g,g])]
        for u in G.nodes():
            LHS += [(G.nodes[u]['population'],X[u,g])]
        model.addConstr(LinExpr(LHS)<=0, name='Eq.upper(%s)'%(g))


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



def solveMaster(master,A,c,b,numDistricts,numColumns,nodes):
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

    return master

    
def ROUND(fracX,numDistricts,G):
    district = {}
    for d in range(numDistricts):
        district[d] = []
    
    done = []
    notDone = list(G.nodes())
    
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
            #ptbX[u,g] = halfX[u,g] + (1 - halfX[u,g]) * random.random()
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

def ISERROR(district,lower,upper,numDistricts,G):
    isError = False
    for i in range(numDistricts):
        population_i = 0
        for u in district[i]:
            population_i += G.nodes[u]['population']
        lower_error = lower - population_i
        if lower_error > 0:
            isError = True
            break
        
        upper_error = population_i - upper
        if upper_error > 0:
            isError = True
            break
        
    return isError


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



def gerry(district,G,numDistricts,nx):
    gerry = {}
    for g in range(numDistricts):
        gerry_district = -1
        subG = G.subgraph(district[g])
        for c in subG.nodes():
            shortestLength = nx.shortest_path_length(subG, source = c)
            sumDistance_c = 0
            for u in subG.nodes():
                sumDistance_c += shortestLength[u] 

            if gerry_district == -1:
                gerry_district = sumDistance_c
            else:
                if gerry_district > sumDistance_c:
                    gerry_district = sumDistance_c
        gerry[g] = gerry_district
    return gerry 



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



def subProblem(dual,lower,upper,G):
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
    ## Upper Bound Population: sum_u population_u X[u,g] <= upper * X[g,g]
    for g in G.nodes():
        LHS = [(-upper,X[g,g])]
        for u in G.nodes():
            LHS += [(G.nodes[u]['population'],X[u,g])]
        model.addConstr(LinExpr(LHS)<=0, name='Eq.UpperBoundPopulation(%s)'%(g))
    
    ## Lower Bound Population: sum_u population_u X[u,g] >= lower * X[g,g]
    for g in G.nodes():
        LHS = [(-lower,X[g,g])]
        for u in G.nodes():
            LHS += [(G.nodes[u]['population'],X[u,g])]
        model.addConstr(LinExpr(LHS)>=0, name='Eq.LowerBoundPopulation(%s)'%(g))    
                
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
        

