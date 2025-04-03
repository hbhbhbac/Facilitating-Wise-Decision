import pandas as pd
import requests
import urllib3
import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

data = pd.read_csv('./internalCsv/linkProject.csv')
token = 'your_api_token'

def getPulls(owner, repo, number):
    while True:
        try:
            print(f"[trying]https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
            response = requests.get(url= f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}", headers={'Authorization': 'token {}'.format(token)}, verify=False)
            pr_list = response.json()
            return pr_list, response.status_code
        except requests.exceptions.RequestException as e:
            print(e)

def getRepo(owner, repo):
    while True:
        try:
            print(f"https://api.github.com/repos/{owner}/{repo}")
            response = requests.get(url= f"https://api.github.com/repos/{owner}/{repo}", headers={'Authorization': 'token {}'.format(token)}, verify=False)
            repo_list = response.json()
            commit_response = requests.get(url= f"https://api.github.com/repos/{owner}/{repo}/commits", headers={'Authorization': 'token {}'.format(token)}, verify=False)
            print(f"https://api.github.com/repos/{owner}/{repo}/commits")
            files = []
            additions, deletions, commits = 0, 0, 0
            commit_list = commit_response.json()
            if isinstance(commit_list, list):
                for commit in commit_list:
                    commits += 1
                    commit_url = commit['url']
                    print(commit['url'])
                    commit_response = requests.get(url= commit_url, headers={'Authorization': 'token {}'.format(token)}, verify=False)
                    commit_json = commit_response.json()
                    if (commit_json.get('stats', None) is not None):
                        additions += commit_json["stats"]["additions"]
                        deletions += commit_json["stats"]["deletions"]
                    if (commit_json.get('files', None) is not None):
                        for file in commit_json["files"]:
                            files.append(file["filename"])
            return repo_list, response.status_code, additions, deletions, len(set(files)), commits
        except requests.exceptions.RequestException as e:
            print(e)

def linkCode(data):
    dropIndex = []
    for index, row in data.iterrows():
        pr = row['github_pr']
        if (pr.find('github') == -1):
            dropIndex.append(index)
            continue
        pr = pr.replace(']','')
        pr = pr.replace('[','')
        pr = pr.replace('\'', '')
        repo_json, status_code = getPulls(row['github_org_name'], row['github_repo_name'], pr.split('/')[-1])
        if status_code == 200:
            data.loc[index, 'code_additions'] = repo_json['additions']
            data.loc[index, 'code_deletions'] = repo_json['deletions']
            data.loc[index, 'code_changed_files'] = repo_json['changed_files']
            data.loc[index, 'code_commits'] = repo_json['commits']
            data.loc[index, 'code_comments'] = repo_json['comments']
            data.loc[index, 'code_created_at'] = repo_json['created_at']
            data.loc[index, 'code_merged_at'] = repo_json['merged_at']
            data.loc[index, 'code_finish_time'] = (datetime.strptime(row['code_created_at'], "%Y-%m-%dT%H:%M:%SZ") - datetime.strptime(row['created_on'], "%Y-%m-%dT%H:%M:%S")).seconds // 60
        else:
            need_drop = True
            for i in range(len(pr.split('/'))):
                if (pr.split('/')[i] == 'github.com' and i < len(pr.split('/')) - 2):
                    need_drop = False
                    repo_json, status_code, additions, deletions, changed_files, commits = getRepo(pr.split('/')[i + 1], pr.split('/')[i + 2])
                    if status_code == 200:
                        data.loc[index, 'code_created_at'] = repo_json['created_at']
                        data.loc[index, 'code_additions'] = additions
                        data.loc[index, 'code_deletions'] = deletions
                        data.loc[index, 'code_changed_files'] = changed_files
                        data.loc[index, 'code_commits'] = commits
                        data.loc[index, 'code_finish_time'] = (datetime.strptime(row['code_created_at'], "%Y-%m-%dT%H:%M:%SZ") - datetime.strptime(row['created_on'], "%Y-%m-%dT%H:%M:%S")).seconds // 60
                if need_drop:
                    dropIndex.append(index)

    return data.drop(dropIndex, axis=0)

df = linkCode(data)
print(f"bounty issues that have accepted code with a GitHub pull request link and projects on GitHub that are accessible: {df.shape[0]}")
df.to_csv('./internalCsv/linkCode.csv', index=False)