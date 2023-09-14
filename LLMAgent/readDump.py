import pandas as pd
import xml.dom.minidom


def read_last_dump(dumpfile: str):
    dom = xml.dom.minidom.parse(dumpfile)
    root = dom.documentElement
    interval = root.getElementsByTagName('interval')[-1]
    edges = interval.getElementsByTagName('edge')
    LinkTDMOE = []
    for edge in edges:
        edge_id = edge.getAttribute('id')
        if eval(edge.getAttribute('sampledSeconds')) != 0:
            try:
                speed = eval(edge.getAttribute('speed'))
                waitingTime = eval(edge.getAttribute('waitingTime'))
                timeLoss = eval(edge.getAttribute('timeLoss'))
                left = eval(edge.getAttribute('left'))
                density = eval(edge.getAttribute('density'))
            except SyntaxError:
                speed = float('nan')
                waitingTime = float('nan')
                timeLoss = float('nan')
                left = float('nan')
                density = float('nan')
        else:
            speed = float('nan')
            waitingTime = float('nan')
            timeLoss = float('nan')
            left = float('nan')
            density = float('nan')
            # print(speed)
        LinkTDMOE.append(
            [edge_id, speed, waitingTime, timeLoss, left, density])

    df = pd.DataFrame(LinkTDMOE, columns=[
                        'edgeID', 'speed', 'waitingTime', 'timeLoss', 'left', 'density'])

    return df