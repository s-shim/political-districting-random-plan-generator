import pandas as pd
import os
import glob

nodes = pd.read_csv('../gerrymandered_dist_mass_1812_nodes_3.csv')
#nodes = pd.read_csv('gerrymandereded_dist_mass_1812_nodes.csv')
#nodes = pd.read_csv('analysis_normalized.csv')
analysis = pd.read_csv('gerry_mass.csv')
#feas_MD_sophisticatedFinal_iter502
for name in glob.glob('feas*.csv'):
    planID = int(name[17:-4])
    print(name,planID)
    plan = pd.read_csv(name)
    agsColumn = []
    for prec in nodes['Node']:
        [dist_node] = plan.loc[plan['Node']==prec, 'District']
        dist_node = int(dist_node)
        [avgGerryScore] = analysis.loc[(analysis['simID']==planID) & (analysis['districtID']==dist_node),'gerry normalized']
        avgGerryScore = float(avgGerryScore)
        agsColumn += [avgGerryScore]
    nodes['%s'%planID] = agsColumn
    
    nodes.to_csv('analysis_normalized.csv',index = False)
    
    

