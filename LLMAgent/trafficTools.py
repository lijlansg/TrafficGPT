
import os
import sys
import pandas as pd
import traci
from sumolib import checkBinary

from LLMAgent.buildGraph import Lane, Edge, Junction, Graph, build_graph
from LLMAgent.websterOptimize import Webster
from LLMAgent.plotIntersections import plot_intersections
from LLMAgent.plotHeatmap import plot_heatmap
from LLMAgent.readDump import read_last_dump


def prompts(name, description):
    def decorator(func):
        func.name = name
        func.description = description
        return func

    return decorator


class simulationControl:
    def __init__(self, sumocfgfile: str, netfile: str, dumpfile: str, originalstatefile: str, tempstatefile: str, figfolder: str) -> None:
        self.sumocfgfile = sumocfgfile
        self.netfile = netfile
        self.dumpfile = dumpfile
        self.originalstatefile = originalstatefile
        self.tempstatefile = tempstatefile
        self.figfolder = figfolder

    @prompts(name='Simulation Controller',
             description="""
             This tool is used to proceed and run the traffic simulation on SUMO. 
             The output will tell you whether you have finished this command successfully.
             This tool will also return the file path of a heat map of the road network as a supplementary information for you to provide the final answer. 
             The input should be a string, representing how many times have you called this tool, which shoule be a number greater than or equal to 0. 
             For example: if you never called this tool before and this is your first time calling this tool, the input should be 0; if you have called this tool twice, the imput should be 2.""")
    def inference(self, ordinal: str) -> str:
        ordinal_number = eval(ordinal)
        STEP = 600

        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            raise RuntimeError(
                "please declare environment variable 'SUMO_HOME'")

        if_show_gui = False

        if not if_show_gui:
            sumoBinary = checkBinary('sumo')
        else:
            sumoBinary = checkBinary('sumo-gui')

        traci.start([sumoBinary, "-c", self.sumocfgfile])
        print('start reading state')
        if ordinal_number > 0:
            traci.simulation.loadState(self.tempstatefile)
        else:
            traci.simulation.loadState(self.originalstatefile)

        start_time = int(traci.simulation.getTime() / 1000)
        print('read state done!')
        for step in range(start_time, start_time + STEP):
            traci.simulationStep()

        traci.simulation.saveState(self.tempstatefile)

        traci.close()
        args = f'''-v -n {self.netfile} --measures speed,occupancy -i {self.dumpfile} \
            --default-width .5 --colormap RdYlGn  --max-width 3 --min-width .5 \
            --min-color-value 0 --max-color-value 15 --max-width-value 100 --min-width-value 0'''
        fig_path = plot_heatmap(self.figfolder, args)

        return f"You have successfully proceeded the traffic simulation on SUMO for 600 seconds. And your final answer should include this sentence without changing anything: the road network heat map is kept at: `{fig_path}`."


class intersectionPerformance:
    def __init__(self, netfile: str, dumpfile: str) -> None:
        self.netfile = netfile
        self.dumpfile = dumpfile

    @prompts(name='Get Intersection Performance',
             description="""
            This tool is used to get the traffic performance of all the intersections or several target intersections in the simulation road network.
            The output will provid traffic status information of intersetions in a tabular dataset.
            with various columns, such as Junction_id, speed_avg, volume_avg, and timeLoss_avg. Each row represents data for a specific junction. 
            Include the tabular dataset in markdown formart directly in your final answer! Do not try to change anything including the format! 
            The input If you do not have information of any specific intersection ID and the human didn't specify to get information of all the intersections, the input should be a string: 'None', and the tool will give you an overview data for the final answer so you don't need more specific information about certain intersections. 
            If you have specific target intersection IDs, the input should be a comma seperated string, with each part representing a target intersection ID.
            Only if you can find a word 'all' in the human message, the input can be a string: 'All'. """)
    def inference(self, target: str) -> str:

        if 'None' in target.replace(' ', '') or 'All' in target.replace(' ', ''):
            # print('no target' + target.replace(' ', ''))
            have_target = False
            target_junction_id = []
        else:
            have_target = True
            target_junction_id = target.replace(' ', '').split(',')
            # print('target'+ str(target.replace(' ', '').split(',')))

        graph = build_graph(self.netfile)
        edgedata = read_last_dump(self.dumpfile)

        junction_list = graph.junctions
        junction_summary_table = pd.DataFrame(
            columns=['Juction_id', 'speed_avg', 'volume_avg', 'timeLoss_avg'])
        for j_id, junction in junction_list.items():
            if len(junction.inEdges) <= 2:
                continue
            # print(j_id)
            if have_target and j_id not in target_junction_id:
                continue
            # print(j_id)
            upstream_list = []
            for edge in junction.inEdges:
                upstream_list.append(edge.id[0])
            junction_data = edgedata[edgedata["edgeID"].isin(upstream_list)]
            speed_avg = (
                junction_data['speed'] * junction_data['left']).sum() / junction_data['left'].sum()
            waitingTime_avg = (
                junction_data['waitingTime'] * junction_data['left']).sum() / junction_data['left'].sum()
            timeLoss_avg = (
                junction_data['timeLoss'] * junction_data['left']).sum() / junction_data['left'].sum()
            volume_avg = (
                junction_data['speed'] * 3.6 * junction_data['density']).mean()
            junction_summary_dic = {"Juction_id": j_id, "speed_avg": speed_avg,
                                    "volume_avg": volume_avg, "timeLoss_avg": timeLoss_avg}
            new_row = pd.DataFrame(junction_summary_dic, index=[0])
            junction_summary_table = pd.concat(
                [junction_summary_table, new_row], axis=0).reset_index(drop=True)
            # print(junction_summary_dic)
        sorted_table = junction_summary_table.sort_values(
            by=['speed_avg', 'volume_avg', 'timeLoss_avg'], ascending=[True, False, False]).reset_index(drop=True)
        # print(sorted_table)
        if 'None' in target.replace(' ', ''):
            msg = 'No specific target intersections. So, I can show you the overview by providing the traffic status of 5 intersections in the worst operating condition by default. Make sure you output the tabular content in markdown format into your final answer. \n'
            return msg + sorted_table.head().to_markdown()
        elif 'All' in target.replace(' ', ''):
            msg = 'Here are the traffic status of all intersections. Make sure you output the tabular content in markdown format into your final answer. \n'
            return msg + sorted_table.to_markdown()
        else:
            msg = 'Here are the traffic status of your targeted intersections. Make sure you output the tabular content in markdown format into your final answer. \n'
            return msg + sorted_table.to_markdown()


class intersectionSignalOptimization:
    def __init__(self, netfile: str, configfile: str, routefile: str, tlsfile: str) -> None:
        self.netfile = netfile
        self.configfile = configfile
        self.routefile = routefile
        self.tlsfile = tlsfile

    @prompts(name='Optimize Intersection Signal Control Scheme',
             description="""
            This tool is used to optimize the signal control scheme of several target intersections in the simulation road network.
            Do not use this tool unless the human user asks to optimize intersections.
            The output will tell you whether you have finished this command successfully.
            The input should be a comma seperated string, with each part representing a target intersection ID. """)
    def inference(self, target: str) -> str:

        if 'None' in target:
            return "Please provide the target intersection IDs."

        options = f'-n {self.netfile} -f {self.configfile} -r {self.routefile} -o {self.tlsfile}'
        target_ID = target.replace(' ', '').split(',')

        optimizer = Webster(target_ID, options)
        optimizer.run_webster()
        optimizer.add_TLS()

        return f"The signal control scheme for intersection {target} has already been optimized successfully according to Webster's algorithm. The new TLS program has been written to the configuration file. If you want to see the traffic status after the optimization, you need to run the simulation again."


class intersectionVisulization:
    def __init__(self, netfile: str, figfolder: str) -> None:
        self.netfile = netfile
        self.figfolder = figfolder

    @prompts(name='Visualize Intersections',
             description="""
            This tool is used to show the locations of several target intersections by visualize them on a map.
            Use this tool more than others if the question is about locations of intersections.
            The output will tell you whether you have finished this command successfully.
            The input should be a comma seperated string, with each part representing a target intersection ID. """)
    def inference(self, target: str) -> str:

        target_junction_id = target.replace(' ', '').split(',')
        options = f'-n {self.netfile} --width 5 --edge-color #606060'

        fig_path = plot_intersections(
            target_junction_id,
            self.figfolder,
            options
        )

        return f"You have successfully visualized the location of intersection {target} on the following map. And your final answer should include this sentence without changing anything: The location of intersection {target} is kept at: `{fig_path}`."
