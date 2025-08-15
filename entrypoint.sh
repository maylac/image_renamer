#!/bin/sh
set -e

# 最初の引数をコマンドとして取得
COMMAND=$1
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
