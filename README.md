# Construire l'image du container 1 (download des raw depuis OpenWeather). 
# Depuis airflow_dst/docker/dev/python_load 
docker build -t python_load .
# Lancer le container
docker run -it -v $PWD/app:/app --name python_load python_load bash
# Execution de la fonction Python de download depuis le container
python3 main.py 
# -> ecrit bien dans app/raw_files



# Construire l'image des containers 2 et 3 (transformer les raw_files au format csv.). 
# Depuis airflow_dst/docker/dev/python_transform
docker build -t python_transform .
# Lancer le container
docker run -it -v $PWD/app:/app --name python_transform python_transform bash
# Execution de la fonction Python de download depuis le container
python3 main.py 
# -> ecrit bien dans app/clean_data