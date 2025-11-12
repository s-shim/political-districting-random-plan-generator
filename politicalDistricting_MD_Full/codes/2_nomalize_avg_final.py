import pandas as pd
import os
import glob

nodes = pd.read_csv('../precinct2010_nodes_adj.csv')
#nodes = pd.read_csv('analysis_normalized.csv')
analysis = pd.read_csv('analysis_MD_final.csv')
analysis_avg = pd.read_csv('analysis_normalized_avg.csv')

total_avg_GS = {}
num_prec_dist = {}
for index, row in analysis.iterrows():
    planID = int(row['simID'])
    district_plan = int(row['districtID'])
    total_avg_GS[planID,district_plan] = 0.0
    num_prec_dist[planID,district_plan] = 0

for name in glob.glob('sim*feas*.csv'):
    planID = int(name[3:7])
    plan = pd.read_csv('sim%s_feas_MD_sophisticatedFinal_core0_sol0.csv'%planID)
    for prec in plan['Node']:
        [district_prec] = plan.loc[plan['Node']==prec,'District']
        [avg_gs] = analysis_avg.loc[analysis_avg['Node']==prec,'AVG GS']

        total_avg_GS[planID,district_prec] += float(avg_gs)
        num_prec_dist[planID,district_prec] += 1

avg_norm_column = []
for index, row in analysis.iterrows():
    planID = int(row['simID'])
    district_plan = int(row['districtID'])
    avg_norm_column += [total_avg_GS[planID,district_plan]/num_prec_dist[planID,district_plan]]

analysis['avgNorm'] = avg_norm_column
analysis.to_csv('analysis_MD_final2.csv',index = False)
        
