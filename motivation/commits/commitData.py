import requests
import pandas as pd
import json
import urllib3
import logging
import ast
import os

with open('commit_data_log.txt', 'w'):
    pass

log_file = 'commit_data_log.txt'
log_level = logging.INFO
log_format = '%(asctime)s - %(message)s'
logging.basicConfig(filename=log_file, level=log_level, format=log_format, encoding='utf-8')
print = logging.info

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
token = 'your_api_token'

bounty_issue_list = []
repoData = pd.DataFrame()
data_exist = True

repoUserSet = set()
analysed_repo = set()

repoUserDict = dict()

def getBountyTime():
    columns = ['id_url', 'github_owner', 'github_repo', 'fullfillers']
    with open('../../rawData/bounties_gitcoin_214.json', 'r', encoding='utf-8') as f:
        json_list = json.load(f)
        print(f"open_source_data_completed. all: {len(json_list)}")
    data_list = []
    with open('preProcess.js', 'r') as file:
        for line in file:
            split_line = line.rstrip('\n').split(' ')
            issue_url = split_line[0]
            github_owner, github_repo = split_line[1].split('/')[3], split_line[1].split('/')[4]
            source_data = [x for x in json_list if x['url'] == issue_url][0]
            fullfillers = []
            for item in source_data['fulfillments']:
                if item.get('fulfiller_github_username'):
                    fullfillers.append([item['fulfiller_github_username'], item['created_on']])
            data_list.append([issue_url, github_owner, github_repo, fullfillers])
    print(f"analyse fullfillers and time completed. all: {len(data_list)}")
    df = pd.DataFrame(data_list, columns=columns)
    df.to_csv('./internalCsv/commitPreProcess.csv', index=False)
    return df

def analyseCommits(repo, owner, name, create_time):
    if f"{owner}:{repo}:{name}" in repoUserSet:
        return
    repoUserDict[f"{owner}:{repo}"]['all'] += 1
    commit_list = []
    if f"{owner}:{repo}" in analysed_repo or os.path.exists(f'./repoCommits/repo_{owner}_{repo}.json'):
        with open(f"./repoCommits/repo_{owner}_{repo}.json", 'r') as f:
            commit_list = json.load(f)
            print(f'open exist repo json file   reponName: https://github.com/{owner}/{repo} commitNum: {len(commit_list)}')
    else:
        per_page = 100  
        page = 1  
        print(f'request github api to {owner}:{repo}')
        while True:
            try:
                # print(f'getting issue: https://api.github.com/repos/{owner}/{repo}/issues?state=all&&per_page={per_page}&page={page}')
                response = requests.get(url=f"https://api.github.com/repos/{owner}/{repo}/commits",
                                        headers={'Authorization': 'token {}'.format(token)}, verify=False, params={'per_page': per_page, 'page': page})
                
                if response.status_code != 200:
                    print(f"Error occurred while retrieving https://api.github.com/repos/{name}/{repo}/commits/{per_page}/{page}")
                    break

                current_commits = response.json()
                commit_list.extend(current_commits)
                if len(current_commits) < per_page:
       
                    print(f'Request all successed!! repo: https://api.github.com/repos/{owner}/{repo}/commits all: len{len(commit_list)}')
                    break

                page += 1
            
            except requests.exceptions.RequestException as e:
                print(f"exception:https://api.github.com/repos/{name}/{repo}/commits{e}")
                break
        with open(f"./repoCommits/repo_{owner}_{repo}.json", 'w') as f:
            json.dump(commit_list, f)
        print(f"finish: repo_{owner}_{repo}")
        
        analysed_repo.add(f"{owner}:{repo}")
    
    for commit in commit_list:
        commit_name = commit['commit']['author']['name']
        date = commit['commit']['author']['date']
        if name == commit_name and create_time < date:
            repoUserSet.add(f"{owner}:{repo}:{name}")
            repoUserDict[f"{owner}:{repo}"]['continue'] += 1
            print(f'{name} has contribute in {owner}:{repo}  bounty_done_time: {create_time} commit_time: {date}')
            break




if data_exist:
    repoData = pd.read_csv('./internalCsv/commitPreProcess.csv')
else:
    repoData = getBountyTime()

print(f"repoData len: {len(repoData)}")
repoNum = 0

for index, row in repoData.iterrows():
    github_owner, github_repo = row['github_owner'], row['github_repo']
    fullfillers = ast.literal_eval(row['fullfillers'])

    if f"{github_owner}:{github_repo}" not in repoUserDict:
        repoUserDict[f"{github_owner}:{github_repo}"] = {
            'continue': 0,
            'all': 0
        } 
        repoNum += 1
        print(f"index {repoNum} add repo {github_owner}:{github_repo}")

    for item in fullfillers:
        name = item[0]
        create_time = item[1]
        analyseCommits(github_repo, github_owner, name, create_time)

    with open('commit_analyse_result.json', 'w') as f:
        json.dump(repoUserDict, f)

        


