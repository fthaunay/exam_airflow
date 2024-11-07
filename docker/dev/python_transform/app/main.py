import os
import pandas as pd
import json

def transform_data_into_csv(n_files=None, filename='data.csv'):
    parent_folder = '/home/ubuntu/airflow_dst/raw_files'
    # parent_folder = 'raw_files'
    files = sorted(os.listdir(parent_folder), reverse=True)
    if n_files:
        files = files[:n_files]
    dfs = []

    for f in files:
        with open(os.path.join(parent_folder, f), 'r') as file:
            data_temp = json.load(file)
            
        for data_city in data_temp:
            data_temp[data_city] = json.loads(data_temp[data_city])
            dfs.append(
                {
                    'temperature': data_temp[data_city]['main']['temp'],
                    'city': data_temp[data_city]['name'],
                    'pression': data_temp[data_city]['main']['pressure'],
                    'date': f.split('.')[0]
                }
            )

    df = pd.DataFrame(dfs)

    print('\n', df.head(10))

    p = '/app/clean_data'
    # p = 'clean_data'
    df.to_csv(os.path.join(p, filename), index=False)

if __name__ == '__main__':
    transform_data_into_csv()
