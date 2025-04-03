import pandas as pd
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

data = pd.read_csv('./internalCsv/dataFilter.csv')
token = 'your_api_token'

def get(owner, repo):
    while True:
        try:
            print(f"https://api.github.com/repos/{owner}/{repo}")
            response = requests.get(url= f"https://api.github.com/repos/{owner}/{repo}", headers={'Authorization': 'token {}'.format(token)}, verify=False)
            repo_list = response.json()
            return repo_list, response.status_code
        except requests.exceptions.RequestException as e:
            continue

def linkRepo(data):
    dropIndex = []
    for index, row in data.iterrows():
        repo_json, status_code = get(row['github_org_name'], row['github_repo_name'])
        if status_code == 200:
            data.loc[index, 'repo_forks_count'] = repo_json['forks_count']
            data.loc[index, 'repo_stargazers_count'] = repo_json['stargazers_count']
            data.loc[index, 'repo_watchers_count'] = repo_json['watchers_count']
            data.loc[index, 'repo_open_issues_count'] = repo_json['open_issues_count']
            data.loc[index, 'repo_created_at'] = repo_json['created_at']
            data.loc[index, 'repo_subscribers_count'] = repo_json['subscribers_count']
            data.loc[index, 'repo_language'] = repo_json['language']
            data.loc[index, 'repo_size'] = repo_json['size']
        else:
            dropIndex.append(index)
    data.drop(dropIndex, axis=0, inplace=True)
    return data

data = linkRepo(data)
data.to_csv('./internalCsv/linkProject.csv', index=False)


        