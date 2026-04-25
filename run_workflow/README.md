# run_workflow

ComfyUI の REST API と WebSocket を使い、ワークフローを Python から自動実行するツールです。

LoRA の枚数に応じてテンプレートを自動選択し、プロンプトと LoRA を差し込んで実行します。

実行結果（出力ファイル一覧・エラー情報）は `result.json` に記録されます。

## 機能

- LoRA 0〜4 個に対応したテンプレートの自動選択
- プロンプト（positive / negative）と LoRA の差し込み
- WebSocket によるリアルタイム進捗監視
- 実行ごとにシード値をランダム生成
- 成功・失敗を `result.json` に記録

## 必要環境

- Python 3.12+
- 起動済みの ComfyUI（デフォルト: `http://127.0.0.1:8188`）

## セットアップ

```bash
cd run_workflow
pip install -r requirements.txt
```

## 設定

**`config.json`** — ComfyUI の接続先と LoRA マッピングを記述します。

```json
{
  "comfyui_url": "http://127.0.0.1:8188",
  "lora_list": {
    "my_lora": {"file": "my_lora.safetensors", "strength": 0.8}
  }
}
```

## 使い方

### CLI

```bash
python run_workflow.py --input input.json --output result.json
```

**`input.json` フォーマット:**

```json
{
  "loras": ["my_lora"],
  "prompts": {
    "positive": "masterpiece, best quality, 1girl ...",
    "negative": "worst quality, bad quality ..."
  }
}
```

`loras` は `config.json` の `lora_list` に定義したキー名を 0〜4 個指定します。

### Python から import

```python
from run_workflow import WorkflowRunner

runner = WorkflowRunner("config.json")
runner.execute(["my_lora"], {"positive": "...", "negative": "..."})
```

## 出力

実行後に `result.json` が生成されます。

```json
{
  "status": "success",
  "prompt_id": "abc123",
  "timestamp": "2026-04-25T12:00:00",
  "outputs": [
    {"filename": "ComfyUI_00001_.png", "subfolder": "", "type": "output"}
  ],
  "error": null
}
```

## テスト

```bash
python -m pytest test/ -v
```

## テンプレートについて

`templates/` に収録されているワークフローはサンプルです。

ComfyUI で作成した任意のワークフローに差し替えて使用できます（テンプレートのノード特定方法は [SPEC.md](SPEC.md) を参照）。

サンプルテンプレートを実際に動作させるには、ComfyUI に以下が必要です。

| 種別 | 名前 |
|---|---|
| カスタムノード | [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack) |
| モデル | WAI-illustrious-SDXL v16.0 |
| アップスケーラー | RealESRGAN x2 |

## ファイル構成

```
run_workflow/
  run_workflow.py         # メインスクリプト
  config.json             # 接続設定・LoRAマッピング
  requirements.txt
  templates/
    template_lora_0.json  # LoRA 0個用テンプレート
    template_lora_1.json
    template_lora_2.json
    template_lora_3.json
    template_lora_4.json
  test/
    test_run_workflow.py
```
