# Media Organizer & Renamer

このプロジェクトは、画像や動画ファイルをEXIF情報に基づいて整理・リネームするための多機能ツールです。
Dockerコンテナとして実行されることを前提としています。

## 主な機能

- **リネーム (`rename`)**: ファイル名を `撮影日_連番_デバイス名.拡張子` の形式に一括で変更します。
- **整理 (`organize`)**: ファイルを撮影年月日に基づいて `YYYY/MM/` のディレクトリ構造に整理・移動します。

## 必要なもの

- Docker
- NASまたは画像が保存されているサーバー

## 使い方

このツールはDockerイメージとして配布されます。`main`ブランチにマージされるたびに、自動的にGitHub Container Registry (GHCR)に新しいイメージが公開されます。

### 1. NASで最新イメージを取得

NASにSSHでログインし、以下のコマンドで最新のDockerイメージを取得（プル）します。

```bash
sudo docker pull ghcr.io/maylac/image_renamer:latest
```

### 2. コマンドの実行

目的に応じて `rename` または `organize` コマンドを実行します。

--- 

### コマンド詳細

#### A) ファイルのリネーム (`rename`)

指定したディレクトリ内のファイル名を変更します。

**実行例:**
```bash
# /path/to/photos 内のファイルをリネーム（プレビュー実行）
sudo docker run --rm \
  -v "/path/to/photos:/data" \
  ghcr.io/maylac/image_renamer:latest \
  rename /data --recursive --dry-run
```

**オプション:**
- `directory`: (必須) 処理対象のディレクトリパス（コンテナ内のパス）。
- `--recursive`, `-r`: サブディレクトリも再帰的に処理します。
- `--force`: 一度リネームしたファイルも、再度リネームの対象とします。
- `--dry-run`: 実際の処理は行わず、実行結果のプレビューのみ表示します。
- `--log-file <path>`: ログを指定したファイルに出力します。

--- 

#### B) ファイルの整理 (`organize`)

ソースディレクトリのファイルを、宛先ディレクトリに `YYYY/MM/` のフォルダを作成して移動します。

**実行例:**
```bash
# /source_dir のファイルを /dest_dir に整理（プレビュー実行）
sudo docker run --rm \
  -v "/source_dir:/source" \
  -v "/dest_dir:/destination" \
  ghcr.io/maylac/image_renamer:latest \
  organize --source /source --destination /destination --dry-run
```

**オプション:**
- `--source`: (必須) 整理したいファイルがあるソースディレクトリ。
- `--destination`: (必須) 整理後のファイルの移動先ディレクトリ。
- `--dry-run`: 実際の処理は行わず、実行結果のプレビューのみ表示します。
- `--log-file <path>`: ログを指定したファイルに出力します。

---

## ローカル実行（開発向け）

Docker を使わずにローカルで試す場合の手順です。

1. 依存関係のインストール
   - Python 3.9+ を用意
   - ExifTool のインストール（macOS: `brew install exiftool`、Debian/Ubuntu: `sudo apt-get install -y libimage-exiftool-perl`）
   - ライブラリ: `pip install -r requirements.txt`

2. 実行例
   - リネーム（プレビュー）: `python rename_images.py /path/to/photos --recursive --dry-run`
   - 整理（プレビュー）: `python organize_files.py --source /source_dir --destination /dest_dir --dry-run`

3. テスト実行
   - `pytest`

補足: 直接 `entrypoint.sh` を実行した場合は `rename` または `organize` を最初の引数に指定してください。
```
