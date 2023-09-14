# TrafficGPT

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

然后，请在根目录下创建 `./dbconfig.yaml` 文件，并将如下内容写入文件中：

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

