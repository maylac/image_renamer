import os
import argparse
import logging
import shutil
from pathlib import Path
from datetime import datetime

from utils import setup_logging, get_exif_data_with_exiftool

# EXIF情報のタグID (ExifToolのタグ名に合わせる)
EXIFTOOL_DATETIME_ORIGINAL_TAG = 'DateTimeOriginal'

def get_target_date(file_path):
    """ファイルの整理基準となる日付を取得する。EXIFを優先し、なければファイルの更新日時を使う。"""
    exif_data = get_exif_data_with_exiftool(file_path)
    date_str_exif = exif_data.get(EXIFTOOL_DATETIME_ORIGINAL_TAG)

    if date_str_exif:
        try:
            return datetime.strptime(date_str_exif, '%Y:%m:%d %H:%M:%S')
        except ValueError:
            logging.warning(f"不正な日付フォーマットのため、更新日時を使用: {file_path}")

    mtime = file_path.stat().st_mtime
    return datetime.fromtimestamp(mtime)

def organize_files(source_dir: str, dest_dir: str, dry_run: bool):
    """指定されたディレクトリのファイルを、日付に基づいて整理する。"""
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)

    if not source_path.is_dir() or not dest_path.is_dir():
        logging.error("ソースディレクトリまたは宛先ディレクトリが存在しないか、ディレクトリではありません。")
        return

    logging.info(f"処理を開始します。ソース: '{source_path}', 宛先: '{dest_path}'")

    for file_path in source_path.rglob('*'):
        if not file_path.is_file() or file_path.name.startswith('.'):
            continue

        try:
            target_date = get_target_date(file_path)
            year = target_date.strftime("%Y")
            month = target_date.strftime("%m")

            target_dir = dest_path / year / month
            target_file_path = target_dir / file_path.name

            if dry_run:
                logging.info(f"[DRY RUN] 移動: '{file_path}' -> '{target_file_path}'")
            else:
                logging.info(f"移動: '{file_path}' -> '{target_file_path}'")
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(target_file_path))

        except Exception as e:
            logging.error(f"エラー: '{file_path}' の処理中に予期せぬエラーが発生しました: {e}")

    logging.info("処理が完了しました。")

if __name__ == '__main__':
    default_dry_run = os.getenv('ORGANIZE_DRY_RUN', 'false').lower() in ('true', '1', 't')
    default_log_file = os.getenv('ORGANIZE_LOG_FILE')

    parser = argparse.ArgumentParser(description='日付情報に基づいてファイルを `YYYY/MM` 形式のディレクトリに整理します。')
    parser.add_argument('--source', required=True, help='処理対象のファイルが含まれるソースディレクトリ')
    parser.add_argument('--destination', required=True, help='ファイルの移動先となるルートディレクトリ')
    parser.add_argument('--log-file', default=default_log_file, help=f'ログをファイルに出力する場合のパス。デフォルト: {default_log_file}')
    parser.add_argument('--dry-run', action='store_true', default=default_dry_run, help=f'実際にはファイルの移動を行わず、実行結果をプレビューします。デフォルト: {default_dry_run}')

    args = parser.parse_args()
    setup_logging(args.log_file)
    organize_files(args.source, args.destination, args.dry_run)
