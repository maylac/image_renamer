import json
import shutil
from pathlib import Path
from datetime import datetime
from PIL import Image
import pytest
from unittest.mock import patch, MagicMock

# テスト用のダミーディレクトリ
SOURCE_DIR = Path("./test_source")
DEST_DIR = Path("./test_dest")


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # テストディレクトリが存在すれば削除
    for dir_path in [SOURCE_DIR, DEST_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
        dir_path.mkdir()
    yield
    # テスト後にディレクトリを削除
    for dir_path in [SOURCE_DIR, DEST_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)


def create_dummy_image(file_path: Path, datetime_str: str = None):
    """ダミー画像を生成し、EXIFデータを埋め込む"""
    img = Image.new('RGB', (100, 100), color='red')
    exif_data = img.getexif()
    if datetime_str:
        exif_data[0x9003] = datetime_str  # DateTimeOriginal
    img.save(file_path, exif=exif_data.tobytes())


@patch('subprocess.run')
def test_organize_basic(mock_subprocess_run):
    """基本的なファイル整理のテスト"""
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:06:15 10:00:00"}]),
        stderr="",
        returncode=0
    )

    # ダミー画像を作成
    original_path = SOURCE_DIR / "IMG_1234.JPG"
    create_dummy_image(original_path, "2023:06:15 10:00:00")

    from organize_files import organize_files
    organize_files(str(SOURCE_DIR), str(DEST_DIR), dry_run=False)

    # ファイルが正しいディレクトリに移動されていることを確認
    expected_path = DEST_DIR / "2023" / "06" / "IMG_1234.JPG"
    assert expected_path.exists()
    assert not original_path.exists()


@patch('subprocess.run')
def test_organize_dry_run(mock_subprocess_run):
    """dry-runモードのテスト（ファイルが移動されないこと）"""
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:06:15 10:00:00"}]),
        stderr="",
        returncode=0
    )

    original_path = SOURCE_DIR / "IMG_1234.JPG"
    create_dummy_image(original_path, "2023:06:15 10:00:00")

    from organize_files import organize_files
    organize_files(str(SOURCE_DIR), str(DEST_DIR), dry_run=True)

    # ファイルが元の場所に残っていることを確認
    assert original_path.exists()
    # 宛先ディレクトリにファイルが作成されていないことを確認
    assert not (DEST_DIR / "2023" / "06" / "IMG_1234.JPG").exists()


@patch('subprocess.run')
def test_organize_file_collision(mock_subprocess_run):
    """同名ファイルが存在する場合の衝突処理テスト"""
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{"DateTimeOriginal": "2023:06:15 10:00:00"}]),
        stderr="",
        returncode=0
    )

    # 宛先に既存ファイルを作成
    target_dir = DEST_DIR / "2023" / "06"
    target_dir.mkdir(parents=True, exist_ok=True)
    existing_file = target_dir / "IMG_1234.JPG"
    create_dummy_image(existing_file, "2023:06:15 10:00:00")

    # ソースに同名ファイルを作成
    original_path = SOURCE_DIR / "IMG_1234.JPG"
    create_dummy_image(original_path, "2023:06:15 10:00:00")

    from organize_files import organize_files
    organize_files(str(SOURCE_DIR), str(DEST_DIR), dry_run=False)

    # 既存ファイルが残っていることを確認
    assert existing_file.exists()
    # 連番付きで新しいファイルが作成されていることを確認
    expected_new_path = target_dir / "IMG_1234_0001.JPG"
    assert expected_new_path.exists()
    assert not original_path.exists()


@patch('subprocess.run')
def test_organize_no_exif_uses_mtime(mock_subprocess_run):
    """EXIF情報がない場合、ファイル更新日時が使われることをテスト"""
    mock_subprocess_run.return_value = MagicMock(
        stdout=json.dumps([{}]),  # EXIF情報なし
        stderr="",
        returncode=0
    )

    original_path = SOURCE_DIR / "IMG_NOEXIF.JPG"
    create_dummy_image(original_path)

    from organize_files import organize_files
    organize_files(str(SOURCE_DIR), str(DEST_DIR), dry_run=False)

    # ファイルが移動されたことを確認（日付はファイルの更新日時に基づく）
    assert not original_path.exists()
    # いずれかの年月ディレクトリに移動されていることを確認
    moved_files = list(DEST_DIR.rglob("IMG_NOEXIF.JPG"))
    assert len(moved_files) == 1


@patch('subprocess.run')
def test_organize_multiple_files(mock_subprocess_run):
    """複数ファイルの整理テスト"""
    def mock_exiftool(command, **kwargs):
        file_path = command[-1]
        if "IMG_JAN" in file_path:
            return MagicMock(
                stdout=json.dumps([{"DateTimeOriginal": "2023:01:10 10:00:00"}]),
                stderr="", returncode=0
            )
        elif "IMG_FEB" in file_path:
            return MagicMock(
                stdout=json.dumps([{"DateTimeOriginal": "2023:02:20 10:00:00"}]),
                stderr="", returncode=0
            )
        return MagicMock(stdout=json.dumps([{}]), stderr="", returncode=0)

    mock_subprocess_run.side_effect = mock_exiftool

    # 異なる月のダミー画像を作成
    jan_file = SOURCE_DIR / "IMG_JAN.JPG"
    feb_file = SOURCE_DIR / "IMG_FEB.JPG"
    create_dummy_image(jan_file, "2023:01:10 10:00:00")
    create_dummy_image(feb_file, "2023:02:20 10:00:00")

    from organize_files import organize_files
    organize_files(str(SOURCE_DIR), str(DEST_DIR), dry_run=False)

    # それぞれ正しいディレクトリに移動されていることを確認
    assert (DEST_DIR / "2023" / "01" / "IMG_JAN.JPG").exists()
    assert (DEST_DIR / "2023" / "02" / "IMG_FEB.JPG").exists()
    assert not jan_file.exists()
    assert not feb_file.exists()


def test_get_unique_filepath():
    """get_unique_filepath関数の単体テスト"""
    from organize_files import get_unique_filepath

    # 存在しないファイルはそのまま返す
    non_existing = Path("./nonexistent.jpg")
    assert get_unique_filepath(non_existing) == non_existing

    # 既存ファイルがある場合は連番を付与
    existing_file = SOURCE_DIR / "existing.jpg"
    create_dummy_image(existing_file)

    result = get_unique_filepath(existing_file)
    assert result == SOURCE_DIR / "existing_0001.jpg"

    # さらに連番ファイルも存在する場合
    create_dummy_image(SOURCE_DIR / "existing_0001.jpg")
    result = get_unique_filepath(existing_file)
    assert result == SOURCE_DIR / "existing_0002.jpg"
