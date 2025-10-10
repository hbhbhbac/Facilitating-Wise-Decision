import json
import datetime
import bisect
import seaborn as sns
from typing import  Optional, Dict, Any
from scipy import stats 
import pandas as pd
import matplotlib.pyplot as plt
import os
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

def RQ1_star_fork_change_comparison():
    try:
        with open('data/stars_info.json', 'r', encoding='utf-8') as f:
            stars_data = json.load(f)
        with open('data/forks_info.json', 'r', encoding='utf-8') as f:
            forks_data = json.load(f)
        with open('data/repo_bounty_issues.json', 'r', encoding='utf-8') as f:
            bounty_issues_dict = json.load(f)
    except FileNotFoundError as e:
        print(f"Error: Required file not found. Details: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: JSON decoding failed. Details: {e}")
        return
    
    def load_cache() -> Dict[str, str]:
        CACHE_FILE = './data/repo_creation_cache.json'
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Cache file {CACHE_FILE} not found. Starting with empty cache.")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding cache file {CACHE_FILE}. Starting with empty cache.")
            return {}

    
    def fetch_repo_creation_date(
        repo_full_name: str, 
        cache: Dict[str, str]
    ) -> Optional[datetime.datetime]:

        if repo_full_name in cache:
            created_at_str = cache[repo_full_name]
            try:
                return datetime.datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            except ValueError:
                return None
                pass 
    
    repo_cache = load_cache() 

    processed_stars = {repo: sorted([datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps])
                       for repo, timestamps in stars_data.items()}
    processed_forks = {repo: sorted([datetime.datetime.fromisoformat(ts.replace('Z', '+00:00')) for ts in timestamps])
                       for repo, timestamps in forks_data.items()}

    project_periods: Dict[str, Dict[str, Any]] = {} 
    repos_to_check = set(bounty_issues_dict.keys())
    skipped_by_date_check = 0
    
    crawl_time = datetime.datetime(2025, 8, 1, tzinfo=datetime.timezone.utc) 

    for repo, issues in bounty_issues_dict.items():
        if not issues:
            continue

        try:
            valid_issues = [
                (datetime.datetime.fromisoformat(i['created_on'].replace('Z', '+00:00')), 
                 datetime.datetime.fromisoformat(i['closed_at'].replace('Z', '+00:00')))
                for i in issues if i.get('created_on') and i.get('closed_at')
            ]
            
            if not valid_issues:
                continue

            T_Bounty_start = min([c for c, _ in valid_issues])
            T_Bounty_end = max([cl for _, cl in valid_issues])
            
        except (AttributeError, ValueError):
            continue

        if T_Bounty_end <= T_Bounty_start:
            continue

        delta_t_bounty_sec = (T_Bounty_end - T_Bounty_start).total_seconds()
        delta_t_bounty_days = delta_t_bounty_sec / (24 * 3600)
        duration = datetime.timedelta(days=delta_t_bounty_days)

        T_Pre_start_required = T_Bounty_start - duration
        repo_created_at = fetch_repo_creation_date(repo, repo_cache) 
        
        if repo_created_at is None or repo_created_at > T_Pre_start_required:
            skipped_by_date_check += 1
            continue
            
        star_list = processed_stars.get(repo, [])
        fork_list = processed_forks.get(repo, [])
        
        stars_at_start = bisect.bisect_left(star_list, T_Bounty_start)
        stars_at_end = bisect.bisect_left(star_list, T_Bounty_end)
        star_change_bounty = stars_at_end - stars_at_start
        fork_change_bounty = bisect.bisect_left(fork_list, T_Bounty_end) - bisect.bisect_left(fork_list, T_Bounty_start)

        project_periods[repo] = {
            'duration_days': delta_t_bounty_days,
            'T_Bounty_start': T_Bounty_start,
            'T_Bounty_end': T_Bounty_end,
            'star_change_bounty': star_change_bounty,
            'fork_change_bounty': fork_change_bounty,
            'star_change_pre': 0.0, 'fork_change_pre': 0.0,
        }

    for repo, data in project_periods.items():
        duration = datetime.timedelta(days=data['duration_days'])
        star_list = processed_stars.get(repo, [])
        fork_list = processed_forks.get(repo, [])

        T_Pre_start = data['T_Bounty_start'] - duration
        T_Pre_end = data['T_Bounty_start']
        star_change_pre = bisect.bisect_left(star_list, T_Pre_end) - bisect.bisect_left(star_list, T_Pre_start)
        fork_change_pre = bisect.bisect_left(fork_list, T_Pre_end) - bisect.bisect_left(fork_list, T_Pre_start)
        data['star_change_pre'] = star_change_pre 
        data['fork_change_pre'] = fork_change_pre 
    
    valid_projects = list(project_periods.values())
    num_projects = len(valid_projects)
    
    print("-" * 70)
    print(f"🌟 Fork/Star Change Analysis Results (Pre-Bounty Control)")
    print(f"| Result Variable: Total Star/Fork Change Count (during the period)")
    print("-" * 70)

    if num_projects == 0:
        print("No valid project data found for analysis.")
        return

    def calculate_did_mean(change_bounty, change_control, name, control_type):
        avg_bounty = np.mean(change_bounty)
        avg_control = np.mean(change_control)
        did_effect = avg_bounty - avg_control
        
        print(f"\n--- {name} Change (Mean, {control_type} Control) ---")
        print(f"Avg. {name} Change (Bounty Period): {avg_bounty:.2f} total")
        print(f"Avg. {name} Change ({control_type} Period): {avg_control:.2f} total")
        return did_effect

    def calcualte_did_median(change_bounty, change_control, name, control_type):
        median_bounty = np.median(change_bounty)
        median_control = np.median(change_control)
        did_effect = median_bounty - median_control
        
        print(f"\n--- {name} Change (Median, {control_type} Control) ---")
        print(f"Median {name} Change (Bounty Period): {median_bounty:.2f} total")
        print(f"Median {name} Change ({control_type} Period): {median_control:.2f} total")
        return did_effect

    star_change_bounty = [p['star_change_bounty'] for p in valid_projects]
    fork_change_bounty = [p['fork_change_bounty'] for p in valid_projects]
    star_change_pre = [p['star_change_pre'] for p in valid_projects]
    fork_change_pre = [p['fork_change_pre'] for p in valid_projects]

    calculate_did_mean(star_change_bounty, star_change_pre, "Star", "Pre-Bounty")
    calculate_did_mean(fork_change_bounty, fork_change_pre, "Fork", "Pre-Bounty")
    calcualte_did_median(star_change_bounty, star_change_pre, "Star", "Pre-Bounty")
    calcualte_did_median(fork_change_bounty, fork_change_pre, "Fork", "Pre-Bounty")

    print("\n" + "=" * 70)
    print("✨ Significance Test (Wilcoxon Signed-Rank Test on Total Change Counts)")
    print("=" * 70)
    
    def perform_wilcoxon_test(change_bounty, change_control, name, control_type):
        stat, p_value = stats.wilcoxon(change_bounty, change_control)
        
        print(f"\n--- Statistical Significance Test ({name} Change: {control_type}) ---")
        print(f"Sample Size (N): {len(change_bounty)}")
        print(f"Wilcoxon statistic (W): {stat:.4f}")
        print(f"P-value: {p_value:.6f}")
        
        alpha = 0.05
        if p_value < alpha:
            print(f"Conclusion: Reject H0. The difference in total {name.lower()} change is statistically significant at $\\alpha={alpha}$.")
        else:
            print(f"Conclusion: Fail to reject H0. The difference in total {name.lower()} change is NOT statistically significant at $\\alpha={alpha}$.")

    perform_wilcoxon_test(star_change_bounty, star_change_pre, "Star", "Pre-Bounty")
    perform_wilcoxon_test(fork_change_bounty, fork_change_pre, "Fork", "Pre-Bounty")
    
    print("-" * 70)
    print("Analysis complete.")

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

def RQ1_rate_and_time():
    output_dir: str = "./results"
    config = default_config = {
        "fontsize": 10,
        "dpi": 200,
        "transparent": False ,
        "figsizeBountyRate": (6.4, 4.8),
        "figsizeCompletionTime": (10, 6),
        "palette": [
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
    }
    grouped_df = pd.read_csv('./data/github_issues_grouped.csv', encoding='utf-8-sig')
    os.makedirs(output_dir, exist_ok=True)

    def parse_rate(rate_str):
        if isinstance(rate_str, str) and rate_str.endswith('%'):
            try:
                return float(rate_str.replace('%', '')) / 100.0
            except ValueError:
                return np.nan
        return np.nan

    
    time_cols = [
        "bounty_cost_time_median", "bounty_cost_time_mean",
        "unbounty_cost_time_median", "unbounty_cost_time_mean"
    ]
    
    time_filter = pd.Series(True, index=grouped_df.index)
    for col in time_cols:
        if col in grouped_df.columns:
            time_filter &= grouped_df[col].notnull() & (grouped_df[col] != 0)
            
    handled_time_df = grouped_df[time_filter].copy()

    def zScoreFilter(data):
        if not data:
            return []
        
        mean_value = np.mean(data)
        std_value = np.std(data)

        if std_value == 0:
            return list(data)
        z_scores = [(x - mean_value) / std_value for x in data]
        threshold = 3
        filtered_data = [x for i, x in enumerate(data) if abs(z_scores[i]) <= threshold]

        return filtered_data

    bounty_median_h = zScoreFilter([round(x / 60 / 24, 2) for x in handled_time_df["bounty_cost_time_median"]])
    unbounty_median_h = zScoreFilter([round(x / 60 / 24, 2) for x in handled_time_df["unbounty_cost_time_median"]])
    
    if bounty_median_h and unbounty_median_h:
        bounty_median_mean = np.mean(bounty_median_h)
        unbounty_median_mean = np.mean(unbounty_median_h)
    else:
        bounty_median_mean, unbounty_median_mean = np.nan, np.nan
    
    print(f"Time Mean (days): {bounty_median_mean if not np.isnan(bounty_median_mean) else 'N/A'}")
    print(f"Time Mean (days): {unbounty_median_mean if not np.isnan(unbounty_median_mean) else 'N/A'}")
    print(f"Time Median (days): {np.median(bounty_median_h) if bounty_median_h else 'N/A'}")
    print(f"Time Median (days): {np.median(unbounty_median_h) if unbounty_median_h else 'N/A'}")
        
    if bounty_median_h and unbounty_median_h:
        data_time = {
            "Group": ["bounty_median"] * len(bounty_median_h) + ["unbounty_median"] * len(unbounty_median_h),
            "Value": bounty_median_h + unbounty_median_h,
        }
        df_time = pd.DataFrame(data_time)

        plt.figure(figsize=config.get("figsizeCompletionTime", (10, 6)))
            
        sns.violinplot(
            data=df_time,
            x="Group",
            hue="Group",
            legend=False,
            y="Value",
            palette=config.get("palette", ["#7178E0", "#A0BF7A"])[:2],
            inner='box' 
        )


        xticks_pos = np.array([0, 1])
        legend_value = [bounty_median_mean, unbounty_median_mean]
        legend_color_value = config.get("palette", ["#7178E0", "#A0BF7A"])[:2]
        

        for i, position in enumerate(xticks_pos):
            plt.axhline(
                y=legend_value[i] ,
                xmin=position / 2 + 0.1, 
                xmax=position / 2 + 0.4, 
                color=legend_color_value[i],
                linestyle="--",
                linewidth=1.5,
            )
        

        filename = "issue_completion_time.png" 
        plt.savefig(os.path.join(output_dir, filename), dpi=config.get("dpi", 300), transparent=default_config.get('transparent', True))
        plt.close()
        print(f"Saved plot to {os.path.join(output_dir, filename)}\n")


    rate_filter = (grouped_df["bounty_num"] > 0) & (grouped_df["unbounty_num"] > 0)
    handled_rate_df = grouped_df[rate_filter].copy()

    bounty_rate_list = handled_rate_df["bounty_done_rate"].apply(parse_rate).dropna().tolist()
    unbounty_rate_list = handled_rate_df["unbounty_done_rate"].apply(parse_rate).dropna().tolist()
    
    if not bounty_rate_list or not unbounty_rate_list:
        return


    bounty_mean_rate = np.mean(bounty_rate_list)
    unbounty_mean_rate = np.mean(unbounty_rate_list)

    print(f"Rate Mean: {bounty_mean_rate:.4f}")
    print(f"Rate Mean: {unbounty_mean_rate:.4f}")
    print(f"Rate Median: {np.median(bounty_rate_list):.4f}")
    print(f"Rate Median: {np.median(unbounty_rate_list):.4f}")
    

    data_rate = {
        "Group": ["Bounty"] * len(bounty_rate_list) + ["Unbounty"] * len(unbounty_rate_list),
        "Rate": [r * 100 for r in bounty_rate_list] + [r * 100 for r in unbounty_rate_list],
    }
    df_rate = pd.DataFrame(data_rate)

    plt.figure(figsize=config.get("figsizeBountyRate", (6.4, 4.8)))
        
    sns.violinplot(
        data=df_rate,
        x="Group",
        y="Rate",
        hue="Group",
        legend=False,
        palette=config.get("palette", ["#7178E0", "#A0BF7A"])[:2],
        inner='box'
    )


    xticks_pos = np.array([0, 1])
    legend_value = [bounty_mean_rate * 100, unbounty_mean_rate * 100]
    
    legend_color_value = config.get("palette", ["#7178E0", "#A0BF7A"])[:2]
    
    for i, position in enumerate(xticks_pos):
        plt.axhline(
            y=legend_value[i],
            xmin=position / 2 + 0.1, 
            xmax=position / 2 + 0.4, 
            color=legend_color_value[i],
            linestyle="--",
            linewidth=1.5,
        )
    

    filename = "issue_completion_rate.png" 
    plt.savefig(os.path.join(output_dir, filename), dpi=config.get("dpi", 300), transparent=default_config.get('transparent', True))
    plt.close()
    print(f"Saved plot to {os.path.join(output_dir, filename)}")

def RQ2_show_characteristics_distribution():
    rcParams['font.size'] = 10

    df = pd.read_csv('./data/rawData.csv')

    def drawFreqDistribution(feature, df, save, figsize=(12, 5)):
        fig = plt.figure(figsize=figsize, dpi=200)
        
        grouped = df.groupby(feature).count().sort_values('Unnamed: 0', ascending=False)
        
        academic_colors = ['#4e79a7', '#f28e2c', '#59a14f', '#edc949', '#af7aa1', '#76b7b2', '#e15759', '#b07aa1', '#ff9d9a', '#9c755f']
        academic_colors = academic_colors[:len(grouped.index)]
        
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
    
    df[feature] = df[feature].fillna('Unknown')
    
    drawFreqDistribution(feature, df, 'experience')

    feature = 'bounty_type'
    
    df.loc[df[feature] == '0', feature] = 'Unknown'
    
    df[feature] = df[feature].fillna('Unknown')
    
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
    academic_colors = academic_colors[:len(grouped.index)]
    
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
    
    df[feature] = df[feature].fillna('Unknown')
    
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
    print("\nRQ1_star_fork_change_comparison")
    RQ1_star_fork_change_comparison()
    print("\nRQ1_developer")
    RQ1_developer()
    print("\nRQ1_issue_completion_rate && RQ1_issue_completion_time")
    RQ1_rate_and_time()

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