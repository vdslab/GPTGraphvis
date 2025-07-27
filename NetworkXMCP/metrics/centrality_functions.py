"""
中心性計算関数モジュール
===================

NetworkXを使用したグラフの中心性計算関数を提供します。
"""

import networkx as nx
import numpy as np
import logging

# ロギングの設定
logger = logging.getLogger("networkx_mcp.metrics.centrality")

def calculate_degree_centrality(G):
    """
    次数中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.degree_centrality(G)
    except Exception as e:
        logger.error(f"Error calculating degree centrality: {e}")
        return {}

def calculate_closeness_centrality(G):
    """
    近接中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.closeness_centrality(G)
    except Exception as e:
        logger.error(f"Error calculating closeness centrality: {e}")
        return {}

def calculate_betweenness_centrality(G, k=None, normalized=True, weight=None, endpoints=False, seed=None):
    """
    媒介中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        k (int, optional): サンプリングするノード数
        normalized (bool, optional): 正規化するかどうか
        weight (str, optional): エッジの重みの属性名
        endpoints (bool, optional): 端点を含めるかどうか
        seed (int, optional): 乱数シード
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.betweenness_centrality(G, k=k, normalized=normalized, weight=weight, endpoints=endpoints, seed=seed)
    except Exception as e:
        logger.error(f"Error calculating betweenness centrality: {e}")
        return {}

def calculate_eigenvector_centrality(G, max_iter=100, tol=1.0e-6, nstart=None, weight=None):
    """
    固有ベクトル中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        max_iter (int, optional): 最大反復回数
        tol (float, optional): 収束許容誤差
        nstart (dict, optional): 初期値
        weight (str, optional): エッジの重みの属性名
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        # 通常の固有ベクトル中心性計算を試みる
        try:
            return nx.eigenvector_centrality(G, max_iter=max_iter, tol=tol, nstart=nstart, weight=weight)
        except nx.PowerIterationFailedConvergence:
            # 収束しない場合はNumPy実装を使用
            logger.warning("Eigenvector centrality failed to converge, using NumPy implementation")
            return nx.eigenvector_centrality_numpy(G, weight=weight)
    except Exception as e:
        logger.error(f"Error calculating eigenvector centrality: {e}")
        return {}

def calculate_pagerank(G, alpha=0.85, personalization=None, max_iter=100, tol=1.0e-6, nstart=None, weight=None, dangling=None):
    """
    PageRankを計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        alpha (float, optional): ダンピング係数
        personalization (dict, optional): パーソナライゼーション
        max_iter (int, optional): 最大反復回数
        tol (float, optional): 収束許容誤差
        nstart (dict, optional): 初期値
        weight (str, optional): エッジの重みの属性名
        dangling (dict, optional): ダングリングノードの処理
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.pagerank(G, alpha=alpha, personalization=personalization, max_iter=max_iter, tol=tol, nstart=nstart, weight=weight, dangling=dangling)
    except Exception as e:
        logger.error(f"Error calculating PageRank: {e}")
        return {}

def calculate_katz_centrality(G, alpha=0.1, beta=1.0, max_iter=1000, tol=1.0e-6, nstart=None, normalized=True, weight=None):
    """
    Katz中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        alpha (float, optional): 減衰係数
        beta (float, optional): 外因性の影響
        max_iter (int, optional): 最大反復回数
        tol (float, optional): 収束許容誤差
        nstart (dict, optional): 初期値
        normalized (bool, optional): 正規化するかどうか
        weight (str, optional): エッジの重みの属性名
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.katz_centrality(G, alpha=alpha, beta=beta, max_iter=max_iter, tol=tol, nstart=nstart, normalized=normalized, weight=weight)
    except Exception as e:
        logger.error(f"Error calculating Katz centrality: {e}")
        return {}

def calculate_load_centrality(G, v=None, cutoff=None, normalized=True, weight=None):
    """
    負荷中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        v (node, optional): 単一ノードの中心性を計算する場合のノード
        cutoff (int, optional): 最短経路の最大長
        normalized (bool, optional): 正規化するかどうか
        weight (str, optional): エッジの重みの属性名
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.load_centrality(G, v=v, cutoff=cutoff, normalized=normalized, weight=weight)
    except Exception as e:
        logger.error(f"Error calculating load centrality: {e}")
        return {}

def calculate_harmonic_centrality(G, nbunch=None, distance=None, weight=None):
    """
    調和中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        nbunch (container, optional): 中心性を計算するノードのコンテナ
        distance (str, optional): 距離の属性名
        weight (str, optional): エッジの重みの属性名
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.harmonic_centrality(G, nbunch=nbunch, distance=distance)
    except Exception as e:
        logger.error(f"Error calculating harmonic centrality: {e}")
        return {}

def calculate_subgraph_centrality(G):
    """
    部分グラフ中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.subgraph_centrality(G)
    except Exception as e:
        logger.error(f"Error calculating subgraph centrality: {e}")
        return {}

def calculate_communicability_betweenness_centrality(G, normalized=True):
    """
    通信媒介中心性を計算する
    
    Args:
        G (nx.Graph): NetworkXグラフ
        normalized (bool, optional): 正規化するかどうか
        
    Returns:
        dict: ノードIDをキー、中心性値を値とする辞書
    """
    try:
        return nx.communicability_betweenness_centrality(G, normalized=normalized)
    except Exception as e:
        logger.error(f"Error calculating communicability betweenness centrality: {e}")
        return {}

def get_centrality_function(centrality_type):
    """
    中心性タイプに基づいて中心性計算関数を取得する
    
    Args:
        centrality_type (str): 中心性タイプ
        
    Returns:
        function: 中心性計算関数
    """
    centrality_functions = {
        "degree": calculate_degree_centrality,
        "closeness": calculate_closeness_centrality,
        "betweenness": calculate_betweenness_centrality,
        "eigenvector": calculate_eigenvector_centrality,
        "pagerank": calculate_pagerank,
        "katz": calculate_katz_centrality,
        "load": calculate_load_centrality,
        "harmonic": calculate_harmonic_centrality,
        "subgraph": calculate_subgraph_centrality,
        "communicability_betweenness": calculate_communicability_betweenness_centrality
    }
    
    return centrality_functions.get(centrality_type, calculate_degree_centrality)
