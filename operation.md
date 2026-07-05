# 運用仕様（Operation Specs）

このドキュメントは、Media Organizer & Renamer の実運用に関する仕様とベストプラクティスをまとめたものです。

## コマンド概要

- `rename`: EXIF 情報に基づき、`YYYYMMDD_####_DeviceName.ext` 形式に一括リネーム。
- `organize`: 撮影日（または更新日時）に基づき、`YYYY/MM/` ディレクトリ構成へ移動。

## サポートファイル形式

### 画像ファイル
`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff`, `.tif`, `.heic`, `.heif`, `.webp`, `.raw`, `.cr2`, `.nef`, `.arw`, `.dng`

### 動画ファイル
`.mp4`, `.mov`, `.avi`, `.mkv`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.3gp`

**注意:** 上記以外のファイル形式は自動的にスキップされます。

## リネーム仕様（rename）

- 日付情報: EXIF の `DateTimeOriginal` を使用（フォーマット: `%Y:%m:%d %H:%M:%S`）。
- デバイス名: 以下の優先順で採用し、空白は `_` に置換。
  - `Model`（存在すれば最優先）
  - `Software`（バージョン表記を除去。`\d+(\.\d+){1,2}` のみの値は `iOS` に正規化）
  - どちらも無い場合は `UnknownDevice`
- 連番付与: 同一日付・同一ディレクトリで `0001` から空き番号を探索して採番。
- スキップ条件: 既に `^\d{8}_\d{4}_.*` 形式のファイル名は既定ではスキップ。
- `--force`: スキップ条件を無視して再リネームを実施。
- `--recursive`: サブディレクトリも再帰的に処理。
- `--dry-run`: 実ファイル操作を行わず、実行結果のみログに出力。

### 環境変数（rename）

- `RENAME_DRY_RUN`: `true/1/t` でデフォルト dry-run 有効。
- `RENAME_RECURSIVE`: `true/1/t` で再帰処理をデフォルト有効化。
- `RENAME_FORCE`: `true/1/t` で既リネームファイルも再処理。
- `RENAME_LOG_FILE`: ログ出力先パス。

## 整理仕様（organize）

- 日付決定: EXIF `DateTimeOriginal` を優先。無い/不正な場合はファイル更新日時（mtime）。
- 生成先: `YYYY/MM/` 配下にオリジナルファイル名のまま移動。
- `--dry-run`: 実ファイル移動無しでログのみ出力。

### 環境変数（organize）

- `ORGANIZE_DRY_RUN`: `true/1/t` でデフォルト dry-run 有効。
- `ORGANIZE_LOG_FILE`: ログ出力先パス。

## ログ運用

- 全コマンドは標準出力に INFO レベルで進捗を出力。
- `--log-file` または環境変数でファイル出力を併用可能。
- 処理完了時に結果サマリーを表示: `成功 X件, スキップ Y件, エラー Z件`
- トラブルシューティングについては [README.md](./README.md#トラブルシューティング) を参照。

## Docker 実行例

```
# rename（再帰＋プレビュー）
docker run --rm \
  -v "/path/to/photos:/data" \
  ghcr.io/maylac/image-renamer:latest \
  rename /data --recursive --dry-run

# organize（プレビュー）
docker run --rm \
  -v "/source_dir:/source" \
  -v "/dest_dir:/destination" \
  ghcr.io/maylac/image-renamer:latest \
  organize --source /source --destination /destination --dry-run
```

## 注意点 / 既知事項

- `rename` はデフォルトで既リネーム済み形式をスキップします。全面再生成は `--force` を使用。
- `Software` からのデバイス名抽出時は、バージョン表記（例: `v1.2`、`15.6.1`）を除去します。
- `organize` はファイル名は変更せず、移動のみ行います。
- サポート対象外のファイル形式は自動的にスキップされ、処理結果サマリーのスキップ件数に含まれます。
- エラーが発生した場合の詳細な対処方法は [README.md](./README.md#トラブルシューティング) を参照してください。
