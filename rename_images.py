import os
import re
import argparse
import logging
from pathlib import Path
from datetime import datetime

from utils import setup_logging, get_exif_data_with_exiftool

# EXIF情報のタグID (ExifToolのタグ名に合わせる)
EXIFTOOL_DATETIME_ORIGINAL_TAG = 'DateTimeOriginal'
EXIFTOOL_MODEL_TAG = 'Model'
EXIFTOOL_SOFTWARE_TAG = 'Software'

# リネーム済みファイル名の形式
RENAMED_FILE_PATTERN = re.compile(r"^\d{8}_\d{4}_.*")

def get_next_filename(base_path: Path, date_str: str, device_name: str, suffix: str) -> Path:
    """指定された日付とデバイス名で、連番のファイル名を生成する"""
    counter = 1
    while True:
        new_name = f"{date_str}_{counter:04d}_{device_name}{suffix}"
        new_path = base_path / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def get_device_name(exif_data):
    """EXIFデータからデバイス名を取得する。Modelを優先し、なければSoftwareを整形して使用する。"""
    model = exif_data.get(EXIFTOOL_MODEL_TAG, '')
    if model:
        return model.replace(' ', '_')

    software = exif_data.get(EXIFTOOL_SOFTWARE_TAG, '')
    if software:
        software_cleaned = re.sub(r'_?v\d+\.\d+', '', software, flags=re.IGNORECASE).strip()
        software_cleaned = re.sub(r'^\d{1,2}(\.\d{1,2}){1,2}$', 'iOS', software_cleaned)
        if software_cleaned:
            return software_cleaned.replace(' ', '_')

    return 'UnknownDevice'

def rename_image_files(directory: str, dry_run: bool = False, recursive: bool = False, force: bool = False):
    """
    指定されたディレクトリ内の画像ファイルのファイル名を、
    EXIF情報に基づいてリネームする。
    """
    target_dir = Path(directory)
    if not target_dir.is_dir():
        logging.error(f"指定されたパス '{directory}' はディレクトリではありません。")
        return

    logging.info(f"ディレクトリ '{target_dir.resolve()}' の処理を開始します...")
    if force:
        logging.warning("強制実行モード: リネーム済みのファイルも再処理します。")

    if recursive:
        logging.info("再帰モード: サブディレクトリを検索します...")
        files_to_process = target_dir.rglob('*')
    else:
        files_to_process = target_dir.iterdir()

    for original_path in sorted(list(files_to_process)):
        if not original_path.is_file() or original_path.name.startswith('.'):
            continue

        # --forceが指定されていない場合のみ、リネーム済みファイルをスキップ
        if not force and RENAMED_FILE_PATTERN.match(original_path.name):
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

            device_name = get_device_name(exif_data)

            suffix = original_path.suffix.lower()
            new_path = get_next_filename(parent_dir, date_prefix, device_name, suffix)

            if dry_run:
                logging.info(f"[DRY RUN] リネーム: '{original_path.name}' -> '{new_path.name}'")
            else:
                original_path.rename(new_path)
                logging.info(f"リネーム: '{original_path.name}' -> '{new_path.name}'")

        except Exception as e:
            logging.error(f"エラー: '{original_path.name}' の処理中に予期せぬエラーが発生しました: {e}")

    logging.info("処理が完了しました。")

if __name__ == '__main__':
    default_dry_run = os.getenv('RENAME_DRY_RUN', 'false').lower() in ('true', '1', 't')
    default_recursive = os.getenv('RENAME_RECURSIVE', 'false').lower() in ('true', '1', 't')
    default_force = os.getenv('RENAME_FORCE', 'false').lower() in ('true', '1', 't')
    default_log_file = os.getenv('RENAME_LOG_FILE')

    parser = argparse.ArgumentParser(description='EXIF情報に基づいて画像ファイルをリネームします。\n環境変数でも設定が可能です: RENAME_DRY_RUN, RENAME_RECURSIVE, RENAME_FORCE, RENAME_LOG_FILE')
    parser.add_argument('directory', help='画像ファイルが格納されているディレクトリのパス')
    parser.add_argument('--dry-run', action='store_true', default=default_dry_run, help=f'プレビューのみ表示します。デフォルト: {default_dry_run}')
    parser.add_argument('-r', '--recursive', action='store_true', default=default_recursive, help=f'サブディレクトリも処理します。デフォルト: {default_recursive}')
    parser.add_argument('--force', action='store_true', default=default_force, help=f'リネーム済みのファイルも再処理します。デフォルト: {default_force}')
    parser.add_argument('--log-file', default=default_log_file, help=f'ログをファイルに出力します。デフォルト: {default_log_file}')
    args = parser.parse_args()

    setup_logging(args.log_file)
    # CLI からの実行時エントリポイント
    rename_image_files(
        directory=args.directory,
        dry_run=args.dry_run,
        recursive=args.recursive,
        force=args.force,
    )

    rename_image_files(args.directory, args.dry_run, args.recursive, args.force)
