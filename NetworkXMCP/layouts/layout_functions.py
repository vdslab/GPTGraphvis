"""
レイアウト計算関数モジュール
===================

NetworkXを使用したグラフのレイアウト計算関数を提供します。
"""

import networkx as nx
import numpy as np
import logging
import random

# ロギングの設定
logger = logging.getLogger("networkx_mcp.layouts.layout")

def calculate_spring_layout(G, k=None, pos=None, fixed=None, iterations=50, threshold=1e-4, weight='weight', scale=1.0, center=None, dim=2, seed=None):
    """
    スプリングレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        k (float, optional): バネの強さ
        pos (dict, optional): 初期位置
        fixed (list, optional): 固定するノードのリスト
        iterations (int, optional): 反復回数
        threshold (float, optional): 収束閾値
        weight (str, optional): エッジの重みの属性名
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        dim (int, optional): 次元数
        seed (int, optional): 乱数シード
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        return nx.spring_layout(G, k=k, pos=pos, fixed=fixed, iterations=iterations, threshold=threshold, weight=weight, scale=scale, center=center, dim=dim, seed=seed)
    except Exception as e:
        logger.error(f"Error calculating spring layout: {e}")
        # フォールバック: ランダムレイアウト
        return nx.random_layout(G, center=center, dim=dim, seed=seed)

def calculate_circular_layout(G, scale=1, center=None, dim=2):
    """
    円形レイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        dim (int, optional): 次元数
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        return nx.circular_layout(G, scale=scale, center=center, dim=dim)
    except Exception as e:
        logger.error(f"Error calculating circular layout: {e}")
        # フォールバック: ランダムレイアウト
        return nx.random_layout(G, center=center, dim=dim)

def calculate_random_layout(G, center=None, dim=2, seed=None):
    """
    ランダムレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        center (tuple, optional): 中心座標
        dim (int, optional): 次元数
        seed (int, optional): 乱数シード
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        return nx.random_layout(G, center=center, dim=dim, seed=seed)
    except Exception as e:
        logger.error(f"Error calculating random layout: {e}")
        # フォールバック: 手動でランダムレイアウトを生成
        pos = {}
        for node in G.nodes():
            pos[node] = np.array([random.uniform(-1, 1), random.uniform(-1, 1)])
        return pos

def calculate_spectral_layout(G, weight='weight', scale=1, center=None, dim=2):
    """
    スペクトルレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        weight (str, optional): エッジの重みの属性名
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        dim (int, optional): 次元数
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        return nx.spectral_layout(G, weight=weight, scale=scale, center=center, dim=dim)
    except Exception as e:
        logger.error(f"Error calculating spectral layout: {e}")
        # フォールバック: スプリングレイアウト
        return nx.spring_layout(G, scale=scale, center=center, dim=dim)

def calculate_shell_layout(G, nlist=None, scale=1, center=None, dim=2):
    """
    シェルレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        nlist (list, optional): ノードのリストのリスト
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        dim (int, optional): 次元数
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        # nlistが指定されていない場合は、連結成分ごとにノードをグループ化
        if nlist is None:
            components = list(nx.connected_components(G))
            if not components:
                # 連結成分がない場合は全ノードを1つのグループとする
                nlist = [list(G.nodes())]
            else:
                nlist = components
        
        return nx.shell_layout(G, nlist=nlist, scale=scale, center=center, dim=dim)
    except Exception as e:
        logger.error(f"Error calculating shell layout: {e}")
        # フォールバック: 円形レイアウト
        return nx.circular_layout(G, scale=scale, center=center, dim=dim)

def calculate_kamada_kawai_layout(G, dist=None, pos=None, weight='weight', scale=1, center=None, dim=2):
    """
    カマダ・カワイレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        dist (dict, optional): ノード間の距離
        pos (dict, optional): 初期位置
        weight (str, optional): エッジの重みの属性名
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        dim (int, optional): 次元数
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        return nx.kamada_kawai_layout(G, dist=dist, pos=pos, weight=weight, scale=scale, center=center, dim=dim)
    except Exception as e:
        logger.error(f"Error calculating Kamada-Kawai layout: {e}")
        # フォールバック: スプリングレイアウト
        return nx.spring_layout(G, pos=pos, weight=weight, scale=scale, center=center, dim=dim)

def calculate_fruchterman_reingold_layout(G, k=None, pos=None, fixed=None, iterations=50, threshold=1e-4, weight='weight', scale=1, center=None, dim=2, seed=None):
    """
    フルクターマン・レインゴールドレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        k (float, optional): 最適距離
        pos (dict, optional): 初期位置
        fixed (list, optional): 固定するノードのリスト
        iterations (int, optional): 反復回数
        threshold (float, optional): 収束閾値
        weight (str, optional): エッジの重みの属性名
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        dim (int, optional): 次元数
        seed (int, optional): 乱数シード
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        return nx.fruchterman_reingold_layout(G, k=k, pos=pos, fixed=fixed, iterations=iterations, threshold=threshold, weight=weight, scale=scale, center=center, dim=dim, seed=seed)
    except Exception as e:
        logger.error(f"Error calculating Fruchterman-Reingold layout: {e}")
        # フォールバック: スプリングレイアウト
        return nx.spring_layout(G, k=k, pos=pos, fixed=fixed, iterations=iterations, threshold=threshold, weight=weight, scale=scale, center=center, dim=dim, seed=seed)

def calculate_spiral_layout(G, scale=1, center=None, dim=2, resolution=0.35, equidistant=False):
    """
    スパイラルレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        dim (int, optional): 次元数
        resolution (float, optional): 解像度
        equidistant (bool, optional): 等間隔にするかどうか
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        return nx.spiral_layout(G, scale=scale, center=center, dim=dim, resolution=resolution, equidistant=equidistant)
    except Exception as e:
        logger.error(f"Error calculating spiral layout: {e}")
        # フォールバック: 円形レイアウト
        return nx.circular_layout(G, scale=scale, center=center, dim=dim)

def calculate_multipartite_layout(G, subset_key='subset', align='vertical', scale=1, center=None):
    """
    多部グラフレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        subset_key (str, optional): 部分集合を示すノード属性のキー
        align (str, optional): 配置方向
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        # ノードに部分集合属性がない場合は、次数に基づいて割り当て
        for node in G.nodes():
            if subset_key not in G.nodes[node]:
                G.nodes[node][subset_key] = G.degree(node) % 3
        
        return nx.multipartite_layout(G, subset_key=subset_key, align=align, scale=scale, center=center)
    except Exception as e:
        logger.error(f"Error calculating multipartite layout: {e}")
        # フォールバック: シェルレイアウト
        return nx.shell_layout(G, scale=scale, center=center)

def calculate_bipartite_layout(G, nodes, align='vertical', scale=1, center=None):
    """
    二部グラフレイアウトを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        nodes (list): 一方の部分集合のノードのリスト
        align (str, optional): 配置方向
        scale (float, optional): スケール
        center (tuple, optional): 中心座標
        
    Returns:
        dict: ノードIDをキー、位置を値とする辞書
    """
    try:
        return nx.bipartite_layout(G, nodes, align=align, scale=scale, center=center)
    except Exception as e:
        logger.error(f"Error calculating bipartite layout: {e}")
        # フォールバック: シェルレイアウト
        return nx.shell_layout(G, scale=scale, center=center)

def get_layout_function(layout_type):
    """
    レイアウトタイプに基づいてレイアウト計算関数を取得する
    
    Args:
        layout_type (str): レイアウトタイプ
        
    Returns:
        function: レイアウト計算関数
    """
    layout_functions = {
        "spring": calculate_spring_layout,
        "circular": calculate_circular_layout,
        "random": calculate_random_layout,
        "spectral": calculate_spectral_layout,
        "shell": calculate_shell_layout,
        "kamada_kawai": calculate_kamada_kawai_layout,
        "fruchterman_reingold": calculate_fruchterman_reingold_layout,
        "spiral": calculate_spiral_layout,
        "multipartite": calculate_multipartite_layout,
        "bipartite": calculate_bipartite_layout
    }
    
    return layout_functions.get(layout_type, calculate_spring_layout)
