# Pythonの公式イメージをベースにする
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なパッケージ（ExifTool）をインストール
RUN apt-get update && apt-get install -y libimage-exiftool-perl && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして、ライブラリをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# スクリプトとユーティリティファイルをコピー
COPY utils.py .
COPY rename_images.py .
COPY organize_files.py .
COPY entrypoint.sh .

# エントリポイントスクリプトに実行権限を付与
RUN chmod +x entrypoint.sh

# スクリプトの実行コマンドを設定
ENTRYPOINT ["./entrypoint.sh"]

# デフォルトではコマンドを指定せず、entrypoint.shがUsageを表示
CMD []