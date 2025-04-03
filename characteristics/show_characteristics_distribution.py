import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.size'] = 10

df = pd.read_csv('../rawData/rawData.csv')

def drawFreqDistribution(feature, df, save, figsize=(12, 5)):
    fig = plt.figure(figsize=figsize, dpi=200)
    grouped = df.groupby(feature).count().sort_values('Unnamed: 0', ascending=False)
    academic_colors = ['#4e79a7', '#f28e2c', '#59a14f', '#edc949', '#af7aa1', '#76b7b2', '#e15759', '#b07aa1', '#ff9d9a', '#9c755f']
    academic_colors = academic_colors[:len(grouped.index) + 1]
    bars = plt.bar(grouped.index, grouped['Unnamed: 0'], color = academic_colors)
    plt.xlabel(f'{feature}', fontsize=15)
    plt.ylabel('Number of Bounty Issues', fontsize=15)

    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(int(bar.get_height())),
                ha='center', va='bottom', color='black')

    plt.savefig(f"{save}.pdf", dpi=200)

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
drawFreqDistribution(feature, df, 'experience')

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

fig = plt.figure(figsize=(12, 5), dpi=200)
grouped = df.groupby(feature).count().sort_values('Unnamed: 0', ascending=False)
academic_colors = ['#4e79a7', '#f28e2c', '#59a14f', '#edc949', '#af7aa1', '#76b7b2', '#e15759', '#b07aa1', '#ff9d9a', '#9c755f']
bars = plt.bar(grouped.index, grouped['Unnamed: 0'], color = academic_colors)
plt.xlabel(f'{feature}', fontsize=15)
plt.ylabel('Number of Bounty Issues', fontsize=15)
plt.xticks([])
plt.legend(bars, grouped.index, ncol=2)

for bar in bars:
    plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), str(int(bar.get_height())),
            ha='center', va='bottom', color='black')

plt.savefig(f"bountytype.pdf", dpi=200)

feature = 'project_length'
df.loc[df[feature] == 'Tage', feature] = 'Days'
df.loc[df[feature] == 'hours', feature] = 'Hours'
df.loc[df[feature] == 'ชั่วโมง', feature] = 'Hours'
df.loc[df[feature] == '周', feature] = 'Weeks'
df.loc[df[feature] == 'Miesięcy', feature] = 'Months'
df.loc[df[feature] == '0', feature] = 'Unknown'
df.loc[df[feature] == 'ay', feature] = 'Unknown'
df['project_length'].fillna('Unknown', inplace=True)
drawFreqDistribution(feature, df, 'projectlength')
