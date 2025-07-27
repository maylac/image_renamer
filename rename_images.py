import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

# リネーム済みファイル名の形式
RENAMED_FILE_PATTERN = re.compile(r"^\d{8}_\d{4}_.*")

def get_exif_data(file_path: Path):
    """ExifToolを使ってファイルから撮影日時とソフトウェア名を取得する"""
    try:
        # ExifToolで必要なタグのみをJSON形式で取得
        cmd = [
            "exiftool",
            "-j",
            "-DateTimeOriginal",
            "-Software",
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # ExifToolは常にリストを返すので、最初の要素を取得
        data = result.stdout.strip()
        if not data or not data.startswith('['):
            return None
        return eval(data)[0]
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError, SyntaxError):
        return None

def get_next_filename(base_path: Path, date_str: str, app_name: str, suffix: str) -> Path:
    """指定された日付とアプリ名で、連番のファイル名を生成する"""
    counter = 1
    while True:
        # アプリ名からバージョン情報を削除
        app_name_base = app_name.split('_')[0]
        new_name = f"{date_str}_{counter:04d}_{app_name_base}{suffix}"
        new_path = base_path / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def rename_image_files(directory: str):
    """
    指定されたディレクトリ内の画像ファイル（ARW, DNG, JPGなど）のファイル名を、
    EXIF情報に基づいてリネームする。
    """
    target_dir = Path(directory)
    if not target_dir.is_dir():
        print(f"エラー: 指定されたパス '{directory}' はディレクトリではありません。")
        return

    print(f"ディレクトリ '{target_dir.resolve()}' の処理を開始します...")

    all_files = sorted(target_dir.iterdir())

    for original_path in all_files:
        if not original_path.is_file() or original_path.name.startswith('.'):
            continue

        # 既にリネーム済みのファイルはスキップ
        if RENAMED_FILE_PATTERN.match(original_path.name):
            print(f"スキップ: '{original_path.name}' はリネーム済み、またはその形式です。")
            continue

        exif_data = get_exif_data(original_path)

        if not exif_data or 'DateTimeOriginal' not in exif_data:
            print(f"スキップ: '{original_path.name}' に撮影日時のEXIF情報がありません。")
            continue

        try:
            date_str_exif = exif_data['DateTimeOriginal']
            # 時刻の区切り文字が異なる場合に対応
            dt_original = datetime.strptime(date_str_exif.split(' ')[0], '%Y:%m:%d')
            date_prefix = dt_original.strftime('%Y%m%d')

            app_name = exif_data.get('Software', 'UnknownApp').replace(' ', '_')
            # iOSバージョンと思われるものは「iOS」に統一
            if re.match(r"^\d{1,2}(\.\d{1,2}){1,2}$", app_name):
                app_name = "iOS"
            suffix = original_path.suffix.lower()

            # 新しいファイル名を決定
            new_path = get_next_filename(target_dir, date_prefix, app_name, suffix)

            # 同じベース名を持つ関連ファイル（例: .ARWと.JPG）を一緒にリネーム
            base_name = original_path.stem
            related_files = list(target_dir.glob(f"{base_name}.*"))

            for related_file in related_files:
                if RENAMED_FILE_PATTERN.match(related_file.name):
                    continue # 既にリネーム済みの関連ファイルはスキップ
                
                related_suffix = related_file.suffix.lower()
                app_name_base = app_name.split('_')[0]
                final_new_name = f"{date_prefix}_{new_path.stem.split('_')[1]}_{app_name_base}{related_suffix}"
                final_new_path = target_dir / final_new_name

                if not final_new_path.exists():
                    related_file.rename(final_new_path)
                    print(f"リネーム: '{related_file.name}' -> '{final_new_path.name}'")
                else:
                    # 既にリネームしようとしているファイルが存在する場合（例えばループで先に見つかった場合）
                    if related_file.resolve() != final_new_path.resolve():
                         print(f"スキップ（重複）: '{final_new_path.name}'は既に存在します。")

        except Exception as e:
            print(f"エラー: '{original_path.name}' の処理中に予期せぬエラーが発生しました: {e}")

    print("処理が完了しました。")

if __name__ == '__main__':
    # スクリプト実行後に対象ディレクトリのパスをユーザーに尋ねる
    directory_path = input("画像ファイルが格納されているディレクトリのパスを入力してください: ")
    rename_image_files(directory_path)