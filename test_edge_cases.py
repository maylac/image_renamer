import json
import logging
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


REPO_ROOT = Path(__file__).resolve().parent
TEST_WORKDIR = REPO_ROOT / "test_edge_cases_tmp"


@pytest.fixture
def repo_workdir():
    assert not TEST_WORKDIR.exists(), f"refusing to delete existing path: {TEST_WORKDIR}"
    TEST_WORKDIR.mkdir()
    try:
        yield TEST_WORKDIR
    finally:
        if TEST_WORKDIR.exists():
            shutil.rmtree(TEST_WORKDIR)


def touch_file(path: Path, content: bytes = b"data"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_get_device_name_prefers_model_and_handles_fallbacks():
    from rename_images import get_device_name
    from utils import EXIFTOOL_MODEL_TAG, EXIFTOOL_SOFTWARE_TAG

    assert get_device_name({
        EXIFTOOL_MODEL_TAG: "iPhone 15 Pro",
        EXIFTOOL_SOFTWARE_TAG: "Ignored App 1.2.3",
    }) == "iPhone_15_Pro"
    assert get_device_name({EXIFTOOL_SOFTWARE_TAG: "17.5.1"}) == "iOS"
    assert get_device_name({}) == "UnknownDevice"


def test_get_next_filename_skips_existing_and_reserved_paths(repo_workdir):
    from rename_images import get_next_filename

    touch_file(repo_workdir / "20240102_0001_Camera.jpg")
    reserved = {
        repo_workdir / "20240102_0002_Camera.jpg",
        repo_workdir / "20240102_0003_Camera.jpg",
    }

    assert get_next_filename(
        repo_workdir,
        "20240102",
        "Camera",
        ".jpg",
        reserved_paths=reserved,
    ) == repo_workdir / "20240102_0004_Camera.jpg"


def test_rename_image_files_logs_error_for_non_directory(repo_workdir, caplog):
    from rename_images import rename_image_files

    not_directory = repo_workdir / "not-a-directory"
    touch_file(not_directory)

    with caplog.at_level(logging.ERROR):
        rename_image_files(str(not_directory))

    assert str(not_directory) in caplog.text
    assert not_directory.exists()


def test_rename_image_files_force_processes_renamed_file(repo_workdir, monkeypatch):
    import rename_images
    from utils import EXIFTOOL_DATETIME_ORIGINAL_TAG, EXIFTOOL_MODEL_TAG

    original = repo_workdir / "20230101_0001_Old_Device.JPG"
    touch_file(original)
    monkeypatch.setattr(
        rename_images,
        "get_exif_data_with_exiftool",
        lambda path: {
            EXIFTOOL_DATETIME_ORIGINAL_TAG: "2024:05:06 07:08:09",
            EXIFTOOL_MODEL_TAG: "New Phone",
        },
    )

    rename_images.rename_image_files(str(repo_workdir), force=True)

    expected = repo_workdir / "20240506_0001_New_Phone.jpg"
    assert expected.exists()
    assert not original.exists()


def test_rename_image_files_recursive_processes_nested_files_and_skips_hidden(repo_workdir, monkeypatch):
    import rename_images
    from utils import EXIFTOOL_DATETIME_ORIGINAL_TAG, EXIFTOOL_SOFTWARE_TAG

    visible = repo_workdir / "nested" / "IMG_0001.JPG"
    hidden = repo_workdir / "nested" / ".hidden.JPG"
    touch_file(visible)
    touch_file(hidden)
    calls = []

    def fake_exif_reader(path):
        calls.append(path.name)
        return {
            EXIFTOOL_DATETIME_ORIGINAL_TAG: "2024:05:06 07:08:09",
            EXIFTOOL_SOFTWARE_TAG: "Camera App",
        }

    monkeypatch.setattr(rename_images, "get_exif_data_with_exiftool", fake_exif_reader)

    rename_images.rename_image_files(str(repo_workdir), recursive=True)

    assert (repo_workdir / "nested" / "20240506_0001_Camera_App.jpg").exists()
    assert not visible.exists()
    assert hidden.exists()
    assert calls == ["IMG_0001.JPG"]


def test_rename_image_files_invalid_exif_date_logs_error_and_keeps_original(repo_workdir, monkeypatch, caplog):
    import rename_images
    from utils import EXIFTOOL_DATETIME_ORIGINAL_TAG, EXIFTOOL_MODEL_TAG

    original = repo_workdir / "IMG_BAD_DATE.JPG"
    touch_file(original)
    monkeypatch.setattr(
        rename_images,
        "get_exif_data_with_exiftool",
        lambda path: {
            EXIFTOOL_DATETIME_ORIGINAL_TAG: "not-a-date",
            EXIFTOOL_MODEL_TAG: "Camera",
        },
    )

    with caplog.at_level(logging.ERROR):
        rename_images.rename_image_files(str(repo_workdir))

    assert original.exists()
    assert "IMG_BAD_DATE.JPG" in caplog.text
    assert "not-a-date" in caplog.text


def test_rename_image_files_catches_exif_reader_exception_and_keeps_processing(repo_workdir, monkeypatch, caplog):
    import rename_images

    original = repo_workdir / "IMG_ERROR.JPG"
    touch_file(original)

    def raise_from_reader(path):
        raise RuntimeError("reader failed")

    monkeypatch.setattr(rename_images, "get_exif_data_with_exiftool", raise_from_reader)

    with caplog.at_level(logging.ERROR):
        rename_images.rename_image_files(str(repo_workdir))

    assert original.exists()
    assert "reader failed" in caplog.text


def test_get_unique_filepath_skips_reserved_paths(repo_workdir):
    from organize_files import get_unique_filepath

    target = repo_workdir / "photo.jpg"
    reserved = {
        target,
        repo_workdir / "photo_0001.jpg",
    }

    assert get_unique_filepath(target, reserved_paths=reserved) == repo_workdir / "photo_0002.jpg"


def test_get_target_date_invalid_exif_uses_mtime_and_logs_warning(repo_workdir, monkeypatch, caplog):
    import organize_files
    from utils import EXIFTOOL_DATETIME_ORIGINAL_TAG

    source_file = repo_workdir / "IMG_BAD_DATE.JPG"
    touch_file(source_file)
    timestamp = 1_710_000_000
    os.utime(source_file, (timestamp, timestamp))
    monkeypatch.setattr(
        organize_files,
        "get_exif_data_with_exiftool",
        lambda path: {EXIFTOOL_DATETIME_ORIGINAL_TAG: "bad-date"},
    )

    with caplog.at_level(logging.WARNING):
        target_date = organize_files.get_target_date(source_file)

    assert target_date == datetime.fromtimestamp(timestamp)
    assert str(source_file) in caplog.text


def test_organize_files_logs_error_for_invalid_directory(repo_workdir, caplog):
    from organize_files import organize_files

    missing_source = repo_workdir / "missing-source"
    destination = repo_workdir / "destination"
    destination.mkdir()

    with caplog.at_level(logging.ERROR):
        organize_files(str(missing_source), str(destination), dry_run=False)

    assert str(missing_source) not in [str(path) for path in destination.rglob("*")]
    assert "ソースディレクトリ" in caplog.text


def test_organize_files_skips_hidden_files(repo_workdir, monkeypatch):
    import organize_files

    source = repo_workdir / "source"
    destination = repo_workdir / "destination"
    source.mkdir()
    destination.mkdir()
    hidden = source / ".hidden.JPG"
    touch_file(hidden)
    exif_reader = Mock(return_value={})
    monkeypatch.setattr(organize_files, "get_exif_data_with_exiftool", exif_reader)

    organize_files.organize_files(str(source), str(destination), dry_run=False)

    assert hidden.exists()
    assert list(destination.rglob("*")) == []
    exif_reader.assert_not_called()


def test_organize_files_catches_processing_exception_and_continues(repo_workdir, monkeypatch, caplog):
    import organize_files

    source = repo_workdir / "source"
    destination = repo_workdir / "destination"
    source.mkdir()
    destination.mkdir()
    bad_file = source / "bad.jpg"
    good_file = source / "good.jpg"
    touch_file(bad_file)
    touch_file(good_file)

    def fake_target_date(path):
        if path.name == "bad.jpg":
            raise RuntimeError("date failed")
        return datetime(2024, 7, 8, 9, 10, 11)

    monkeypatch.setattr(organize_files, "get_target_date", fake_target_date)

    with caplog.at_level(logging.ERROR):
        organize_files.organize_files(str(source), str(destination), dry_run=False)

    assert bad_file.exists()
    assert not good_file.exists()
    assert (destination / "2024" / "07" / "good.jpg").exists()
    assert "date failed" in caplog.text


def test_get_exif_data_with_exiftool_success_builds_expected_command(repo_workdir, monkeypatch):
    import utils
    from utils import EXIFTOOL_DATETIME_ORIGINAL_TAG

    image = repo_workdir / "image.jpg"
    touch_file(image)
    calls = []

    def fake_run(command, capture_output, text, check):
        calls.append({
            "command": command,
            "capture_output": capture_output,
            "text": text,
            "check": check,
        })
        return SimpleNamespace(
            stdout=json.dumps([{EXIFTOOL_DATETIME_ORIGINAL_TAG: "2024:01:02 03:04:05"}])
        )

    monkeypatch.setattr(utils.subprocess, "run", fake_run)

    assert utils.get_exif_data_with_exiftool(image) == {
        EXIFTOOL_DATETIME_ORIGINAL_TAG: "2024:01:02 03:04:05"
    }
    assert calls == [{
        "command": [
            "exiftool",
            "-json",
            "-s",
            "-d",
            "%Y:%m:%d %H:%M:%S",
            str(image),
        ],
        "capture_output": True,
        "text": True,
        "check": True,
    }]


def test_get_exif_data_with_exiftool_returns_empty_dict_for_empty_result(repo_workdir, monkeypatch):
    import utils

    image = repo_workdir / "image.jpg"
    touch_file(image)
    monkeypatch.setattr(
        utils.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="[]"),
    )

    assert utils.get_exif_data_with_exiftool(image) == {}


@pytest.mark.parametrize(
    "mode",
    ["called-process-error", "bad-json", "missing-exiftool"],
)
def test_get_exif_data_with_exiftool_errors_return_empty_dict(repo_workdir, monkeypatch, caplog, mode):
    import utils

    image = repo_workdir / "image.jpg"
    touch_file(image)

    def fake_run(command, *args, **kwargs):
        if mode == "called-process-error":
            raise subprocess.CalledProcessError(1, command)
        if mode == "missing-exiftool":
            raise FileNotFoundError("exiftool")
        return SimpleNamespace(stdout="{not-json")

    monkeypatch.setattr(utils.subprocess, "run", fake_run)

    with caplog.at_level(logging.ERROR):
        assert utils.get_exif_data_with_exiftool(image) == {}

    assert str(image) in caplog.text


def test_setup_logging_with_log_file_adds_file_handler_and_writes(repo_workdir):
    import utils

    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    log_file = repo_workdir / "app.log"

    for handler in original_handlers:
        root_logger.removeHandler(handler)

    try:
        utils.setup_logging(log_file)
        logging.info("edge case log line")
        for handler in root_logger.handlers:
            handler.flush()

        file_handlers = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert Path(file_handlers[0].baseFilename) == log_file
        assert "edge case log line" in log_file.read_text(encoding="utf-8")
    finally:
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)


def test_entrypoint_requires_command():
    result = subprocess.run(
        ["sh", str(REPO_ROOT / "entrypoint.sh")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Usage: <command> [args...]" in result.stderr
    assert "Available commands: rename, organize" in result.stderr


def test_entrypoint_rejects_unknown_command():
    result = subprocess.run(
        ["sh", str(REPO_ROOT / "entrypoint.sh"), "unknown"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "Unknown command: unknown" in result.stderr


@pytest.mark.parametrize(
    ("command", "script_name"),
    [
        ("rename", "rename_images.py"),
        ("organize", "organize_files.py"),
    ],
)
def test_entrypoint_dispatches_known_commands_to_python(repo_workdir, command, script_name):
    fake_bin = repo_workdir / "bin"
    fake_bin.mkdir()
    args_file = repo_workdir / "python-args.txt"
    fake_python = fake_bin / "python"
    fake_python.write_text(
        "#!/bin/sh\n"
        'printf "%s\\n" "$@" > "$FAKE_PYTHON_ARGS"\n',
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["FAKE_PYTHON_ARGS"] = str(args_file)

    result = subprocess.run(
        ["sh", str(REPO_ROOT / "entrypoint.sh"), command, "arg1", "--flag"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert f"Executing {command} script..." in result.stdout
    assert args_file.read_text(encoding="utf-8").splitlines() == [
        script_name,
        "arg1",
        "--flag",
    ]
