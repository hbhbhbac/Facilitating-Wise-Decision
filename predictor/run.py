import pandas as pd
import numpy as np
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
from predictors.bounty_predictor import BountyPredictor
import sys


def save_summary_to_file(all_results, filename='summary.txt'):
    output_dir = 'modelResults'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    file_path = os.path.join(output_dir, filename)
    exact_results = {k: v for k, v in all_results.items()}

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("--- Model Performance Summary ---\n\n")

        if exact_results:
            f.write("## Point Prediction Model Results\n\n")
        
            exact_df = pd.DataFrame(columns=['Model', 'R²', 'RMSE', 'MAE'])

            for model_name, metrics in exact_results.items():
                if metrics is None:
                    continue
                
                if isinstance(metrics['r2'], list):
                    mean_r2 = np.mean(metrics['r2'])
                    std_r2 = np.std(metrics['r2'])
                    mean_rmse = np.mean(metrics['rmse'])
                    std_rmse = np.std(metrics['rmse'])
                    mean_mae = np.mean(metrics['mae'])
                    std_mae = np.std(metrics['mae'])

                    exact_df.loc[len(exact_df)] = [
                        model_name,
                        f"{mean_r2:.4f} ± {std_r2:.4f}",
                        f"{mean_rmse:.2f} ± {std_rmse:.2f}",
                        f"{mean_mae:.2f} ± {std_mae:.2f}"
                    ]
                else:
                    exact_df.loc[len(exact_df)] = [
                        model_name,
                        f"{metrics['r2']:.4f}",
                        f"{metrics['rmse']:.2f}",
                        f"{metrics['mae']:.2f}" if 'mae' in metrics else 'N/A'
                    ]
            
            f.write(tabulate(exact_df, headers='keys', tablefmt='pipe', showindex=False))
            f.write("\n\n")

    print(f"\n--- Model summary saved to '{file_path}' ---")

def preprocess_data():
    try:
        df = pd.read_csv('data.csv')
        print(f"Successfully loaded {len(df)} rows from data.csv.")
    except FileNotFoundError:
        print("Error: data.csv not found.")
        sys.exit(1)
    
    df_filtered = df[df['token_name'] == 'ETH'].copy()

    Q1 = df_filtered['bounty_amount'].quantile(0.25)
    Q3 = df_filtered['bounty_amount'].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    df_filtered = df_filtered[(df_filtered['bounty_amount'] >= lower_bound) & (df_filtered['bounty_amount'] <= upper_bound)]
    return df_filtered

def exact_model():
    df = preprocess_data()
    predictor = BountyPredictor(df, 'bounty_amount', 'modelResults/figs')

    predictor.preprocess_data()
    all_results = {}
    
    print("\n\n--- Training Models ---")
    all_results['GLM'] = predictor.train_glm_model()
    all_results['Linear Regression'] = predictor.train_sklearn_model('linear', times=1000)
    all_results['Ridge Regression'] = predictor.train_sklearn_model('ridge', times=1000)
    all_results['Decision Tree'] = predictor.train_sklearn_model('dt', times=1000)
    all_results['Random Forest'] = predictor.train_sklearn_model('rf', times=1000)
    all_results['Support Vector Regression'] = predictor.train_sklearn_model('svr', times=1000)
    all_results['XGBoost'] = predictor.train_sklearn_model('xgb', times=1000)
    
    print("\n--- Training DNN Model ---")
    all_results['DNN'] = predictor.train_dnn_model()
    
    print(all_results)
    
    save_summary_to_file(all_results, f'summary.txt')

def main():
    exact_model()

if __name__ == '__main__':
    main()
