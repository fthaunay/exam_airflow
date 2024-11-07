from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.dummy import DummyOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.operators.python import get_current_context
import random
import sys
from pathlib import Path
import os
# Add parent directory to path
parent_folder = str(Path(__file__).parent)
sys.path.append(parent_folder)


import requests
import datetime
import time
import json
from pathlib import Path
#Path("/app/raw_files").mkdir(parents=True, exist_ok=True)

def get_data():
    filename = datetime.datetime.today().strftime("%Y-%m-%d %H:%m")
    with open(f"/app/raw_files/{filename}.json", "w") as outfile:
        objects = []
        for city in ['paris', 'london', 'washington']:
            r = requests.get(
                    url='http://api.openweathermap.org/data/2.5/weather',
                    
                    params = {
                'q': city,
                'appid': 'a23000e179258d19cf0fbe51908d00d1'
                }
                )

            objects.append(r.json())
        json_object = json.dumps(objects)

    
        outfile.write(json_object)
            



import os
import pandas as pd
import json

def transform_data_into_csv(n_files=None, filename='data.csv'):
    parent_folder = '/app/raw_files'
    files = sorted(os.listdir(parent_folder), reverse=True)
    if n_files:
        files = files[:n_files]
    dfs = []

    for f in files:
        with open(os.path.join(parent_folder, f), 'r') as file:
            data_temp = json.load(file)
            
        for data_city in data_temp:
            # data_city = json.loads(data_city)
            dfs.append(
                {
                    'temperature': data_city['main']['temp'],
                    'city': data_city['name'],
                    'pression': data_city['main']['pressure'],
                    'date': f.split('.')[0]
                }
            )

    df = pd.DataFrame(dfs)

    print('\n', df.head(10))

    p = '/app/clean_data'
    df.to_csv(os.path.join(p, filename), index=False)


import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
pd.options.mode.chained_assignment = None

from joblib import dump


def train_and_save_model(model, X, y, path_to_model='.app/model.pckl'):
    # training the model
    model.fit(X, y)
    # saving model
    print(str(model), 'saved at ', path_to_model)
    dump(model, path_to_model)



def train_and_score_model(model_name, **kwargs):
    X, y = prepare_data('/app/clean_data/fulldata.csv')
    models = {'LinearRegression': LinearRegression(),
               'DecisionTreeRegressor': DecisionTreeRegressor(),
               'RandomForestRegressor':  RandomForestRegressor()}
    model = models[model_name]
    score = compute_model_score(model, X, y)

    ti = kwargs['ti']
    ti.xcom_push(key='score', value=score)
    return




import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
pd.options.mode.chained_assignment = None

from joblib import dump


def compute_model_score(model, X, y):
    #raise ValueError(f'A very specific bad thing happened. {len(X)}')
    # computing cross val
    cross_validation = cross_val_score(
        model,
        X,
        y,
        cv=3,
        scoring='neg_mean_squared_error')

    model_score = cross_validation.mean()

    return model_score


def train_and_save_model(model, X, y, path_to_model='.app/model.pckl'):
    # training the model
    model.fit(X, y)
    # saving model
    print(str(model), 'saved at ', path_to_model)
    dump(model, path_to_model)


def prepare_data(path_to_data):
    # reading data
    df = pd.read_csv(path_to_data)
    assert len(df) > 0, (len(df), path_to_data)
    # ordering data according to city and date
    df = df.sort_values(['city', 'date'], ascending=True)

    dfs = []

    for c in df['city'].unique():
        df_temp = df[df['city'] == c]

        # creating target
        df_temp.loc[:, 'target'] = df_temp['temperature'].shift(1)

        # creating features
        for i in range(1, 10):
            df_temp.loc[:, 'temp_m-{}'.format(i)
                        ] = df_temp['temperature'].shift(-i)

        # deleting null values
        df_temp = df_temp.dropna()

        dfs.append(df_temp)

    # concatenating datasets
    df_final = pd.concat(
        dfs,
        axis=0,
        ignore_index=False
    )

    # deleting date variable
    df_final = df_final.drop(['date'], axis=1)

    # creating dummies for city variable
    df_final = pd.get_dummies(df_final)

    features = df_final.drop(['target'], axis=1)
    target = df_final['target']

    return features, target





def train_best_model(score_lr, score_dt, score_rf):

    X, y = prepare_data('/app/clean_data/fulldata.csv')

    models = [LinearRegression(), DecisionTreeRegressor(), RandomForestRegressor()]

    scores = [score_lr, score_dt, score_rf]
    
    best_model = models[scores.index(max(scores))]


    train_and_save_model(
            best_model,
            X,
            y,
            '/app/clean_data/best_model.pickle'
        )

    

    


def push_xcom(**kwargs):
    # La fonction qui pousse une valeur dans XCom
    ti = kwargs['ti']
    # On pousse une valeur (par exemple, un string ou un dict)
    ti.xcom_push(key='example_key', value='Hello from the previous task!')

def pull_xcom(**kwargs):
    # La fonction qui récupère la valeur du XCom
    ti = kwargs['ti']
    value = ti.xcom_pull(task_ids='push_task', key='example_key')
    print(f"Value pulled from XCom: {value}")
    # Faites quelque chose avec la valeur récupérée
    return value




@task
def function_with_return():
    return random.uniform(a=0, b=1)

@task
def function_with_return_and_push():
    task_instance = get_current_context()['task_instance']
    value = train_and_score_model(mypath, 'LinearRegression')
    task_instance.xcom_push(key="score_lr", value=value)
    return value


@task
def function_with_return_and_push():
    task_instance = get_current_context()['task_instance']
    value = train_and_score_model(mypath, 'DecisionTreeRegressor')
    task_instance.xcom_push(key="score_dt", value=value)
    return value


@task
def function_with_return_and_push():
    task_instance = get_current_context()['task_instance']
    value = train_and_score_model(mypath, 'RandomForestRegressor')
    task_instance.xcom_push(key="score_rf", value=value)
    return value



@task
def read_data_from_xcom(my_xcom_value):
    print(my_xcom_value)


def read_score_from_xcom(task_instance, task_id):
    print(
        task_instance.xcom_pull(
            key="score",
            task_ids=[task_id]
        )
    )



@dag(
    dag_id='openweatherdata_dag',
    tags=['exam', 'datascientest'],
    schedule_interval=None,
    start_date=days_ago(0),
    default_args={
        'owner': 'airflow',
        'start_date': days_ago(0, minute=1),
    },
    catchup=False
)
def my_dag():

        # Définition des tâches
    

    # Définition de l'ordre des tâches
    start_task = DummyOperator(task_id='start_task')

    # (1) Récupération de données depuis l'API OpenWeatherMap

    task_1 = PythonOperator(
        task_id='task_1',
        python_callable=get_data,
        provide_context=True,
    )

    # task_1 = DockerOperator(
    #    task_id='task_1',
    #    image='python_load'
    #)

    # La tâche (2) devra prendre les 20 derniers fichiers,
    #  les concaténer et les transformer dans un fichier data.csv 
    # alors que la tâche (3) devra prendre en compte tous les fichiers dans le dossier
    #  et créer un fichier fulldata.csv.

    # Le premier fichier sera utilisé par le dashboard pour visualiser les dernières observations
    #  alors que le deuxième fichier sera utilisé dans la suite du DAG pour entraîner un algorithme.


    task_2 = PythonOperator(
        task_id='task_2',
        python_callable=transform_data_into_csv,
        op_kwargs={"filename": 'data.csv',
                   "n_files":20}
        
    )


    # task_2 = DockerOperator(
    #    task_id='task_2',
    #    image='python_transform',
    #    n_files=20, filename='data.csv'
    #)


    task_3 = PythonOperator(
        task_id='task_3',
        python_callable=transform_data_into_csv,
        op_kwargs={"filename": 'fulldata.csv'}
        
    )

    # task_3 = DockerOperator(
    #    task_id='task_3',
    #    image='python_transform',
    #    op_kwargs={"filename": 'fulldata.csv'}
    #)


    # Les tâches (4'), (4'') et (4''') correspondent à l'entraînement de différents modèles de régression
    #  (respectivement LinearRegression, DecisionTreeRegressor, RandomForestRegressor).
    #  Une fois ces modèles entraînés et testés avec une méthode de validation croisée,
    #  on pourra utiliser un XCom pour transmettre la valeur du score de validation. 


    with TaskGroup("group_4") as group_4:

        task_4a = PythonOperator(
            task_id='task_4a',
            python_callable=train_and_score_model,
            op_kwargs={"model_name": 'RandomForestRegressor'}
        
        )



        #task_4a = DockerOperator(
        #    task_id='task_4a',
        #    image='python_train',
        #    model_name='LinearRegression',
        #    xcom_push=True
        #)


        task_4b = PythonOperator(
            task_id='task_4b',
            python_callable=train_and_score_model,
            op_kwargs={"model_name": 'DecisionTreeRegressor'}
        
        )
        #task_4b = DockerOperator(
        #    task_id='task_4b',
        #    image='python_train',
        #    model_name='DecisionTreeRegressor',
        #    xcom_push=True
        #)

        task_4c = PythonOperator(
            task_id='task_4c',
            python_callable=train_and_score_model,
            op_kwargs={"model_name": 'RandomForestRegressor'}
        
        )
        
        #task_4c = DockerOperator(
        #    task_id='task_4c',
        #    image='python_train',
        #    model_name='RandomForestRegressor',
        #    xcom_push=True
        #)

    # La tâche (5) permettra de choisir le meilleur modèle, de le réentraîner sur toutes les données et de le sauvegarder.  
    
    task_5 = PythonOperator(
            task_id='task_5',
            python_callable=train_best_model,
            op_kwargs={
           'score_lr': '{{ task_instance.xcom_pull(task_ids="task_4a", key="score") }}',
           'score_dt': '{{ task_instance.xcom_pull(task_ids="task_4b", key="score") }}',
           'score_rf': '{{ task_instance.xcom_pull(task_ids="task_4c", key="score") }}'
    },
            
        )
    # task_5 = DockerOperator(
    #        task_id='task_5',
    #        image='python_selection',
    #        environment={
    #       'score_lr': '{{ task_instance.xcom_pull(task_ids="task_4a", key="score") }}',
    #       'score_dt': '{{ task_instance.xcom_pull(task_ids="task_4b", key="score") }}',
    #       'score_rf': '{{ task_instance.xcom_pull(task_ids="task_4c", key="score") }}'
    #},
            
    #    )

    start_task >> task_1
    task_1 >> [task_2, task_3]
    task_3 >> group_4 >> task_5  


my_dag = my_dag()







