import pandas as pd
import matplotlib.pyplot as plt

from LLMAgent.dbConnector import fetch_from_database
from LLMAgent.plotGeoMap import plot_geo_heatmap, plot_road_segements, plot_OD_map
from LLMAgent.getTime import get_time_period, get_fake_current_time


def prompts(name, description):
    def decorator(func):
        func.name = name
        func.description = description
        return func

    return decorator



class roadVolumeTrend:
    def __init__(self, figfolder: str) -> None:
        self.figfolder = figfolder

    @prompts(name='Visualize Road Traffic Trends',
             description="""
            This tool is used to show the traffic volume trend of several target roads on a specific day by visualize it on a histogram.
            Use this tool more than others if the question is about traffic trends.
            The output will tell you whether you have finished this command successfully.
            The input should be one sigle semicolon-separated string that separate two parts of information, and the two parts to the left and right of the semicolon are date and roadID, respectively. 
            The input date should be an integer, representing the day of the month. The input roadID should be a "|" seperated string, representing the id of the target roads. For example: 15;1076|30188""")
    def inference(self, target: str) -> str:

        day, road_id = target.replace(' ', '').split(';')

        # query
        query = f"""
        select date_trunc('hour', departure_time) as hours, count(*) as volume  
        from the_synthetic_individual_level_trip_dataset
        where path similar to '%({road_id})%' AND extract(day from departure_time) = {day}
        group by hours
        order by hours;
        """

        rows = fetch_from_database(query)

        time = []
        volume = []
        for row in rows:
            time.append(row[0].strftime('%Y-%m-%d %H'))
            volume.append(row[-1])


        plt.figure(figsize=(16,8),dpi=300)
        plt.bar(time,volume)
        plt.xticks(rotation=70)
        fig_path = f'{self.figfolder}volume_bar.png'
        plt.savefig(fig_path, dpi=300)

        return f"You have successfully visualized the Road Traffic Trends. And your final answer should include this sentence without changing anything: The histogram showing the traffic trend is kept at: `{fig_path}`."


class roadVolume:
    def __init__(self) -> None:
        pass

    @prompts(name='Get Road Volume',
             description="""
            This tool is used to count the traffic volume of roads during a specific time period.
            Use this tool more than others if the question is about specific traffic volume.
            The output will provid road volume information in a tabular dataset.
            The input should be one sigle semicolon-separated string that separate two parts of information, and the two parts to the left and right of the semicolon are time_period and targets, respectively: 
            1. The time_period: The input time_period should be a comma seperated string, with each part representing the start and end date and time of the time_period in the "YYYY-MM-DD HH:MM:SS" format.
            2. The targets: If you do not have information of any specific road ID, the input should be a string: 'None', and the tool will output an overview data for the final answer. If you have specific target road IDs, the input should be a comma seperated string, with each part representing a target road ID. Only if you can find a word 'all' in the human message, the input can be a string: 'All'.
            For example: 2019-08-13 08:00:00,2019-08-13 09:00:00;None  /  2019-08-13 08:00:00,2019-08-13 09:00:00;2023,3486""")
    def inference(self, inputs: str) -> str:
        
        time_period, target = inputs.split(';')
        begin, end = time_period.split(',')
        if 'None' in target or 'All' in target:
            # print('no target' + target.replace(' ', ''))
            have_target = False
            target_road_id = []
        else:
            have_target = True
            target_road_id = target.split(',')
            # print('target'+ str(target.replace(' ', '').split(','))) 
            idlist = ', '.join(f"'{item}'" for item in target_road_id)
        
        # query
        if have_target == False and 'None' in target:
            query = f"""
            select road as road_id, SUM(road_count) as volume
            from road_volume_per_hour
            WHERE hour_start >= '{begin}' AND hour_start < '{end}'
            group by road_id
            ORDER BY volume DESC
            LIMIT 5;
            """
        elif have_target == False and 'All' in target:
            query = f"""
            select road as road_id, SUM(road_count) as volume
            from road_volume_per_hour
            WHERE hour_start >= '{begin}' AND hour_start < '{end}'
            group by road_id
            ORDER BY volume DESC
            """
        else:
            query = f"""
            select road as road_id, SUM(road_count) as volume
            from road_volume_per_hour
            WHERE hour_start >= '{begin}' AND hour_start < '{end}' AND road IN ({idlist})
            group by road_id
            ORDER BY volume DESC
            """

        rows = fetch_from_database(query)
        data = pd.DataFrame(rows,columns=['road_id','volume'])

        if 'None' in target:
            msg = 'No specific target roads. The human user just wants to see an overview. So, I can show you the overview by providing traffic data for the 5 highest volume roads by default. Make sure you output the tabular content in markdown format into your final answer. \n'
            return msg + data.to_markdown()
        elif 'All' in target:
            msg = 'Here are the traffic volume of all roads. Make sure you output the tabular content in markdown format into your final answer. \n'
            return msg + data.to_markdown()
        else:
            msg = 'Here are the traffic status of your targeted roads. Make sure you output the tabular content in markdown format into your final answer. \n'
            return msg + data.to_markdown()


class roadNameToID:
    def __init__(self) -> None:
        pass

    @prompts(name='Get Road_ID From Road Name',
             description="""
            This tool is used to get the specific road id according to road names.
            Use this tool before others if the target road info given by human user is the Name of Road rather than ids(which is series of figures). In this case, use this tool to get the road id as input for other tools.
            The output will tell you the id of the road that corresponds to the road name in a tabular dataset.
            The input should be a string representing the road name, for example: 青弋江西大道.
            NOTE that a road name may correspond to several road ids, remember them all! """)
    def inference(self, target: str) -> str:

        road_name = target.replace(' ', '')

        # query
        query = f"""
        select objectid,mc
        from topo_centerroad
        where mc = '{road_name}'
        """

        rows = fetch_from_database(query)
        data = pd.DataFrame(rows,columns=['road_id','road_name'])
        road_id_list = data['road_id'].tolist()
        road_ids = ', '.join(str(int(road)) for road in road_id_list)
        msg = f'Here are the road ids of all roads corresponding to the road name {road_name}:'
        return msg + road_ids


class plotGeoHeatmap:
    def __init__(self, figfolder: str) -> None:
        self.figfolder = figfolder

    @prompts(name='Plot Heatmap',
             description="""
            This tool is used to show the traffic status of the network by ploting a heatmap of the road network at a certain point in time.
            If you do not have a specific point in time, use "Get Current Time" tool to get the time before using this tool.
            Use this tool more than others if the human user want to see the traffic status of the network.
            The output will tell you the file path of the heat mapas a supplementary information for you to provide the final answer. 
            The input must be the target point in time in the "YYYY-MM-DD HH:MM:SS" format. 
            
            """)
    def inference(self, time: str) -> str:
        try:
            start, end = get_time_period(time)
        except:
            return "Wrong format of input parameters, The input must be the target point in time in the 'YYYY-MM-DD HH:MM:SS' format."

        # query
        query = f"""SELECT mc, objectid, volume, geom 
        FROM topo_centerroad join (
        select road as road_ID, SUM(road_count) as volume
        from road_volume_per_hour
        WHERE hour_start >= '{start}' AND hour_start < '{end}'
        group by road_ID) as traffic_volume
        on CAST(ROUND(objectid) as varchar) = traffic_volume.road_ID;"""

        fig_path = plot_geo_heatmap(query,self.figfolder)

        return f"The heat map is ploted according to traffic volume data at {time}. And your final answer should include this sentence without changing anything: the road network heat map is kept at: `{fig_path}`."
    

class getCurrentTime:
    def __init__(self) -> None:
        pass

    @prompts(name='Get Current Time',
             description="""
            This tool is used to get the current date and time.
            Use this tool before others if you need to know the current date and time.
            The output will tell you the current time in the "YYYY-MM-DD HH:MM:SS" format.
            """)
    def inference(self, time: str) -> str:

        # 根据数据库数据，获取虚拟的当前时间
        current_time = get_fake_current_time()

        return f"The current time is {current_time}"
    

class roadVisulization:
    def __init__(self, figfolder: str) -> None:
        self.figfolder = figfolder

    @prompts(name='Visualize Roads',
             description="""
            This tool is used to show the locations of several target roads by visualize them on a map.
            Use this tool more than others if the question is about locations of roads.
            The output will tell you whether you have finished this command successfully.
            The input should be a comma seperated string, with each part be a series of figures representing a target road_id. 
            For example: 1076,30188 """)
    def inference(self, target: str) -> str:

        road_ids = target.replace(' ', '')

        fig_path = plot_road_segements(road_ids, self.figfolder)

        return f"You have successfully visualized the location of road {target} on the following map. And your final answer should include the following sentence without changing words: The location of road {target} is kept at: `{fig_path}`."
    

class odVolume:
    def __init__(self) -> None:
        pass

    @prompts(name='Get OD Volume',
             description="""
            This tool is used to count the traffic volume of OD pairs during a specific time period.
            Use this tool more than others if the question is about OD pair traffic volume.
            The output will provid OD pair volume information in a tabular dataset.
            The input should be one sigle semicolon-separated string that separate two parts of information, and the two parts to the left and right of the semicolon are time_period and Number of data items you want to see, respectively: 
            1. The time_period: The input time_period should be a comma seperated string, with each part representing the start and end date and time of the time_period in the "YYYY-MM-DD HH:MM:SS" format.
            2. Number of data items: If you want to see the traffic volume data of OD pairs with top 10 traffic volume, the input should be 10. If no specific number of data items given, the input should be 5 as default.
            For example: 2019-08-13 08:00:00,2019-08-13 09:00:00;5 """)
    def inference(self, inputs: str) -> str:
        time_period, number = inputs.split(';')
        begin, end = time_period.split(',')
        if number == "None":
            N =5
        else:
            N = eval(number)

        query = f"""
        SELECT o_zone, d_zone, COUNT(*) AS od_pair_volume
        FROM the_synthetic_individual_level_trip_dataset
        WHERE departure_time >= '{begin}' AND departure_time < '{end}'
        GROUP BY o_zone, d_zone
        ORDER BY od_pair_volume DESC
        LIMIT {N};"""

        rows = fetch_from_database(query)
        data = pd.DataFrame(rows,columns=['o_zone','d_zone','od_pair_volume'])

        msg = f'Here are the traffic volume data of top{N} OD pairs. Make sure you output the tabular content in markdown format into your final answer. \n'
        return msg + data.to_markdown()
    

class odMap:
    def __init__(self, figfolder: str) -> None:
        self.figfolder = figfolder

    @prompts(name='Plot OD Map',
             description="""
            This tool is used to visulize the traffic volume of OD pairs during a specific time period on a OD map.
            Use this tool more than others if the question is about OD map.
            The output will tell you the file path of the OD map as a supplementary information for you to provide the final answer. 
            The input time_period should be a comma seperated string, with each part representing the start and end date and time of the time_period in the "YYYY-MM-DD HH:MM:SS" format.
            
            """)
    def inference(self, time: str) -> str:

        begin, end = time.split(',')
        
        fig_path = plot_OD_map(begin, end, self.figfolder)

        return f"The OD map is ploted according to traffic volume data at from {begin} to {end}. And your final answer should include this sentence without changing anything: The OD map is kept at: `{fig_path}`."
    