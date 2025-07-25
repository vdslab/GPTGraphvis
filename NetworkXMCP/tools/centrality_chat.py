"""
中心性計算のためのチャット処理モジュール
===============================

NetworkXを使用したグラフの中心性計算に関するチャットメッセージを処理します。
"""

import re
import networkx as nx
import io
import logging

# ロギングの設定
logger = logging.getLogger("networkx_mcp.centrality_chat")

def process_chat_message(message, network_info=None, graphml_content=None):
    """
    チャットメッセージを処理して、中心性計算に関する応答を返します。
    
    Args:
        message (str): ユーザーからのチャットメッセージ
        network_info (dict, optional): ネットワークの基本情報
        graphml_content (str, optional): GraphML形式のネットワークデータ
        
    Returns:
        dict: 処理結果を含む辞書
    """
    try:
        # メッセージを小文字に変換して処理しやすくする
        message_lower = message.lower()
        
        # GraphMLコンテンツがない場合
        if not graphml_content:
            return {
                "success": True,
                "content": "ネットワークデータが読み込まれていません。サンプルネットワークを読み込むか、GraphMLファイルをアップロードしてください。"
            }
        
        # GraphMLからグラフを生成
        G = None
        try:
            content_io = io.BytesIO(graphml_content.encode('utf-8'))
            G = nx.read_graphml(content_io)
        except Exception as e:
            logger.error(f"Error parsing GraphML: {e}")
            return {
                "success": False,
                "content": f"GraphMLの解析に失敗しました: {str(e)}"
            }
        
        # 中心性計算のパターン
        centrality_patterns = {
            "degree": r'\b(次数|ディグリー|degree)\b',
            "closeness": r'\b(近接|クローズネス|closeness)\b',
            "betweenness": r'\b(媒介|ビトウィーンネス|betweenness)\b',
            "eigenvector": r'\b(固有ベクトル|アイゲンベクトル|eigenvector)\b',
            "pagerank": r'\b(ページランク|pagerank)\b'
        }
        
        # レイアウトのパターン
        layout_patterns = {
            "spring": r'\b(バネモデル|スプリング|spring)\b',
            "circular": r'\b(円形|サークル|circular)\b',
            "random": r'\b(ランダム|random)\b',
            "spectral": r'\b(スペクトル|spectral)\b',
            "shell": r'\b(シェル|shell)\b',
            "kamada_kawai": r'\b(カマダ|カワイ|kamada|kawai)\b',
            "fruchterman_reingold": r'\b(フルクターマン|レインゴールド|fruchterman|reingold)\b'
        }
        
        # ネットワーク情報の要求
        if re.search(r'\b(情報|統計|概要|情報を教えて|statistics|info)\b', message_lower):
            return generate_network_info_response(G, network_info)
        
        # 中心性計算の要求
        for centrality_type, pattern in centrality_patterns.items():
            if re.search(pattern, message_lower):
                return calculate_centrality_response(G, centrality_type, graphml_content)
        
        # レイアウト変更の要求
        for layout_type, pattern in layout_patterns.items():
            if re.search(pattern, message_lower) and re.search(r'\b(レイアウト|配置|layout)\b', message_lower):
                return change_layout_response(G, layout_type, graphml_content)
        
        # 一般的なレイアウト変更の要求
        if re.search(r'\b(レイアウト|配置|layout)\b', message_lower):
            return {
                "success": True,
                "content": "以下のレイアウトから選択できます：\n\n" +
                           "- スプリングレイアウト (spring): バネモデルに基づく自然な配置\n" +
                           "- 円形レイアウト (circular): ノードを円形に配置\n" +
                           "- ランダムレイアウト (random): ランダムな配置\n" +
                           "- スペクトルレイアウト (spectral): グラフのスペクトル特性に基づく配置\n" +
                           "- シェルレイアウト (shell): 同心円状の配置\n" +
                           "- カマダ・カワイレイアウト (kamada_kawai): エネルギー最小化に基づく配置\n" +
                           "- フルクターマン・レインゴールドレイアウト (fruchterman_reingold): 力学モデルに基づく配置\n\n" +
                           "「スプリングレイアウトを適用して」のように指示してください。"
            }
        
        # 一般的な中心性の要求
        if re.search(r'\b(中心性|センタリティ|重要|centrality)\b', message_lower):
            return {
                "success": True,
                "content": "以下の中心性指標から選択できます：\n\n" +
                           "- 次数中心性 (degree): ノードの接続数に基づく指標\n" +
                           "- 近接中心性 (closeness): ノードから他のノードへの距離に基づく指標\n" +
                           "- 媒介中心性 (betweenness): 最短経路上にあるノードの重要性を示す指標\n" +
                           "- 固有ベクトル中心性 (eigenvector): 接続先の重要性を考慮した指標\n" +
                           "- PageRank: Webページの重要性を測るアルゴリズムに基づく指標\n\n" +
                           "「次数中心性を計算して」のように指示してください。"
            }
        
        # ヘルプの要求
        if re.search(r'\b(ヘルプ|help|使い方)\b', message_lower):
            return {
                "success": True,
                "content": "NetworkX MCPでは以下の操作ができます：\n\n" +
                           "1. ネットワーク情報の表示: 「ネットワークの情報を教えて」\n" +
                           "2. 中心性の計算: 「次数中心性を計算して」「媒介中心性を適用して」など\n" +
                           "3. レイアウトの変更: 「円形レイアウトに変更して」「スプリングレイアウトを適用して」など\n\n" +
                           "また、GraphMLファイルをアップロードしてネットワークを読み込むこともできます。"
            }
        
        # デフォルトの応答
        return {
            "success": True,
            "content": "ネットワーク分析に関するご質問や操作をお願いします。「ヘルプ」と入力すると、利用可能な機能の一覧が表示されます。"
        }
    
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return {
            "success": False,
            "content": f"メッセージの処理中にエラーが発生しました: {str(e)}"
        }

def generate_network_info_response(G, network_info=None):
    """ネットワーク情報のレスポンスを生成する"""
    try:
        if network_info:
            # 既に計算された情報がある場合はそれを使用
            info = network_info
        else:
            # 情報を計算
            info = {
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "density": nx.density(G),
                "is_connected": nx.is_connected(G),
                "num_components": nx.number_connected_components(G),
                "avg_degree": sum(dict(G.degree()).values()) / G.number_of_nodes(),
                "clustering_coefficient": nx.average_clustering(G)
            }
        
        # レスポンスの生成
        response = f"""# ネットワーク情報

- **ノード数**: {info['num_nodes']}
- **エッジ数**: {info['num_edges']}
- **密度**: {info['density']:.4f}
- **連結グラフ**: {'はい' if info['is_connected'] else 'いいえ'}
- **連結成分数**: {info['num_components']}
- **平均次数**: {info['avg_degree']:.2f}
- **クラスタリング係数**: {info['clustering_coefficient']:.4f}

このネットワークに対して中心性計算やレイアウト変更などの操作ができます。"""
        
        return {
            "success": True,
            "content": response
        }
    except Exception as e:
        logger.error(f"Error generating network info response: {e}")
        return {
            "success": False,
            "content": f"ネットワーク情報の生成中にエラーが発生しました: {str(e)}"
        }

def calculate_centrality_response(G, centrality_type, graphml_content):
    """中心性計算のレスポンスを生成する"""
    try:
        # 中心性の計算
        centrality_functions = {
            "degree": nx.degree_centrality,
            "closeness": nx.closeness_centrality,
            "betweenness": nx.betweenness_centrality,
            "eigenvector": nx.eigenvector_centrality_numpy,
            "pagerank": nx.pagerank
        }
        
        centrality_names = {
            "degree": "次数中心性",
            "closeness": "近接中心性",
            "betweenness": "媒介中心性",
            "eigenvector": "固有ベクトル中心性",
            "pagerank": "PageRank"
        }
        
        centrality_descriptions = {
            "degree": "ノードの接続数に基づく指標です。多くのノードと接続しているノードほど高い値を持ちます。",
            "closeness": "ノードから他のすべてのノードへの距離の逆数に基づく指標です。ネットワーク内で中心に位置するノードほど高い値を持ちます。",
            "betweenness": "他のノード間の最短経路上に位置する頻度に基づく指標です。情報の流れを制御するノードほど高い値を持ちます。",
            "eigenvector": "接続先の重要性を考慮した指標です。重要なノードと接続しているノードほど高い値を持ちます。",
            "pagerank": "Googleの検索アルゴリズムの基礎となった指標です。接続先の重要性と接続数を考慮します。"
        }
        
        # 中心性の計算
        centrality_values = centrality_functions[centrality_type](G)
        
        # 上位5ノードを抽出
        top_nodes = sorted(centrality_values.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # レスポンスの生成
        response = f"""# {centrality_names[centrality_type]}の計算結果

{centrality_descriptions[centrality_type]}

## 上位5ノード

| ノード | 中心性値 |
|-------|---------|
"""
        
        for node, value in top_nodes:
            response += f"| {node} | {value:.4f} |\n"
        
        response += """
ノードのサイズと色は中心性値に基づいて更新されました。
中心性値が高いノードほど大きく、赤色で表示されます。"""
        
        # GraphMLを更新
        # ノードの属性に中心性値を追加
        for node, value in centrality_values.items():
            G.nodes[node]['centrality_value'] = str(value)
            G.nodes[node]['centrality_type'] = centrality_type
        
        # GraphMLにエクスポート
        output = io.BytesIO()
        nx.write_graphml(G, output)
        output.seek(0)
        updated_graphml = output.read().decode("utf-8")
        
        return {
            "success": True,
            "content": response,
            "graphml_content": updated_graphml,
            "networkUpdate": {
                "type": "centrality",
                "centralityType": centrality_type
            }
        }
    except Exception as e:
        logger.error(f"Error calculating centrality: {e}")
        return {
            "success": False,
            "content": f"中心性計算中にエラーが発生しました: {str(e)}"
        }

def change_layout_response(G, layout_type, graphml_content):
    """レイアウト変更のレスポンスを生成する"""
    try:
        layout_names = {
            "spring": "スプリングレイアウト",
            "circular": "円形レイアウト",
            "random": "ランダムレイアウト",
            "spectral": "スペクトルレイアウト",
            "shell": "シェルレイアウト",
            "kamada_kawai": "カマダ・カワイレイアウト",
            "fruchterman_reingold": "フルクターマン・レインゴールドレイアウト"
        }
        
        layout_descriptions = {
            "spring": "バネモデルに基づくレイアウトで、接続されたノード同士が適切な距離を保つように配置されます。",
            "circular": "ノードを円形に配置するシンプルなレイアウトです。",
            "random": "ノードをランダムに配置するレイアウトです。",
            "spectral": "グラフのスペクトル特性（固有値と固有ベクトル）に基づくレイアウトです。",
            "shell": "ノードを同心円状に配置するレイアウトです。",
            "kamada_kawai": "エネルギー最小化に基づくレイアウトで、ノード間の理想的な距離を保つように配置されます。",
            "fruchterman_reingold": "力学モデルに基づくレイアウトで、ノード間の反発力とエッジによる引力のバランスを取ります。"
        }
        
        # レスポンスの生成
        response = f"""# {layout_names[layout_type]}を適用しました

{layout_descriptions[layout_type]}

このレイアウトでは、ネットワークの構造が視覚的に理解しやすくなります。
ノードの位置が更新されました。"""
        
        return {
            "success": True,
            "content": response,
            "networkUpdate": {
                "type": "layout",
                "layout": layout_type
            }
        }
    except Exception as e:
        logger.error(f"Error changing layout: {e}")
        return {
            "success": False,
            "content": f"レイアウト変更中にエラーが発生しました: {str(e)}"
        }
