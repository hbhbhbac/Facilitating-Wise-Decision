import pandas as pd
import json
import pandas as pd
from sklearn.preprocessing import *
from sklearn.model_selection import *
from sklearn.svm import *
from sklearn.naive_bayes import *
from sklearn.neighbors import *
from sklearn.ensemble import *
from sklearn.tree import *
from sklearn.metrics import *
import xgboost as xgb

times = 10
label = 'have_changed'
columns = ['issue_len_description', 'time_limit',
           'bounty_num', 'bounty_change_num', 'bounty_amount',
           'title_len','owner_follwers', 'until_time', 'until_fulfilment']
cat_columns = ['project_length_Hours', 'project_length_Days', 'project_length_Weeks', 'project_length_Months',
               "bounty_type_Bug", "bounty_type_Design", "bounty_type_Feature",
               "bounty_type_Improvement","bounty_type_Project","bounty_type_Security",
               'experience_level_Advanced','experience_level_Intermediate',
               'never_expires']

with open('bestParams.json', 'r') as fp:
    dictModelParams = json.load(fp)

params_xgb = {
    'objective':'binary:logistic',
    'eval_metric':'auc'
}
params_xgb = dict(params_xgb, **dictModelParams['xgb'])

import numpy as np

best_auc = 0

for i in range(times):
    df = pd.read_csv('features.csv')
    df_not_changed = df[df['have_changed'] == 1]
    df_pos_changed = df[df['have_changed'] == 2]
    df_neg_changed = df[df['have_changed'] == 0]
    
    pnum = len(df_pos_changed)
    nnum = len(df_neg_changed)
    snum = len(df_not_changed)
    
    scaler = MinMaxScaler(feature_range=(-1,1))

    p1 = df[df['have_changed'] == 2].sample(n = int(pnum * 0.8))
    n1 = df[df['have_changed'] == 0].sample(n = int(nnum * 0.8))
    s1 = df[df['have_changed'] == 1].sample(n = int(snum * 0.8))

    train = pd.concat([p1, n1])
    df = df.drop(train.index)

    Y_train_origin = train[label]
    X_train, Y_train = np.c_[scaler.fit_transform(train[columns].values), train[cat_columns].values], Y_train_origin


    test = pd.concat([p1, n1])
    X_test = np.c_[scaler.fit_transform(test[columns].values), test[cat_columns].values]
    Y_test = test[label]

    xgbModel = xgb.XGBClassifier(**params_xgb)
    xgbModel.fit(X_train, Y_train)
    Y_predict = xgbModel.predict(X_test)
    auc = roc_auc_score(Y_test, Y_predict)

    if auc > best_auc:
        best_auc = auc
        best_feautres = xgbModel.feature_importances_

import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.size'] = 10

columns.extend(cat_columns)

dataList = []
for index in range(len(columns)):
    dataList.append([columns[index], best_feautres[index]])
df = pd.DataFrame(dataList, columns=['features', 'feature_importances'])
fig = plt.figure(figsize=(12, 5), dpi=200)
df = df.sort_values('feature_importances',ascending=False).head(5)
academic_colors = ['#4e79a7', '#f28e2c', '#59a14f', '#edc949', '#af7aa1', '#76b7b2', '#e15759', '#b07aa1', '#ff9d9a', '#9c755f']
academic_colors = academic_colors[:len(df.index) + 1]
bars = plt.bar(df['features'], df['feature_importances'], color = academic_colors)

plt.savefig(f"feature_importances.pdf", dpi=200)





