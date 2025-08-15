import os
import re
import subprocess
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

# EXIF情報のタグID (ExifToolのタグ名に合わせる)
EXIFTOOL_DATETIME_ORIGINAL_TAG = 'DateTimeOriginal'
EXIFTOOL_SOFTWARE_TAG = 'Software'

# リネーム済みファイル名の形式
RENAMED_FILE_PATTERN = re.compile(r"^\d{8}_\d{4}_.*")

def setup_logging(log_file=None):
    """ロギングを設定する。コンソールと、指定されていればファイルにも出力する。"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logging.getLogger().addHandler(file_handler)

def get_exif_data_with_exiftool(file_path):
    """ExifToolを使ってEXIFデータをJSON形式で取得する"""
    try:
        command = ['exiftool', '-json', '-s', '-d', '%Y:%m:%d %H:%M:%S', str(file_path)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        exif_json = result.stdout
        data = json.loads(exif_json)
        if data:
            return data[0]
        return {}
    except subprocess.CalledProcessError as e:
        logging.error(f"ExifToolの実行エラー: {e}")
        logging.error(f"Stderr: {e.stderr}")
        return {}
    except json.JSONDecodeError:
        logging.error(f"ExifToolの出力がJSON形式ではありません: {exif_json}")
        return {}
    except FileNotFoundError:
        logging.error("ExifToolが見つかりません。インストールされているか確認してください。")
        return {}

def get_next_filename(base_path: Path, date_str: str, app_name: str, suffix: str) -> Path:
    """指定された日付とアプリ名で、連番のファイル名を生成する"""
    counter = 1
    while True:
        new_name = f"{date_str}_{counter:04d}_{app_name}{suffix}"
        new_path = base_path / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def rename_image_files(directory: str, dry_run: bool, recursive: bool):
    """
    指定されたディレクトリ内の画像ファイルのファイル名を、
    EXIF情報に基づいてリネームする。
    """
    target_dir = Path(directory)
    if not target_dir.is_dir():
        logging.error(f"指定されたパス '{directory}' はディレクトリではありません。")
        return

    logging.info(f"ディレクトリ '{target_dir.resolve()}' の処理を開始します...")

    if recursive:
        logging.info("再帰モード: サブディレクトリを検索します...")
        files_to_process = target_dir.rglob('*')
    else:
        files_to_process = target_dir.iterdir()

    for original_path in sorted(list(files_to_process)):
        if not original_path.is_file() or original_path.name.startswith('.'):
            continue

        if RENAMED_FILE_PATTERN.match(original_path.name):
            logging.info(f"スキップ: '{original_path.name}' はリネーム済みです。")
            continue

        try:
            parent_dir = original_path.parent
            exif_data = get_exif_data_with_exiftool(original_path)
            date_str_exif = exif_data.get(EXIFTOOL_DATETIME_ORIGINAL_TAG)

            if not date_str_exif:
                logging.warning(f"スキップ: '{original_path.name}' に撮影日時のEXIF情報がありません。")
                continue

            dt_original = datetime.strptime(date_str_exif, '%Y:%m:%d %H:%M:%S')
            date_prefix = dt_original.strftime('%Y%m%d')

            app_name = exif_data.get(EXIFTOOL_SOFTWARE_TAG, 'UnknownApp').replace(' ', '_')
            if re.match(r"^\d{1,2}(\.\d{1,2}){1,2}$", app_name):
                app_name = "iOS"

            suffix = original_path.suffix.lower()
            new_path = get_next_filename(parent_dir, date_prefix, app_name, suffix)

            if dry_run:
                logging.info(f"[DRY RUN] リネーム: '{original_path.name}' -> '{new_path.name}'")
            else:
                original_path.rename(new_path)
                logging.info(f"リネーム: '{original_path.name}' -> '{new_path.name}'")

        except Exception as e:
            logging.error(f"エラー: '{original_path.name}' の処理中に予期せぬエラーが発生しました: {e}")

    logging.info("処理が完了しました。")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EXIF情報に基づいて画像ファイルをリネームします。')
    parser.add_argument('directory', help='画像ファイルが格納されているディレクトリのパス')
    parser.add_argument('--dry-run', action='store_true', help='実際にはファイルをリネームせず、実行結果のプレビューを表示します。')
    parser.add_argument('-r', '--recursive', action='store_true', help='サブディレクトリ内のファイルも再帰的に処理します。')
    parser.add_argument('--log-file', help='ログをファイルに出力する場合のパス')
    args = parser.parse_args()

    setup_logging(args.log_file)

    rename_image_files(args.directory, args.dry_run, args.recursive)