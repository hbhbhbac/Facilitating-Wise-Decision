import pandas as pd
import numpy as np

df = pd.read_csv('./internalCsv/linkCode.csv')

feature = 'bounty_type'
df.loc[df[feature] == 'Andere', feature] = 'Other'
df.loc[df[feature] == '0', feature] = 'Project'

feature = 'project_length'
df.loc[df[feature] == 'Tage', feature] = 'Days'
df.loc[df[feature] == '0', feature] = 'Unknown'
df['project_length'].fillna('Unknown', inplace=True)

feature = 'experience_level'
df.loc[df[feature] == 'Mittlere', feature] = 'Intermediate'
df.loc[df[feature] == '0', feature] = 'Intermediate'
df['experience_level'].fillna('Unknown', inplace=True)

feature = 'repo_language'
df['repo_language'].fillna('Unknown', inplace=True)

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

dummies = pd.get_dummies(df['bounty_type'])
dummies = dummies.add_prefix("bounty_type_")
df = df.join(dummies)

language_counts = df['repo_language'].value_counts()
other_languages = language_counts[language_counts <= 76].index.tolist()
df.loc[df['repo_language'].isin(other_languages), 'repo_language'] = 'Others'
dummies = pd.get_dummies(df['repo_language'])
dummies = dummies.add_prefix("repo_language_")
df = df.join(dummies)

df = df.rename(columns={'bounty_type_Code Review': 'bounty_type_Code_Review',
                        'repo_language_Vim script': 'repo_language_Vim_script',
                        'repo_language_C#' : 'repo_language_C_sharp',
                        'repo_language_F#' : 'repo_language_F_sharp',
                        'repo_language_C++':'repo_language_Cpp'})

import numpy as np
threshold = 3
mean = np.mean(df['value_in_usdt'])
std = np.std(df['value_in_usdt'])
df['z_score'] = abs((df['value_in_usdt'] - mean) / std)
df = df[df['z_score'] < threshold]
df = df.drop('z_score', axis=1)
print(f"Remove feature outliers: {df.shape[0]}")

cols = [
    'project_length_Hours', 'project_length_Days', 
    'project_length_Months', 'project_length_Weeks', 
    "bounty_type_Bug", "bounty_type_Code_Review", "bounty_type_Design", "bounty_type_Documentation", "bounty_type_Feature",
    "bounty_type_Improvement","bounty_type_Other","bounty_type_Project","bounty_type_Security", "issue_timeout",
    "experience_level_Beginner",
    'experience_level_Advanced', 
    'experience_level_Intermediate',
    'repo_forks_count',
    "repo_language_JavaScript",
    "repo_language_TypeScript", 
    'repo_language_Others',
    'repo_stargazers_count', 
    'repo_watchers_count', 
    'repo_open_issues_count',
    'repo_subscribers_count', 
    'repo_size', 'code_additions', 'code_deletions',
    'code_changed_files', 'code_finish_time', 'issue_len_description',
    'fulfillments_len',
    'bounty_num',
    'bounty_change_num', 
    'owner_followers'
]

max_values = df[cols].max()
cols_to_log = max_values[max_values > 1].index.tolist()
df[cols_to_log] = np.log1p(df[cols_to_log])

df.to_csv('./model.csv', index=False)
