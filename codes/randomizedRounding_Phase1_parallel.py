import pandas as pd
import networkx as nx
#import myDictionary as md
import copy
import random
import math
import multiprocessing as mp


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



def phase1_2(arg):
    iteration, halfX, numDistricts, G, tolerance = arg
    return phase1(iteration, halfX, numDistricts, G, tolerance)
    
def phase1(iteration, halfX, numDistricts, G, tolerance):

    ptbX = PTBX(halfX,numDistricts,G)
    
    RMSD = RMSD_Alg(halfX,numDistricts,G)
    
    district = ROUND(ptbX,numDistricts,G)
    
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
    
    totalError = EQERROR(district,lower,upper,numDistricts,G)
    
    bestDistrict = copy.deepcopy(district)
    bestTrial = 0
    bestError = totalError    
    trial = 0
    print(trial,totalError)

    iterArray = [iteration]
    bestErrorArray = [bestError]
    bestTrialArray = [bestTrial]
    
    
    seed = copy.deepcopy(halfX)
    nLocal = 0
    move = True
    while bestError - 0 >= 1e-6:
        trial += 1
        ptbX = PTBX(seed,numDistricts,G)    
        RMSD = RMSD_Alg(seed,numDistricts,G)    
        district = ROUND(ptbX,numDistricts,G)
        totalError = EQERROR(district,lower,upper,numDistricts,G)          
    
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

                iterArray += [iteration]
                bestErrorArray += [bestError]
                bestTrialArray += [bestTrial]
                
                listPhase1 = list(zip(iterArray,bestErrorArray,bestTrialArray))
                nameColumn = ['iterArray','bestErrorArray','bestTrialArray']                
                progressTable = pd.DataFrame(listPhase1,columns =nameColumn)
                progressTable.to_csv(r'parallel_process/process_iter%s.csv'%(iteration), index = False)#Check
                
                if abs(bestError - 0) < 1e-6:
                    districtArray = []
                    nodeArray = []
                    for g in range(numDistricts):
                        for u in bestDistrict[g]:
                            districtArray += [g]
                            nodeArray += [u]
                    feasSolution = pd.DataFrame(list(zip(districtArray, nodeArray)),columns =['District', 'Node'])
                    feasSolution.to_csv(r'parallel_solution/feas_MD_sophisticatedFinal_iter%s.csv'%(iteration), index = False)#Check
    
    
        if move == True:
            alpha = 1 / (1 + math.exp(4 * RMSD))
            for g in range(numDistricts):
                for u in G.nodes():
                    seed[u,g] = (1 - alpha) * seed[u,g]
    
            for g in range(numDistricts):
                for u in bestDistrict[g]:
                    seed[u,g] += alpha * 1


def PTBX(halfX,numDistricts,G):
    ptbX = {}
    for u in G.nodes():
        for g in range(numDistricts):
            ptbX[u,g] = halfX[u,g] * random.random()
            #ptbX[u,g] = halfX[u,g] + (1 - halfX[u,g]) * random.random()
    return ptbX


def RMSD_Alg(ptbX,numDistricts,G):     
    RMSD = 0.0
    for u in G.nodes():
        for g in range(numDistricts):
            RMSD += (ptbX[u,g] - 0.5) ** 2
    RMSD = RMSD/len(G.nodes()) / numDistricts
    RMSD = math.sqrt(RMSD)
    return RMSD



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

halfX = {}    
for u in G.nodes():
    for g in range(numDistricts):
        halfX[u,g] = 0.5


if __name__ == '__main__':
    numCores = mp.cpu_count()
    p = mp.Pool(numCores)

    multiArgs = []  
    for iteration in range(numCores):
        multiArgs += [(iteration, halfX, numDistricts, G, tolerance)]  

    results = p.map(phase1_2, multiArgs)
    
    
    
    
