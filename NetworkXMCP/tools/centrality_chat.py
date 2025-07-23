"""
Centrality chat tools for the NetworkX MCP server.
"""

import networkx as nx
from typing import Dict, Any, List, Optional
import re

# 中心性に関する説明
CENTRALITY_DESCRIPTIONS = {
    "degree": {
        "name": "次数中心性 (Degree Centrality)",
        "description": "ノードが持つ接続数（次数）に基づく中心性指標です。多くの他のノードと直接つながっているノードほど重要とみなされます。",
        "use_cases": "直接的な影響力や情報伝達の速さを測りたい場合に適しています。ソーシャルネットワークでの「人気者」の特定や、通信ネットワークのハブの特定に役立ちます。",
        "advantages": "計算が単純で直感的に理解しやすい指標です。",
        "limitations": "ネットワーク全体の構造を考慮せず、直接的な接続のみを考慮します。"
    },
    "closeness": {
        "name": "近接中心性 (Closeness Centrality)",
        "description": "ノードから他のすべてのノードへの最短経路の長さの逆数に基づく中心性指標です。ネットワーク内の他のすべてのノードに素早くアクセスできるノードほど重要とみなされます。",
        "use_cases": "情報の効率的な拡散や、ネットワーク全体への到達性が重要な場合に適しています。物流ネットワークでの配送センターの配置や、緊急時の情報伝達者の特定に役立ちます。",
        "advantages": "ネットワーク全体での位置を考慮し、間接的な接続も評価します。",
        "limitations": "非連結グラフでは一部のノードが到達不可能なため、計算が複雑になります。大規模ネットワークでは計算コストが高くなります。"
    },
    "betweenness": {
        "name": "媒介中心性 (Betweenness Centrality)",
        "description": "ノードを通過する最短経路の数に基づく中心性指標です。他のノード間の情報や資源の流れを制御できるノードほど重要とみなされます。",
        "use_cases": "情報や資源の流れの制御点、ブリッジ的役割を果たすノードの特定に適しています。交通ネットワークのボトルネック検出や、コミュニティ間のゲートキーパーの特定に役立ちます。",
        "advantages": "ネットワークの構造的な「橋渡し」役を見つけるのに優れています。",
        "limitations": "計算コストが高く、大規模ネットワークでは時間がかかります。"
    },
    "eigenvector": {
        "name": "固有ベクトル中心性 (Eigenvector Centrality)",
        "description": "接続先ノードの重要度を考慮した中心性指標です。重要なノードとつながっているノードほど重要とみなされます。",
        "use_cases": "影響力の伝播や、「重要な人とつながっている人」を特定したい場合に適しています。Webページのランキングや、科学論文の引用ネットワーク分析に役立ちます。",
        "advantages": "接続の質（重要度）を考慮するため、より洗練された重要度の指標となります。",
        "limitations": "非連結グラフや有向グラフでは計算が複雑になることがあります。"
    },
    "pagerank": {
        "name": "PageRank",
        "description": "Googleの検索アルゴリズムの基礎となった中心性指標です。ランダムウォークモデルに基づき、ノードへの訪問確率を計算します。",
        "use_cases": "Webページのランキングや、複雑なネットワークでの影響力測定に適しています。ソーシャルメディアでの影響力者の特定や、論文の重要度評価に役立ちます。",
        "advantages": "有向グラフに適しており、固有ベクトル中心性の一般化と考えられます。",
        "limitations": "パラメータ（ダンピングファクター）の選択に結果が依存します。"
    }
}

# ネットワーク特性に基づく中心性推奨
def recommend_centrality_for_network(G: nx.Graph, user_query: str = "") -> Dict[str, Any]:
    """
    ネットワーク特性とユーザーのクエリに基づいて最適な中心性指標を推奨します。
    
    Args:
        G: NetworkXグラフオブジェクト
        user_query: ユーザーの質問や要求
        
    Returns:
        推奨される中心性に関する情報を含む辞書
    """
    # 基本的なネットワーク特性を取得
    try:
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        density = nx.density(G)
        is_connected = nx.is_connected(G)
        avg_degree = sum(dict(G.degree()).values()) / num_nodes if num_nodes > 0 else 0
        try:
            clustering_coef = nx.average_clustering(G)
        except:
            clustering_coef = 0
        
        # クエリのキーワードマッチング
        query_lower = user_query.lower()
        
        # コミュニティや橋渡しに関するキーワード
        bridge_keywords = ["bridge", "橋渡し", "橋", "ブリッジ", "コミュニティ間", "仲介", "媒介"]
        if any(keyword in query_lower for keyword in bridge_keywords):
            return {
                "recommended_centrality": "betweenness",
                "reason": "ネットワーク内の「橋渡し」役割を果たすノードを特定するのに最適な指標です。異なるコミュニティや集団をつなぐノードを見つけることができます。",
                "description": CENTRALITY_DESCRIPTIONS["betweenness"]
            }
        
        # 直接的な影響力やハブに関するキーワード
        hub_keywords = ["hub", "ハブ", "接続数", "次数", "直接", "人気", "多くの接続"]
        if any(keyword in query_lower for keyword in hub_keywords):
            return {
                "recommended_centrality": "degree",
                "reason": "直接的な接続数に基づく最もシンプルな中心性指標です。多くの他のノードと接続しているハブを特定するのに適しています。",
                "description": CENTRALITY_DESCRIPTIONS["degree"]
            }
        
        # グローバルな影響力や到達性に関するキーワード
        global_keywords = ["global", "グローバル", "全体", "到達", "近さ", "効率", "距離"]
        if any(keyword in query_lower for keyword in global_keywords):
            return {
                "recommended_centrality": "closeness",
                "reason": "ネットワーク全体での位置を考慮し、他のすべてのノードへの到達性が高いノードを特定するのに適しています。",
                "description": CENTRALITY_DESCRIPTIONS["closeness"]
            }
        
        # 影響力の伝播や重要なノードとの接続に関するキーワード
        influence_keywords = ["influence", "影響力", "伝播", "重要な接続", "固有", "質"]
        if any(keyword in query_lower for keyword in influence_keywords):
            return {
                "recommended_centrality": "eigenvector",
                "reason": "接続先ノードの重要度を考慮した中心性指標です。「重要なノードとつながっているノード」を特定するのに適しています。",
                "description": CENTRALITY_DESCRIPTIONS["eigenvector"]
            }
        
        # ネットワーク特性に基づく推奨
        if density < 0.05 and not is_connected:
            # 疎で非連結なネットワーク
            return {
                "recommended_centrality": "betweenness",
                "reason": "ネットワークが疎で非連結な場合、異なるコンポーネントをつなぐ重要なノードを特定するのに媒介中心性が適しています。",
                "description": CENTRALITY_DESCRIPTIONS["betweenness"]
            }
        elif density > 0.3:
            # 密なネットワーク
            return {
                "recommended_centrality": "eigenvector",
                "reason": "ネットワークが密な場合、単純な接続数だけでなく接続の質も考慮する固有ベクトル中心性が適しています。",
                "description": CENTRALITY_DESCRIPTIONS["eigenvector"]
            }
        elif avg_degree > 10:
            # 平均次数が高いネットワーク
            return {
                "recommended_centrality": "pagerank",
                "reason": "平均次数が高いネットワークでは、接続数だけでなく接続の質と確率的な訪問頻度を考慮するPageRankが適しています。",
                "description": CENTRALITY_DESCRIPTIONS["pagerank"]
            }
        elif clustering_coef > 0.5:
            # クラスタリング係数が高いネットワーク
            return {
                "recommended_centrality": "betweenness",
                "reason": "クラスタリング係数が高いネットワークでは、異なるクラスタをつなぐ橋渡し的なノードを特定するのに媒介中心性が適しています。",
                "description": CENTRALITY_DESCRIPTIONS["betweenness"]
            }
        else:
            # デフォルト
            return {
                "recommended_centrality": "degree",
                "reason": "最もシンプルで直感的に理解しやすい中心性指標です。多くの分析の出発点として適しています。",
                "description": CENTRALITY_DESCRIPTIONS["degree"]
            }
    except Exception as e:
        # エラーが発生した場合はデフォルトを返す
        return {
            "recommended_centrality": "degree",
            "reason": f"最もシンプルで計算が安定している中心性指標です。（注：推奨処理中にエラーが発生しました: {str(e)}）",
            "description": CENTRALITY_DESCRIPTIONS["degree"]
        }

def get_centrality_explanation(centrality_type: str) -> Dict[str, str]:
    """
    指定された中心性指標の説明を取得します。
    
    Args:
        centrality_type: 中心性の種類
        
    Returns:
        中心性の説明を含む辞書
    """
    if centrality_type in CENTRALITY_DESCRIPTIONS:
        return CENTRALITY_DESCRIPTIONS[centrality_type]
    else:
        return {
            "name": "未知の中心性",
            "description": "指定された中心性に関する情報が見つかりません。",
            "use_cases": "不明",
            "advantages": "不明",
            "limitations": "不明"
        }

def get_all_centrality_explanations() -> Dict[str, Dict[str, str]]:
    """
    すべての中心性指標の説明を取得します。
    
    Returns:
        すべての中心性の説明を含む辞書
    """
    return CENTRALITY_DESCRIPTIONS

def process_centrality_chat_message(message: str, G: Optional[nx.Graph] = None) -> Dict[str, Any]:
    """
    中心性に関するチャットメッセージを処理します。
    
    Args:
        message: ユーザーのメッセージ
        G: NetworkXグラフオブジェクト（オプション）
        
    Returns:
        応答メッセージと関連情報を含む辞書
    """
    message_lower = message.lower()
    
    # 重要度や中心性に関する一般的な質問
    importance_keywords = [
        "重要", "中心性", "重要度", "中心", "重要なノード", "important", "centrality", 
        "significance", "central", "ノードの大きさ"
    ]
    
    if any(keyword in message_lower for keyword in importance_keywords):
        # 具体的な中心性タイプの言及があるか確認
        centrality_types = {
            "degree": ["次数", "degree", "次数中心性", "ディグリー"],
            "closeness": ["近接", "closeness", "近接中心性", "クローズネス"],
            "betweenness": ["媒介", "betweenness", "媒介中心性", "ビトウィーンネス"],
            "eigenvector": ["固有ベクトル", "eigenvector", "固有ベクトル中心性", "アイゲンベクトル"],
            "pagerank": ["pagerank", "ページランク"]
        }
        
        for centrality_type, keywords in centrality_types.items():
            if any(keyword in message_lower for keyword in keywords):
                explanation = get_centrality_explanation(centrality_type)
                return {
                    "success": True,
                    "response_type": "centrality_explanation",
                    "centrality_type": centrality_type,
                    "content": f"{explanation['name']}について：\n\n{explanation['description']}\n\n**用途**：{explanation['use_cases']}\n\n**長所**：{explanation['advantages']}\n\n**制限**：{explanation['limitations']}",
                    "recommendation": None
                }
        
        # 具体的な言及がなければ、ネットワークに基づいて推奨
        if G:
            recommendation = recommend_centrality_for_network(G, message)
            return {
                "success": True,
                "response_type": "centrality_recommendation",
                "content": f"ネットワークの重要なノードを可視化するには、**{recommendation['description']['name']}**が適しているでしょう。\n\n{recommendation['reason']}\n\n{recommendation['description']['description']}\n\n**用途**：{recommendation['description']['use_cases']}\n\n他の中心性指標について詳しく知りたい場合や、別の中心性を試したい場合はお知らせください。",
                "recommendation": recommendation
            }
        else:
            # グラフがない場合は一般的な説明
            return {
                "success": True,
                "response_type": "centrality_general",
                "content": """ネットワークのノードの重要度を測る中心性指標にはいくつかの種類があります：

1. **次数中心性 (Degree Centrality)** - 直接接続しているノードの数に基づく指標
2. **近接中心性 (Closeness Centrality)** - ネットワーク内の他のノードへの近さに基づく指標
3. **媒介中心性 (Betweenness Centrality)** - 他のノード間の最短経路上にあるかに基づく指標
4. **固有ベクトル中心性 (Eigenvector Centrality)** - 接続先ノードの重要度を考慮した指標
5. **PageRank** - Googleの検索アルゴリズムの基礎となった確率的な中心性指標

どのような分析をしたいのか、またはネットワークのどのような特性に興味があるかを教えていただければ、最適な中心性指標を推奨できます。""",
                "recommendation": None
            }
    
    # 中心性の比較に関する質問
    comparison_keywords = ["比較", "違い", "どちらが", "どれが", "compare", "difference", "which"]
    if any(keyword in message_lower for keyword in comparison_keywords):
        return {
            "success": True,
            "response_type": "centrality_comparison",
            "content": """各中心性指標の主な違いと特徴は以下の通りです：

**次数中心性**: 最もシンプルで、直接つながっているノードの数だけを考慮します。計算が容易で直感的ですが、ネットワーク全体の構造は考慮しません。

**近接中心性**: ノードから他のすべてのノードへの距離を考慮します。ネットワーク全体での位置を評価しますが、非連結グラフでは問題が生じます。

**媒介中心性**: ノードを通過する最短経路の数を測定します。「橋渡し」的役割を果たすノードを特定するのに優れていますが、計算コストが高いです。

**固有ベクトル中心性**: 接続先ノードの重要度を考慮します。「重要なノードとつながっているノード」を評価しますが、計算が複雑になることがあります。

**PageRank**: ランダムウォークモデルに基づく指標で、有向グラフに適しています。Webページのランキングなどに使用されます。

あなたのネットワークの分析目的に応じて、最適な指標は異なります。どのような分析をしたいですか？""",
            "recommendation": None
        }
    
    # ネットワークの特性に関する質問
    network_keywords = ["ネットワーク", "グラフ", "特性", "構造", "network", "graph", "property", "structure"]
    if G and any(keyword in message_lower for keyword in network_keywords):
        try:
            num_nodes = G.number_of_nodes()
            num_edges = G.number_of_edges()
            density = nx.density(G)
            is_connected = nx.is_connected(G)
            avg_degree = sum(dict(G.degree()).values()) / num_nodes if num_nodes > 0 else 0
            
            return {
                "success": True,
                "response_type": "network_info",
                "content": f"""現在のネットワークの特性：

- ノード数: {num_nodes}
- エッジ数: {num_edges}
- 密度: {density:.4f}
- 連結: {'はい' if is_connected else 'いいえ'}
- 平均次数: {avg_degree:.2f}

これらの特性に基づくと、{recommend_centrality_for_network(G)['description']['name']}が適しているかもしれません。他に何か知りたい情報はありますか？""",
                "recommendation": None
            }
        except Exception as e:
            return {
                "success": False,
                "response_type": "error",
                "content": f"ネットワーク情報の取得中にエラーが発生しました: {str(e)}",
                "recommendation": None
            }
    
    # その他の質問や理解できない場合のデフォルト応答
    return {
        "success": True,
        "response_type": "default",
        "content": "ネットワークの中心性に関する質問や、ノードの重要度の可視化方法についてお答えできます。例えば「次数中心性とは何ですか？」や「このネットワークではどの中心性が適していますか？」などと質問してみてください。",
        "recommendation": None
    }
