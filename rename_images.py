import os
import re
from pathlib import Path
from datetime import datetime
from PIL import Image

# EXIF情報のタグID
DATETIME_ORIGINAL_TAG = 36867  # 撮影日時
SOFTWARE_TAG = 305             # ソフトウェア

# リネーム済みファイル名の形式
RENAMED_FILE_PATTERN = re.compile(r"^\d{8}_\d{4}_.*")

def get_next_filename(base_path: Path, date_str: str, app_name: str, suffix: str) -> Path:
    """指定された日付とアプリ名で、連番のファイル名を生成する"""
    counter = 1
    while True:
        new_name = f"{date_str}_{counter:04d}_{app_name}{suffix}"
        new_path = base_path / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def rename_image_files(directory: str):
    """
    指定されたディレクトリ内の画像ファイルのファイル名を、
    EXIF情報に基づいてリネームする。
    フォーマット: YYYYMMDD_(連番4桁)_(撮影アプリケーション).(拡張子)
    """
    target_dir = Path(directory)
    if not target_dir.is_dir():
        print(f"エラー: 指定されたパス '{directory}' はディレクトリではありません。")
        return

    print(f"ディレクトリ '{target_dir.resolve()}' の処理を開始します...")

    for original_path in sorted(target_dir.iterdir()):
        if not original_path.is_file() or original_path.name.startswith('.'):
            continue

        # 既にリネーム済みのファイルはスキップ
        if RENAMED_FILE_PATTERN.match(original_path.name):
            print(f"スキップ: '{original_path.name}' はリネーム済みです。")
            continue

        try:
            with Image.open(original_path) as img:
                exif_data = img._getexif()

                if not exif_data or DATETIME_ORIGINAL_TAG not in exif_data:
                    print(f"スキップ: '{original_path.name}' に撮影日時のEXIF情報がありません。")
                    continue

                date_str_exif = exif_data[DATETIME_ORIGINAL_TAG]
                dt_original = datetime.strptime(date_str_exif, '%Y:%m:%d %H:%M:%S')
                date_prefix = dt_original.strftime('%Y%m%d')

                app_name = exif_data.get(SOFTWARE_TAG, 'UnknownApp').replace(' ', '_')
                suffix = original_path.suffix.lower()

                new_path = get_next_filename(target_dir, date_prefix, app_name, suffix)

                if original_path.resolve() != new_path.resolve():
                    original_path.rename(new_path)
                    print(f"リネーム: '{original_path.name}' -> '{new_path.name}'")
                else:
                    print(f"スキップ: '{original_path.name}' は既に適切な名前です。")

        except IOError:
            print(f"スキップ: '{original_path.name}' は画像ファイルとして認識できませんでした。")
        except Exception as e:
            print(f"エラー: '{original_path.name}' の処理中に予期せぬエラーが発生しました: {e}")

    print("処理が完了しました。")

if __name__ == '__main__':
    directory_path = input("画像ファイルが格納されているディレクトリのパスを入力してください: ")
    rename_image_files(directory_path)
