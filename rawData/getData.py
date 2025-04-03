import pandas as pd
import json

with open('bounties_gitcoin_214.json', 'r', encoding='utf-8') as f:
    json_list = json.load(f)

json_list[3272]['value_in_usdt'] = 25000
json_list[1301]['value_in_usdt'] = 18000
json_list[1077]['value_in_usdt'] = 14400
json_list[2102]['value_in_usdt'] = 400
json_list[2306]['value_in_usdt'] = 5500
json_list[971]['value_in_usdt'] = 3200
json_list[802]['value_in_usdt'] = 5000
json_list[1583]['value_in_usdt'] = 1250
json_list[1192]['value_in_usdt'] = 1563
json_list[3452]['value_in_usdt'] = 420
json_list[1502]['value_in_usdt'] = 1250
json_list[1781]['value_in_usdt'] = 300
json_list[816]['value_in_usdt'] = 335.39
json_list.pop(608)
json_list.pop(608)
json_list.pop(608)
json_list.pop(3447)

dataList = []
columns = ["created_on", "bounty_type", "project_length", "experience_level",
            "github_url", "bounty_owner_github_username", "url", "keywords",
            "value_in_usdt", "github_org_name", "issue_description_text",
            "github_repo_name", "acceptance_criteria", "custom_issue_description",
            "additional_funding_summary", "token_name"]

for json_obj in json_list:
    data = [json_obj["created_on"], json_obj["bounty_type"],
            json_obj["project_length"], json_obj["experience_level"],
            json_obj["github_url"], json_obj["bounty_owner_github_username"],
            json_obj["url"], json_obj["keywords"],
            json_obj["value_in_usdt"], json_obj["github_org_name"],
            json_obj["issue_description_text"], json_obj["github_repo_name"],
            json_obj["acceptance_criteria"], json_obj["custom_issue_description"],
            json_obj["additional_funding_summary"], json_obj["token_name"]]
    dataList.append(data)

pd.DataFrame(dataList, columns=columns).to_csv('./rawData.csv')