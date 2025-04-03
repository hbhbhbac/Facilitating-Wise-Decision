import pandas as pd
import os
import json
import pandas as pd
from tqdm import tqdm
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


def tuneParams(X_train, Y_train):
    params_rf = {
        'n_estimators':range(10, 110, 10),
    }

    params_svm_rbf = {
        'C':[0.25, 0.5, 1, 2, 4],
        'gamma':[0.1, 0.3, 0.5, 0.7, 0.9],
    }

    params_knn = {
        'n_neighbors':[1, 5, 9, 13, 17]
    }

    params_dt = {
        'criterion':['gini', 'entropy']
    }
    
    params_xgb = {
        'n_estimators':range(10, 110, 10),
        'learning_rate':[0.01, 0.05, 0.1, 0.4, 0.5, 0.6],
    }

    xgbModel = xgb.XGBClassifier(objective='binary:logistic', eval_metric='auc')
    svmModel = SVC(kernel='rbf', max_iter=1000, probability=True)
    knnModel = KNeighborsClassifier()
    dtModel = DecisionTreeClassifier()
    rfModel = RandomForestClassifier()


    modelList = [xgbModel, svmModel, knnModel, dtModel, rfModel]
    paramsList = [params_xgb, params_svm_rbf, params_knn, params_dt, params_rf]
    modelName = ['xgb', 'svmRbf', 'knn', 'dt', 'rf']
    bestParamsList = {}

    roc_auc_scorer = make_scorer(roc_auc_score, multi_class='ovr', needs_proba=True)

    for i in tqdm(range(len(modelList))):
        model = GridSearchCV(modelList[i], paramsList[i], cv=5, scoring=roc_auc_scorer)
        model.fit(X_train, Y_train)
        bestParamsList[modelName[i]] = model.best_params_

    with open('bestParams.json', 'w') as fp:
        json.dump(bestParamsList, indent=4, fp=fp)


modelNameList = ['nb', 'svmLinear', 'svmRbf', 'knn', 'dt', 'rf', 'xgb']
dictModelResults = {}
for modelName in modelNameList:
    dictModelResults[modelName] = {'auc':[], 'acc':[], 'recall':[], 'f1Score':[]}

import numpy as np

for i in range(times):
    df = pd.read_csv('features.csv')
    df_not_changed = df[df['have_changed'] == 1]
    df_pos_changed = df[df['have_changed'] == 2]
    df_neg_changed = df[df['have_changed'] == 0]

    pnum = len(df_pos_changed)
    nnum = len(df_neg_changed)
    snum = len(df_not_changed)

    print(pnum, nnum, snum)

    scaler = MinMaxScaler(feature_range=(-1,1))

    p1 = df[df['have_changed'] == 2].sample(n = int(pnum * 0.8))
    n1 = df[df['have_changed'] == 0].sample(n = int(nnum * 0.8))
    s1 = df[df['have_changed'] == 1].sample(n = int(snum * 0.8))

    train = pd.concat([p1, n1, s1])

    df = df.drop(train.index)

    Y_train_origin = train[label]
    X_train, Y_train = np.c_[scaler.fit_transform(train[columns].values), train[cat_columns].values], Y_train_origin
    
    
    test = df

    X_test = np.c_[scaler.fit_transform(test[columns].values), test[cat_columns].values]
    Y_test = test[label]

    # tuneParams(X_train, Y_train)

    dictModelParams = {}
    with open('bestParams.json', 'r') as fp:
        dictModelParams = json.load(fp)
    
    params_xgb = {
        'objective':'binary:logistic',
        'eval_metric':'auc'
    }
    params_xgb = dict(params_xgb, **dictModelParams['xgb'])


    params_svmRbf = dictModelParams['svmRbf']
    params_svmRbf['kernel'] ='rbf'
    params_svmRbf['max_iter'] = 1000
    params_svmRbf['probability'] = True

    params_knn = dictModelParams['knn']
    params_dt = dictModelParams['dt']
    params_rf = dictModelParams['rf']
    params_svmLinear = {
            'kernel':'linear',
            'C':1,
            'max_iter':1000,
            'probability': True
    }

    nbModel = GaussianNB()
    svmLinearModel = SVC(**params_svmLinear)
    svmRbfModel = SVC(**params_svmRbf)
    knnModel = KNeighborsClassifier(**params_knn)
    dtModel = DecisionTreeClassifier(**params_dt)
    rfModel = RandomForestClassifier(**params_rf)
    xgbModel = xgb.XGBClassifier(**params_xgb)
    xgbModel.fit(X_train, Y_train)
    xgbModel.save_model('xgboost_model.json')
    # break

    modelList = [nbModel, svmLinearModel, svmRbfModel, knnModel, dtModel, rfModel, xgbModel]


    for index in range(len(modelNameList)):
        X_train_new = X_train
        X_test_new = X_test

        modelList[index].fit(X_train_new, Y_train)
        print(modelNameList[index] + ' train done !!!')
        Y_predict = modelList[index].predict(X_test_new)
        Y_predict_proba = modelList[index].predict_proba(X_test_new) 
        accList = dictModelResults[modelNameList[index]]['acc']
        aucList = dictModelResults[modelNameList[index]]['auc']
        recallList = dictModelResults[modelNameList[index]]['recall']
        f1ScoreList = dictModelResults[modelNameList[index]]['f1Score']
        accList.append(accuracy_score(Y_test, Y_predict))
        aucList.append(roc_auc_score(Y_test, Y_predict_proba, multi_class='ovr'))
        recallList.append(recall_score(Y_test, Y_predict, average='macro'))
        f1ScoreList.append(f1_score(Y_test, Y_predict, average='macro'))
        dictModelResults[modelNameList[index]]['auc'] = aucList
        dictModelResults[modelNameList[index]]['recall'] = recallList
        dictModelResults[modelNameList[index]]['f1Score'] = f1ScoreList
        dictModelResults[modelNameList[index]]['acc'] = accList

modelResultsList = []
modelAccList = []
modelAucList = []
modelRecallList = []
modelF1ScoreList = []

for model in dictModelResults:
    for i in range(times):
        modelResults = []
        modelResults.append(dictModelResults[model]['acc'][i])
        modelResults.append(dictModelResults[model]['auc'][i])
        modelResults.append(dictModelResults[model]['recall'][i])
        modelResults.append(dictModelResults[model]['f1Score'][i])
        modelResults.append(model)
        modelResultsList.append(modelResults)
    modelAccList.append(dictModelResults[model]['acc'])
    modelAucList.append(dictModelResults[model]['auc'])
    modelRecallList.append(dictModelResults[model]['recall'])
    modelF1ScoreList.append(dictModelResults[model]['f1Score'])

modelAccList = list(map(list, zip(*modelAccList)))
modelAucList = list(map(list, zip(*modelAucList)))
modelRecallList = list(map(list, zip(*modelRecallList)))
modelF1ScoreList = list(map(list, zip(*modelF1ScoreList)))

dfModelResults = pd.DataFrame(modelResultsList, columns=['acc', 'auc', 'recall', 'f1Score','group'])
dfModelAcc = pd.DataFrame(modelAccList, columns=modelNameList)
dfModelAuc = pd.DataFrame(modelAucList, columns=modelNameList)
dfRecall = pd.DataFrame(modelRecallList, columns=modelNameList)
dfF1Score = pd.DataFrame(modelF1ScoreList, columns=modelNameList)

todir = 'modelResults'
if not os.path.exists(todir):
    os.mkdir(todir)

dfModelResults.to_csv(todir + f'/modelResults.csv', index=False)
dfModelAcc.to_csv(todir + f'/acc.csv', index=False)
dfModelAuc.to_csv(todir + f'/auc.csv', index=False)
dfRecall.to_csv(todir + f'/recall.csv', index=False)
dfF1Score.to_csv(todir + f'/f1Score.csv', index=False)


    
