from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.dummy import DummyOperator
from airflow.operators.docker import DockerOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
from airflow.operators.python import get_current_context
import random


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

    from ..docker.dev.python_load.app.main import get_data
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


    from ..docker.dev.python_transform.app.main import transform_data_into_csv
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

    from ..docker.dev.python_train.app.main import train_and_score_model
    

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
    
    from ..docker.dev.python_selection.app.main import train_and_score_model 
    task_5 = PythonOperator(
            task_id='task_5',
            python_callable='train_best_model',
            environment={
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

    start_task >> [task_1, task_2]
    task_3 >> group_4 >> task_5  


my_dag = my_dag()







