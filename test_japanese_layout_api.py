"""
日本語レイアウトコマンドのAPIテスト

このスクリプトは、ネットワークレイアウトAPIを使用して、日本語のレイアウトコマンドをテストします。
"""

import requests
import json
import matplotlib.pyplot as plt
import networkx as nx
import sys

# APIのURL
API_URL = "http://localhost:8000"

def login(username, password):
    """ログインしてトークンを取得する"""
    response = requests.post(
        f"{API_URL}/auth/token",
        data={"username": username, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"ログイン成功: トークンを取得しました")
        return token
    else:
        print(f"ログイン失敗: {response.status_code} - {response.text}")
        return None

def get_sample_network(token):
    """サンプルネットワークを取得する"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_URL}/network-chat/network",
        headers=headers
    )
    
    if response.status_code == 200:
        print("サンプルネットワークを取得しました")
        return response.json()
    else:
        print(f"サンプルネットワーク取得失敗: {response.status_code} - {response.text}")
        return None

def apply_layout(token, network_data, layout_type, layout_params=None):
    """レイアウトを適用する"""
    if layout_params is None:
        layout_params = {}
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # リクエストデータを作成
    request_data = {
        "nodes": network_data["nodes"],
        "edges": network_data["edges"],
        "layout": layout_type,
        "layout_params": layout_params
    }
    
    # まずMCPサーバーを試す
    try:
        print(f"MCPサーバーを使用して{layout_type}レイアウトを適用しています...")
        mcp_response = requests.post(
            f"{API_URL}/mcp/tools/change_layout",
            headers=headers,
            json={"arguments": {"layout_type": layout_type, "layout_params": layout_params}}
        )
        
        if mcp_response.status_code == 200:
            print("MCPサーバーでレイアウトを適用しました")
            return mcp_response.json()
    except Exception as e:
        print(f"MCPサーバーでのレイアウト適用に失敗しました: {e}")
    
    # MCPサーバーが失敗した場合、従来のAPIを使用
    print(f"従来のAPIを使用して{layout_type}レイアウトを適用しています...")
    response = requests.post(
        f"{API_URL}/network/layout",
        headers=headers,
        json=request_data
    )
    
    if response.status_code == 200:
        print(f"{layout_type}レイアウトを適用しました")
        return response.json()
    else:
        print(f"レイアウト適用失敗: {response.status_code} - {response.text}")
        return None

def visualize_network(network_data, title):
    """ネットワークを可視化する"""
    G = nx.Graph()
    
    # ノードを追加
    for node in network_data["nodes"]:
        G.add_node(node["id"], pos=(node["x"], node["y"]), label=node.get("label", node["id"]))
    
    # エッジを追加
    for edge in network_data["edges"]:
        G.add_edge(edge["source"], edge["target"])
    
    # ノードの位置を取得
    pos = nx.get_node_attributes(G, 'pos')
    
    # グラフを描画
    plt.figure(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=500, edge_color='gray')
    plt.title(title)
    plt.axis('off')
    
    # 画像を保存
    filename = f"{title.replace(' ', '_')}.png"
    plt.savefig(filename)
    print(f"ネットワーク図を{filename}に保存しました")
    
    return G

def main():
    """メイン関数"""
    # コマンドライン引数からユーザー名とパスワードを取得
    if len(sys.argv) < 3:
        print("使用方法: python test_japanese_layout_api.py <ユーザー名> <パスワード>")
        return
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    # ログイン
    token = login(username, password)
    if not token:
        return
    
    # サンプルネットワークを取得
    network_data = get_sample_network(token)
    if not network_data:
        return
    
    # 日本語レイアウト名とその英語名のマッピング
    layout_mapping = {
        "スプリング": "spring",
        "円形": "circular",
        "ランダム": "random",
        "スペクトル": "spectral",
        "殻": "shell",
        "スパイラル": "spiral",
        "カマダカワイ": "kamada_kawai",
        "フルクターマンラインゴールド": "fruchterman_reingold",
        "コミュニティ": "community"
    }
    
    # 各レイアウトを適用して可視化
    for ja_name, en_name in layout_mapping.items():
        print(f"\n{ja_name}レイアウトをテストしています...")
        
        # レイアウトを適用
        layout_result = apply_layout(token, network_data, en_name)
        if layout_result:
            # ネットワークを可視化
            visualize_network(layout_result, f"{ja_name}レイアウト")

if __name__ == "__main__":
    main()
