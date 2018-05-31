#!/usr/bin/env python3

import re
import asyncio
import logging
from io import BytesIO
import matplotlib as mpl ; mpl.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx

import includes.utils.format as formatter
from includes.utils.config import Config

ginfopat = re.compile(r'\s*(?:\n|;|(?<=[\)\]])\s*,)\s*')
edgepat  = re.compile(r'^[\(\[]\s*(.+)\s*,\s*(.+)\s*[\)\]]$', re.S)
setpat   = re.compile(r'^(.+)\s*=\s*(\w+)$', re.S)

logger = logging.getLogger('navi.az')
plt.rc('text', usetex=True)
plt.rcParams['text.latex.preamble'] = [
  r'\usepackage{amsmath}',
  r'\usepackage{amssymb}',
  r'\usepackage{tikz}',
  r'\usepackage{xcolor}',
  r'\usepackage[mathscr]{euscript}',
  r'\usepackage{mathrsfs}',
]

class Math:
  def __init__(self, test=False):
    self.last = {}
    self.conf = Config('configs/math.json', save=(not test))

  @staticmethod
  def renderLatex(text, fntsz=12, dpi=300, fsz=.01,
                  fmt='svg', file=None, **kargs):
    text = text.strip().replace('\n', '\\\\')
    if text.startswith('\\begin'):
      text = f'\\[{text}\\]'
    elif not text.startswith('$') and not text.startswith('\\['):
      text = f'\\[\\begin{{split}}{text}\\end{{split}}\\]'
    logger.debug(f'attempting to render latex string: \"{text}\"')

    fig = plt.figure(figsize=(fsz, fsz))
    fig.text(
      0, 0, text,
      fontsize=fntsz, ha='center', ma='center',
      linespacing=1,
      **kargs
    )

    return _savefig(fig, file, dpi, fmt)

  @staticmethod
  def renderGraph(info, dpi=100, fsz=10,
                  fmt='svg', file=None, **kargs):
    graph=nx.Graph()

    index  = 0
    vars   = {}
    edges  = []
    nodes  = []
    labels = []

    for line in ginfopat.split(info):
      matchset = setpat.search(line)
      matchedg = edgepat.search(line)
      if matchset:
        vars.set(matchset.group(1), matchset.group(2))
      elif matchedg:
        if matchedg.group(1) in labels:
          a = labels.index(matchedg.group(1))
        else:
          labels.append(matchedg.group(1))
          a = index
          index += 1

        if matchedg.group(2) in labels:
          b = labels.index(matchedg.group(2))
        else:
          labels.append(matchedg.group(2))
          b = index
          index += 1
        edges.append( (a, b) )
      elif line not in labels:
        labels.append(line)
        nodes.append(index)
        index += 1

    for i,label in enumerate(labels):
      label = vars.get(label, label)
      labels[i] = label

    graph.add_edges_from(edges)
    graph.add_nodes_from(nodes)

    labels = {i:lable for i,lable in enumerate(labels)}

    fig = plt.figure(figsize=(fsz, fsz))
    nx.draw(graph, ax=fig.add_subplot(111), labels=labels, **kargs)

    return _savefig(fig, file, dpi, fmt)

def _savefig(fig, file, dpi, fmt):
  if type(file) == str:
    if fmt and not file.lower().endswith(fmt):
      file += '.'+fmt
    with open(file, 'w' if fmt.lower()=='svg' else 'wb') as f:
      return _savefig(fig, f, dpi, fmt)
  output = BytesIO() if file is None else file
  fig.savefig(output, dpi=dpi, transparent=True, format=fmt,
              bbox_inches='tight', pad_inches=0.1, frameon=False
  )
  plt.close(fig)
  if file is None:
    output.seek(0)
    return output
