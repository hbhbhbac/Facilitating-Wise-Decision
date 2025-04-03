import json
with open('../rawData/bounties_gitcoin_214.json', 'r', encoding='utf-8') as f:
    json_list = json.load(f)

json_list = json_list[::-1]
ins = 0
des = 0
issue_num = 0

data_list = []
for json_obj in json_list:
    activities = json_obj["activities"]
    insok = 0
    desok = 0
    for activitie in activities:
        if activitie['activity_type'] in ["increased_bounty", "hypercharge_bounty", "new_kudos", "new_crowdfund", "bounty_abandonment_escalation_to_mods",
                                          "bounty_removed_by_funder", "bounty_removed_slashed_by_staff", "bounty_removed_by_staff"]:
            if activitie['activity_type'] in ["increased_bounty", "hypercharge_bounty", "new_kudos", "new_crowdfund"]:
                ins += 1
                insok = 1
            else:
                des += 1
                desok = 1
    if insok > 0 or desok > 0:
        issue_num += 1
print(f"ins: {ins}, des: {des}, issue_num: {issue_num}")