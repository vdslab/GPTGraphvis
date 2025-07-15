# 日本語レイアウトコマンドの実装

このドキュメントでは、日本語でのレイアウトコマンドをチャットインターフェイスで使用する機能の実装について説明します。

## 実装内容

1. **フロントエンド（NetworkChatPage.jsx）**:
   - 日本語のレイアウトコマンドを検出するロジックを追加
   - 「レイアウト」「適応」「変更」「適用」などの日本語キーワードを認識
   - 各レイアウトタイプの日本語名（「円形」「ランダム」「スプリング」など）を認識

2. **バックエンド（network_chat.py）**:
   - OpenAIのシステムプロンプトを更新して日本語コマンドをサポート
   - 日本語のレイアウトタイプを検出するロジックを追加
   - 日本語の例を含むドキュメントを追加

## サポートされているレイアウトコマンド

以下の日本語コマンドがサポートされています：

| 日本語コマンド例 | 対応するレイアウト |
|-----------------|-----------------|
| `springレイアウトを適応させてください` | Spring |
| `円形レイアウトに変更してください` | Circular |
| `ランダムレイアウトを適用` | Random |
| `スペクトルレイアウトを適用してください` | Spectral |
| `カマダカワイレイアウトを適用` | Kamada-Kawai |
| `フルクターマンレイアウトをた適用` | Fruchterman-Reingold |
| `コミュニティレイアウトを適用` | Community |
| `殻レイアウトを適用` | Shell |

## テスト結果

日本語レイアウトコマンドの検出機能は、以下の2つの方法でテストされました：

1. **コードテスト（test_japanese_layout_code.py）**:
   - フロントエンドとバックエンドの両方のコードロジックをシミュレート
   - さまざまな日本語コマンドに対するレイアウトタイプの検出をテスト
   - すべてのテストが成功し、正しいレイアウトタイプが検出されることを確認

2. **APIテスト（test_japanese_layout.py）**:
   - 実際のAPIエンドポイントを使用してテスト
   - 認証の問題により完全なテストは実行できませんでしたが、コードロジックは正しく動作することを確認

## 使用方法

チャットインターフェイスで以下のような日本語コマンドを入力することで、対応するレイアウトアルゴリズムが適用されます：

```
springレイアウトを適応させてください
```

```
円形レイアウトに変更してください
```

```
ランダムレイアウトを適用
```

## 技術的な詳細

### フロントエンドの検出ロジック

```javascript
// Check if the message is a command to change the layout (in English or Japanese)
if ((inputMessage.toLowerCase().includes('change') && inputMessage.toLowerCase().includes('layout')) ||
    (inputMessage.includes('レイアウト') && (inputMessage.includes('適応') || inputMessage.includes('変更') || inputMessage.includes('適用')))) {
  
  // Determine layout type from message (English or Japanese)
  let layoutType = "spring"; // Default
  const message = inputMessage.toLowerCase();
  
  if (message.includes('circular') || message.includes('円形')) {
    layoutType = "circular";
  } else if (message.includes('random') || message.includes('ランダム')) {
    layoutType = "random";
  } else if (message.includes('spectral') || message.includes('スペクトル')) {
    layoutType = "spectral";
  } else if (message.includes('shell') || message.includes('殻')) {
    layoutType = "shell";
  } else if (message.includes('spring') || message.includes('スプリング')) {
    layoutType = "spring";
  } else if (message.includes('kamada') || message.includes('カマダ')) {
    layoutType = "kamada_kawai";
  } else if (message.includes('fruchterman') || message.includes('フルクターマン')) {
    layoutType = "fruchterman_reingold";
  } else if (message.includes('community') || message.includes('コミュニティ')) {
    layoutType = "community";
  }
  
  // Use MCP client to change layout
  // ...
}
```

### バックエンドのシステムプロンプト

```
You are a network visualization assistant that helps users visualize and analyze network data.
Extract network-related commands from user messages in both English and Japanese.

The commands can be:

1. change_layout: Change the layout algorithm or its parameters
   - English examples: "change layout to spring", "apply circular layout"
   - Japanese examples: "springレイアウトを適応させてください", "円形レイアウトに変更", "レイアウトを適用"
   - Parameters: layout_type (string), layout_params (object)

2. calculate_centrality: Calculate node centrality metrics
   - English examples: "calculate degree centrality", "show betweenness centrality"
   - Japanese examples: "次数中心性を計算して", "媒介中心性を表示", "中心性を計算"
   - Parameters: centrality_type (string: degree, closeness, betweenness, eigenvector, pagerank)

...
```

## 今後の改善点

1. **より自然な日本語表現のサポート**: 現在は特定のキーワードに依存していますが、より自然な日本語表現をサポートするために、より高度な自然言語処理を導入できます。

2. **日本語のエラーメッセージ**: ユーザーが日本語でコマンドを入力した場合、エラーメッセージも日本語で表示するとより良いユーザー体験になります。

3. **日本語のヘルプドキュメント**: チャットインターフェイスで使用できる日本語コマンドの一覧と使用例を提供するヘルプコマンドを追加すると便利です。
