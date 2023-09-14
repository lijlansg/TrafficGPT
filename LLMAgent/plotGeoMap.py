import geopandas as gpd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colorbar import ColorbarBase
import sqlalchemy as sa
import yaml


def plot_geo_heatmap(query,figfolder):
    
    # 读取配置文件
    with open("dbconfig.yaml", "r") as f:
        config = yaml.safe_load(f)

    # 连接到PostgreSQL数据库
    db_uri = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['db_name']}"
    engine = sa.create_engine(db_uri)
    conn = engine.connect()
    query_obj = sa.text(query)
    
    # 获取几何数据和交通流量数据
    gdf = gpd.GeoDataFrame.from_postgis(query_obj, conn, geom_col='geom')

    # 关闭数据库连接
    conn.close()

    # 创建渐变颜色映射和线条宽度映射
    colors = [(0, 1, 0), (1, 1, 0), (1, 0, 0)]  # 绿-黄-红的渐变色
    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=100)
    volume_normalized = (gdf['volume'] - gdf['volume'].min()) / (gdf['volume'].max() - gdf['volume'].min())

    # 设置绘图参数
    fig, ax = plt.subplots(figsize=(8, 6), dpi=800)
    ax.set_aspect('equal')

    # 绘制地图，根据交通流量数据设置颜色和线条宽度
    gdf['geom'].plot(ax=ax, cmap=cmap, linewidth=volume_normalized * 5)

    # 添加颜色图例（放在左侧）
    cax_position = [0.08, 0.25, 0.02, 0.5]
    norm = plt.Normalize(gdf['volume'].min(), gdf['volume'].max())
    cax = fig.add_axes(cax_position)  # 调整位置参数
    cb = ColorbarBase(cax, cmap=cmap, norm=norm, orientation='vertical')

    # 添加标题
    cb_title = 'Traffic Volume'
    cb_title_fontsize = 12
    plt.text(cax_position[0] + cax_position[2] / 2 + 0.01, cax_position[1] + cax_position[3] + 0.01,
            cb_title, fontsize=cb_title_fontsize, ha='center', va='bottom', fontname='Times New Roman', weight='bold', transform=fig.transFigure)

    # 隐藏坐标轴
    ax.set_axis_off()

    # 输出热力图
    fig_path = f'{figfolder}heatmap.png'
    fig.savefig(fig_path, dpi=800)
    return fig_path


def plot_road_segements(road_ids,figfolder):
    
    # 读取配置文件
    with open("dbconfig.yaml", "r") as f:
        config = yaml.safe_load(f)

    # 连接到PostgreSQL数据库
    db_uri = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['db_name']}"
    engine = sa.create_engine(db_uri)
    conn = engine.connect()

    # 获取几何数据和路名id
    query1 = "SELECT mc, objectid, geom FROM topo_centerroad"
    query1_obj = sa.text(query1)
    gdf1 = gpd.GeoDataFrame.from_postgis(query1_obj, conn, geom_col='geom')

    query2 = f"SELECT mc, objectid, geom FROM topo_centerroad WHERE objectid IN ({road_ids})"
    query2_obj = sa.text(query2)
    gdf2 = gpd.GeoDataFrame.from_postgis(query2_obj, conn, geom_col='geom')

    # 关闭数据库连接
    conn.close()

    # 设置参数
    annotation_params = {'fontsize': 8, 'color': 'black', 'fontname':'Times New Roman', 'weight':'bold'}  # 标注文本的参数
    fig, ax = plt.subplots(figsize=(8, 6), dpi=800)

    # 绘制地图，根据颜色数据设置颜色
    ax = gdf1['geom'].plot(ax=ax,color= 'grey')
    ax = gdf2['geom'].plot(ax=ax,color= 'red')

    # 标注每条路的id
    for idx, row in gdf2.iterrows():
        ax.text(row['geom'].centroid.x, row['geom'].centroid.y, int(row['objectid']), **annotation_params)

    fig_path = f'{figfolder}roads.png'
    fig.savefig(fig_path, dpi=800)
    return fig_path

def plot_OD_map(begin, end, figfolder):

    # 读取配置文件
    with open("dbconfig.yaml", "r") as f:
        config = yaml.safe_load(f)

    # 连接到PostgreSQL数据库
    db_uri = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['db_name']}"
    engine = sa.create_engine(db_uri)
    conn = engine.connect()

    # 获取OD数据
    query1 = f"""
    SELECT o_zone, d_zone, od_pair_count, ST_MakeLine(ST_MakePoint(ozone_long, ozone_lat), ST_MakePoint(dzone_long, dzone_lat)) AS geom 
    from (
            SELECT
                o_zone,
                d_zone,
                od_pair_count,
                ozone_info.longitude AS ozone_long,
                ozone_info.latitude AS ozone_lat,
                dzone_info.longitude AS dzone_long,
                dzone_info.latitude AS dzone_lat
            FROM
                (
                    SELECT
                        o_zone,
                        d_zone,
                        od_pair_count
                    FROM
                        (SELECT o_zone, d_zone, COUNT(*) AS od_pair_count
                                    FROM the_synthetic_individual_level_trip_dataset
                                    WHERE departure_time >= '{begin}' AND departure_time < '{end}'
                                    GROUP BY o_zone, d_zone
                                    ORDER BY od_pair_count DESC) as od_pair_count
                ) AS od
            JOIN
                zone_roads AS ozone_info ON od.o_zone = ozone_info.zone_id
            JOIN
                zone_roads AS dzone_info ON od.d_zone = dzone_info.zone_id
            ) as OD_volume;
    """
    query1_obj = sa.text(query1)
    gdf1 = gpd.GeoDataFrame.from_postgis(query1_obj, conn, geom_col='geom')

    # 获取地图数据
    query2 = "SELECT mc, objectid, geom FROM topo_centerroad"
    query2_obj = sa.text(query2)
    gdf2 = gpd.GeoDataFrame.from_postgis(query2_obj, conn, geom_col='geom')

    # 关闭数据库连接
    conn.close()

    # 创建渐变颜色映射（绿-黄-红）
    colors = [(0, 1, 0), (1, 1, 0), (1, 0, 0)]  # 绿-黄-红的渐变色
    cmap = LinearSegmentedColormap.from_list('custom_cmap', colors, N=100)
    volume_normalized = (gdf1['od_pair_count'] - gdf1['od_pair_count'].min()) / (gdf1['od_pair_count'].max() - gdf1['od_pair_count'].min())

    # 设置绘图参数
    fig, ax = plt.subplots(figsize=(8, 6), dpi=800)
    ax.set_aspect('equal')

    # 绘制地图，根据交通流量数据设置颜色和线条宽度
    gdf1['geom'].plot(ax=ax, cmap=cmap, linewidth=volume_normalized*5)
    gdf2['geom'].plot(ax=ax,color= 'grey')

    cax_position = [0.08, 0.25, 0.02, 0.5]
    norm = plt.Normalize(gdf1['od_pair_count'].min(), gdf1['od_pair_count'].max())
    cax = fig.add_axes(cax_position)  # 调整位置参数
    cb = ColorbarBase(cax, cmap=cmap, norm=norm, orientation='vertical')
    # cb.set_label('Traffic Volume', rotation=270, labelpad=15)  # 设置颜色图例标题

    # 添加标题
    cb_title = 'Traffic Volume'
    cb_title_fontsize = 12
    plt.text(cax_position[0] + cax_position[2] / 2 + 0.01, cax_position[1] + cax_position[3] + 0.01,
            cb_title, fontsize=cb_title_fontsize, ha='center', va='bottom', fontname='Times New Roman', weight='bold', transform=fig.transFigure)

    ax.set_axis_off()

    fig_path = f'{figfolder}ODmap.png'
    fig.savefig(fig_path, dpi=800)
    return fig_path
