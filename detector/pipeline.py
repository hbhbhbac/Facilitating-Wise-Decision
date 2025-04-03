import os
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, roc_auc_score, recall_score, f1_score
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import xgboost as xgb

CONFIG = {
    "experiment": {
        "times": 10,
        "test_size": 0.2,
        "random_state": 42,
        "results_dir": "modelResults"
    },
    "data": {
        "file_path": "features.csv",
        "label": "have_changed",
        "numeric_features": [
            'issue_len_description', 'time_limit', 'bounty_num',
            'bounty_change_num', 'bounty_amount', 'title_len',
            'owner_follwers', 'until_time', 'until_fulfilment'
        ],
        "categorical_features": [
            'project_length_Hours', 'project_length_Days', 
            'project_length_Weeks', 'project_length_Months',
            "bounty_type_Bug", "bounty_type_Design", "bounty_type_Feature",
            "bounty_type_Improvement", "bounty_type_Project", "bounty_type_Security",
            'experience_level_Advanced', 'experience_level_Intermediate',
            'never_expires'
        ]
    },
    "best_params_exist": True,
    "models": {
        "xgb": {
            "class": xgb.XGBClassifier,
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [3, 5, 7],
                "learning_rate": [0.01, 0.1, 0.2],
                "subsample": [0.8, 1.0],
                "colsample_bytree": [0.8, 1.0],
                "gamma": [0, 1]
            }
        },
        "svmRbf": {
            "class": SVC,
            "params": {
                "kernel": ["rbf"],
                "C": [0.1, 1, 10],
                "gamma": [0.01, 0.1, 1]
            }
        },
        "knn": {
            "class": KNeighborsClassifier,
            "params": {
                "n_neighbors": [3, 5, 7],
                "weights": ["uniform", "distance"],
                "metric": ["euclidean", "manhattan"]
            }
        },
        "svmLinear": {
            "class": SVC,
            "params": {
                "kernel": ["linear"],
                "C": [0.1, 1, 10]
            }
        },
        "naive_bayes": {
            "class": GaussianNB,
            "params": {
            }
        },
        "decision_tree": {
            "class": DecisionTreeClassifier,
            "params": {
                "criterion": ["gini", "entropy"],
                "max_depth": [None, 5, 10],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4]
            }
        },
        "random_forest": {
            "class": RandomForestClassifier,
            "params": {
                "n_estimators": [100, 200],
                "max_depth": [None, 5, 10],
                "min_samples_split": [2, 5, 10],
                "min_samples_leaf": [1, 2, 4],
                "bootstrap": [True, False]
            }
        }
    }
}

class ExperimentRunner:
    def __init__(self, config):
        self.config = config
        self.results = {}
        self._prepare_directories()
        
    def _prepare_directories(self):
        os.makedirs(self.config["experiment"]["results_dir"], exist_ok=True)

    def load_data(self):
        df = pd.read_csv(self.config["data"]["file_path"])
        return df

    def preprocess_data(self, df):
        scaler = MinMaxScaler()
        numeric_features = self.config["data"]["numeric_features"]
        categorical_features = self.config["data"]["categorical_features"]
        

        X_numeric = scaler.fit_transform(df[numeric_features])
        X_categorical = df[categorical_features].values
        X = np.hstack([X_numeric, X_categorical])
        y = df[self.config["data"]["label"]]
        return X, y

    def tune_hyperparameters(self, X_train, y_train):
        best_params = {}
        for model_name, model_config in tqdm(self.config["models"].items(), desc="Tuning Models"):
            gs = GridSearchCV(
                estimator=model_config["class"](),
                param_grid=model_config["params"],
                scoring="roc_auc_ovr",
                cv=5,
                n_jobs=-1
            )
            gs.fit(X_train, y_train)
            best_params[model_name] = gs.best_params_
        
        params_path = os.path.join(self.config["experiment"]["results_dir"], "bestParams.json")
        with open(params_path, "w") as f:
            json.dump(best_params, f)
        return best_params

    def initialize_models(self, best_params):
        models = {}
        for model_name, model_config in self.config["models"].items():
            model_class = model_config["class"]
            params = best_params.get(model_name, {})
            if model_name.startswith("svm"):
                params["probability"] = True
            models[model_name] = model_class(**params)
        return models

    def evaluate_model(self, model, X_test, y_test):
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)
        
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "roc_auc_ovr": roc_auc_score(y_test, y_proba, multi_class="ovr"),
            "roc_auc_classes": roc_auc_score(y_test, y_proba, multi_class="ovr", average=None),
            "recall": recall_score(y_test, y_pred, average="macro"),
            "f1": f1_score(y_test, y_pred, average="macro")
        }
        return metrics

    def run_experiments(self):
        df = self.load_data()
        exp_results = {model: [] for model in self.config["models"]}

        for exp_num in tqdm(range(self.config["experiment"]["times"]), desc="Running Experiments"):
            train_df, test_df = train_test_split(
                df,
                test_size=self.config["experiment"]["test_size"],
                stratify=df[self.config["data"]["label"]],
                random_state=self.config["experiment"]["random_state"] + exp_num
            )
            

            X_train, y_train = self.preprocess_data(train_df)
            X_test, y_test = self.preprocess_data(test_df)

            best_params_exist = self.config["best_params_exist"]
            if not best_params_exist:
                best_params = self.tune_hyperparameters(X_train, y_train)
                self.config["best_params_exist"] = True
            else:
                with open(os.path.join(self.config["experiment"]["results_dir"], "bestParams.json"), 'r') as f:
                    best_params = json.load(f)
            
            models = self.initialize_models(best_params)
            for model_name, model in models.items():
                model.fit(X_train, y_train)
                metrics = self.evaluate_model(model, X_test, y_test)
                exp_results[model_name].append(metrics)
                
        self.save_results(exp_results)
        return exp_results

    def save_results(self, results):
        records = []
        for model_name, metrics_list in results.items():
            for exp_num, metrics in enumerate(metrics_list):
                record = {
                    "model": model_name,
                    "roc_auc_ovr": metrics["roc_auc_ovr"],
                }
                for i, auc in enumerate(metrics["roc_auc_classes"]):
                    record[f"auc_class_{i}"] = auc
                records.append(record)
        
        results_df = pd.DataFrame(records)
        results_path = os.path.join(self.config["experiment"]["results_dir"], "all_results.csv")
        results_df.to_csv(results_path, index=False)

if __name__ == "__main__":
    runner = ExperimentRunner(CONFIG)
    final_results = runner.run_experiments()