import pandas as pd
import json
import datetime
from dateutil import parser

with open('../rawData/bounties_gitcoin_214.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

data[3272]['value_in_usdt'] = 25000
data[1301]['value_in_usdt'] = 18000
data[1077]['value_in_usdt'] = 14400
data[2102]['value_in_usdt'] = 400
data[2306]['value_in_usdt'] = 5500
data[971]['value_in_usdt'] = 3200
data[802]['value_in_usdt'] = 5000
data[1583]['value_in_usdt'] = 1250
data[1192]['value_in_usdt'] = 1563
data[3452]['value_in_usdt'] = 420
data[1502]['value_in_usdt'] = 1250
data[1781]['value_in_usdt'] = 300
data[816]['value_in_usdt'] = 335.39
data.pop(608)
data.pop(608)
data.pop(608)
data.pop(3447)

def count_done_activities(json_list):
    dataList = []
    columns = ["created_on", "bounty_type", "project_length", "experience_level",
               "github_url", "bounty_owner_github_username", "url",
               "value_in_usdt", "github_org_name", "description_len",
               "github_repo_name", "additional_funding_summary", "token_name",
               "github_pr", "fulfillments_len", 'issue_timeout']

    for json_obj in json_list:
        if json_obj['status'] == 'done':
            github_pr = []
            fulfillments = json_obj['fulfillments']
            for f in fulfillments:
                if f['accepted'] and f['fulfiller_metadata'].get("data") is not None and f['fulfiller_metadata']["data"]["payload"]["fulfiller"].get('githubPRLink') is not None and \
                    f['fulfiller_metadata']["data"]["payload"]["fulfiller"].get('githubPRLink') != '':
                    github_pr.append(f['fulfiller_metadata']["data"]["payload"]["fulfiller"].get('githubPRLink'))
            
            expires_date_str = parser.parse(json_obj["expires_date"]).strftime('%Y-%m-%d %H:%M:%S')
            created_on_str = parser.parse(json_obj["created_on"]).strftime('%Y-%m-%d %H:%M:%S')
            expires_date = datetime.datetime.strptime(expires_date_str, "%Y-%m-%d %H:%M:%S")
            created_on = datetime.datetime.strptime(created_on_str, "%Y-%m-%d %H:%M:%S")
            issue_timeout = (expires_date - created_on).days

            data = [json_obj['created_on'].split('.')[0].replace('Z', ''), json_obj["bounty_type"], json_obj["project_length"], json_obj["experience_level"],
                    json_obj["github_url"], json_obj["bounty_owner_github_username"],
                    json_obj["url"], json_obj["value_in_usdt"], json_obj["github_org_name"],
                    len(json_obj["issue_description_text"]), json_obj["github_repo_name"],
                    json_obj["additional_funding_summary"], json_obj["token_name"], github_pr,
                    len(fulfillments), issue_timeout]
            dataList.append(data)
    return pd.DataFrame(dataList, columns=columns)

data = count_done_activities(data)
print(f'Done bounty issues number is {len(data)}')

import matplotlib.pyplot as plt
freq = data['token_name'].value_counts()
freq = freq.sort_values(ascending=False).head(10)
fig = plt.figure(figsize=(6, 9))
plt.bar(freq.index, freq / data.shape[0])
plt.xlabel('token name')
plt.ylabel('percent')
plt.savefig(f"./TOkenNameDistribution.png")

data = data[data['token_name'] == 'ETH']
data = data[data['additional_funding_summary'] == {}]
print(f"Reward only in ETH {data.shape[0]}")

import os
if not os.path.exists('./internalCsv'):
    os.mkdir('./internalCsv')

data.to_csv('./internalCsv/dataFilter.csv',index=False)
