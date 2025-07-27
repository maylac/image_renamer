import os
<<<<<<< HEAD
<<<<<<< HEAD
=======
import re
import subprocess
import json # Added for parsing ExifTool JSON output
>>>>>>> 90f7736 (feat: Integrate ExifTool for robust EXIF reading and ARW file handling)
from pathlib import Path
from datetime import datetime
from PIL import Image # Still needed for opening common image types, but not for EXIF

<<<<<<< HEAD
# EXIF情報から撮影日時のタグID (DateTimeOriginal)
DATETIME_ORIGINAL_TAG = 36867
=======
import re
from pathlib import Path
from datetime import datetime
from PIL import Image

# EXIF情報のタグID
DATETIME_ORIGINAL_TAG = 36867  # 撮影日時
DATETIME_DIGITIZED_TAG = 36868 # デジタル化日時
DATETIME_TAG = 306             # ファイル変更日時
SOFTWARE_TAG = 305             # ソフトウェア
=======
# EXIF情報のタグID (ExifToolのタグ名に合わせる)
EXIFTOOL_DATETIME_ORIGINAL_TAG = 'DateTimeOriginal'
EXIFTOOL_SOFTWARE_TAG = 'Software'
>>>>>>> 90f7736 (feat: Integrate ExifTool for robust EXIF reading and ARW file handling)

# リネーム済みファイル名の形式
RENAMED_FILE_PATTERN = re.compile(r"^\d{8}_\d{4}_.*")

<<<<<<< HEAD
=======
def get_exif_data_with_exiftool(file_path):
    """ExifToolを使ってEXIFデータをJSON形式で取得する"""
    try:
        # ExifToolコマンドを実行し、JSON形式で出力
        # -json: JSON形式で出力
        # -s: タグ名を短縮 (e.g., DateTimeOriginal instead of EXIF:DateTimeOriginal)
        # -d "%Y:%m:%d %H:%M:%S": 日付フォーマットを指定
        command = ['exiftool', '-json', '-s', '-d', '%Y:%m:%d %H:%M:%S', str(file_path)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        exif_json = result.stdout
        data = json.loads(exif_json)
        if data:
            return data[0] # 最初のファイルのデータ
        return {}
    except subprocess.CalledProcessError as e:
        print(f"ExifToolの実行エラー: {e}")
        print(f"Stderr: {e.stderr}")
        return {}
    except json.JSONDecodeError:
        print(f"ExifToolの出力がJSON形式ではありません: {exif_json}")
        return {}
    except FileNotFoundError:
        print("エラー: ExifToolが見つかりません。インストールされているか確認してください。")
        return {}

>>>>>>> 90f7736 (feat: Integrate ExifTool for robust EXIF reading and ARW file handling)
def get_next_filename(base_path: Path, date_str: str, app_name: str, suffix: str) -> Path:
    """指定された日付とアプリ名で、連番のファイル名を生成する"""
    counter = 1
    while True:
        new_name = f"{date_str}_{counter:04d}_{app_name}{suffix}"
        new_path = base_path / new_name
        if not new_path.exists():
            return new_path
        counter += 1
<<<<<<< HEAD
>>>>>>> af51e85 (fix: Improve Pillow EXIF reading and add datetime fallback)

def find_datetime_from_exif(exif_data):
    """EXIFデータから日付時刻情報を探す"""
    if not exif_data:
        return None
    # 優先順位: DateTimeOriginal -> DateTimeDigitized -> DateTime
    for tag in [DATETIME_ORIGINAL_TAG, DATETIME_DIGITIZED_TAG, DATETIME_TAG]:
        if tag in exif_data:
            return exif_data[tag]
    return None
=======
>>>>>>> 90f7736 (feat: Integrate ExifTool for robust EXIF reading and ARW file handling)

def rename_image_files(directory: str):
    """
    指定されたディレクトリ内の画像ファイルのファイル名を、
<<<<<<< HEAD
<<<<<<< HEAD
    EXIFの撮影日時に基づいてリネームする。
    例: IMG_1234.JPG -> 20230727_153000.jpg

    Args:
        directory (str): 対象の画像ファイルが含まれるディレクトリのパス。
=======
    EXIF情報に基づいてリネームする。
    フォーマット: YYYYMMDD_(連番4桁)_(撮影アプリケーション).(拡張子)
>>>>>>> af51e85 (fix: Improve Pillow EXIF reading and add datetime fallback)
=======
    EXIF情報に基づいてリネームする。
    フォーマット: YYYYMMDD_(連番4桁)_(撮影アプリケーション).(拡張子)
>>>>>>> 90f7736 (feat: Integrate ExifTool for robust EXIF reading and ARW file handling)
    """
    target_dir = Path(directory)
    if not target_dir.is_dir():
        print(f"エラー: 指定されたパス '{directory}' はディレクトリではありません。")
        return

    print(f"ディレクトリ '{target_dir.resolve()}' の処理を開始します...")

<<<<<<< HEAD
<<<<<<< HEAD
    for original_path in target_dir.iterdir():
        # ファイルでない場合、または隠しファイルの場合はスキップ
=======
    for original_path in sorted(target_dir.iterdir()):
>>>>>>> 90f7736 (feat: Integrate ExifTool for robust EXIF reading and ARW file handling)
        if not original_path.is_file() or original_path.name.startswith('.'):
            continue

        # 既にリネーム済みのファイルはスキップ
        if RENAMED_FILE_PATTERN.match(original_path.name):
            print(f"スキップ: '{original_path.name}' はリネーム済みです。")
            continue

        try:
            # ExifToolでEXIFデータを取得
            exif_data = get_exif_data_with_exiftool(original_path)

            date_str_exif = exif_data.get(EXIFTOOL_DATETIME_ORIGINAL_TAG)
            if not date_str_exif:
                # Fallback to file modification time if EXIF datetime is not found
                # For now, just skip if no EXIF datetime
                print(f"スキップ: '{original_path.name}' に撮影日時のEXIF情報がありません。")
                continue

            dt_original = datetime.strptime(date_str_exif, '%Y:%m:%d %H:%M:%S')
            date_prefix = dt_original.strftime('%Y%m%d')

            app_name = exif_data.get(EXIFTOOL_SOFTWARE_TAG, 'UnknownApp').replace(' ', '_')
            suffix = original_path.suffix.lower()

<<<<<<< HEAD
                import os
import re
import subprocess
import json # Added for parsing ExifTool JSON output
from pathlib import Path
from datetime import datetime
from PIL import Image # Still needed for opening common image types, but not for EXIF

# EXIF情報のタグID (ExifToolのタグ名に合わせる)
EXIFTOOL_DATETIME_ORIGINAL_TAG = 'DateTimeOriginal'
EXIFTOOL_SOFTWARE_TAG = 'Software'

# リネーム済みファイル名の形式
RENAMED_FILE_PATTERN = re.compile(r"^\d{8}_\d{4}_.*")

def get_exif_data_with_exiftool(file_path):
    """ExifToolを使ってEXIFデータをJSON形式で取得する"""
    try:
        # ExifToolコマンドを実行し、JSON形式で出力
        # -json: JSON形式で出力
        # -s: タグ名を短縮 (e.g., DateTimeOriginal instead of EXIF:DateTimeOriginal)
        # -d "%Y:%m:%d %H:%M:%S": 日付フォーマットを指定
        command = ['exiftool', '-json', '-s', '-d', '%Y:%m:%d %H:%M:%S', str(file_path)]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        exif_json = result.stdout
        data = json.loads(exif_json)
        if data:
            return data[0] # 最初のファイルのデータ
        return {}
    except subprocess.CalledProcessError as e:
        print(f"ExifToolの実行エラー: {e}")
        print(f"Stderr: {e.stderr}")
        return {}
    except json.JSONDecodeError:
        print(f"ExifToolの出力がJSON形式ではありません: {exif_json}")
        return {}
    except FileNotFoundError:
        print("エラー: ExifToolが見つかりません。インストールされているか確認してください。")
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
            # ExifToolでEXIFデータを取得
            exif_data = get_exif_data_with_exiftool(original_path)

            date_str_exif = exif_data.get(EXIFTOOL_DATETIME_ORIGINAL_TAG)
            if not date_str_exif:
                # Fallback to file modification time if EXIF datetime is not found
                # For now, just skip if no EXIF datetime
                print(f"スキップ: '{original_path.name}' に撮影日時のEXIF情報がありません。")
                continue

            dt_original = datetime.strptime(date_str_exif, '%Y:%m:%d %H:%M:%S')
            date_prefix = dt_original.strftime('%Y%m%d')

            app_name = exif_data.get(EXIFTOOL_SOFTWARE_TAG, 'UnknownApp').replace(' ', '_')
            suffix = original_path.suffix.lower()

            new_path = get_next_filename(target_dir, date_prefix, app_name, suffix)

            original_path.rename(new_path)
            print(f"リネーム: '{original_path.name}' -> '{new_path.name}'")

        except Exception as e:
            print(f"エラー: '{original_path.name}' の処理中に予期せぬエラーが発生しました: {e}")

    print("処理が完了しました。")

if __name__ == '__main__':
    directory_path = input("画像ファイルが格納されているディレクトリのパスを入力してください: ")
    rename_image_files(directory_path)
                import os
import re
from pathlib import Path
from datetime import datetime
from PIL import Image

# EXIF情報のタグID
DATETIME_ORIGINAL_TAG = 36867  # 撮影日時
DATETIME_DIGITIZED_TAG = 36868 # デジタル化日時
DATETIME_TAG = 306             # ファイル変更日時
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

def find_datetime_from_exif(exif_data):
    """EXIFデータから日付時刻情報を探す"""
    if not exif_data:
        return None
    # 優先順位: DateTimeOriginal -> DateTimeDigitized -> DateTime
    for tag in [DATETIME_ORIGINAL_TAG, DATETIME_DIGITIZED_TAG, DATETIME_TAG]:
        if tag in exif_data:
            return exif_data[tag]
    return None

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
                exif_data = img.getexif()
                date_str_exif = find_datetime_from_exif(exif_data)

                if not date_str_exif:
                    print(f"スキップ: '{original_path.name}' に撮影日時のEXIF情報がありません。")
                    continue

                dt_original = datetime.strptime(date_str_exif, '%Y:%m:%d %H:%M:%S')
                date_prefix = dt_original.strftime('%Y%m%d')

                app_name = exif_data.get(SOFTWARE_TAG, 'UnknownApp').replace(' ', '_')
                suffix = original_path.suffix.lower()

                new_path = get_next_filename(target_dir, date_prefix, app_name, suffix)

                original_path.rename(new_path)
                print(f"リネーム: '{original_path.name}' -> '{new_path.name}'")

        except IOError:
            print(f"スキップ: '{original_path.name}' は画像ファイルとして認識できませんでした。")
        except Exception as e:
            print(f"エラー: '{original_path.name}' の処理中に予期せぬエラーが発生しました: {e}")

    print("処理が完了しました。")

if __name__ == '__main__':
    directory_path = input("画像ファイルが格納されているディレクトリのパスを入力してください: ")
    rename_image_files(directory_path)
=======
    for original_path in sorted(target_dir.iterdir()):
        if not original_path.is_file() or original_path.name.startswith('.'):
            continue

        # 既にリネーム済みのファイルはスキップ
        if RENAMED_FILE_PATTERN.match(original_path.name):
            print(f"スキップ: '{original_path.name}' はリネーム済みです。")
            continue

        try:
            with Image.open(original_path) as img:
                exif_data = img.getexif()
                date_str_exif = find_datetime_from_exif(exif_data)

                if not date_str_exif:
                    print(f"スキップ: '{original_path.name}' に撮影日時のEXIF情報がありません。")
                    continue

                dt_original = datetime.strptime(date_str_exif, '%Y:%m:%d %H:%M:%S')
                date_prefix = dt_original.strftime('%Y%m%d')

                app_name = exif_data.get(SOFTWARE_TAG, 'UnknownApp').replace(' ', '_')
                suffix = original_path.suffix.lower()

                new_path = get_next_filename(target_dir, date_prefix, app_name, suffix)

                original_path.rename(new_path)
                print(f"リネーム: '{original_path.name}' -> '{new_path.name}'")
>>>>>>> af51e85 (fix: Improve Pillow EXIF reading and add datetime fallback)
=======
            new_path = get_next_filename(target_dir, date_prefix, app_name, suffix)

            original_path.rename(new_path)
            print(f"リネーム: '{original_path.name}' -> '{new_path.name}'")
>>>>>>> 90f7736 (feat: Integrate ExifTool for robust EXIF reading and ARW file handling)

        except Exception as e:
            print(f"エラー: '{original_path.name}' の処理中に予期せぬエラーが発生しました: {e}")

    print("処理が完了しました。")

if __name__ == '__main__':
    directory_path = input("画像ファイルが格納されているディレクトリのパスを入力してください: ")
    rename_image_files(directory_path)
