"""
NetworkX MCP Server
=================

FastAPI Model Context Protocol (MCP) サーバー
ネットワーク分析と可視化のためのAPIを提供します。
GraphML形式のデータをサポートし、NetworkXを使用したグラフ分析を行います。
"""

__version__ = "0.1.0"
__author__ = "NetworkX MCP Team"
__description__ = "NetworkX MCP Server for graph analysis and visualization"

from . import metrics
from . import layouts
from . import tools
