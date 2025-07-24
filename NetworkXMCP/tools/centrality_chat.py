"""
ネットワーク中心性に関するチャットツール
ネットワークの中心性指標に関する説明と対話を行う機能を提供します
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Any, Optional

# 中心性指標の知識ベース
CENTRALITY_KNOWLEDGE = {
    "degree": {
        "name": "次数中心性",
        "name_en": "Degree Centrality",
        "description": "ノードの接続数（次数）に基づく中心性指標です。多くのノードと直接つながっているノードほど重要とみなします。",
        "use_cases": "ソーシャルネットワークでの人気度や影響力の測定、交通網での主要ハブの特定などに適しています。",
        "advantages": "計算が非常に簡単で直感的に理解しやすい指標です。ローカルな接続性を反映します。",
        "limitations": "ネットワーク全体の構造を考慮せず、直接のつながりのみを評価するため、間接的な影響力を測れません。"
    },
    "closeness": {
        "name": "近接中心性",
        "name_en": "Closeness Centrality",
        "description": "ノードから他のすべてのノードへの最短経路の長さの逆数に基づく中心性指標です。ネットワーク内の他のノードに素早くアクセスできるノードほど重要とみなします。",
        "use_cases": "情報拡散の効率性、緊急対応施設の配置、物流センターの立地選定などに適しています。",
        "advantages": "ネットワーク全体における位置を考慮し、情報伝達の効率性を反映します。",
        "limitations": "非連結グラフでは計算が複雑になり、大規模ネットワークでの計算コストが高くなります。"
    },
    "betweenness": {
        "name": "媒介中心性",
        "name_en": "Betweenness Centrality",
        "description": "あるノードが他のノード間の最短経路上に位置する頻度に基づく中心性指標です。情報や資源の流れを制御できるノードほど重要とみなします。",
        "use_cases": "通信ネットワークのボトルネック検出、コミュニティ間の橋渡し役の特定、交通網の要所分析などに適しています。",
        "advantages": "ネットワークの「橋渡し」役となるノードを特定でき、情報や資源の流れの制御力を評価できます。",
        "limitations": "計算コストが高く、大規模ネットワークでは近似アルゴリズムが必要になることがあります。"
    },
    "eigenvector": {
        "name": "固有ベクトル中心性",
        "name_en": "Eigenvector Centrality",
        "description": "重要なノードとつながっているノードほど重要とみなす再帰的な中心性指標です。ノードの重要性は、隣接するノードの重要性に比例します。",
        "use_cases": "影響力のあるユーザーの特定、Webページのランキング（GoogleのPageRankの基礎）、推薦システムなどに適しています。",
        "advantages": "ノードの直接のつながりだけでなく、ネットワーク内での「質的な」つながりを考慮します。",
        "limitations": "方向性のあるネットワークでは解釈が複雑になることがあり、計算が収束しない場合があります。"
    },
    "pagerank": {
        "name": "ページランク",
        "name_en": "PageRank",
        "description": "固有ベクトル中心性を拡張した指標で、Webページのランキングに使用されるアルゴリズムです。リンクの重みと確率的な遷移を考慮します。",
        "use_cases": "Web検索エンジン、学術論文の引用分析、ソーシャルメディアの影響力分析などに適しています。",
        "advantages": "有向グラフに適しており、ランダムウォークモデルに基づく堅牢な指標です。",
        "limitations": "パラメータ設定（減衰係数など）が結果に影響し、大規模ネットワークでは計算時間がかかります。"
    }
}

def get_centrality_info(centrality_type: str) -> Dict:
    """
    指定された中心性タイプの情報を取得します
    
    Args:
        centrality_type: 中心性のタイプ（degree, closeness, betweenness, eigenvector, pagerank）
        
    Returns:
        中心性に関する情報を含む辞書
    """
    return CENTRALITY_KNOWLEDGE.get(centrality_type.lower(), {
        "name": "不明な中心性指標",
        "description": "指定された中心性タイプの情報は利用できません。"
    })

def recommend_centrality(network_info: Dict, question: str) -> Dict:
    """
    ネットワーク特性と質問に基づいて適切な中心性指標を推奨します
    
    Args:
        network_info: ネットワークの特性情報（ノード数、エッジ数、密度など）
        question: ユーザーの質問やタスクの内容
        
    Returns:
        推奨される中心性指標とその理由を含む辞書
    """
    # ネットワークの特性を解析
    is_large = network_info.get("num_nodes", 0) > 1000
    is_dense = network_info.get("density", 0) > 0.1
    is_connected = network_info.get("is_connected", False)
    avg_degree = network_info.get("avg_degree", 0)
    
    # 質問からキーワードを抽出（簡易実装）
    keywords = {
        "direct_influence": ["直接", "つながり", "隣接", "次数", "degree", "人気", "接続数"],
        "information_flow": ["情報", "伝達", "流れ", "拡散", "近い", "距離", "closeness", "近接"],
        "control": ["制御", "橋渡し", "間", "ブリッジ", "媒介", "betweenness", "仲介"],
        "prestige": ["重要", "権威", "影響力", "再帰", "固有", "eigenvector", "権威", "評判"],
        "ranking": ["ランク", "順位", "pagerank", "検索", "参照", "引用"]
    }
    
    # 質問に含まれるキーワードを分析
    matched_categories = {}
    for category, words in keywords.items():
        score = sum(1 for word in words if word.lower() in question.lower())
        matched_categories[category] = score
    
    # ネットワーク特性と質問内容から最適な中心性を決定
    if max(matched_categories.values(), default=0) > 0:
        # 質問内容から明確な好みがある場合
        best_match = max(matched_categories.items(), key=lambda x: x[1])[0]
        
        if best_match == "direct_influence":
            return {
                "recommended_centrality": "degree",
                "reason": "質問内容から、ノードの直接的なつながりや人気度に関心があることが伺えます。次数中心性は接続数に基づく最も直感的な指標で、このケースに最適です。"
            }
        elif best_match == "information_flow":
            return {
                "recommended_centrality": "closeness",
                "reason": "情報の流れや伝達効率に関心があるようです。近接中心性はノード間の距離の近さを測る指標であり、情報がどれだけ速く広がるかを評価するのに適しています。"
            }
        elif best_match == "control":
            return {
                "recommended_centrality": "betweenness",
                "reason": "ネットワーク内での制御や橋渡し的役割に関心があるようです。媒介中心性はノードがどれだけ他のノード間の最短経路上に位置するかを測り、情報や資源の流れを制御する能力を評価します。"
            }
        elif best_match == "prestige":
            return {
                "recommended_centrality": "eigenvector",
                "reason": "ノードの質的な重要性や影響力に関心があるようです。固有ベクトル中心性は、重要なノードとつながっているノードほど重要とみなす再帰的な指標で、このような分析に適しています。"
            }
        elif best_match == "ranking":
            return {
                "recommended_centrality": "pagerank",
                "reason": "ノードのランキングや評価に関心があるようです。PageRankはGoogleの検索エンジンでも使われる堅牢なランキングアルゴリズムで、ネットワーク内での相対的な重要性を評価します。"
            }
    
    # 質問から明確な傾向が読み取れない場合はネットワーク特性から判断
    if is_large and not is_dense:
        return {
            "recommended_centrality": "degree",
            "reason": "大規模で疎なネットワークでは、計算効率の高い次数中心性が実用的です。基本的な接続パターンを把握するのに役立ちます。"
        }
    elif not is_connected:
        return {
            "recommended_centrality": "degree",
            "reason": "非連結グラフでは近接中心性や媒介中心性の計算が複雑になるため、次数中心性を推奨します。"
        }
    elif is_dense and avg_degree > 5:
        return {
            "recommended_centrality": "eigenvector",
            "reason": "密で平均次数が高いネットワークでは、単純な接続数よりも質的なつながりが重要です。固有ベクトル中心性はそのような関係性を評価できます。"
        }
    else:
        return {
            "recommended_centrality": "betweenness",
            "reason": "一般的なネットワークでは、媒介中心性がネットワークの構造と情報の流れを理解するための優れた指標です。ブリッジとなるノードを特定できます。"
        }

def process_centrality_chat(message: str, network_info: Optional[Dict] = None) -> Dict:
    """
    中心性に関するチャットメッセージを処理し、適切な応答を返します
    
    Args:
        message: ユーザーからのチャットメッセージ
        network_info: 現在のネットワークの特性情報（オプション）
        
    Returns:
        応答内容と推奨される中心性指標を含む辞書
    """
    message_lower = message.lower()
    
    # ネットワーク情報がない場合のデフォルト値
    if not network_info:
        network_info = {
            "num_nodes": 100,
            "num_edges": 300,
            "density": 0.06,
            "is_connected": True,
            "num_components": 1,
            "avg_degree": 6.0,
            "clustering_coefficient": 0.3
        }
    
    # 特定の中心性タイプについての質問かチェック
    for centrality_type in CENTRALITY_KNOWLEDGE:
        if (centrality_type in message_lower or 
            CENTRALITY_KNOWLEDGE[centrality_type]["name"] in message or
            CENTRALITY_KNOWLEDGE[centrality_type]["name_en"] in message):
            
            info = get_centrality_info(centrality_type)
            return {
                "success": True,
                "content": f"{info['name']}（{info['name_en']}）: {info['description']}\n\n"
                           f"用途: {info['use_cases']}\n\n"
                           f"利点: {info['advantages']}\n\n"
                           f"制限: {info['limitations']}",
                "centrality_type": centrality_type
            }
    
    # 重要なノードや中心性に関する一般的な質問の場合
    centrality_keywords = ["中心性", "centrality", "重要", "重要度", "中心", "影響力", "大きく表示"]
    if any(keyword in message_lower for keyword in centrality_keywords):
        recommendation = recommend_centrality(network_info, message)
        
        return {
            "success": True,
            "content": f"ネットワークの重要なノードを可視化するには、いくつかの中心性指標があります。あなたのケースでは「{CENTRALITY_KNOWLEDGE[recommendation['recommended_centrality']]['name']}」が適しているでしょう。\n\n"
                      f"{recommendation['reason']}\n\n"
                      f"この中心性を適用してノードサイズを変更しますか？または他の中心性指標について詳しく知りたい場合は、「次数中心性について教えて」のように質問してください。",
            "recommended_centrality": recommendation["recommended_centrality"]
        }
    
    # 中心性に関する説明を求められた場合
    if "中心性について" in message or "中心性とは" in message or "中心性の種類" in message:
        return {
            "success": True,
            "content": "ネットワーク中心性とは、グラフ内でのノードの重要度を測る指標です。主な中心性指標には以下のようなものがあります：\n\n"
                      "1. 次数中心性（Degree Centrality）: ノードの接続数に基づく指標\n"
                      "2. 近接中心性（Closeness Centrality）: ノードから他のノードへの距離の近さを測る指標\n"
                      "3. 媒介中心性（Betweenness Centrality）: ノードが他のノード間の最短経路上にある頻度を測る指標\n"
                      "4. 固有ベクトル中心性（Eigenvector Centrality）: 重要なノードとつながっているノードほど重要とみなす指標\n"
                      "5. PageRank: Webページのランキングに使われる固有ベクトル中心性の拡張版\n\n"
                      "特定の中心性について詳しく知りたい場合は、「次数中心性について教えて」のように質問してください。",
            "general_info": True
        }
    
    # その他の中心性に関連しそうな質問の場合
    return {
        "success": True,
        "content": "ネットワークの重要なノードを分析するには中心性指標が役立ちます。次数中心性、近接中心性、媒介中心性、固有ベクトル中心性、PageRankなど、様々な指標があります。\n\n"
                  "具体的に何を知りたいですか？例えば：\n"
                  "- 「ノードの重要度で可視化したい」\n"
                  "- 「次数中心性について教えて」\n"
                  "- 「このネットワークにはどの中心性が適していますか？」\n"
                  "などと質問できます。",
        "general_info": True
    }

def calculate_centrality(G: nx.Graph, centrality_type: str) -> Dict[str, float]:
    """
    指定された中心性指標をネットワークに対して計算します
    
    Args:
        G: NetworkXのグラフオブジェクト
        centrality_type: 計算する中心性のタイプ
        
    Returns:
        ノードIDと中心性値のマッピング辞書
    """
    if centrality_type == "degree":
        centrality = nx.degree_centrality(G)
    elif centrality_type == "closeness":
        # 非連結グラフの場合は連結成分ごとに計算
        if not nx.is_connected(G):
            centrality = {}
            for component in nx.connected_components(G):
                subgraph = G.subgraph(component)
                comp_centrality = nx.closeness_centrality(subgraph)
                centrality.update(comp_centrality)
        else:
            centrality = nx.closeness_centrality(G)
    elif centrality_type == "betweenness":
        centrality = nx.betweenness_centrality(G)
    elif centrality_type == "eigenvector":
        try:
            centrality = nx.eigenvector_centrality(G, max_iter=1000)
        except nx.PowerIterationFailedConvergence:
            # 収束しない場合は近似アルゴリズムを使用
            centrality = nx.eigenvector_centrality_numpy(G)
    elif centrality_type == "pagerank":
        centrality = nx.pagerank(G)
    else:
        # デフォルトは次数中心性
        centrality = nx.degree_centrality(G)
    
    return centrality

def normalize_centrality_values(centrality: Dict[str, float]) -> Dict[str, float]:
    """
    中心性の値を0-1の範囲に正規化します
    
    Args:
        centrality: ノードIDと中心性値のマッピング辞書
        
    Returns:
        正規化された中心性値の辞書
    """
    if not centrality:
        return {}
    
    values = list(centrality.values())
    min_val = min(values)
    max_val = max(values)
    
    # 最大値と最小値が同じ場合（すべての値が同じ）
    if max_val == min_val:
        return {node: 0.5 for node in centrality}
    
    # 正規化
    normalized = {node: (val - min_val) / (max_val - min_val) 
                 for node, val in centrality.items()}
    
    return normalized

def centrality_to_node_sizes(centrality: Dict[str, float], 
                           min_size: float = 3.0, 
                           max_size: float = 15.0) -> Dict[str, float]:
    """
    中心性の値をノードサイズにマッピングします
    
    Args:
        centrality: ノードIDと中心性値のマッピング辞書
        min_size: 最小ノードサイズ
        max_size: 最大ノードサイズ
        
    Returns:
        ノードIDとサイズのマッピング辞書
    """
    normalized = normalize_centrality_values(centrality)
    
    # サイズへのマッピング
    sizes = {node: min_size + val * (max_size - min_size) 
            for node, val in normalized.items()}
    
    return sizes

def process_chat_message(message: str, network_info: Optional[Dict] = None) -> Dict:
    """
    チャットメッセージを処理し、中心性に関する応答を返します
    
    Args:
        message: ユーザーからのチャットメッセージ
        network_info: ネットワークの特性情報（オプション）
        
    Returns:
        応答内容と推奨操作を含む辞書
    """
    return process_centrality_chat(message, network_info)
