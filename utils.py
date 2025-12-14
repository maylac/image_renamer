import logging
import subprocess
import json

# EXIF情報のタグ名 (ExifToolのタグ名に合わせる)
EXIFTOOL_DATETIME_ORIGINAL_TAG = 'DateTimeOriginal'
EXIFTOOL_MODEL_TAG = 'Model'
EXIFTOOL_SOFTWARE_TAG = 'Software'

# サポートされている画像・動画ファイルの拡張子
SUPPORTED_IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.heic', '.heif', '.webp', '.raw', '.cr2', '.nef', '.arw', '.dng'
}
SUPPORTED_VIDEO_EXTENSIONS = {
    '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'
}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_VIDEO_EXTENSIONS

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
    except FileNotFoundError:
        logging.error(
            "ExifToolが見つかりません。インストールされているか確認してください。\n"
            "  - macOS: brew install exiftool\n"
            "  - Debian/Ubuntu: sudo apt-get install -y libimage-exiftool-perl"
        )
        return {}
    except subprocess.CalledProcessError as e:
        logging.error(f"ExifToolの実行に失敗しました ({file_path}): {e.stderr if e.stderr else str(e)}")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"ExifToolの出力をJSON形式でパースできませんでした ({file_path}): {e}")
        return {}
