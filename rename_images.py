import os
import argparse
from pathlib import Path
from datetime import datetime
from PIL import Image

# EXIF情報から撮影日時のタグID (DateTimeOriginal)
DATETIME_ORIGINAL_TAG = 36867

def rename_image_files(directory: str):
    """
    指定されたディレクトリ内の画像ファイルのファイル名を、
    EXIFの撮影日時に基づいてリネームする。
    例: IMG_1234.JPG -> 20230727_153000.jpg

    Args:
        directory (str): 対象の画像ファイルが含まれるディレクトリのパス。
    """
    target_dir = Path(directory)
    if not target_dir.is_dir():
        print(f"エラー: 指定されたパス '{directory}' はディレクトリではありません。")
        return

    print(f"ディレクトリ '{target_dir.resolve()}' の処理を開始します...")

    for original_path in target_dir.iterdir():
        # ファイルでない場合、または隠しファイルの場合はスキップ
        if not original_path.is_file() or original_path.name.startswith('.'):
            continue

        try:
            with Image.open(original_path) as img:
                # EXIFデータを取得
                exif_data = img._getexif()

                if not exif_data or DATETIME_ORIGINAL_TAG not in exif_data:
                    print(f"スキップ: '{original_path.name}' に撮影日時のEXIF情報がありません。")
                    continue

                date_str = exif_data[DATETIME_ORIGINAL_TAG]
                dt_original = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')

                new_name_base = dt_original.strftime('%Y%m%d_%H%M%S')
                suffix = original_path.suffix.lower()
                new_name = f"{new_name_base}{suffix}"
                new_path = target_dir / new_name

                counter = 1
                while new_path.exists():
                    if new_path.resolve() == original_path.resolve():
                        print(f"スキップ: '{original_path.name}' は既にリネーム済みです。")
                        break
                    new_name = f"{new_name_base}_{counter}{suffix}"
                    new_path = target_dir / new_name
                    counter += 1
                else:
                    original_path.rename(new_path)
                    print(f"リネーム: '{original_path.name}' -> '{new_path.name}'")

        except IOError:
            print(f"スキップ: '{original_path.name}' は画像ファイルとして認識できませんでした。")
        except Exception as e:
            print(f"エラー: '{original_path.name}' の処理中に予期せぬエラーが発生しました: {e}")

    print("処理が完了しました。")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="画像ファイルをEXIFの撮影日時に基づいてリネームするスクリプト。"
    )
    parser.add_argument(
        "directory",
        type=str,
        help="画像ファイルが格納されているディレクトリのパス。"
    )
    args = parser.parse_args()
    rename_image_files(args.directory)
