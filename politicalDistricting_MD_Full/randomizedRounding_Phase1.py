import pandas as pd
import networkx as nx
import myDictionary as md
import copy
import random
import math
import datetime
import time
import socket
machineName = socket.gethostname()
print(machineName)
print(datetime.datetime.now())
print('Start Randomized Rounding')

numDistricts = 8 
tolerance = 0.05
lines = pd.read_csv('precinct2010_lines_revised.csv')
nodes = pd.read_csv('precinct2010_nodes_adj.csv')
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

numSols = 1

for coreID in [0]:
    coreArray = []
    solArray = []
    gerryArray = []

    for solutionID in range(numSols):
        
        halfX = {}    
        for u in G.nodes():
            for g in range(numDistricts):
                halfX[u,g] = 0.5
        
        ptbX = md.PTBX(halfX,numDistricts,G)
        
        RMSD = md.RMSD(halfX,numDistricts,G)
        
        district = md.ROUND(ptbX,numDistricts,G)
                
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
        
        print('trial =',bestTrial)
        print('total violation =',bestError)
        print()
        
        
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
                    print('trial =',bestTrial)
                    print('total violation =',bestError)
                    print()
                    if abs(bestError - 0) < 1e-6:
                        districtArray = []
                        nodeArray = []
                        for g in range(numDistricts):
                            for u in bestDistrict[g]:
                                districtArray += [g]
                                nodeArray += [u]   
                                
                        gerry_district = md.GERRYSCORE(numDistricts, G, bestDistrict, nx)
                        print('gerrymander score =',gerry_district)
        
                        coreArray += [coreID]
                        solArray += [solutionID]
                        gerryArray += [gerry_district]
        
                        result = pd.DataFrame(list(zip(coreArray,solArray,gerryArray)),columns =['Core','SolutionID','Gerry Score'])
                        result.to_csv(r'result_core%s.csv'%(coreID), index = False)#Check
                        
                        feasSolution = pd.DataFrame(list(zip(districtArray, nodeArray)),columns =['District', 'Node'])
                        feasSolution.to_csv(r'feas_MD_sophisticatedFinal_core%s_sol%s.csv'%(coreID,solutionID), index = False)#Check
                        
                        break
        
        
            if move == True:
                alpha = 1 / (1 + math.exp(4 * RMSD))
                for g in range(numDistricts):
                    for u in G.nodes():
                        seed[u,g] = (1 - alpha) * seed[u,g]
        
                for g in range(numDistricts):
                    for u in bestDistrict[g]:
                        seed[u,g] += alpha * 1
        
        
        
        
        
        
