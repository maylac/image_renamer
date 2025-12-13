import logging
import subprocess
import json

# EXIF情報のタグ名 (ExifToolのタグ名に合わせる)
EXIFTOOL_DATETIME_ORIGINAL_TAG = 'DateTimeOriginal'
EXIFTOOL_MODEL_TAG = 'Model'
EXIFTOOL_SOFTWARE_TAG = 'Software'

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
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"ExifToolの実行エラー ({file_path}): {e}")
        return {}
