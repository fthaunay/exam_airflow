import requests
import datetime
import time
import json
from pathlib import Path
#Path("/app/raw_files").mkdir(parents=True, exist_ok=True)

def get_data():
    filename = datetime.datetime.today().strftime("%Y-%m-%d %H:%m")
    with open(f"/app/raw_files/{filename}.json", "w") as outfile:
        for city in ['paris', 'london', 'washington']:
            r = requests.get(
                    url='http://api.openweathermap.org/data/2.5/weather',
                    
                    params = {
                'q': city,
                'appid': 'a23000e179258d19cf0fbe51908d00d1'
                }
                )

            json_object = json.dumps(r.json())

    
            outfile.write(json_object)

if __name__ == '__main__':
    get_data()
    

             