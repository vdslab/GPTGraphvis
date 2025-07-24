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
        "limitations": "ネットワーク全体の構造を考慮せず、直接のつながりのみを評価するため、間接的な影響力を測れません。",
        "visual_explanation": "次数中心性を適用すると、多くの接続を持つノードが大きく表示されます。SNSでの「友達が多い」ユーザーや、交通網での「多くの路線が通る駅」などが目立つようになります。"
    },
    "closeness": {
        "name": "近接中心性",
        "name_en": "Closeness Centrality",
        "description": "ノードから他のすべてのノードへの最短経路の長さの逆数に基づく中心性指標です。ネットワーク内の他のノードに素早くアクセスできるノードほど重要とみなします。",
        "use_cases": "情報拡散の効率性、緊急対応施設の配置、物流センターの立地選定などに適しています。",
        "advantages": "ネットワーク全体における位置を考慮し、情報伝達の効率性を反映します。",
        "limitations": "非連結グラフでは計算が複雑になり、大規模ネットワークでの計算コストが高くなります。",
        "visual_explanation": "近接中心性を適用すると、ネットワーク全体の中心に位置するノードが大きく表示されます。情報が素早く広がりやすい位置にあるノードや、全体へのアクセスが良い位置にあるノードが強調されます。"
    },
    "betweenness": {
        "name": "媒介中心性",
        "name_en": "Betweenness Centrality",
        "description": "あるノードが他のノード間の最短経路上に位置する頻度に基づく中心性指標です。情報や資源の流れを制御できるノードほど重要とみなします。",
        "use_cases": "通信ネットワークのボトルネック検出、コミュニティ間の橋渡し役の特定、交通網の要所分析などに適しています。",
        "advantages": "ネットワークの「橋渡し」役となるノードを特定でき、情報や資源の流れの制御力を評価できます。",
        "limitations": "計算コストが高く、大規模ネットワークでは近似アルゴリズムが必要になることがあります。",
        "visual_explanation": "媒介中心性を適用すると、異なるグループやコミュニティを結ぶ「橋渡し」の役割を果たすノードが大きく表示されます。これらは情報や物資の流れを制御できる重要な位置にあるノードです。"
    },
    "eigenvector": {
        "name": "固有ベクトル中心性",
        "name_en": "Eigenvector Centrality",
        "description": "重要なノードとつながっているノードほど重要とみなす再帰的な中心性指標です。ノードの重要性は、隣接するノードの重要性に比例します。",
        "use_cases": "影響力のあるユーザーの特定、Webページのランキング（GoogleのPageRankの基礎）、推薦システムなどに適しています。",
        "advantages": "ノードの直接のつながりだけでなく、ネットワーク内での「質的な」つながりを考慮します。",
        "limitations": "方向性のあるネットワークでは解釈が複雑になることがあり、計算が収束しない場合があります。",
        "visual_explanation": "固有ベクトル中心性を適用すると、「重要なノードとつながっているノード」が大きく表示されます。たとえば、影響力のある人とつながりのある人が強調されるため、「権威性」や「社会的地位」を反映した可視化が可能です。"
    },
    "pagerank": {
        "name": "ページランク",
        "name_en": "PageRank",
        "description": "固有ベクトル中心性を拡張した指標で、Webページのランキングに使用されるアルゴリズムです。リンクの重みと確率的な遷移を考慮します。",
        "use_cases": "Web検索エンジン、学術論文の引用分析、ソーシャルメディアの影響力分析などに適しています。",
        "advantages": "有向グラフに適しており、ランダムウォークモデルに基づく堅牢な指標です。",
        "limitations": "パラメータ設定（減衰係数など）が結果に影響し、大規模ネットワークでは計算時間がかかります。",
        "visual_explanation": "ページランクを適用すると、「多くの重要なノードから参照されているノード」が大きく表示されます。これはGoogleの検索アルゴリズムの基礎となった指標で、リンクの質と量の両方を考慮した重要度を表現します。"
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
    
    # 質問からキーワードを抽出（強化版）
    keywords = {
        "direct_influence": ["直接", "つながり", "隣接", "次数", "degree", "人気", "接続数", "友達", "リンク数", "接続", "直接的", "ハブ", "中心人物"],
        "information_flow": ["情報", "伝達", "流れ", "拡散", "近い", "距離", "closeness", "近接", "効率", "速さ", "アクセス", "到達", "伝播", "全体的", "中心"],
        "control": ["制御", "橋渡し", "間", "ブリッジ", "媒介", "betweenness", "仲介", "橋", "連結", "つなぐ", "経路", "パス", "通り道", "コミュニティ間"],
        "prestige": ["重要", "権威", "影響力", "再帰", "固有", "eigenvector", "権威", "評判", "質", "連鎖", "価値", "地位", "重要な人とのつながり"],
        "ranking": ["ランク", "順位", "pagerank", "検索", "参照", "引用", "評価", "格付け", "Webページ", "グーグル", "ページランク"]
    }
    
    # 重要なノードの視覚化に関するキーワード
    visualization_keywords = ["大きく表示", "視覚化", "可視化", "強調", "目立つ", "サイズ", "色", "ノードの大きさ", "表示"]
    
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

def process_centrality_chat(message: str, network_info: Optional[Dict] = None, graphml_content: Optional[str] = None) -> Dict:
    """
    中心性に関するチャットメッセージを処理し、適切な応答を返します
    
    Args:
        message: ユーザーからのチャットメッセージ
        network_info: 現在のネットワークの特性情報（オプション）
        graphml_content: GraphML形式のネットワークデータ（オプション）
        
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
    
    # 「はい」または「適用」などの承認応答をチェック - 直前に中心性の推奨があった場合
    approval_keywords = ["はい", "適用", "お願い", "実行", "計算", "やって", "ok", "yes", "実施", "適用してください"]
    if any(keyword in message_lower for keyword in approval_keywords):
        # ここでは推奨された中心性を実行するための応答を返す
        # 注: 実際の適用はフロントエンドのapplyCentrality関数で行われる
        return {
            "success": True,
            "content": "了解しました。中心性に基づいてノードの大きさを変更しています。大きいノードほど、その中心性指標において重要度が高いことを示しています。",
            "apply_centrality": True,
            # 前回推奨された中心性タイプがあればそれを使用、なければデフォルトで次数中心性を使用
            "centrality_type": "degree",  # 実際の実装ではユーザーの対話履歴から推奨された中心性を取得
            "networkUpdate": {
                "type": "centrality",
                "centralityType": "degree"  # 同上
            }
        }
    
    # 「中心性で可視化して」などの直接的なリクエスト
    visualization_keywords = ["中心性で可視化", "可視化して", "中心性を適用", "中心性を計算", "計算して"]
    if any(keyword in message for keyword in visualization_keywords):
        # ネットワーク特性に基づいて最適な中心性を推奨
        recommendation = recommend_centrality(network_info, message)
        centrality_type = recommendation["recommended_centrality"]
        centrality_info = CENTRALITY_KNOWLEDGE[centrality_type]
        
        return {
            "success": True,
            "content": f"ネットワークの分析に基づき、**{centrality_info['name']}**を使った可視化が最適だと考えられます。\n\n"
                       f"{recommendation['reason']}\n\n"
                       f"{centrality_info['visual_explanation']}\n\n"
                       f"この中心性を適用しますか？「はい」と返信すると、ノードの大きさが中心性値に応じて変化します。他の中心性指標を検討したい場合は、「他の選択肢を教えて」と入力してください。",
            "recommended_centrality": centrality_type,
            "networkUpdate": {
                "type": "centrality",
                "centralityType": centrality_type
            }
        }
    
    # 「他の選択肢」や「別の中心性」を尋ねる場合
    alternative_keywords = ["他の選択肢", "別の中心性", "他の中心性", "他には", "別の指標"]
    if any(keyword in message for keyword in alternative_keywords):
        return {
            "success": True,
            "content": "以下の中心性指標から選択できます：\n\n"
                       "1. **次数中心性（Degree Centrality）**: 多くの直接的なつながりを持つノードを重視します。「人気者」や「ハブ」を見つけるのに適しています。\n\n"
                       "2. **近接中心性（Closeness Centrality）**: ネットワーク全体への近さを測ります。情報が素早く広がる位置にあるノードを特定するのに適しています。\n\n"
                       "3. **媒介中心性（Betweenness Centrality）**: 異なるグループ間の「橋渡し」役となるノードを重視します。情報や資源の流れを制御できる位置にあるノードを特定します。\n\n"
                       "4. **固有ベクトル中心性（Eigenvector Centrality）**: 重要なノードとつながっているノードを重視します。影響力のあるノードを特定するのに適しています。\n\n"
                       "5. **PageRank**: Googleの検索エンジンで使われる指標で、重要なノードからの参照を重視します。\n\n"
                       "どの中心性を適用しますか？例えば「次数中心性を適用」のように指定してください。",
            "options": ["degree", "closeness", "betweenness", "eigenvector", "pagerank"]
        }
    
    # 特定の中心性タイプについての質問かチェック
    for centrality_type in CENTRALITY_KNOWLEDGE:
        if (centrality_type in message_lower or 
            CENTRALITY_KNOWLEDGE[centrality_type]["name"] in message or
            CENTRALITY_KNOWLEDGE[centrality_type]["name_en"] in message):
            
            # 「適用」を含む場合は、その中心性を適用するリクエストとして処理
            if "適用" in message or "計算" in message or "可視化" in message:
                info = get_centrality_info(centrality_type)
                return {
                    "success": True,
                    "content": f"{info['name']}を適用します。{info['visual_explanation']}",
                    "centrality_type": centrality_type,
                    "networkUpdate": {
                        "type": "centrality",
                        "centralityType": centrality_type
                    }
                }
            
            # それ以外は説明を返す
            info = get_centrality_info(centrality_type)
            return {
                "success": True,
                "content": f"{info['name']}（{info['name_en']}）: {info['description']}\n\n"
                           f"用途: {info['use_cases']}\n\n"
                           f"利点: {info['advantages']}\n\n"
                           f"制限: {info['limitations']}\n\n"
                           f"可視化の効果: {info['visual_explanation']}\n\n"
                           f"この中心性を適用しますか？「はい、適用してください」と返信すると、ノードの大きさが中心性に応じて変化します。",
                "centrality_type": centrality_type
            }
    
    # ノードの大きさ変更や重要なノードの可視化に関する一般的な質問の場合
    node_size_keywords = ["ノードの大きさ", "大きく表示", "サイズを変更", "重要なノードを強調", "重要なノード", "重要度に応じて"]
    
    # 具体的な要望を示すキーワード
    specific_request_keywords = {
        "degree": ["接続数", "つながり", "次数", "友達", "フォロワー", "ハブ", "直接", "リンク数"],
        "closeness": ["最短距離", "近い", "アクセス", "効率", "中心", "情報伝達", "情報拡散"],
        "betweenness": ["橋渡し", "仲介", "制御", "経路", "コミュニティ間", "グループ間"],
        "eigenvector": ["影響力", "重要な人", "権威", "質的", "連鎖", "重要なノードとつながり"],
        "pagerank": ["ランキング", "評価", "参照", "引用", "Webページ"]
    }
    
    # 具体的な要望があるかチェック
    has_specific_request = False
    specific_centrality_type = None
    
    for centrality_type, keywords in specific_request_keywords.items():
        if any(keyword in message for keyword in keywords):
            has_specific_request = True
            specific_centrality_type = centrality_type
            break
    
    if any(keyword in message for keyword in node_size_keywords):
        # 具体的な要望がある場合
        if has_specific_request and specific_centrality_type:
            centrality_info = CENTRALITY_KNOWLEDGE[specific_centrality_type]
            
            return {
                "success": True,
                "content": f"ご要望に基づき、**{centrality_info['name']}**を使った可視化が最適です。\n\n"
                          f"{centrality_info['description']}\n\n"
                          f"{centrality_info['visual_explanation']}\n\n"
                          f"この中心性を適用しますか？「はい、適用してください」と返信すると、ノードの大きさが中心性に応じて変化します。",
                "recommended_centrality": specific_centrality_type,
                "networkUpdate": {
                    "type": "centrality",
                    "centralityType": specific_centrality_type
                }
            }
        # 具体的な要望がない場合は、中心性の概念と種類について説明
        else:
            return {
                "success": True,
                "content": "ネットワークの重要なノードを大きさで表現するには、中心性指標が役立ちます。中心性とは、ネットワーク内でのノードの重要度を測る指標です。\n\n"
                          "中心性には様々な種類があり、ネットワークの特徴や分析目的によって最適な指標が異なります。主な中心性指標は以下の通りです：\n\n"
                          "1. **次数中心性（Degree Centrality）**: 多くのノードと直接つながっているノードを重要とみなします。SNSで友達が多い人や、交通網で多くの路線が通る駅などが該当します。\n\n"
                          "2. **近接中心性（Closeness Centrality）**: ネットワーク全体の中心に位置し、他のノードへの距離が近いノードを重要とみなします。情報が速く広がる位置にあるノードなどが該当します。\n\n"
                          "3. **媒介中心性（Betweenness Centrality）**: 異なるグループを「橋渡し」するノードを重要とみなします。情報や物資の流れを制御できる位置にあるノードが該当します。\n\n"
                          "4. **固有ベクトル中心性（Eigenvector Centrality）**: 重要なノードとつながっているノードほど重要とみなします。「重要な人とつながりのある人」が重要という考え方です。\n\n"
                          "5. **PageRank**: Googleの検索エンジンで使われる指標で、多くの重要なノードから参照されているノードを重要とみなします。\n\n"
                          "どのような重要性を可視化したいですか？例えば：\n"
                          "- 「接続数が多いノードを大きく表示したい」\n"
                          "- 「他のノードに最短の距離で行けるノードを大きくしたい」\n"
                          "- 「コミュニティ間の橋渡し役となるノードを強調したい」\n"
                          "- 「影響力のあるノードとつながっているノードを大きく表示したい」\n"
                          "などと具体的に教えていただければ、最適な中心性指標を提案できます。",
                "general_info": True
            }
    
    # 重要なノードや中心性に関する一般的な質問の場合
    centrality_keywords = ["中心性", "centrality", "重要", "重要度", "中心", "影響力"]
    if any(keyword in message_lower for keyword in centrality_keywords):
        # 具体的な要望がある場合
        if has_specific_request and specific_centrality_type:
            centrality_info = CENTRALITY_KNOWLEDGE[specific_centrality_type]
            
            return {
                "success": True,
                "content": f"ご要望に基づき、**{centrality_info['name']}**を使った可視化が最適です。\n\n"
                          f"{centrality_info['description']}\n\n"
                          f"{centrality_info['visual_explanation']}\n\n"
                          f"この中心性を適用しますか？「はい、適用してください」と返信すると、ノードの大きさが中心性に応じて変化します。",
                "recommended_centrality": specific_centrality_type,
                "networkUpdate": {
                    "type": "centrality",
                    "centralityType": specific_centrality_type
                }
            }
        # 具体的な要望がない場合は、中心性の概念と種類について説明
        else:
            return {
                "success": True,
                "content": "ネットワークの重要なノードを可視化するには、中心性指標が役立ちます。中心性とは、ネットワーク内でのノードの重要度を測る指標です。\n\n"
                          "中心性には様々な種類があり、ネットワークの特徴や分析目的によって最適な指標が異なります。主な中心性指標は以下の通りです：\n\n"
                          "1. **次数中心性（Degree Centrality）**: 多くのノードと直接つながっているノードを重要とみなします。SNSで友達が多い人や、交通網で多くの路線が通る駅などが該当します。\n\n"
                          "2. **近接中心性（Closeness Centrality）**: ネットワーク全体の中心に位置し、他のノードへの距離が近いノードを重要とみなします。情報が速く広がる位置にあるノードなどが該当します。\n\n"
                          "3. **媒介中心性（Betweenness Centrality）**: 異なるグループを「橋渡し」するノードを重要とみなします。情報や物資の流れを制御できる位置にあるノードが該当します。\n\n"
                          "4. **固有ベクトル中心性（Eigenvector Centrality）**: 重要なノードとつながっているノードほど重要とみなします。「重要な人とつながりのある人」が重要という考え方です。\n\n"
                          "5. **PageRank**: Googleの検索エンジンで使われる指標で、多くの重要なノードから参照されているノードを重要とみなします。\n\n"
                          "どのような重要性を可視化したいですか？例えば：\n"
                          "- 「接続数が多いノードを大きく表示したい」\n"
                          "- 「他のノードに最短の距離で行けるノードを大きくしたい」\n"
                          "- 「コミュニティ間の橋渡し役となるノードを強調したい」\n"
                          "- 「影響力のあるノードとつながっているノードを大きく表示したい」\n"
                          "などと具体的に教えていただければ、最適な中心性指標を提案できます。",
                "general_info": True
            }
    
    # 中心性に関する説明を求められた場合
    if "中心性について" in message or "中心性とは" in message or "中心性の種類" in message:
        return {
            "success": True,
            "content": "ネットワーク中心性とは、グラフ内でのノードの重要度を測る指標です。中心性を使うと、ネットワーク内で重要な役割を果たすノードを大きく表示するなど、視覚的に強調することができます。\n\n"
                      "主な中心性指標には以下のようなものがあります：\n\n"
                      "1. **次数中心性（Degree Centrality）**: 多くのノードと直接つながっているノードを重要とみなします。SNSで友達が多い人や、交通網で多くの路線が通る駅などが該当します。\n\n"
                      "2. **近接中心性（Closeness Centrality）**: ネットワーク全体の中心に位置し、他のノードへの距離が近いノードを重要とみなします。情報が速く広がる位置にあるノードなどが該当します。\n\n"
                      "3. **媒介中心性（Betweenness Centrality）**: 異なるグループを「橋渡し」するノードを重要とみなします。情報や物資の流れを制御できる位置にあるノードが該当します。\n\n"
                      "4. **固有ベクトル中心性（Eigenvector Centrality）**: 重要なノードとつながっているノードほど重要とみなします。「重要な人とつながりのある人」が重要という考え方です。\n\n"
                      "5. **PageRank**: Googleの検索エンジンで使われる指標で、多くの重要なノードから参照されているノードを重要とみなします。\n\n"
                      "あなたのネットワークではどのような重要性を可視化したいですか？例えば：\n"
                      "- 「多くのノードと直接つながっているノードを強調したい」\n"
                      "- 「情報が最も効率的に広がるノードを知りたい」\n"
                      "- 「ネットワークを分断せずに取り除けないノードを特定したい」\n"
                      "などと具体的に教えていただければ、最適な中心性指標を提案できます。",
            "general_info": True
        }
    
    # その他の中心性に関連しそうな質問の場合
    return {
        "success": True,
        "content": "ネットワークの重要なノードを分析するには中心性指標が役立ちます。ノードの重要度に応じて大きさや色を変えることで、視覚的に重要なノードを強調できます。\n\n"
                  "次数中心性、近接中心性、媒介中心性、固有ベクトル中心性、PageRankなど、様々な指標があり、それぞれ異なる「重要さ」を表現します。\n\n"
                  "何を知りたいですか？例えば：\n"
                  "- 「中心性で可視化して」\n"
                  "- 「ノードの重要度で視覚化したい」\n"
                  "- 「多くのノードとつながっているノードを大きく表示したい」\n"
                  "- 「ネットワークの橋渡し役になっているノードを強調したい」\n"
                  "- 「次数中心性について教えて」\n"
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

def process_chat_message(message: str, network_info: Optional[Dict] = None, graphml_content: Optional[str] = None) -> Dict:
    """
    チャットメッセージを処理し、中心性に関する応答を返します
    
    Args:
        message: ユーザーからのチャットメッセージ
        network_info: ネットワークの特性情報（オプション）
        graphml_content: GraphML形式のネットワークデータ（オプション）
        
    Returns:
        応答内容と推奨操作を含む辞書およびGraphML形式のデータ
    """
    result = process_centrality_chat(message, network_info, graphml_content)
    
    # GraphML形式のレスポンスに関連情報を追加
    if graphml_content is not None:
        result["graphml_content"] = graphml_content
    
    return result
