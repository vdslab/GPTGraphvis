import requests
import json
import sys

def test_convert_graphml(file_path):
    """
    GraphMLファイルを標準形式に変換するテスト
    
    Args:
        file_path (str): GraphMLファイルのパス
    """
    try:
        # ファイルを読み込む
        with open(file_path, 'r', encoding='utf-8') as f:
            graphml_content = f.read()
        
        # APIエンドポイントにリクエストを送信
        url = "http://localhost:8000/proxy/networkx/tools/convert_graphml"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlcjEyMyIsImV4cCI6MTc1MzY4Njc1Nn0.dxp3_NKd94_Sn-0GHoQMs43KarjFN7d85z_LXk9usU8"
        }
        # NetworkXMCPサーバーの期待する形式に合わせる
        payload = {
            "arguments": {
                "graphml_content": graphml_content
            }
        }
        
        print(f"Sending request to convert GraphML: {file_path}")
        response = requests.post(url, headers=headers, json=payload)
        
        # レスポンスを解析
        if response.status_code == 200:
            result = response.json()
            # APIプロキシのレスポンス形式に合わせる
            if result.get("success"):
                print("GraphML conversion successful!")
                # 変換されたGraphMLを保存
                output_path = file_path.replace(".graphml", "_converted.graphml")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result["graphml_content"])
                print(f"Converted GraphML saved to: {output_path}")
                return True
            # 結果がresultオブジェクト内にある場合
            elif "result" in result and result["result"].get("success"):
                print("GraphML conversion successful!")
                # 変換されたGraphMLを保存
                output_path = file_path.replace(".graphml", "_converted.graphml")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result["result"]["graphml_content"])
                print(f"Converted GraphML saved to: {output_path}")
                return True
            else:
                error = result.get("error", "Unknown error")
                if "result" in result and "error" in result["result"]:
                    error = result["result"]["error"]
                print(f"GraphML conversion failed: {error}")
                return False
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        test_convert_graphml(file_path)
    else:
        print("Please provide a GraphML file path")
        sys.exit(1)