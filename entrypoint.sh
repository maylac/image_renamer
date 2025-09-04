#!/bin/sh
set -e

# 最初の引数をコマンドとして取得
COMMAND=$1

# 引数が無い場合は使用方法を表示
if [ -z "$COMMAND" ]; then
    echo "Usage: <command> [args...]" >&2
    echo "Available commands: rename, organize" >&2
    exit 1
fi

shift

case "$COMMAND" in
    rename)
        echo "Executing rename script..."
        exec python rename_images.py "$@"
        ;;
    organize)
        echo "Executing organize script..."
        exec python organize_files.py "$@"
        ;;
    *)
        echo "Error: Unknown command: $COMMAND" >&2
        echo "Available commands: rename, organize" >&2
        exit 1
        ;;
esac
