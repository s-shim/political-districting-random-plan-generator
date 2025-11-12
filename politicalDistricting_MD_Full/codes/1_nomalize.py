import pandas as pd
import os
import glob

nodes = pd.read_csv('../precinct2010_nodes_adj.csv')
#nodes = pd.read_csv('analysis_normalized.csv')
analysis = pd.read_csv('analysis_MD_final.csv')

for name in glob.glob('sim*feas*.csv'):
    planID = int(name[3:7])
    plan = pd.read_csv('sim%s_feas_MD_sophisticatedFinal_core0_sol0.csv'%planID)
    agsColumn = []
    for prec in nodes['Node']:
        [dist_node] = plan.loc[plan['Node']==prec, 'District']
        dist_node = int(dist_node)
        [avgGerryScore] = analysis.loc[(analysis['simID']==planID) & (analysis['districtID']==dist_node),'gerry normalized']
        avgGerryScore = float(avgGerryScore)
        agsColumn += [avgGerryScore]
    nodes['%s'%planID] = agsColumn
    
    nodes.to_csv('analysis_normalized.csv',index = False)
    
    
