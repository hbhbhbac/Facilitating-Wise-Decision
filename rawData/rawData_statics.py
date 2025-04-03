import json
import numpy as np

######################### Dataset #########################

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

setBackers, setHunters = set(), set()
bounty_amount_change, bounty_amount_increase, bounty_amount_decrease = 0, 0, 0

for json_obj in data:
    setBackers.add(json_obj["org_name"])
    for full in json_obj["fulfillments"]:
        setHunters.add(full["fulfiller_github_username"])
    

bounty_amount = [float(entry['value_in_usdt']) for entry in data if entry['value_in_usdt'] is not None]

print(f"bounty issues number is : {len(data)}")
print(f"Duration is : {data[-1]['created_on']} ----- {data[0]['created_on']}")
print(f"backers number is {len(setBackers)} \nhunters number is {len(setHunters)}")
print(f"mean value is : {np.mean(bounty_amount)}")
print(f"median value is : {np.median(bounty_amount)}")
print(f"max value is : {np.max(bounty_amount)}")
print(f"min value is : {np.min(bounty_amount)}")
