# TrafficGPT

[![Static Badge](https://img.shields.io/badge/Readme-English-blue)
](https://github.com/lijlansg/TrafficGPT/tree/main)[![Static Badge](https://img.shields.io/badge/Readme-Chinese-red)
](https://github.com/lijlansg/TrafficGPT/blob/main/readme.zh.md)
[![Static Badge](https://img.shields.io/badge/Paper-Arxiv-red)](https://arxiv.org/abs/2309.06719)

## Installation

TrafficGPT does not require installation, you should just clone the code and run locally.

```Powershell
clone https://github.com/lijlansg/TrafficGPT.git
cd TrafficGPT
```

The operation of TrafficGPT requires the following software support:

- Python
- [SUMO](https://sumo.dlr.de/docs/Downloads.php)
- [PostgreSQL](https://www.postgresql.org/download/)

At the same time, please install the required third-party libraries:

```Powershell
pip install -r requirements
```

## Configuration

### LLM Configuration

First, you need to configure OpenAI-Key. Please create a `./config.yaml` file in the root directory and add the following content to the file (please modify the content to your own settings):

```yaml
OPENAI_API_TYPE: 'azure' #'azure'  OR 'openai'
# for 'openai'
OPENAI_KEY: 'sk-xxxxxxxxxxx' # your openai key
# for 'azure'
AZURE_MODEL: 'XXXXX' # your deploment_model_name 
AZURE_API_BASE: https://xxxxxxxx.openai.azure.com/ # your deployment endpoint
AZURE_API_KEY: 'xxxxxx' # your deployment key
AZURE_API_VERSION: '2023-03-15-preview'
```

Here we recommend using ChatGPT-3.5 to run as LLM. If you want to use your own LLM, please refer to [LangChain-Large Language Models](https://python.langchain.com/docs/modules/model_io/models/) to define Your own LLM. In this case, please modify the following sections in `./DataProcessBot.py` and `./SimulationProcessBot.py` to configure your own LLM.

```Python
OPENAI_CONFIG = yaml.load(open('config.yaml'), Loader=yaml.FullLoader)
if OPENAI_CONFIG['OPENAI_API_TYPE'] == 'azure':
    os.environ["OPENAI_API_TYPE"] = OPENAI_CONFIG['OPENAI_API_TYPE']
    os.environ["OPENAI_API_VERSION"] = OPENAI_CONFIG['AZURE_API_VERSION']
    os.environ["OPENAI_API_BASE"] = OPENAI_CONFIG['AZURE_API_BASE']
    os.environ["OPENAI_API_KEY"] = OPENAI_CONFIG['AZURE_API_KEY']
    llm = AzureChatOpenAI(
        deployment_name=OPENAI_CONFIG['AZURE_MODEL'],
        temperature=0,
        max_tokens=1024,
        request_timeout=60
    )
elif OPENAI_CONFIG['OPENAI_API_TYPE'] == 'openai':
    os.environ["OPENAI_API_KEY"] = OPENAI_CONFIG['OPENAI_KEY']
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo-16k-0613',  # or any other model with 8k+ context
        max_tokens=1024,
        request_timeout=60
    )
```

Fine, now, you can run `./SimulationProcessBot.py`.

```Powershel
python ./SimulationProcessBot.py
```

### Database Configuration

Then, in order to run `./DataProcessBot.py`, we need to configure the database. Until then, please refer to [Github:OpenITS-PG-SUMO
](https://github.com/Fdarco/OpenITS-PG-SUMO) Import data into a PostgreSQL database.

Afterwards, your database should contain the following four data tables: `topo_centerroad`, `spatial_ref_sys`, `zone_roads`, `the_synthetic_individual_level_trip_dataset`.
In order to simplify the real-time query operation, two new tables need to be created in the following query sequence: `road_level_trip_dataset` and `road_volume_per_hour`.

1. Create `road_level_trip_dataset`：
```sql
CREATE TABLE road_level_trip_dataset (
  trip_id INT,
  traveller_id VARCHAR(50),
  traveller_type VARCHAR(50),
  departure_time TIMESTAMP,
  time_slot VARCHAR(50),
  o_zone VARCHAR(50),
  d_zone VARCHAR(50),
  path VARCHAR(50),
  duration FLOAT
);

INSERT INTO road_level_trip_dataset
SELECT
  trip_id,
  traveller_id,
  traveller_type,
  departure_time,
  time_slot,
  o_zone,
  d_zone,
  path::VARCHAR, 
  duration
FROM
  (
    WITH split_paths AS (
      SELECT
        trip_id,
        traveller_id,
        traveller_type,
        departure_time,
        time_slot,
        o_zone,
        d_zone,
        unnest(string_to_array(path, '-')) AS path,
        duration
      FROM
        the_synthetic_individual_level_trip_dataset
    )
    SELECT * FROM split_paths
  ) AS split_data;
```
2. Create `road_volume_per_hour`
```sql
CREATE TABLE road_volume_per_hour (
  hour_start TIMESTAMP,
  road VARCHAR(50),
  road_count INT
);

INSERT INTO road_volume_per_hour
SELECT
  DATE_TRUNC('hour', departure_time) AS hour_start,
  path AS road, 
  COUNT(*) AS road_count
FROM road_level_trip_dataset
GROUP BY hour_start, road
ORDER BY hour_start, road;
```

After all data tables are created, please create a `./dbconfig.yaml` file in the root directory and write the following content into the file:

```yaml
username: your_user_name
password: your_password
host: localhost
port: 5432
db_name: OPENITS
```

Fine, now, you can run `./DataProcessBot.py`.

```Powershell
python ./DataProcessBot.py
```

## Demo 

### Simple Commands Multi-round dialogue

https://github.com/lijlansg/TrafficGPT/assets/26219929/c8765850-1e16-41e5-bf2b-de558a6acb12

### Fuzzy Instructions and Human Intervention

https://github.com/lijlansg/TrafficGPT/assets/26219929/ac017333-0683-4128-a25c-3b8bee5df786

### Insightfull Assitance

https://github.com/lijlansg/TrafficGPT/assets/26219929/feba9e3d-0fc2-4bae-9763-224f817e772f

# Contact 

If you have any questions or suggestions about this project, please send me an Issue and PR, or contact us by email: siyaozhang@buaa.edu.cn
