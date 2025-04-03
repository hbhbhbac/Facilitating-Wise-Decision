import requests
import pandas as pd
import json
import urllib3
import logging

with open('preprocess_log.txt', 'w'):
    pass

log_file = 'preprocess_log.txt'
log_level = logging.INFO
log_format = '%(asctime)s - %(message)s'
logging.basicConfig(filename=log_file, level=log_level, format=log_format, encoding='utf-8')
print = logging.info

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
token = 'your_api_token'

json_list = []
data_list = []
columns = ['git_coin_issue_url', 'issue_url', 'bounty_owner_url', 'issue_url']
feature_analyse = False

def PreProcessData():
    with open('../../rawData/bounties_gitcoin_214.json', 'r', encoding='utf-8') as f:
        json_list = json.load(f)
    all_issue = len(json_list)
    github_url_num, done_num, github_and_done_num, done_and_bounty_owner, pay_date = 0, 0, 0, 0, 0
    for index, json_obj in enumerate(json_list):
        if json_obj['status'] == 'done':
            done_num += 1
        if json_obj.get('github_url') is not None:
            github_url_num += 1
        if json_obj.get('github_url') is not None and json_obj['status'] == 'done':
            github_and_done_num += 1
            if json_obj.get('bounty_owner_profile') is not None and json_obj['bounty_owner_profile'].get('github_url') is not None :
                done_and_bounty_owner += 1
                if json_obj.get('payout_date') is not None:
                    pay_date += 1
                else:
                    print(f"no pay date: issue: {json_obj['url']}")
            else:
                print(f"done but no bounty owner: issue: {json_obj['url']}")
        if feature_analyse:
            continue
        if not (json_obj.get('github_url') is not None and len(json_obj['github_url'].split('/')) > 5 and json_obj['github_url'].split('/') != 'pull'):
            continue
        if json_obj['status'] == 'done' and json_obj.get('bounty_owner_profile') is not None and json_obj['bounty_owner_profile'].get('github_url') is not None:
            issue_url = json_obj['github_url']
            owner = issue_url.split('/')[3] if len(issue_url.split('/')) > 6 else None
            repo  = issue_url.split('/')[4] if len(issue_url.split('/')) > 6 else None
            issue_num  = issue_url.split('/')[6] if len(issue_url.split('/')) > 6 else None
            
            try:
                response = requests.get(url=f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}",
                                            headers={'Authorization': 'token {}'.format(token)}, verify=False)
                if response.status_code == 200:
                    update_url = issue_url if response.json()['html_url'] == issue_url else response.json()['html_url']
                    data_list.append([json_obj['url'], update_url, json_obj['bounty_owner_profile']['github_url'], json_obj['url']])
            except requests.exceptions.RequestException as e:
                print(f"{index}failed repo: {issue_url}")

        if index % 100 == 0:
            print(f"success: {index}/{all_issue}")
    
    if feature_analyse:
        print(f"{github_and_done_num} {github_url_num} {done_num} {done_and_bounty_owner} {pay_date}")
    else:
        with open('preProcess.js', 'w') as file:
            for item in data_list:
                file.write(f"{item[0]} {item[1]} {item[2]} {item[3]}\n")

PreProcessData()