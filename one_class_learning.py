# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %% [markdown]
# # Libaries

# %%
#Data Structures and Utilities
import numpy as np
import pandas as pd
import time
import os

# Learning evaluation
from  sklearn.model_selection import KFold
from sklearn.metrics import f1_score
from sklearn.metrics import accuracy_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score

from sklearn.metrics import roc_auc_score
from sklearn.metrics import confusion_matrix



# %% [markdown]
# # Definitions

# %%
SEED = 42
np.random.seed(SEED) #seed for random selections



# %% [markdown]
# # Functions

# %%
#Split the dataset into train and test data

# split_type: type os splitting of the examples from the interest class: "cross-validation" or "random"
# number: number of folds in case of type == "cross-validation", or number or examples in case of type == "random"
def get_indexes(data, split_type, number_trials, number_examples): 
    indexes = []
    if split_type == 'cross-validation': 
        kf = KFold(n_splits=number_trials, shuffle=True, random_state=SEED)
        for ids_train, ids_test in kf.split(data):
            indexes_train = data[ids_train]
            indexes.append(indexes_train)
    elif split_type == 'random':
        for it in range(number_trials):
            indexes.append(np.random.choice(data, size=number_examples, replace=False))
    else:
        raise ValueError('Unsuported split type. Please, use split_type = {"cross-validation","random"}.')
    return indexes


# %%
def get_train_test_data(X, all_indexes, indexes_train):
    indexes_test = list(set(all_indexes) - set(indexes_train))
    return X[indexes_train], X[indexes_test]


# %%
def get_classes_test(y, classe, all_indexes, indexes_train): 
    indexes_test = list(set(all_indexes) - set(indexes_train))
    y_test = np.ones(len(indexes_test), dtype=np.int)
    for i, element in enumerate(y[indexes_test]): 
        if element != classe: 
            y_test[i] = -1
    return y_test


# %%
def get_evaluation_metrics(classifier, X_test, y_test, classe, num_labeled_exs, it_number, model_building_time=0): 
  
  evaluation = {} 
  start_time_classification = time.time()
  predictions = classifier.predict(X_test)
  elapsed_time_classification = (time.time() - start_time_classification) / 1000
  evaluation['Algorithm'] = classifier.__class__.__name__
  evaluation['Parameters'] = str(classifier.get_params())
  evaluation['Class'] = classe
  evaluation['Number_Labeled_Examples'] = num_labeled_exs
  evaluation['Iteration'] = it_number
  evaluation['Accuracy'] = accuracy_score(y_test,predictions)
  evaluation['Precision'] = precision_score(y_test,predictions)
  evaluation['Recall'] = recall_score(y_test,predictions)
  evaluation['F1'] = f1_score(y_test,predictions)
  evaluation['ROC_AUC'] = roc_auc_score(y_test,predictions,average=None)
  evaluation['Building_Time'] = model_building_time
  evaluation['Confusion_Matrix'] = confusion_matrix(y_test,predictions).tolist()
  evaluation['Classification_Time'] = elapsed_time_classification
  evaluation['Memory'] = sys.getsizeof(classifier) / 1024
  
  return evaluation 


# %%
def get_data_frame(path_results): 
    results = None 
    if (os.path.exists(path_results)):
        results = pd.read_csv(path_results)
    else: 
        results = pd.DataFrame(columns=['Algorithm',
            'Parameters',
            'Class',
            'Number_Labeled_Examples',
            'Iteration',
            'Accuracy',
            'Precision',
            'Recall',
            'F1',
            'ROC_AUC',  
            'Building_Time',
            'Confusion_Matrix',
            'Classification_Time',
            'Memory'
        ])
    return results


# %%
def check_exp(results, classifier, classe, iteration, num_labeled_exes): 
    if len(results[(results['Algorithm'] == classifier.__class__.__name__) &  (results['Parameters'] == str(classifier.get_params())) & (results['Class'] == classe) & (results['Number_Labeled_Examples'] == num_labeled_exes) & (results['Iteration'] == iteration)]) > 0: 
        return False
    else: 
        return True
    


# %%
#X: dada
#y: classes
# split_type: type os splitting of the examples from the interest class: "cross-validation" or "random"
#classifier: OCL algorithm
# number_trials: number of folds in case of split_type == "cross-validation", or number or repetitions in case of split_type == "random"
# number_examples: number of labeled_examples if split_type == "random"
def one_class_learning(X, y, classifier, path_results, split_type='cross-validation', number_trials=10, number_examples=10): 
    current_results = get_data_frame(path_results)
    all_indexes = set(range(len(X)))
    classes = np.unique(y)
    for classe in classes: 
        classe_indexes = np.argwhere(y == classe).reshape(-1)
        for it, indexes_train in enumerate(get_indexes(classe_indexes, split_type, number_trials, number_examples)):
            X_train, X_test = get_train_test_data(X, all_indexes, indexes_train)
            y_test = get_classes_test(y, classe, all_indexes, indexes_train)
            num_labeled_exes = len(X_train)
            if check_exp(current_results, classifier, classe, it, num_labeled_exes):
                classifier.fit(X_train)
                result = get_evaluation_metrics(classifier, X_test, y_test, classe, num_labeled_exes, it, model_building_time=0)
                print(result, '\n')
                current_results = current_results.append(result,ignore_index=True)
                current_results.to_csv(config['path_results'], index=False)
    


# %%
def execute_exp(X, y, classifier, config): 
    path_results = None
    if 'path_results' not in config: 
        raise ValueError('Config file must be a "path_result" entry')
    else: 
        path_results = config['path_results']
    if 'path_dataset' not in config: 
        raise ValueError('Config file must be a "path_dataset" entry')
    if 'algorithms' not in config: 
        raise ValueError('Config file must be a "algorithm" entry')
    if len(config['algorithms']) == 0:
        raise ValueError('At least one algorhtm should be specified')
    
    number_trials = None 
    if 'number_trials' not in config: 
        number_trials=10
    else: 
        number_trials= config['number_trials']

    number_examples = None 
    if 'number_examples' not in config:
        number_examples = 10
    else: 
        number_examples = config['number_examples']

    split_type = None
    if 'split_type' not in config: 
        split_type = 'cross-validation'
        number_examples=None
    else: 
        split_type = config['split_type']

    one_class_learning(X, y, classifier, path_results, split_type=split_type, number_trials=number_trials, number_examples=number_examples)

    print('Done')



