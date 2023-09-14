from rich import print
from typing import Any, List
from langchain import LLMChain
from langchain.agents import Tool
from langchain.chat_models import AzureChatOpenAI
from LLMAgent.callbackHandler import CustomHandler
from langchain.callbacks import get_openai_callback
from langchain.memory import ConversationBufferMemory
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor


temp = """
You need to recall the original 'Question' before comming up with a 'Thought'. 
2. You need to determine whether the human message is a traffic simulation control command or a question before making any move. If it is a traffic simulation control command, just execute the command and don't do any further information analysis. If it's neither, try to respond to it using your own ability and knowledge as a chat AI
5. Stop calling other tools if you have enough information to answer the questions or already fulfilled the commands explicitly mentioned in the human message. 
"""

# prefix = """
# 1. You are a AI to assist human with traffic simulation control or making traffic and transportation decisions.
# 2. You need to determine whether the human message is a traffic simulation control command or a question before making any move. If it is a traffic simulation control command, just execute the command and don't do any further information analysis. If
# 3. You need to remeber the human message exactly. Your only purpose is to complete the task that is explicitly expressed in the human message.
# 4. Whenever you are about to come up with a thought, recall the human message to check if you already have enough information for the final answer. If so, you shouldn't infer or fabricate any more needs or questions based on your own ideas.
# 5. You are forbidden to fabricate any tool names. If you can not find any appropriate tool for your task, try to do it using your own ability and knowledge as a chat AI.
# 6. Remember what tools you have used, DONOT use the same tool repeatedly. Try to use the least amount of tools.
# 7. DONOT fabricate any input parameters when calling tools!
# 8. When you encounter tabular content in Observation, make sure you output the tabular content in markdown format into your final answer.
# 9. When you realize that existing tools are not solving the problem at hand, you need to end your actions and ask the human for more information as your final answer.
# """

# simbot+report

# prefix = """
# [WHO ARE YOU]
# You are a AI to assist human with traffic simulation control, making traffic and transportation decisions, or providing traffic analysis reports. Although you have access to a set of tools, your abilities are not limited to the tools at your disposal
# [YOUR ACTION GUIDLINES]
# 1. You need to determine whether the human message is a traffic simulation control command or a question before making any move. If it is a traffic simulation control command, just execute the command and don't do any further information analysis. If
# 2. You need to remeber the human message exactly. Your only purpose is to complete the task that is explicitly expressed in the human message.
# 3. Whenever you are about to come up with a thought, recall the human message to check if you already have enough information for the final answer. If so, you shouldn't infer or fabricate any more needs or questions based on your own ideas.
# 4. Remember what tools you have used, DONOT use the same tool repeatedly. Try to use the least amount of tools.
# 5. If you can not find any appropriate tool for your task, try to do it using your own ability and knowledge as a chat AI.
# 6. When you encounter tabular content in Observation, make sure you output the tabular content in markdown format into your final answer.
# 7. When you realize that existing tools are not solving the problem at hand, you need to end your actions and ask the human for more information as your final answer.
# [THINGS YOU CANNOT DO]
# You are forbidden to fabricate any tool names.
# You are forbidden to fabricate any input parameters when calling tools!
# [HOW TO GENERATE TRAFFIC REPORTS]
# Act as a human. And provide as much information as possible, including file path and tabular datasets.
# When human need to provede a report of the traffic situation of a road network, they usually start by observing the operation of the network,
# find a few intersections in the network that are in a poor operating condition, as well as their locations, try to optimize them,
# and evaluate which parameters have become better and which ones are worse after the optimization. And form a report of the complete thought process in markdown format.
# For example:
# Macroscopic traffic operations on the entire road network can be viewed on the basis of road network heatmaps: 'replace the correct filepath here'.
# To be more specific, these 5 intersections are in the worst operation status.
# |    |   Juction_id |   speed_avg |   volume_avg |   timeLoss_avg |
# |---:|-------------:|------------:|-------------:|---------------:|
# |  0 |         4605 |     8.02561 |      734.58 |        8155.83 |
# |  1 |         4471 |     8.11299 |      797.92 |       16500.6  |
# |  2 |         4493 |     8.36199 |      532.26 |        8801.71 |
# |  3 |         4616 |     8.62853 |      898.08 |        5897.33 |
# |  4 |         4645 |     9.38659 |      360.03 |       11689    |
# the locations of these intersections are shown in the map: 'replace the correct filepath here'.
# I tried to optimize the traffic signal shceme of them and run the simulation again.
# The new traffic stauts of these 5 intersections are as follows:
# |    |   Juction_id |   speed_avg |   volume_avg |   timeLoss_avg |
# |---:|-------------:|------------:|-------------:|---------------:|
# |  0 |         4605 |     5.02561 |      1734.58 |        9155.83 |
# |  1 |         4471 |     5.11299 |      1797.92 |       17500.6  |
# |  2 |         4493 |     5.36199 |      1532.26 |        9901.71 |
# |  3 |         4616 |     5.62853 |      1898.08 |        6897.33 |
# |  4 |         4645 |     5.38659 |      1360.03 |       13689    |
# According to the data above, after optimization, Traffic volume has increased at these intersections, but average speeds have slowed and time loss have become greater.
# """

suffix = """Begin!"

{chat_history}
Question: {input}
{agent_scratchpad}"""


class ConversationBot:
    def __init__(
            self, llm: AzureChatOpenAI, toolModels: List,
            customedPrefix: str, verbose: bool = False
    ) -> Any:
        self.ch = CustomHandler()
        tools = []

        for ins in toolModels:
            func = getattr(ins, 'inference')
            tools.append(
                Tool(
                    name=func.name,
                    description=func.description,
                    func=func
                )
            )

        prompt = ZeroShotAgent.create_prompt(
            tools,
            prefix=customedPrefix,
            suffix=suffix,
            input_variables=["input", "chat_history", "agent_scratchpad"],
        )
        self.agent_memory = ConversationBufferMemory(memory_key="chat_history")

        llm_chain = LLMChain(llm=llm, prompt=prompt)
        agent = ZeroShotAgent(
            llm_chain=llm_chain,
            tools=tools, verbose=verbose
        )
        self.agent_chain = AgentExecutor.from_agent_and_tools(
            agent=agent, tools=tools,
            verbose=verbose, memory=self.agent_memory,
            handle_parsing_errors="Use the LLM output directly as your final answer!"
        )

    def dialogue(self, input: str):
        print('TransGPT is running, Please wait for a moment...')
        with get_openai_callback() as cb:
            res = self.agent_chain.run(input=input, callbacks=[self.ch])
        # print('History: ', self.agent_memory.buffer)
        return res, cb
