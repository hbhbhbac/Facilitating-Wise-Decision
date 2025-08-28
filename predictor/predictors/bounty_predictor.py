import pandas as pd
import numpy as np
import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
import statsmodels.api as sm
from pygam import LinearGAM
from tqdm import tqdm
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, make_scorer
from ast import literal_eval
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
import xgboost as xgb
import matplotlib.pyplot as plt

class BountyPredictor:
    def __init__(self, df, label='bounty_amount',  save_dir='modelResults/figs'):

        self.df = df
        self.label = label
        
        self.columns = [
            'repo_bounty_mean', 'repo_bounty_median', 'repo_bounty_std', 'repo_bounty_var', 
            'repo_bounty_q25', 'repo_bounty_q75', 'repo_bounty_max', 'repo_bounty_min', 
            'code_smells', 'ncloc', 'complexity',
            'star_count_at_issue_creation', 'fork_count_at_issue_creation', 'bounty_num', 'bounty_change_num', 'time_limit', 'title_len'
        ]
        self.cat_columns = [
            'project_length_Hours', 'project_length_Days', 'project_length_Weeks', 'project_length_Months',
            "bounty_type_Bug", "bounty_type_Design", "bounty_type_Feature", "bounty_type_Improvement","bounty_type_Project","bounty_type_Security",
            'experience_level_Advanced','experience_level_Intermediate', 'experience_level_Beginner',
            'never_expires'
        ]
        self.embedded_col = 'issue_len_description'
        self.all_numerical_cols = self.columns.copy()
        
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.X_train_tensor = None
        self.X_test_tensor = None
        self.y_train_tensor = None
        self.y_test_tensor = None

        self.model_map = {
            'linear': LinearRegression,
            'ridge': Ridge,
            'dt': DecisionTreeRegressor,
            'rf': RandomForestRegressor,
            'svr': SVR,
            'xgb': xgb.XGBRegressor
        }
        self.model_params = {}
        
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def preprocess_data(self, filter_condition=None):
        df_filtered = self.df.copy()
        if filter_condition:
            df_filtered = df_filtered.query(filter_condition).copy()
        
        def expand_array_column(row):
            try:
                arr = np.array(literal_eval(str(row)))
                return pd.Series(arr)
            except (ValueError, TypeError, NameError, SyntaxError):
                return pd.Series([np.nan] * 64)

        if self.embedded_col in df_filtered.columns:
            embeddings_df = df_filtered[self.embedded_col].apply(expand_array_column)
            embeddings_df.columns = [f'{self.embedded_col}_{j}' for j in range(embeddings_df.shape[1])]
            df_filtered = pd.concat([df_filtered.drop(columns=[self.embedded_col]), embeddings_df], axis=1)
            self.all_numerical_cols.extend(embeddings_df.columns.tolist())

        df_filtered = df_filtered.fillna(0)
        
        X = df_filtered[self.all_numerical_cols + self.cat_columns]
        y = df_filtered[self.label]
        
        X_train, X_test, y_train_raw, y_test_raw = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )

        scaler_sklearn = MinMaxScaler()
        X_train_scaled_sklearn = pd.DataFrame(
            scaler_sklearn.fit_transform(X_train[self.all_numerical_cols]),
            columns=self.all_numerical_cols,
            index=X_train.index
        )
        X_test_scaled_sklearn = pd.DataFrame(
            scaler_sklearn.transform(X_test[self.all_numerical_cols]),
            columns=self.all_numerical_cols,
            index=X_test.index
        )

        X_train_cat = pd.get_dummies(X_train[self.cat_columns], drop_first=True)
        X_test_cat = pd.get_dummies(X_test[self.cat_columns], drop_first=True)
        
        self.X_train = pd.concat([X_train_scaled_sklearn, X_train_cat], axis=1)
        self.X_test = pd.concat([X_test_scaled_sklearn, X_test_cat], axis=1)
        
        self.y_train = y_train_raw
        self.y_test = y_test_raw
        
        self.X_train = self.X_train.astype(float)
        self.X_test = self.X_test.astype(float)
        
        scaler_dnn = StandardScaler()
        X_train_scaled_dnn = scaler_dnn.fit_transform(self.X_train)
        X_test_scaled_dnn = scaler_dnn.transform(self.X_test)

        self.X_train_tensor = torch.tensor(X_train_scaled_dnn, dtype=torch.float32)
        self.X_test_tensor = torch.tensor(X_test_scaled_dnn, dtype=torch.float32)
        self.y_train_tensor = torch.tensor(self.y_train.values, dtype=torch.float32).unsqueeze(1)
        self.y_test_tensor = torch.tensor(self.y_test.values, dtype=torch.float32).unsqueeze(1)

        
    def _evaluate_predictions(self, y_true, y_pred):
        y_pred[y_pred < 0] = 0
        
        r2 = r2_score(y_true, y_pred)
        rmse = mean_squared_error(y_true, y_pred, squared=False)
        mae = mean_absolute_error(y_true, y_pred)
        
        return r2, rmse, mae
    
    def _plot_predictions(self, y_true, y_pred, model_name):
        y_pred[y_pred < 0] = 0
        y_true[y_true < 0] = 0
        
        fig, ax = plt.subplots(figsize=(10, 8))
        plt.scatter(y_true, y_pred, alpha=1, color='blue', label='Predictions')
        
        min_val = min(y_true.min(), y_pred.min())
        max_val = max(y_true.max(), y_pred.max())
        plt.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect Prediction')
        
        ax.set_xlabel('Actual')
        ax.set_ylabel('Predict')
        
        
        plt.tight_layout()
        
        file_name = f"{model_name}.png"
        file_path = os.path.join(self.save_dir, file_name)
        plt.savefig(file_path)
        plt.close()
        print(f"Prediction plot saved to: {file_path}")

    def tune_params(self):
        params_rf = {'n_estimators': range(50, 201, 50)}
        params_xgb = {'n_estimators': range(50, 201, 50), 'learning_rate': [0.01, 0.1, 0.5]}
        params_dt = {'criterion': ['squared_error', 'absolute_error']}
        params_svr = {'C': [0.1, 1, 10], 'gamma': [0.1, 1, 10]}
        
        tune_models = [RandomForestRegressor(), xgb.XGBRegressor(objective='reg:squarederror'), DecisionTreeRegressor(), SVR()]
        tune_params = [params_rf, params_xgb, params_dt, params_svr]
        model_names = ['rf', 'xgb', 'dt', 'svr']
        
        r2_scorer = make_scorer(r2_score)
        self.model_params = {}
        
        for i in tqdm(range(len(tune_models))):
            model = GridSearchCV(tune_models[i], tune_params[i], cv=5, scoring=r2_scorer, n_jobs=-1)
            model.fit(self.X_train, self.y_train)
            self.model_params[model_names[i]] = model.best_params_
            print(f"Best params for {model_names[i]}: {model.best_params_}")
            
        with open('bestParams_regression.json', 'w') as fp:
            json.dump(self.model_params, indent=4, fp=fp)

    def train_sklearn_model(self, model_name, times=10):
        if model_name not in self.model_map:
            raise ValueError(f"Model '{model_name}' not supported.")

        results = self._evaluation(model_name, times)
        print(f"\n--- {model_name.upper()} Final Results ---")
        print(f"Optimism-Adjusted R²: {results['r2']:.4f}")
        print(f"Optimism-Adjusted RMSE: {results['rmse']:.2f}")
        print(f"Optimism-Adjusted MAE: {results['mae']:.2f}")
        return results
    

    def _evaluation(self, model_name, times):
        X_combined = pd.concat([self.X_train, self.X_test]).reset_index(drop=True)
        y_combined = pd.concat([self.y_train, self.y_test]).reset_index(drop=True)
        
        try:
            with open('bestParams_regression.json', 'r') as fp:
                params = json.load(fp).get(model_name, {})
        except (FileNotFoundError, KeyError):
            params = {}

        model = self.model_map[model_name](**params)
        
        model.fit(X_combined, y_combined)
        y_pred_orig = model.predict(X_combined)
        original_r2, original_rmse, original_mae = self._evaluate_predictions(y_combined, y_pred_orig)
        
        r2_optimism, rmse_optimism, mae_optimism = [], [], []
        n_obs = len(X_combined)
        

        all_predictions = []

        for i in tqdm(range(times), desc=f"ping {model_name}"):
            boot_indices = np.random.choice(n_obs, size=n_obs, replace=True)
            boot_X = X_combined.iloc[boot_indices]
            boot_y = y_combined.iloc[boot_indices]
            
            boot_model = self.model_map[model_name](**params)
            boot_model.fit(boot_X, boot_y)
            
            y_pred_boot = boot_model.predict(boot_X)
            boot_r2, boot_rmse, boot_mae = self._evaluate_predictions(boot_y, y_pred_boot)
            
            y_pred_orig_boot_model = boot_model.predict(X_combined)
            orig_r2_from_boot, orig_rmse_from_boot, orig_mae_from_boot = self._evaluate_predictions(y_combined, y_pred_orig_boot_model)
            
            r2_optimism.append(boot_r2 - orig_r2_from_boot)
            rmse_optimism.append(orig_rmse_from_boot - boot_rmse)
            mae_optimism.append(orig_mae_from_boot - boot_mae)

            all_predictions.append(y_pred_orig_boot_model)

        avg_r2_optimism = np.mean(r2_optimism)
        avg_rmse_optimism = np.mean(rmse_optimism)
        avg_mae_optimism = np.mean(mae_optimism)
        
        adjusted_r2 = original_r2 - avg_r2_optimism
        adjusted_rmse = original_rmse + avg_rmse_optimism
        adjusted_mae = original_mae + avg_mae_optimism

        mean_pred = np.mean(all_predictions, axis=0)

        self._plot_predictions(y_combined, mean_pred, f'{model_name}')
        
        return {
            'r2': adjusted_r2,
            'rmse': adjusted_rmse,
            'mae': adjusted_mae
        }

    def train_glm_model(self):
        X_combined = pd.concat([self.X_train, self.X_test]).reset_index(drop=True).astype(float)
        y_combined = pd.concat([self.y_train, self.y_test]).reset_index(drop=True).astype(float)
        X_combined_glm = sm.add_constant(X_combined)
        
        model_orig = sm.GLM(y_combined, X_combined_glm, family=sm.families.Gaussian())
        results_orig = model_orig.fit()
        y_pred_orig = results_orig.predict(X_combined_glm)
        original_r2, original_rmse, original_mae = self._evaluate_predictions(y_combined, y_pred_orig)
        
        r2_optimism, rmse_optimism, mae_optimism = [], [], []
        n_obs = len(X_combined)

        for i in tqdm(range(100), desc="ping GLM"):
            boot_indices = np.random.choice(n_obs, size=n_obs, replace=True)
            boot_X = X_combined.iloc[boot_indices]
            boot_y = y_combined.iloc[boot_indices]
            boot_X_glm = sm.add_constant(boot_X)

            boot_model = sm.GLM(boot_y, boot_X_glm, family=sm.families.Gaussian())
            boot_results = boot_model.fit()
            
            y_pred_boot = boot_results.predict(boot_X_glm)
            boot_r2, boot_rmse, boot_mae = self._evaluate_predictions(boot_y, y_pred_boot)
            
            y_pred_orig_boot_model = boot_results.predict(X_combined_glm)
            orig_r2_from_boot, orig_rmse_from_boot, orig_mae_from_boot = self._evaluate_predictions(y_combined, y_pred_orig_boot_model)
            
            r2_optimism.append(boot_r2 - orig_r2_from_boot)
            rmse_optimism.append(orig_rmse_from_boot - boot_rmse)
            mae_optimism.append(orig_mae_from_boot - boot_mae)

        avg_r2_optimism = np.mean(r2_optimism)
        avg_rmse_optimism = np.mean(rmse_optimism)
        avg_mae_optimism = np.mean(mae_optimism)

        adjusted_r2 = original_r2 - avg_r2_optimism
        adjusted_rmse = original_rmse + avg_rmse_optimism
        adjusted_mae = original_mae + avg_mae_optimism
        
        print(f"\n--- GLM Final Results  ---")
        print(f"Optimism-Adjusted R²: {adjusted_r2:.4f}")
        print(f"Optimism-Adjusted RMSE: {adjusted_rmse:.2f}")
        print(f"Optimism-Adjusted MAE: {adjusted_mae:.2f}")

        self._plot_predictions(y_combined, y_pred_orig, 'GLM')
        return {'r2': adjusted_r2, 'rmse': adjusted_rmse, 'mae': adjusted_mae}
  
    def train_dnn_model(self, epochs=10000, lr=0.001):
        class SimpleDNN(nn.Module):
            def __init__(self, input_size):
                super(SimpleDNN, self).__init__()
                self.fc1 = nn.Linear(input_size, 128)
                self.relu1 = nn.ReLU()
                self.fc2 = nn.Linear(128, 64)
                self.relu2 = nn.ReLU()
                self.fc3 = nn.Linear(64, 1)

            def forward(self, x):
                x = self.fc1(x)
                x = self.relu1(x)
                x = self.fc2(x)
                x = self.relu2(x)
                x = self.fc3(x)
                return x

        input_size = self.X_train_tensor.shape[1]
        model = SimpleDNN(input_size)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=lr)

        y_train_tensor_transformed = self.y_train_tensor

        for epoch in tqdm(range(epochs), desc="Training DNN"):
            model.train()
            optimizer.zero_grad()
            outputs = model(self.X_train_tensor)
            loss = criterion(outputs, y_train_tensor_transformed)
            loss.backward()
            optimizer.step()
        
        model.eval()
        with torch.no_grad():
            y_predict_tensor = model(self.X_test_tensor)
            
            y_predict = y_predict_tensor.numpy().flatten()
            y_test = self.y_test_tensor.numpy().flatten()
            
            y_predict[y_predict < 0] = 0

        r2 = r2_score(y_test, y_predict)
        rmse = mean_squared_error(y_test, y_predict, squared=False)
        mae = mean_absolute_error(y_test, y_predict)

        print(f"\n--- DNN Final Results ---")
        print(f"R²: {r2:.4f}")
        print(f"RMSE: {rmse:.2f}")
        print(f"MAE: {mae:.2f}")

        self._plot_predictions(y_test, y_predict, 'DNN')
        return {'r2': r2, 'rmse': rmse, 'mae': mae}