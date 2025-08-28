import json
import datetime
import bisect
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rcParams
import numpy as np

def RQ1_star_fork_change():
    try:
        with open('data/stars_info.json', 'r', encoding='utf-8') as f:
            stars_data = json.load(f)
        with open('data/forks_info.json', 'r', encoding='utf-8') as f:
            forks_data = json.load(f)
        with open('../rawData/repo_bounty_issues.json', 'r', encoding='utf-8') as f:
            bounty_issues_dict = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Required file not found. Details: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: JSON decoding failed. Details: {e}")
        return

    processed_stars = {repo: sorted([datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps])
                       for repo, timestamps in stars_data.items()}
    processed_forks = {repo: sorted([datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps])
                       for repo, timestamps in forks_data.items()}

    for repo, issues in bounty_issues_dict.items():
        star_list = processed_stars.get(repo, [])
        fork_list = processed_forks.get(repo, [])

        for issue in issues:
            created_on_str = issue.get('created_on')
            closed_at_str = issue.get('closed_at')
            
            if created_on_str and closed_at_str:
                created_on = datetime.datetime.fromisoformat(created_on_str.replace('Z', '+00:00'))
                closed_at = datetime.datetime.fromisoformat(closed_at_str.replace('Z', '+00:00'))

                if created_on > closed_at:
                    issue['stars_before'] = -1
                    issue['stars_after'] = -1
                    issue['star_change'] = 0
                    issue['forks_before'] = -1
                    issue['forks_after'] = -1
                    issue['fork_change'] = 0
                    continue
                
    
                before_stars = bisect.bisect_left(star_list, created_on)
                after_stars = bisect.bisect_left(star_list, closed_at)
                
                before_forks = bisect.bisect_left(fork_list, created_on)
                after_forks = bisect.bisect_left(fork_list, closed_at)

                issue['stars_before'] = before_stars
                issue['stars_after'] = after_stars
                issue['star_change'] = after_stars - before_stars
                
                issue['forks_before'] = before_forks
                issue['forks_after'] = after_forks
                issue['fork_change'] = after_forks - before_forks
            else:
                issue['stars_before'] = -1
                issue['stars_after'] = -1
                issue['star_change'] = 0
                issue['forks_before'] = -1
                issue['forks_after'] = -1
                issue['fork_change'] = 0

    star_changes = [issue['star_change'] for issues in bounty_issues_dict.values() for issue in issues if issue.get('stars_before') != -1 and issue.get('star_change') >= 0]
    fork_changes = [issue['fork_change'] for issues in bounty_issues_dict.values() for issue in issues if issue.get('forks_before') != -1 and issue.get('fork_change') >= 0]

    def calculate_stats(data, name):
        if not data:
            print(f"{name} Change - No valid data found.")
            return

        avg_change = sum(data) / len(data)
        max_change = max(data)
        min_change = min(data)
        data.sort()
        mid = len(data) // 2
        median_change = (data[mid - 1] + data[mid]) / 2 if len(data) % 2 == 0 else data[mid]

        print("-" * 50)
        print(f"{name} Change - Num: {len(data)}, Avg: {avg_change:.2f}, Median: {median_change}, Max: {max_change}, Min: {min_change}")

    calculate_stats(star_changes, "Star")
    calculate_stats(fork_changes, "Fork")

def RQ1_developer():
    with open('data/repo_contributors.json', 'r') as f:
        repoDict = json.load(f)
    df = pd.DataFrame.from_dict(repoDict, orient='index')
    df = df.reset_index().rename(columns={'index': 'repo'})

    handled_csv = df[df['all'] != 0].copy()
    handled_csv.loc[:, 'rate'] = (handled_csv['continue'] - handled_csv['before']) / handled_csv['all'] * 100
    handled_csv.loc[:, 'rate'] = handled_csv['rate'].round(2)
    rate_list = handled_csv['rate'].tolist()
    rate_zero = len(handled_csv[handled_csv['rate'] == 0])
    rate_all = len(handled_csv['rate'])
    rate = handled_csv['continue'].sum() / handled_csv['all'].sum()
    print(f"rate_zero_repo: {rate_zero}  all_repo: {rate_all}  all_contributors: {handled_csv['all'].sum()} keep_contributors: {handled_csv['continue'].sum()} before: {handled_csv['before'].sum()} rate: {round(rate, 2)}")

def RQ1_issue_completion_rate():
    csv_df = pd.read_csv("./data/github_issues.csv")

    handled_csv_df = csv_df[(csv_df["bounty"] != 0) & (csv_df["unbounty"] != 0)]
    handled_csv_df.loc[:, "bounty_done_rate"] = (
        handled_csv_df["bounty_done_rate"].str.replace("%", "").astype(float)
    )
    handled_csv_df.loc[:, "unbounty_done_rate"] = (
        handled_csv_df["unbounty_done_rate"].str.replace("%", "").astype(float)
    )

    bounty_list = handled_csv_df["bounty_done_rate"].tolist()
    unbounty_list = handled_csv_df["unbounty_done_rate"].tolist()


    bounty_mean = np.mean(bounty_list)
    unbounty_mean = np.mean(unbounty_list)

    data = {
        "Group": ["Bounty"] * len(bounty_list) + ["Unbounty"] * len(unbounty_list),
        "Rate": bounty_list + unbounty_list,
    }

    df = pd.DataFrame(data)
    default_config = {
        "figsizeBountyRate":(6.4, 4.8),
        "palette":[
            "#7178E0",
            "#A0BF7A",
            "#1AAF89",
            "#DE6552",
            "#FFA07A",
            "#FFD700",
            "#FF6347",
            "#FF4500",
            "#FF69B4",
            "#FF1493",
            "#8A2BE2",
            "#4B0082",
            "#00BFFF",
        ],
        "labelsizeXRate": 15,
        "labelsizeYRate": 15,
    }
    plt.figure(figsize=default_config["figsizeBountyRate"])
    sns.violinplot(data=df, x="Group", y="Rate", palette=default_config["palette"][:2])


    xticks = plt.xticks()[0]
    xticks = [x / 2 for x in xticks]
    gap = xticks[1] - xticks[0]
    legend_value = [bounty_mean, unbounty_mean]
    legend_color_value = default_config["palette"][:2]
    for i, position in enumerate(xticks):
        plt.axhline(
            y=legend_value[i],
            xmin=position + gap / 7,
            xmax=position + gap * 6 / 7,  
            color=legend_color_value[i],
            linestyle="--",
        )


    plt.xlabel("Type", fontsize=default_config["labelsizeXRate"], labelpad=5)
    plt.ylabel("Rate (%)", fontsize=default_config["labelsizeYRate"])
    plt.savefig(f"./results/issue_completion_rate.png", dpi=300,)

def RQ1_issue_completion_time():
    csv_df = pd.read_csv("./data/github_issues.csv")
    handled_csv_df = csv_df[
        (csv_df["bounty_cost_time_median"].notnull())
        & (csv_df["bounty_cost_time_mean"].notnull())
        & (csv_df["unbounty_cost_time_median"].notnull())
        & (csv_df["unbounty_cost_time_mean"].notnull())
        & (csv_df["bounty_cost_time_median"] != 0)
        & (csv_df["bounty_cost_time_mean"] != 0)
        & (csv_df["unbounty_cost_time_median"] != 0)
        & (csv_df["unbounty_cost_time_mean"] != 0)
    ]

    def zScoreFilter(data):
        mean_value = np.mean(data)
        std_value = np.std(data)
        z_scores = [(x - mean_value) / std_value for x in data]
        threshold = 3
        filtered_data = [x for i, x in enumerate(data) if abs(z_scores[i]) <= threshold]
        return filtered_data

    bounty_cost_time_median = zScoreFilter(
        [round(x / 60, 2) for x in handled_csv_df["bounty_cost_time_median"]]
    )
    unbounty_cost_time_median = zScoreFilter(
        [round(x / 60, 2) for x in handled_csv_df["unbounty_cost_time_median"]]
    )
    print(f'Filterd issues number: {len(bounty_cost_time_median)}')

    bounty_cost_time_median_mean = np.mean(bounty_cost_time_median)
    unbounty_cost_time_median_mean = np.mean(unbounty_cost_time_median)

    print("\n----------")
    print(
        f"bounty_median\n max: {round(handled_csv_df['bounty_cost_time_median'].max() / 60, 2)}h min: {round(handled_csv_df['bounty_cost_time_median'].min() / 60, 2)}h median: {round(handled_csv_df['bounty_cost_time_median'].median() / 60, 2)}h mean: {round(handled_csv_df['bounty_cost_time_median'].mean() / 60, 2)}h"
    )
    print(
        f"unbounty_median\n max: {round(handled_csv_df['unbounty_cost_time_median'].max() / 60, 2)}h min: {round(handled_csv_df['unbounty_cost_time_median'].min() / 60, 2)}h median: {round(handled_csv_df['unbounty_cost_time_median'].median() / 60, 2)}h mean: {round(handled_csv_df['unbounty_cost_time_median'].mean() / 60, 2)}h"
    )

    gap_median_mean = (
        round(handled_csv_df["bounty_cost_time_median"].median() / 60, 2)
        - round(handled_csv_df["unbounty_cost_time_median"].median() / 60, 2)
    ) / 24

    print(f"diffs: {gap_median_mean}d")
    print("----------\n")

    data = {
        "Group": ["bounty_cost_time_median"] * len(bounty_cost_time_median)
        + ["unbounty_cost_time_median"] * len(unbounty_cost_time_median),
        "Value": bounty_cost_time_median + unbounty_cost_time_median,

    }
    df = pd.DataFrame(data)

    default_config = {
        "figsizeCompletionTime": (10, 6),
        "palette":[
            "#7178E0",
            "#A0BF7A",
            "#1AAF89",
            "#DE6552",
            "#FFA07A",
            "#FFD700",
            "#FF6347",
            "#FF4500",
            "#FF69B4",
            "#FF1493",
            "#8A2BE2",
            "#4B0082",
            "#00BFFF",
        ],
        "labelsizeXTime": 13,
        "labelsizeYTime": 15,
    }
    plt.figure(figsize=default_config["figsizeCompletionTime"])
    sns.violinplot(
        data=df,
        x="Group",
        y="Value",
        palette=default_config["palette"][:2],
    )

    xticks = plt.xticks()[0]
    xticks = [x / 2 for x in xticks]
    gap = xticks[1] - xticks[0]
    legend_value = [
        bounty_cost_time_median_mean,
        unbounty_cost_time_median_mean,
    ]
    legend_color_value = default_config["palette"][:2]
    for i, position in enumerate(xticks):
        plt.axhline(
            y=legend_value[i],
            xmin=position + gap / 7,
            xmax=position + gap * 6 / 7,
            color=legend_color_value[i],
            linestyle="--",
        )



    plt.xlabel("Type", fontsize=default_config["labelsizeXTime"])
    plt.ylabel("Value (h)", fontsize=default_config["labelsizeYTime"])

    plt.savefig("./results/issue_completion_time.png", dpi=300)
    
def RQ2_show_characteristics_distribution():
    rcParams['font.size'] = 10

    df = pd.read_csv('./data/rawData.csv')

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

        plt.savefig(f"results/{save}.pdf", dpi=200)

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

    plt.savefig(f"results/bountytype.pdf", dpi=200)

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

def RQ2_comments():
    def calculate_stats(df):
        print("-" * 50)
        df['is_bounty'] = df['is_bounty'].astype(bool)

        bounty_df_stats = df[df['is_bounty']].copy()
        unbounty_df_stats = df[~df['is_bounty']].copy()

        try:
            bounty_df_stats['comments_num'] = pd.to_numeric(bounty_df_stats['comments_num'], errors='coerce')
            bounty_df_stats['delta_first_comment_time'] = pd.to_numeric(bounty_df_stats['delta_first_comment_time'], errors='coerce')
            unbounty_df_stats['comments_num'] = pd.to_numeric(unbounty_df_stats['comments_num'], errors='coerce')
            unbounty_df_stats['delta_first_comment_time'] = pd.to_numeric(unbounty_df_stats['delta_first_comment_time'], errors='coerce')
        except KeyError as e:
            print(f"{e}")
            return

        print("\n--- Bounty Issues ---")
        comments_data_bounty = bounty_df_stats['comments_num'].dropna()
        if not comments_data_bounty.empty:
            avg_comments = comments_data_bounty.mean()
            median_comments = comments_data_bounty.median()
            print(f'Number of Comments: - Average: {avg_comments:.2f}, Median: {median_comments:.2f}')
        else:
            print('Number of Comments: No valid data.')

        print("\n--- Non-Bounty Issues ---")
        comments_data_unbounty = unbounty_df_stats['comments_num'].dropna()
        if not comments_data_unbounty.empty:
            avg_comments = comments_data_unbounty.mean()
            median_comments = comments_data_unbounty.median()
            print(f'Number of Comments: - Average: {avg_comments:.2f}, Median: {median_comments:.2f}')
        else:
            print('Number of Comments: No valid data.')
        
        print("-" * 50)
    

    path = './data/github_issues_comments.csv'

    df = pd.read_csv(path, encoding='utf-8', dtype=str)
    with open('./data/repo_bounty_issues.json', 'r', encoding='utf-8') as f:
        repo_info = json.load(f)
    bounty_issues_set = set()
    for repo, issues in repo_info.items():
        for issue in issues:
            if 'updated_github_url' in issue:
                bounty_issues_set.add(issue['updated_github_url'])
    df['is_bounty'] = df['html_url'].apply(lambda x: x in bounty_issues_set)
    calculate_stats(df)

def RQ3_show_amount_change():
    with open('../rawData/bounties_gitcoin_214.json', 'r', encoding='utf-8') as f:
        json_list = json.load(f)

    json_list = json_list[::-1]
    ins = 0
    des = 0
    issue_num = 0

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

def RQ1():
    print("RQ1_star_fork_change")
    RQ1_star_fork_change()
    print("\nRQ1_developer")
    RQ1_developer()
    print("\nRQ1_issue_completion_rate")
    RQ1_issue_completion_rate()
    print("\nRQ1_issue_completion_time")
    RQ1_issue_completion_time()

def RQ2():
    print("\nRQ2_show_characteristics_distribution")
    RQ2_show_characteristics_distribution()
    print("\nRQ2_comments")
    RQ2_comments()

def RQ3():
    print("\nRQ3_show_amount_change")
    RQ3_show_amount_change()

if __name__ == "__main__":
    RQ1()
    RQ2()
    RQ3()