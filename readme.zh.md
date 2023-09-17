# TrafficGPT

[![Static Badge](https://img.shields.io/badge/Readme-English-blue)
](https://github.com/lijlansg/TrafficGPT/tree/main)[![Static Badge](https://img.shields.io/badge/Readme-Chinese-red)
](https://github.com/lijlansg/TrafficGPT/blob/main/readme.zh.md) [![Static Badge](https://img.shields.io/badge/Paper-Arxiv-red)](https://arxiv.org/abs/2309.06719)

## Installation

TrafficGPT 无需安装，可以选择直接将代码 clone 到本地运行。

```Powershell
clone https://github.com/lijlansg/TrafficGPT.git
cd TrafficGPT
```

TrafficGPT 的运行需要如下的软件支持：

- Python
- [SUMO](https://sumo.dlr.de/docs/Downloads.php)
- [PostgreSQL](https://www.postgresql.org/download/)

同时，请安装所需第三方库：

```Powershell
pip install -r requirements
```

## Configuration

### LLM Configuration

首先，需要配置 OpenAI-Key，请在根目录下创建 `./config.yaml` 文件，并将下面的内容添加到该文件中（请将其中的内容修改为你自己的设置）：

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

这里我们推荐使用 ChatGPT-3.5 作为 LLM 运行，如果你要使用自己的 LLM，请参考 [LangChain-Large Language Models](https://python.langchain.com/docs/modules/model_io/models/) 来定义你自己的 LLM。在这种情况下，请修改 `./DataProcessBot.py` 和 `./SimulationProcessBot.py` 中的如下部分，来配置你自己的 LLM。

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

至此，你可以运行 `./SimulationProcessBot.py` 了。

```Powershel
python ./SimulationProcessBot.py
```

### Database Configuration

然后，为了运行 `./DataProcessBot.py`，我们需要配置数据库。在此之前，请参考 [Github:OpenITS-PG-SUMO
](https://github.com/Fdarco/OpenITS-PG-SUMO) 将数据导入到 PostgreSQL 数据库中。

之后，你的数据库应该包含以下四个表：`topo_centerroad` ,`spatial_ref_sys` , `zone_roads` , `the_synthetic_individual_level_trip_dataset`。
为了简化实时查询操作，还需要按照以下查询顺序创建2个新表：`road_level_trip_dataset` 和 `road_volume_per_hour`。

1. 建立`road_level_trip_dataset`：
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
2. 建立`road_volume_per_hour`
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

在所有数据表创建完成后，请在根目录下创建 `./dbconfig.yaml` 文件，并将如下内容写入文件中：

```yaml
username: your_user_name
password: your_password
host: localhost
port: 5432
db_name: OPENITS
```

至此，你可以运行 `./DataProcessBot.py` 了。

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

如果你对该项目有任何疑问或建议，请给我们提 Issue 和 PR，或者直接邮件联系我们，Email: iyaozhang@buaa.edu.cn
