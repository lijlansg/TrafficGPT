import sqlalchemy as sa
import yaml

def fetch_from_database(query):

    # 读取配置文件
    with open("dbconfig.yaml", "r") as f:
        config = yaml.safe_load(f)

    # 连接到PostgreSQL数据库
    db_uri = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['db_name']}"
    engine = sa.create_engine(db_uri)
    conn = engine.connect()
    
    # 执行查询
    query_obj = sa.text(query)
    result = conn.execute(query_obj)
    conn.close()
    return result
