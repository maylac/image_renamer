# Media Organizer & Renamer

このプロジェクトは、画像や動画ファイルをEXIF情報に基づいて整理・リネームするための多機能ツールです。
Dockerコンテナとして実行されることを前提としています。

## 主な機能

- **リネーム (`rename`)**: ファイル名を `撮影日_連番_デバイス名.拡張子` の形式に一括で変更します。
- **整理 (`organize`)**: ファイルを撮影年月日に基づいて `YYYY/MM/` のディレクトリ構造に整理・移動します。

## サポートファイル形式

### 画像ファイル
`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.heic`, `.heif`, `.webp`, `.raw`, `.cr2`, `.nef`, `.arw`, `.dng`

### 動画ファイル
`.mp4`, `.mov`, `.avi`, `.mkv`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.3gp`

> **Note**: 上記以外のファイル形式は自動的にスキップされます。

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

---

## トラブルシューティング

### ExifToolが見つからない

**エラーメッセージ:**
```
ExifToolが見つかりません。インストールされているか確認してください。
```

**解決方法:**
- **macOS**: `brew install exiftool`
- **Debian/Ubuntu**: `sudo apt-get install -y libimage-exiftool-perl`
- **Docker**: 公式イメージには既にExifToolが含まれています

---

### 権限エラー

**エラーメッセージ:**
```
エラー: 'filename.jpg' のリネームに必要な権限がありません。
エラー: 'filename.jpg' の移動に必要な権限がありません。
```

**解決方法:**
1. ファイルとディレクトリの権限を確認: `ls -la /path/to/files`
2. 必要に応じて権限を変更: `chmod -R u+rw /path/to/files`
3. Dockerの場合、ボリュームマウント時の権限を確認

---

### ファイルが処理されない

**原因1: サポート対象外のファイル形式**

ログに以下のメッセージが表示されます（`--verbose`が必要な場合があります）:
```
スキップ: 'document.pdf' はサポート対象外のファイル形式です。
```

**解決方法:** サポート対象のファイル形式（上記参照）のみが処理されます。

**原因2: EXIF情報がない**

```
スキップ: 'image.jpg' に撮影日時のEXIF情報がありません。
```

**解決方法:**
- `organize`コマンドは自動的にファイルの更新日時を使用します
- `rename`コマンドは撮影日時が必須のため、このファイルはスキップされます

**原因3: 既にリネーム済み**

```
スキップ: '20231225_0001_iPhone.jpg' はリネーム済みです。
```

**解決方法:** `--force`オプションを使用して再リネーム

---

### 日付フォーマットエラー

**エラーメッセージ:**
```
エラー: 'image.jpg' の日時フォーマットが不正です
```

**原因:** EXIF情報の日時フォーマットが標準形式 (`YYYY:MM:DD HH:MM:SS`) と異なる

**解決方法:** ExifToolで日時情報を確認・修正:
```bash
exiftool -DateTimeOriginal image.jpg
```

---

### Docker関連のエラー

**エラー: イメージが見つからない**
```bash
# 最新イメージを再取得
sudo docker pull ghcr.io/maylac/image_renamer:latest
```

**エラー: ボリュームマウントできない**
- パスが絶対パスになっているか確認
- ディレクトリが存在するか確認
- Dockerのファイル共有設定を確認（Docker Desktop使用時）

---

## 詳細仕様

より詳細な運用仕様や環境変数については、[operation.md](./operation.md) を参照してください。

```
