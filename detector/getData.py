import pandas as pd

df = pd.read_csv('../rawData/rawData.csv')

feature = 'bounty_type'
df.loc[df[feature] == '0', feature] = 'Unknown'
df[feature].fillna('Unknown', inplace=True)
df.loc[df[feature] == '设计', feature] = 'Design'
df.loc[df[feature] == 'บัก', feature] = 'Bug'
df.loc[df[feature] == 'belgeler', feature] = 'Documentation'
df.loc[df[feature] == 'Docs', feature] = 'Documentation'
df.loc[df[feature] == 'feature', feature] = 'Feature'
df.loc[df[feature] == 'Funkcja', feature] = 'Feature'
df.loc[df[feature] == 'Community Engagement', feature] = 'Community'
df.loc[df[feature] == 'Community Support', feature] = 'Community'
df.loc[df[feature] == 'Code review', feature] = 'Code Review'
feature_count = df[feature].value_counts()
other_type = feature_count[feature_count <= 3].index.tolist()
df.loc[df[feature].isin(other_type), feature] = 'Other'
df.loc[df[feature] == 'Andere', feature] = 'Other'

feature = 'project_length'
df.loc[df[feature] == 'Tage', feature] = 'Days'
df.loc[df[feature] == 'hours', feature] = 'Hours'
df.loc[df[feature] == 'ชั่วโมง', feature] = 'Hours'
df.loc[df[feature] == '周', feature] = 'Weeks'
df.loc[df[feature] == 'Miesięcy', feature] = 'Months'
df.loc[df[feature] == '0', feature] = 'Unknown'
df.loc[df[feature] == 'ay', feature] = 'Unknown'
df['project_length'].fillna('Unknown', inplace=True)

feature = 'experience_level'
df.loc[df[feature] == '中间的', feature] = 'Intermediate'
df.loc[df[feature] == 'Mittlere', feature] = 'Intermediate'
df.loc[df[feature] == 'beginner', feature] = 'Beginner'
df.loc[df[feature] == 'เริ่มต้น', feature] = 'Beginner'
df.loc[df[feature] == 'advanced', feature] = 'Advanced'
df.loc[df[feature] == 'ileri', feature] = 'Advanced'
df.loc[df[feature] == 'Pośredni', feature] = 'Unknown'
df.loc[df[feature] == '0', feature] = 'Unknown'
feature_count = df[feature].value_counts()
other_type = feature_count[feature_count <= 3].index.tolist()
df.loc[df[feature].isin(other_type), feature] = 'Unknown'
df['experience_level'].fillna('Unknown', inplace=True)

dict_project_length = {
    'Hours':0,
    'Days':1,
    'Weeks':2,
    'Months':3
}

dict_experience_level = {
    'Beginner':0,
    'Intermediate':1,
    'Advanced':2
}

df['experience_level'].replace('Unknown', 'Intermediate', inplace=True)
dummies = pd.get_dummies(df['experience_level'])
dummies = dummies.add_prefix("experience_level_")
df = df.join(dummies)

df['project_length'].replace('Unknown', 'Hours', inplace=True)
dummies = pd.get_dummies(df['project_length'])
dummies = dummies.add_prefix("project_length_")
df = df.join(dummies)

df.loc[df['bounty_type'] == 'Andere', 'bounty_type'] = 'Other'
df.loc[df[feature] == '0', feature] = 'Project'
dummies = pd.get_dummies(df['bounty_type'])
dummies = dummies.add_prefix("bounty_type_")
df = df.join(dummies)

df = df.rename(columns={'bounty_type_Code Review': 'bounty_type_Code_Review'})
df = df.iloc[:, ::-1]
df['value_in_usdt'].fillna(0, inplace=True)


#############################################################################################

import json
import datetime
from dateutil import parser

with open('../rawData/bounties_gitcoin_214.json', 'r', encoding='utf-8') as f:
    json_list = json.load(f)

json_list = json_list[::-1]

dict_org = {}
fulfillments_len_list = []
changed = []
time_limit = []
never_expires = []
owner_follwers = []
owner_following = []
owner_grants_contributed = []
dict_bounty_num, dict_bounty_change_num = {}, {}
bounty_num, bounty_change_num  = [], []
title_lens = []
issue_texts = []
issue_indexs = []
until_time, until_fulfilment = [], []


ins = 0
des = 0

org_set = set()

for json_obj in json_list:
    fulfillments = json_obj['fulfillments']
    fulfillments_len_list.append(len(fulfillments))

    expires_date_str = parser.parse(json_obj["expires_date"]).strftime('%Y-%m-%d %H:%M:%S')
    created_on_str = parser.parse(json_obj["created_on"]).strftime('%Y-%m-%d %H:%M:%S')
    expires_date = datetime.datetime.strptime(expires_date_str, "%Y-%m-%d %H:%M:%S")
    created_on = datetime.datetime.strptime(created_on_str, "%Y-%m-%d %H:%M:%S")
    days_diff = (expires_date - created_on).days
    time_limit.append(days_diff)

    if (json_obj['never_expires'] == "true"):
        never_expires.append(1)
    else:
        never_expires.append(0)

    org_set.add(json_obj['org_name'])
    org = json_obj['org_name']
    bounty_num.append(dict_bounty_num.get(org, 0))
    bounty_change_num.append(dict_bounty_change_num.get(org, 0))
    dict_bounty_num[org] = bounty_num[-1] + 1

    if json_obj.get("bounty_owner_profile", {}) is None:
         owner_follwers.append(0)
         owner_following.append(0)
         owner_grants_contributed.append(0)
    else:
        owner_follwers.append(int(json_obj.get("bounty_owner_profile", {}).get("followers", 0)))
        owner_following.append(int(json_obj.get("bounty_owner_profile", {}).get("following", 0)))
        owner_grants_contributed.append(int(json_obj.get("bounty_owner_profile", {}).get("grants_contributed", 0)))

    title_lens.append(len(json_obj['title']))

    if json_obj.get('github_issue_number', 0) is not None:
        issue_indexs.append(int(json_obj.get('github_issue_number', 0)))
    else:
        issue_indexs.append(0)

    activities = json_obj["activities"]
    url = json_obj['url']
    ok = 0
    insok = 0
    desok = 0
    for activitie in activities:
        if activitie['activity_type'] in ["increased_bounty", "hypercharge_bounty", "new_kudos", "new_crowdfund", "bounty_abandonment_escalation_to_mods",
                                          "bounty_removed_by_funder", "bounty_removed_slashed_by_staff", "bounty_removed_by_staff"]:
            if activitie['activity_type'] in ["increased_bounty", "hypercharge_bounty", "new_kudos", "new_crowdfund"]:
                insok = 1
            else:
                desok = 1
            ok = insok - desok
            change_time_str = parser.parse(activitie["created"]).strftime('%Y-%m-%d %H:%M:%S')
            change_time = datetime.datetime.strptime(change_time_str, "%Y-%m-%d %H:%M:%S")

    ful_num = 0
    for ful in json_obj['fulfillments']:
        fulfillment_str = parser.parse(ful["created_on"]).strftime('%Y-%m-%d %H:%M:%S')
        ful_time = datetime.datetime.strptime(fulfillment_str, "%Y-%m-%d %H:%M:%S")
        if ok != 0 and (change_time - ful_time).seconds > 0:
            ful_num += 1

    if ok != 0 :
        until_fulfilment.append(ful_num)
        until_time.append((change_time - created_on).days)
    else:
        if (len(json_obj['fulfillments']) > 0):
            early_ful_str = parser.parse(json_obj['fulfillments'][0]["created_on"]).strftime('%Y-%m-%d %H:%M:%S')
            early_ful_time = datetime.datetime.strptime(early_ful_str, "%Y-%m-%d %H:%M:%S")
        else:
            early_ful_time = expires_date
        until_fulfilment.append(len(json_obj['fulfillments']))
        until_time.append((early_ful_time - created_on).days)

    if ok != 0:
        changed.append(ok + 1)
        issue_texts.append(json_obj['issue_description_text'])
    else:
        changed.append(ok + 1)
    dict_bounty_change_num[org] = bounty_change_num[-1] + abs(ok)
    ins += insok
    des += desok

print(f"org number is {len(org_set)}")

#############################################################################################

dataList = []
for index, row in df.iterrows():
    data = [row['project_length_Hours'], row['project_length_Days'], row['project_length_Weeks'], row['project_length_Months'],
            len(str(row['issue_description_text'])), time_limit[index] ,changed[index],
            row["bounty_type_Bug"], row["bounty_type_Code_Review"], row["bounty_type_Design"], row["bounty_type_Documentation"],
            row["bounty_type_Feature"], row["bounty_type_Improvement"], row["bounty_type_Other"], row["bounty_type_Project"],
            row["bounty_type_Security"], row['experience_level_Advanced'], row['experience_level_Intermediate'], row['experience_level_Beginner'],
            bounty_num[index], bounty_change_num[index], row['value_in_usdt'], title_lens[index],
            never_expires[index], owner_follwers[index], owner_following[index], owner_grants_contributed[index], issue_indexs[index],
            until_time[index], until_fulfilment[index]]
    dataList.append(data)

columns = ['project_length_Days', 'project_length_Hours', 'project_length_Weeks', 'project_length_Months',
           'issue_len_description', 'time_limit', 'have_changed',
           "bounty_type_Bug", "bounty_type_Code_Review", "bounty_type_Design", "bounty_type_Documentation", "bounty_type_Feature",
           "bounty_type_Improvement","bounty_type_Other","bounty_type_Project","bounty_type_Security",
           'experience_level_Advanced','experience_level_Intermediate', 'experience_level_Beginner', 'bounty_num',
           'bounty_change_num', 'bounty_amount', 'title_len', 'never_expires', 'owner_follwers',
           'owner_following', 'owner_grants_contributed', 'issue_index', 'until_time', 'until_fulfilment']

pd.DataFrame(dataList, columns=columns).to_csv('features.csv', index=False)



