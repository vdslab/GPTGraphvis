from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import os
from openai import OpenAI

import models, auth
from database import get_db

router = APIRouter(
    prefix="/chatgpt",
    tags=["chatgpt"],
    responses={401: {"description": "Unauthorized"}},
)

# Pydantic models for request and response
from pydantic import BaseModel
import json

class ChatGPTRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7

class ChatGPTResponse(BaseModel):
    response: str

class LayoutRecommendationRequest(BaseModel):
    description: str  # ネットワークの説明（ノード数、エッジ数、ネットワークの種類など）
    purpose: str  # 可視化の目的（クラスター検出、中心性分析など）

class LayoutRecommendationResponse(BaseModel):
    recommended_layout: str  # 推薦されたレイアウトアルゴリズム
    explanation: str  # 推薦理由の説明
    recommended_parameters: Optional[Dict[str, Any]] = None  # 推薦されるパラメータ（オプション）

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
client = OpenAI(api_key=api_key)

@router.post("/generate", response_model=ChatGPTResponse)
async def generate_response(
    request: ChatGPTRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a response from ChatGPT."""
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": request.prompt}
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        # Extract response text
        response_text = response.choices[0].message.content
        
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

@router.post("/recommend-layout", response_model=LayoutRecommendationResponse)
async def recommend_layout(
    request: LayoutRecommendationRequest,
    current_user: models.User = Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """ネットワークの特性と可視化の目的に基づいて、最適なレイアウトアルゴリズムを推薦します。"""
    try:
        # Function定義
        layout_recommendation_function = {
            "name": "recommend_network_layout",
            "description": "ネットワークの特性と可視化の目的に基づいて、最適なネットワークレイアウトアルゴリズムを推薦します",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommended_layout": {
                        "type": "string",
                        "enum": [
                            "spring", "circular", "random", "spectral", 
                            "shell", "spiral", "planar", "kamada_kawai", 
                            "fruchterman_reingold", "bipartite", "multipartite"
                        ],
                        "description": "推薦されるレイアウトアルゴリズム"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "なぜこのレイアウトアルゴリズムが推薦されるのかの説明"
                    },
                    "recommended_parameters": {
                        "type": "object",
                        "description": "推薦されるレイアウトアルゴリズムのパラメータ（オプション）"
                    }
                },
                "required": ["recommended_layout", "explanation"]
            }
        }
        
        # システムプロンプトの作成
        system_prompt = """
        あなたはネットワーク可視化の専門家です。
        ユーザーが提供するネットワークの特性と可視化の目的に基づいて、最適なレイアウトアルゴリズムを推薦してください。
        
        利用可能なレイアウトアルゴリズム:
        
        1. spring - バネモデルに基づくレイアウト。ノード間の距離を均等にしようとする。中規模のネットワークに適している。
        2. circular - ノードを円形に配置するレイアウト。ネットワークの周期性や対称性を強調したい場合に適している。
        3. random - ノードをランダムに配置するレイアウト。初期配置や他のレイアウトとの比較に使用される。
        4. spectral - スペクトル分解に基づくレイアウト。グラフの構造的特性を反映し、クラスターを視覚化するのに適している。
        5. shell - ノードを同心円状に配置するレイアウト。階層構造やグループ構造を持つネットワークに適している。
        6. spiral - ノードを螺旋状に配置するレイアウト。連続的な順序を持つデータの可視化に適している。
        7. planar - 平面グラフのための平面埋め込みレイアウト。エッジの交差を最小化したい場合に適している。
        8. kamada_kawai - Kamada-Kawaiアルゴリズムに基づくレイアウト。グラフの美的な表現を重視し、ノード間の距離を保持する。
        9. fruchterman_reingold - Fruchterman-Reingoldアルゴリズムに基づくレイアウト。力学モデルを使用し、ノードの分布を均等にする。
        10. bipartite - 二部グラフ用のレイアウト。二部グラフの構造を明確に表示する。
        11. multipartite - 多部グラフ用のレイアウト。複数のグループに分かれたノードを視覚化する。
        
        各アルゴリズムの特性を考慮し、ネットワークの特性と可視化の目的に最も適したアルゴリズムを選択してください。
        また、必要に応じて推奨パラメータも提案してください。
        """
        
        # OpenAI APIの呼び出し
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"ネットワークの特性: {request.description}\n可視化の目的: {request.purpose}"}
            ],
            functions=[layout_recommendation_function],
            function_call={"name": "recommend_network_layout"}
        )
        
        # レスポンスの処理
        function_call = response.choices[0].message.function_call
        function_args = json.loads(function_call.arguments)
        
        result = {
            "recommended_layout": function_args["recommended_layout"],
            "explanation": function_args["explanation"]
        }
        
        # オプションのパラメータがある場合は追加
        if "recommended_parameters" in function_args:
            result["recommended_parameters"] = function_args["recommended_parameters"]
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error recommending layout: {str(e)}"
        )
