import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import logging


with open('commit_data_log.txt', 'w'):
    pass
log_file = 'commit_data_log.txt'
log_level = logging.INFO
log_format = '%(asctime)s - %(message)s'
logging.basicConfig(filename=log_file, level=log_level, format=log_format, encoding='utf-8')
print = logging.info

with open('commit_analyse_result.json', 'r') as f:
    repoDict = json.load(f)
df = pd.DataFrame.from_dict(repoDict, orient='index')
df = df.reset_index().rename(columns={'index': 'repo'})


def analyseContribute():
  
    handled_csv = df[df['all'] != 0].copy()
    handled_csv.loc[:, 'rate'] = handled_csv['continue'] / handled_csv['all'] * 100
    handled_csv.loc[:, 'rate'] = handled_csv['rate'].round(2)
    # handled_csv.to_csv('../internalCsv/commitStatisticResult.csv')
    rate_list = handled_csv['rate'].tolist()
    # continue_list = handled_csv['continue'].tolist()


    plt.figure()
    sns.violinplot(data=rate_list)
    plt.xlabel('')
    plt.xticks([]) 
    plt.ylabel('Rate (%)')
    # plt.title('Keep On Contributing Rate')
    plt.savefig(f"./commitImages/KeepOnContributingRate.png", dpi=300)


    rate_zero = len(handled_csv[handled_csv['rate'] == 0])
    rate_all = len(handled_csv['rate'])
    rate = handled_csv['continue'].sum() / handled_csv['all'].sum()
    print(f"rate_zero_repo: {rate_zero}  all_repo: {rate_all}  all_contributors: {handled_csv['all'].sum()} keep_contributors: {handled_csv['continue'].sum()} rate: {round(rate, 2)}")

analyseContribute()
