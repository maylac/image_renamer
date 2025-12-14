import json
import os
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image
import pytest
from unittest.mock import patch, MagicMock

# テスト対象のスクリプトをインポート
# import rename_images # 直接インポートすると、input()が実行されてしまうため、後でモックする

# テスト用のダミーディレクトリ
TEST_DIR = Path("./test_images")

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # テストディレクトリが存在すれば削除
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    # テストディレクトリを作成
    TEST_DIR.mkdir()
    yield
    # テスト後にディレクトリを削除
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)

def create_dummy_image(file_path: Path, datetime_str: str = None, software: str = None):
    """ダミー画像を生成し、EXIFデータを埋め込む"""
    img = Image.new('RGB', (100, 100), color = 'red')
    exif_data = img.getexif()
    if datetime_str:
        exif_data[0x9003] = datetime_str # DateTimeOriginal
    if software:
        exif_data[0x010F] = software # Make (for testing software tag)
        exif_data[0x0131] = software # Software
    img.save(file_path, exif=exif_data.tobytes())

@patch('subprocess.run')
def test_rename_basic(mock_subprocess_run):
    # ExifToolのモック設定
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:01:01 10:00:00", "Software": "TestApp"}]),
        stderr="",
        returncode=0
    )
    
    # ダミー画像を作成
    original_path = TEST_DIR / "IMG_1234.JPG"
    create_dummy_image(original_path, "2023:01:01 10:00:00", "TestApp")

    # rename_images.py をインポートして実行
    from rename_images import rename_image_files
    rename_image_files(str(TEST_DIR))

    # リネーム後のファイル名を確認
    expected_name = TEST_DIR / "20230101_0001_TestApp.jpg"
    assert expected_name.exists()
    assert not original_path.exists()

@patch('subprocess.run')
def test_rename_with_sequence(mock_subprocess_run):
    # ExifToolのモック設定
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:01:01 10:00:00", "Software": "TestApp"}]),
        stderr="",
        returncode=0
    )

    # ダミー画像を2つ作成（同じ日時）
    original_path1 = TEST_DIR / "IMG_1234.JPG"
    original_path2 = TEST_DIR / "IMG_5678.JPG"
    create_dummy_image(original_path1, "2023:01:01 10:00:00", "TestApp")
    create_dummy_image(original_path2, "2023:01:01 10:00:00", "TestApp")

    from rename_images import rename_image_files
    rename_image_files(str(TEST_DIR))

    # リネーム後のファイル名を確認（連番が付与されること）
    expected_name1 = TEST_DIR / "20230101_0001_TestApp.jpg"
    expected_name2 = TEST_DIR / "20230101_0002_TestApp.jpg"
    assert expected_name1.exists()
    assert expected_name2.exists()
    assert not original_path1.exists()
    assert not original_path2.exists()

@patch('subprocess.run')
def test_skip_no_exif_datetime(mock_subprocess_run):
    # ExifToolのモック設定 (DateTimeOriginalがない場合)
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"Software": "TestApp"}]), # 日時情報なし
        stderr="",
        returncode=0
    )

    original_path = TEST_DIR / "IMG_NODATE.JPG"
    create_dummy_image(original_path, software="TestApp") # 日時なしで作成

    from rename_images import rename_image_files
    rename_image_files(str(TEST_DIR))

    # リネームされずに元のファイルが残っていることを確認
    assert original_path.exists()
    assert len(list(TEST_DIR.iterdir())) == 1 # 他のファイルが作成されていないこと

@patch('subprocess.run')
def test_remove_app_version(mock_subprocess_run):
    # ExifToolのモック設定 (iOSバージョンを含むソフトウェア名)
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:01:01 10:00:00", "Software": "iOS 15.6.1"}]),
        stderr="",
        returncode=0
    )

    original_path = TEST_DIR / "IMG_IOS.JPG"
    create_dummy_image(original_path, "2023:01:01 10:00:00", "iOS 15.6.1")

    from rename_images import rename_image_files
    rename_image_files(str(TEST_DIR))

    # リネーム後のファイル名に「iOS」が含まれていることを確認
    expected_name = TEST_DIR / "20230101_0001_iOS.jpg"
    assert expected_name.exists()
    assert not original_path.exists()

@patch('subprocess.run')
def test_skip_renamed_file(mock_subprocess_run):
    # ExifToolのモック設定
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:01:01 10:00:00", "Software": "TestApp"}]),
        stderr="",
        returncode=0
    )

    # 既にリネーム済みの形式のダミーファイルを作成
    renamed_path = TEST_DIR / "20230101_0001_TestApp.jpg"
    create_dummy_image(renamed_path, "2023:01:01 10:00:00", "TestApp")

    from rename_images import rename_image_files
    rename_image_files(str(TEST_DIR))

    # ファイルがスキップされ、変更されていないことを確認
    assert renamed_path.exists()
    assert len(list(TEST_DIR.iterdir())) == 1 # 他のファイルが作成されていないこと


@patch('subprocess.run')
def test_special_characters_in_filename(mock_subprocess_run):
    """特殊文字を含むファイル名のテスト"""
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:01:01 10:00:00", "Software": "TestApp"}]),
        stderr="",
        returncode=0
    )

    # 特殊文字を含むファイル名を作成
    original_path = TEST_DIR / "IMG_テスト_123.JPG"
    create_dummy_image(original_path, "2023:01:01 10:00:00", "TestApp")

    from rename_images import rename_image_files
    rename_image_files(str(TEST_DIR))

    # リネーム後のファイル名を確認
    expected_name = TEST_DIR / "20230101_0001_TestApp.jpg"
    assert expected_name.exists()
    assert not original_path.exists()


@patch('subprocess.run')
def test_unsupported_file_extension(mock_subprocess_run):
    """サポート対象外のファイル拡張子のテスト"""
    # サポート対象外のファイルを作成
    unsupported_file = TEST_DIR / "document.txt"
    unsupported_file.write_text("This is a text file")

    from rename_images import rename_image_files
    rename_image_files(str(TEST_DIR))

    # ファイルがスキップされ、変更されていないことを確認
    assert unsupported_file.exists()
    assert unsupported_file.read_text() == "This is a text file"


@patch('subprocess.run')
def test_large_sequence_numbers(mock_subprocess_run):
    """大きな連番のテスト（連番の増加を確認）"""
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:01:01 10:00:00", "Software": "TestApp"}]),
        stderr="",
        returncode=0
    )

    # 連番1, 2のファイルが既に存在する状況を作成
    for i in range(1, 3):
        existing_file = TEST_DIR / f"20230101_{i:04d}_TestApp.jpg"
        create_dummy_image(existing_file, "2023:01:01 10:00:00", "TestApp")

    # 新しいファイルを追加
    new_file = TEST_DIR / "IMG_NEW.JPG"
    create_dummy_image(new_file, "2023:01:01 10:00:00", "TestApp")

    from rename_images import rename_image_files
    rename_image_files(str(TEST_DIR), force=True)

    # 3番目のファイルが作成されることを確認（forceモードで既存ファイルも再リネーム）
    expected_new_file = TEST_DIR / "20230101_0003_TestApp.jpg"
    assert expected_new_file.exists()
    # 連番が正しく増えていることを確認
    assert (TEST_DIR / "20230101_0001_TestApp.jpg").exists()
    assert (TEST_DIR / "20230101_0002_TestApp.jpg").exists()


@patch('subprocess.run')
def test_empty_directory(mock_subprocess_run):
    """空のディレクトリのテスト"""
    from rename_images import rename_image_files
    # 空のディレクトリで実行
    rename_image_files(str(TEST_DIR))

    # エラーなく完了することを確認
    assert TEST_DIR.exists()
    assert len(list(TEST_DIR.iterdir())) == 0


@patch('subprocess.run')
def test_quiet_mode(mock_subprocess_run):
    """quietモードのテスト（プログレスバー非表示）"""
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:01:01 10:00:00", "Software": "TestApp"}]),
        stderr="",
        returncode=0
    )

    original_path = TEST_DIR / "IMG_1234.JPG"
    create_dummy_image(original_path, "2023:01:01 10:00:00", "TestApp")

    from rename_images import rename_image_files
    # quietモードで実行（エラーが発生しないことを確認）
    rename_image_files(str(TEST_DIR), quiet=True)

    # リネーム後のファイル名を確認
    expected_name = TEST_DIR / "20230101_0001_TestApp.jpg"
    assert expected_name.exists()
    assert not original_path.exists()
