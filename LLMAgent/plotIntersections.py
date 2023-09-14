from __future__ import absolute_import
from __future__ import print_function

import os
import sys

import matplotlib
matplotlib.use('Agg')

import sumolib  # noqa
from sumolib.visualization import helpers  # noqa
from sumolib.options import ArgumentParser  # noqa
import matplotlib.pyplot as plt  # noqa

def plot_intersections(target_junction_id, folderpath, args=None) -> str:
    """The main function; parses options and plots"""
    # ---------- build and read options ----------
    ap = ArgumentParser()
    ap.add_argument("-n", "--net", dest="net", category="input", type=ap.net_file, metavar="FILE",
                    required=True, help="Defines the network to read")
    ap.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                    default=False, help="If set, the script says what it's doing")
    ap.add_argument("-w", "--width", dest="width",
                    type=float, default=20, help="Defines the width of the dots")
    ap.add_argument("--color", dest="color", category="visualization",
                    default='r', help="Defines the dot color")
    ap.add_argument("--edge-width", dest="defaultWidth", category="visualization",
                    type=float, default=1, help="Defines the edge width")
    ap.add_argument("--edge-color", dest="defaultColor", category="visualization",
                    default='k', help="Defines the edge color")
    # standard plot options
    helpers.addInteractionOptions(ap)
    helpers.addPlotOptions(ap)
    # parse
    options = ap.parse_args(args=args)

    if options.verbose:
        print("Reading network from '%s'" % options.net)
    net = sumolib.net.readNet(options.net)

    tlsn = {}
    for tid in net._id2tls:
        t = net._id2tls[tid]
        tlsn[tid] = set()
        for c in t._connections:
            n = c[0].getEdge().getToNode()
            tlsn[tid].add(n)

    tlspX = []
    tlspY = []
    junctionID = []
    for tid in tlsn:
        if tid in target_junction_id:
            x = 0
            y = 0
            n = 0
            for node in tlsn[tid]:
                x += node._coord[0]
                y += node._coord[1]
                n = n + 1
            x = x / n
            y = y / n
            tlspX.append(x)
            tlspY.append(y)
            junctionID.append(tid)

    fig, ax = helpers.openFigure(options)
    ax.set_aspect("equal", None, 'C')
    helpers.plotNet(net, {}, {}, options)
    plt.plot(tlspX, tlspY, options.color, linestyle='',
                marker='o', markersize=options.width)
    for i in range(len(junctionID)):
        plt.text(tlspX[i]*1.01, tlspY[i]*1.01, str(junctionID[i]), fontsize=10, color = "r", style = "italic", weight = "light", verticalalignment='center', horizontalalignment='right',rotation=0) #给散点加标签

    options.nolegend = True
    fig_path = f'{folderpath}intersections.png'
    fig.savefig(fig_path, dpi=1600)
    helpers.closeFigure(fig, ax, options)

    return fig_path
