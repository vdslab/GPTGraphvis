"""
LLM service for processing chat messages.
"""

import json
import httpx
import re
from typing import List, Dict, Any

async def process_chat_message(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Process chat messages and generate a response using an LLM.
    
    Args:
        messages: A list of message dictionaries with 'role' and 'content' keys
        
    Returns:
        A dictionary containing the assistant's response with 'content' and optional 'metadata'
    """
    try:
        # Get the latest user message for context
        user_message = next((msg["content"] for msg in reversed(messages) 
                            if msg["role"] == "user"), "")

        # 中心性に関する質問かどうかを確認
        centrality_keywords = [
            "中心性", "centrality", "重要度", "重要なノード", "ノードの大きさ", 
            "重要", "中心", "センタリティ", "次数", "degree", "近接", "closeness", 
            "媒介", "betweenness", "固有ベクトル", "eigenvector", "pagerank"
        ]
        
        # 中心性に関する質問であれば、MCPサーバーへのリクエストを準備
        if any(keyword in user_message.lower() for keyword in centrality_keywords):
            try:
                # ここでは実際にMCPサーバーのエンドポイントを直接呼び出すのではなく
                # フロントエンドのchatStoreが処理するためのメタデータを含む応答を返す
                return {
                    "content": "ネットワークの中心性に関するご質問ですね。中心性指標はネットワーク内のノードの重要度を計測するための指標です。",
                    "metadata": {
                        "processed": True,
                        "model": "network-analysis",
                        "isCentralityQuery": True,
                        "originalMessage": user_message
                    }
                }
            except Exception as e:
                print(f"Error processing centrality request: {str(e)}")
                return {
                    "content": "申し訳ありませんが、中心性の処理中にエラーが発生しました。別の方法で質問してみてください。",
                    "metadata": {
                        "error": str(e)
                    }
                }
        
        # サイズや色に関する質問の場合
        size_color_keywords = ["サイズ", "大きさ", "色", "カラー", "size", "color"]
        if any(keyword in user_message.lower() for keyword in size_color_keywords):
            return {
                "content": "ノードのサイズや色を変更するご質問ですね。チャットを通じて「ノードを赤色にして」や「ノードサイズを大きくして」などと指示できます。",
                "metadata": {
                    "processed": True,
                    "model": "network-analysis",
                    "isVisualPropertyQuery": True
                }
            }
        
        # レイアウトに関する質問の場合
        layout_keywords = ["レイアウト", "配置", "layout", "arrange"]
        if any(keyword in user_message.lower() for keyword in layout_keywords):
            return {
                "content": "ネットワークのレイアウトに関するご質問ですね。「円形レイアウトを適用して」や「Fruchterman-Reingoldレイアウトを使って」などとチャットで指示できます。",
                "metadata": {
                    "processed": True,
                    "model": "network-analysis",
                    "isLayoutQuery": True
                }
            }
        
        # ヘルプを求める質問の場合
        help_keywords = ["ヘルプ", "使い方", "どうすれば", "help", "how to"]
        if any(keyword in user_message.lower() for keyword in help_keywords):
            return {
                "content": """このチャットでは以下の操作が可能です：

1. レイアウト変更: 「円形レイアウトを使用」または「Fruchterman-Reingoldレイアウトを適用」
2. レイアウト推奨: 「コミュニティ検出に適したレイアウトを推奨」
3. 中心性の適用: 「次数中心性を表示」または「媒介中心性を適用」
4. 色の変更: 「ノードを赤色にして」または「エッジの色を青にして」
5. サイズ変更: 「ノードサイズを大きくして」または「エッジを細くして」
6. ネットワーク情報の表示: 「ネットワーク統計を表示」

また、ページ上部の「ネットワークファイルをアップロード」ボタンでファイルをアップロードできます。""",
                "metadata": {
                    "processed": True,
                    "model": "help-guide"
                }
            }
        
        # その他の一般的な質問に対する応答
        return {
            "content": f"ネットワーク可視化に関するご質問ですね。チャットを通じてネットワークの表示方法を変更できます。例えば「ノードの大きさを中心性で変更したい」などと質問してみてください。",
            "metadata": {
                "processed": True,
                "model": "general-response"
            }
        }
        
    except Exception as e:
        # Log error and return a generic response
        print(f"Error in process_chat_message: {str(e)}")
        return {
            "content": "申し訳ありませんが、メッセージの処理中にエラーが発生しました。",
            "metadata": {
                "error": str(e)
            }
        }
