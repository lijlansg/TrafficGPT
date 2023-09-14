import os
import re
import yaml
from rich import print
# from langchain import OpenAI
from langchain.chat_models import AzureChatOpenAI, ChatOpenAI

from LLMAgent.ConversationBot import ConversationBot

from LLMAgent.dataTools import (
    roadVolumeTrend,
    roadVolume,
    roadNameToID,
    plotGeoHeatmap,
    getCurrentTime,
    roadVisulization,
    odVolume,
    odMap
)

import gradio as gr
import openai.api_requestor
openai.api_requestor.TIMEOUT_SECS = 30

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

if not os.path.exists('./fig/'):
    os.mkdir('./fig/')

toolModels = [
    roadVolumeTrend('./fig/'),
    roadVolume(),
    roadNameToID(),
    plotGeoHeatmap('./fig/'),
    getCurrentTime(),
    roadVisulization('./fig/'),
    odVolume(),
    odMap('./fig/')
]

botPrefix = """
# 1. You are a AI to assist human with traffic big-data analysis and visulization. #
# 2. You have access to the road network and traffic flow data in Xuancheng City, Anhui Province, China.
# 3. Whenever you are about to come up with a thought, recall the human message to check if you already have enough information for the final answer. If so, you shouldn't infer or fabricate any more needs or questions based on your own ideas.
# 4. You are forbidden to fabricate any tool names. If you can not find any appropriate tool for your task, try to do it using your own ability and knowledge as a chat AI.
# 5. Remember what tools you have used, DONOT use the same tool repeatedly. Try to use the least amount of tools.
# 6. DONOT fabricate any input parameters when calling tools! Check if you have the correct format of input parameters before calling tools!
# 7. When you encounter tabular content in Observation, make sure you output the tabular content in markdown format into your final answer.
# 8. Your tasks will be highly time sensitive. When generating your final answer, you need to state the time of the data you are using.
# 9. It's ok if the human message is not a traffic data related task, don't take any action and just respond to it like an ordinary conversation using your own ability and knowledge as a chat AI.
# 10. When you realize that you need to clarify what the human wants, end your actions and ask the human for more information as your final answer.
"""

bot = ConversationBot(llm, toolModels, botPrefix, verbose=True)


def reset(chat_history: list, thoughts: str):
    chat_history = []
    thoughts = ""
    bot.agent_memory.clear()
    bot.ch.memory = [[]]
    return chat_history, thoughts


def respond(msg: str, chat_history: list, thoughts: str):
    res, cb = bot.dialogue(msg)
    regex = re.compile(r'`([^`]+)`')
    try:
        filenames = regex.findall(res)
    except AttributeError:
        filenames = None
    if filenames:
        chat_history += [(msg, None)]
        for fn in filenames:
            chat_history += [(None, (fn,))]
        chat_history += [(None, res)]
    else:
        chat_history += [(msg, res)]

    thoughts += f"\n>>> {msg}\n"
    for actionMemory in bot.ch.memory[-2]:
        thoughts += actionMemory
        thoughts += '\n'
    thoughts += f"<<< {res}\n"
    return "", chat_history, thoughts


with gr.Blocks(
    title="Traffic Data Process Bot", theme=gr.themes.Base(text_size=gr.themes.sizes.text_md)
) as demo:
    with gr.Row(visible=True, variant="panel"):
        with gr.Column(visible=True, variant='default'):
            chatbot = gr.Chatbot(scale=2, height=650)

            with gr.Row():
                humanMsg = gr.Textbox(scale=2)
                submitBtn = gr.Button("Submit", scale=1)
            clearBtn = gr.ClearButton()
            gr.Examples(
                label='You may want to ask the following questions:',
                examples=[
                    "Show me the OD map from 7am to 9am today.",
                    "Show me the current network heatmap.",
                    "Show me the traffic volume of OD pairs from 5pm to 7pm yesterday.",
                    "Show me the traffic volume data overview of yesterday in a table.",
                    "青弋江西大道在哪？",
                    "How's the traffic volume trend of road 1131 yesterday?"
                ],
                inputs=[humanMsg],
                # outputs=[humanMsg, chatbot],
                # fn=testFunc
            )
        ReActMsg = gr.Text(
            label="Thoughts and Actions of the Chatbot",
            interactive=False,
            lines=50
        )

    humanMsg.submit(
        respond,
        [humanMsg, chatbot, ReActMsg],
        [humanMsg, chatbot, ReActMsg]
    )
    submitBtn.click(
        respond,
        [humanMsg, chatbot, ReActMsg],
        [humanMsg, chatbot, ReActMsg]
    )
    clearBtn.click(reset, [chatbot, ReActMsg], [chatbot, ReActMsg])

if __name__ == "__main__":
    demo.launch()
