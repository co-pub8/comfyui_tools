# run_workflow.py 仕様書

## 概要

ComfyUI のワークフローを Python から自動実行するスクリプト。
WebSocket で進捗をリアルタイム監視し、結果を `result.json` に記録する。

## ファイル構成

```
comfyui_tools/
  run_workflow.py         # メインスクリプト
  config.json             # 接続設定・LoRAマッピング
  templates/                     # ワークフローテンプレート
    template_lora_0.json         # LoRA 0個用
    template_lora_1.json         # LoRA 1個用
    template_lora_2.json         # LoRA 2個用
    template_lora_3.json         # LoRA 3個用
    template_lora_4.json         # LoRA 4個用
  requirements.txt         # 必要ライブラリ
```

## 設定ファイル

### config.json
```json
{
  "comfyui_url": "http://127.0.0.1:8188"
}
```

### lora_list.json
LoRA名（入力JSONのキー）とLoRAファイル名・ストレングスのマッピング。
```json
{
  "my_lora": {"file": "my_lora.safetensors", "strength": 0.8},
  "another_lora": {"file": "another_lora.safetensors", "strength": 0.7}
}
```

## 入力インターフェース

### 実行コマンド

```bash
python run_workflow.py --input input.json --output result.json
```

| オプション | 必須 | 説明 |
|---|---|---|
| `--input` | ○ | 入力 JSON ファイルのパス |
| `--output` | △ | result.json の出力先（省略時: `result.json`） |

### 入力 JSON フォーマット

```json
{
  "loras": ["LoRA_name_1", "LoRA_name_2"],
  "prompts": {
    "positive": "masterpiece, best quality, 1girl ...",
    "negative": "worst quality, bad quality ..."
  }
}
```

- `LoRAs`: `lora_list.json` のキー名を指定する。0〜4個まで指定可能。
- `prompts.positive` / `prompts.negative`: プロンプト文字列。

## テンプレートの自動選択

入力 JSON の `LoRAs` の個数に応じて、使用するテンプレートを自動で選択する。

| LoRA 個数 | 使用テンプレート |
|---|---|
| 0 | `templates/template_lora_0.json` |
| 1 | `templates/template_lora_1.json` |
| 2 | `templates/template_lora_2.json` |
| 3 | `templates/template_lora_3.json` |
| 4 | `templates/template_lora_4.json` |

## テンプレートのノード特定

ワークフロー JSON のノード `_meta.title` で書き換え対象ノードを識別する。
テンプレートを作成する際は、対象ノードに以下のタイトルを設定すること。

| `_meta.title` | 書き換える内容 |
|---|---|
| `positive_prompt` | `prompts.positive` の文字列 |
| `negative_prompt` | `prompts.negative` の文字列 |
| `lora_loader_1` | 1つ目のLoRAファイル名・ストレングス |
| `lora_loader_2` | 2つ目のLoRAファイル名・ストレングス |
| `lora_loader_3` | 3つ目のLoRAファイル名・ストレングス |
| `lora_loader_4` | 4つ目のLoRAファイル名・ストレングス |

`class_type` や `_meta.title` によらず、`inputs.seed` フィールドを持つすべてのノードは実行ごとにランダム生成した値（`0〜2^53`）で上書きする。対象ノードにはすべて同一の seed 値を使用する。

## アーキテクチャ

### クラス構成

| クラス | 責務 |
|---|---|
| `WorkflowBuilder` | テンプレート選択・読み込み・プロンプト/LoRA/seed の書き換え |
| `ComfyUIClient` | ComfyUI REST API 呼び出し・WebSocket 監視 |
| `WorkflowRunner` | 上記2クラスを束ねてワークフロー実行を制御するファサード |

### 実装上の制約

- **WebSocket バイナリフレームのスキップ**: ComfyUI はプレビュー画像をバイナリフレームで送信する。`if isinstance(raw, bytes): continue` を必ず入れること。これを省略すると `json.loads()` が失敗する。
- **テンプレートは deepcopy してから書き換える**: `WorkflowBuilder.apply()` では `copy.deepcopy()` を先頭で行い、元テンプレートを汚染しない。

## 処理フロー

1. `config.json` を読み込み、接続先 URL を取得する
2. 入力 JSON を読み込む
3. `lora_list.json` を読み込み、LoRA名 → ファイル名・ストレングスを解決する
4. LoRA の個数に応じてテンプレートを自動選択し、プロンプト・LoRA を書き換える
5. `POST /prompt` でワークフローを送信し、`prompt_id` を取得する
6. WebSocket (`ws://host/ws?clientId=<uuid>`) で実行完了またはエラーを監視する
7. 完了後、`GET /history/{prompt_id}` で出力ファイル一覧を取得する
8. `result.json` を出力して終了する

## result.json フォーマット

### 成功時
```json
{
  "status": "success",
  "prompt_id": "abc123",
  "timestamp": "2026-04-22T20:30:00",
  "template": "templates/lora2.json",
  "parameters": {
    "positive": "masterpiece, best quality, 1girl ...",
    "negative": "worst quality, bad quality ...",
    "loras": [
      {"name": "my_lora", "file": "my_lora.safetensors", "strength": 0.8},
      {"name": "another_lora", "file": "another_lora.safetensors", "strength": 0.7}
    ]
  },
  "outputs": [
    {"filename": "ComfyUI_00001_.png", "subfolder": "", "type": "output"}
  ],
  "error": null
}
```

### エラー時
```json
{
  "status": "error",
  "prompt_id": null,
  "timestamp": "2026-04-22T20:30:00",
  "template": "templates/lora2.json",
  "parameters": {
    "positive": "masterpiece, best quality, 1girl ...",
    "negative": "worst quality, bad quality ...",
    "loras": [
      {"name": "my_lora", "file": "my_lora.safetensors", "strength": 0.8}
    ]
  },
  "outputs": [],
  "error": "ComfyUI に接続できません: Connection refused"
}
```

## エラーハンドリング

| エラー種別 | 対応 |
|---|---|
| ComfyUI 未起動・接続失敗 | result.json にエラー記録して終了 |
| 入力 JSON のフォーマットが不正 | result.json にエラー記録して終了 |
| LoRA名が lora_list.json に存在しない | result.json にエラー記録して終了 |
| LoRA が 5個以上指定された | result.json にエラー記録して終了 |
| テンプレートファイルが存在しない | result.json にエラー記録して終了 |
| ComfyUI 側のワークフロー実行エラー | result.json にエラー記録して終了 |

## 開発ルール

- `config.json` に統合できるものは別ファイルを作らない。
- 新しいクラスや関数を追加する場合は `WorkflowRunner` → `WorkflowBuilder` → `ComfyUIClient` の依存方向を崩さない。
- プロンプト最大長 `MAX_PROMPT_LENGTH = 3000` はメモリ枯渇防止のため変更・削除しない。

## 依存ライブラリ

- `websockets` — WebSocket 接続・進捗監視
- `requests` — REST API 呼び出し
- `pytest` — テスト

## 実行例(CLI)
```bash
python run_workflow.py --input input.json --output result.json --config config.json
```

## 実行例(Pythonからimportして使用)
```python
runner = WorkflowRunner("config.json")
outputs = runner.execute(["my_lora"], {"positive": "...", "negative": "..."})
```
