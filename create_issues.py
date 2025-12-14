#!/usr/bin/env python3
"""
GitHub issuesを一括作成するスクリプト

使用方法:
  export GITHUB_TOKEN=your_github_token
  python create_issues.py
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, List

# GitHub API設定
REPO_OWNER = "maylac"
REPO_NAME = "image_renamer"
API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

# Issue定義
ISSUES = [
    {
        "title": "feat: プログレスバーの追加",
        "body": """## 概要
大量のファイルを処理する際に、進捗状況を可視化するプログレスバーを追加する。

## 動機
- 現在は処理状況が分かりにくい
- ユーザーが処理完了までの時間を見積もれない
- 大規模なディレクトリ処理時に不安を感じる

## 実装案
- `tqdm` ライブラリを使用
- 処理済みファイル数 / 総ファイル数を表示
- 推定残り時間を表示
- `--quiet` オプションで無効化可能

## 参考
```python
from tqdm import tqdm
for file in tqdm(files, desc="Processing"):
    # process file
```
""",
        "labels": ["enhancement", "good first issue"]
    },
    {
        "title": "feat: 並列処理による高速化",
        "body": """## 概要
マルチプロセッシングを利用して、ファイル処理を並列化し高速化する。

## 動機
- EXIF読み取りはI/O待ちが多い
- マルチコアCPUを活用できていない
- 大量ファイル処理時のパフォーマンス向上

## 実装案
- `multiprocessing.Pool` または `concurrent.futures.ProcessPoolExecutor` を使用
- `--workers N` オプションでワーカー数を指定可能（デフォルト: CPU数）
- dry-runモードでも並列化を適用

## 注意点
- ログ出力の順序が変わる可能性
- エラーハンドリングを適切に行う
- プログレスバーとの統合を考慮
""",
        "labels": ["enhancement", "performance"]
    },
    {
        "title": "feat: 設定ファイルのサポート",
        "body": """## 概要
YAMLまたはJSON形式の設定ファイルで、デフォルト設定を管理できるようにする。

## 動機
- 毎回コマンドライン引数を指定するのが面倒
- プロジェクトごとに設定を保存したい
- 環境変数よりも管理しやすい

## 実装案
設定ファイルの場所:
1. `.image-renamer.yml` (カレントディレクトリ)
2. `~/.config/image-renamer/config.yml` (ユーザーホーム)
3. `--config` オプションで明示的に指定

設定例:
```yaml
rename:
  dry_run: false
  recursive: true
  force: false
  log_file: ~/logs/image-renamer.log

organize:
  dry_run: false
  log_file: ~/logs/image-renamer.log

# カスタムデバイス名マッピング
device_mapping:
  "iPhone14,2": "iPhone_13_Pro"
```

優先順位: CLI引数 > 設定ファイル > 環境変数 > デフォルト
""",
        "labels": ["enhancement"]
    },
    {
        "title": "feat: Undo/ロールバック機能",
        "body": """## 概要
実行した操作を元に戻すためのundo/ロールバック機能を追加する。

## 動機
- 誤った操作を元に戻したい
- バックアップを取らずに実行した場合のリカバリー
- 安心して--forceオプションを使いたい

## 実装案
1. 操作履歴を `.image-renamer-history.json` に保存
2. 新しいコマンド `undo` を追加
   ```bash
   python rename_images.py undo  # 直前の操作を戻す
   python rename_images.py undo --all  # 全ての操作を戻す
   python rename_images.py undo --list  # 操作履歴を表示
   ```
3. 履歴の保持期間を設定可能（デフォルト: 30日）

## 注意点
- ディスク容量を消費する
- ファイルが削除されている場合は復元不可
- dry-runモードでは履歴を保存しない
""",
        "labels": ["enhancement"]
    },
    {
        "title": "feat: 重複ファイル検出機能",
        "body": """## 概要
同一内容のファイルを検出し、処理方法を選択できるようにする。

## 動機
- 同じ写真が複数のフォルダに散在している
- ストレージの無駄を削減したい
- 重複ファイルをマージしたい

## 実装案
1. ハッシュ値（SHA256）で重複を検出
2. 重複処理のオプション:
   - `--duplicates skip`: 重複をスキップ（デフォルト）
   - `--duplicates keep-newest`: 最新のファイルを保持
   - `--duplicates keep-oldest`: 最古のファイルを保持
   - `--duplicates interactive`: 都度確認

## パフォーマンス考慮
- ファイルサイズが同じものだけハッシュ計算
- 最初の数KBだけ比較してから完全ハッシュ
""",
        "labels": ["enhancement"]
    },
    {
        "title": "feat: カスタムファイル名パターンのサポート",
        "body": """## 概要
ユーザーが自由にファイル名のパターンをカスタマイズできるようにする。

## 動機
- 現在のフォーマット `YYYYMMDD_####_DeviceName.ext` が固定
- ユーザーごとに好みのフォーマットがある
- プロジェクトごとに異なる命名規則を使いたい

## 実装案
パターン指定方法:
```bash
python rename_images.py /path/to/images \\
  --pattern "{date:%Y%m%d}_{seq:04d}_{device}_{time:%H%M%S}"
```

利用可能なプレースホルダー:
- `{date}`: 日付（フォーマット指定可能）
- `{time}`: 時刻（フォーマット指定可能）
- `{device}`: デバイス名
- `{model}`: カメラモデル
- `{software}`: ソフトウェア名
- `{seq}`: 連番（桁数指定可能）
- `{original}`: 元のファイル名（拡張子なし）
- `{year}`, `{month}`, `{day}`: 個別の日付要素
- `{hash}`: ファイルハッシュ（先頭8文字）

## バリデーション
- パターンが一意性を保証するか検証
- 不正な文字が含まれていないか確認
""",
        "labels": ["enhancement"]
    },
    {
        "title": "test: テストカバレッジの向上",
        "body": """## 概要
テストカバレッジを向上させ、エッジケースをカバーする。

## 現状
- 基本的な動作はテスト済み
- エッジケースやエラーケースのテストが不足

## 追加すべきテスト

### rename_images.py
- [ ] 巨大ファイル（>100MB）の処理
- [ ] 特殊文字を含むファイル名
- [ ] シンボリックリンクの処理
- [ ] 読み取り専用ファイル
- [ ] 10000件以上の連番処理
- [ ] タイムゾーンが異なるEXIF日時
- [ ] 壊れたEXIFデータ

### organize_files.py
- [ ] 深い階層のディレクトリ処理
- [ ] ディスク容量不足のケース
- [ ] ネットワークドライブでの動作

### utils.py
- [ ] ExifToolがインストールされていない場合
- [ ] ExifToolのバージョン違いによる動作確認
- [ ] 異なるOSでの動作確認

## 目標
- カバレッジ: 90%以上
- 全ての公開関数に対するテスト
""",
        "labels": ["testing", "good first issue"]
    },
    {
        "title": "test: 統合テストの追加",
        "body": """## 概要
実際のExifToolを使用した統合テストを追加する。

## 動機
- 現在のテストは全てExifToolをモック化
- 実際のExifToolとの互換性が保証されていない
- ExifToolのバージョンアップ時の影響が分からない

## 実装案
1. テスト用の実画像ファイルを `tests/fixtures/` に配置
2. 実際にExifToolを呼び出すテストを作成
3. CI/CDでExifToolをインストールして実行

テスト対象:
- [ ] JPEGファイル（各種カメラメーカー）
- [ ] HEICファイル（iPhone）
- [ ] RAWファイル（CR2, NEF, ARW）
- [ ] 動画ファイル（MP4, MOV）
- [ ] ExifToolのバージョン違いによる動作確認

## 注意
- テストファイルはサイズを最小限に（各ファイル<100KB）
- 著作権フリーの画像を使用
- Git LFSの使用を検討
""",
        "labels": ["testing"]
    },
    {
        "title": "docs: CI/CDバッジとサンプル画像の追加",
        "body": """## 概要
READMEにCI/CDステータスバッジと、使用例の画像を追加する。

## 追加内容

### 1. バッジ
```markdown
[![Tests](https://github.com/maylac/image_renamer/actions/workflows/test.yml/badge.svg)](https://github.com/maylac/image_renamer/actions/workflows/test.yml)
[![Docker](https://github.com/maylac/image_renamer/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/maylac/image_renamer/actions/workflows/docker-publish.yml)
```

### 2. 使用例のスクリーンショット
- Before/Afterの比較画像
- コマンド実行時の出力例
- dry-runモードの出力例

### 3. 使用例のGIF動画（オプション）
- 実際の操作を録画したGIF

## ツール
- スクリーンショット: `asciinema` でターミナル録画
- GIF生成: `asciinema2gif` または `terminalizer`
""",
        "labels": ["documentation", "good first issue"]
    },
    {
        "title": "chore: pre-commitフックの設定",
        "body": """## 概要
コード品質を保つためのpre-commitフックを設定する。

## 実装内容
`.pre-commit-config.yaml` の作成:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json

  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/PyCQA/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=120]

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black]
```

## セットアップ手順を README.md に追加
```bash
# 開発者向けセットアップ
pip install pre-commit
pre-commit install
```
""",
        "labels": ["good first issue"]
    },
]


def create_issue(token: str, issue: Dict) -> bool:
    """GitHub issueを作成する"""
    url = f"{API_BASE}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    data = json.dumps(issue).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ Created: {issue['title']}")
            print(f"   URL: {result['html_url']}")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to create: {issue['title']}")
        print(f"   Error: {e.code} - {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error creating: {issue['title']}")
        print(f"   Error: {e}")
        return False


def main():
    # 環境変数からGitHubトークンを取得
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("エラー: GITHUB_TOKEN環境変数が設定されていません。")
        print("\n使用方法:")
        print("  1. GitHubでPersonal Access Tokenを作成")
        print("     https://github.com/settings/tokens")
        print("  2. 'repo' スコープを有効にする")
        print("  3. 環境変数を設定:")
        print("     export GITHUB_TOKEN=your_token_here")
        print("  4. このスクリプトを実行:")
        print("     python create_issues.py")
        return 1

    print(f"GitHubリポジトリ: {REPO_OWNER}/{REPO_NAME}")
    print(f"作成するissue数: {len(ISSUES)}\n")

    # 確認
    response = input("issuesを作成しますか? (y/n): ")
    if response.lower() != 'y':
        print("キャンセルしました。")
        return 0

    # issuesを作成
    success_count = 0
    for issue in ISSUES:
        if create_issue(token, issue):
            success_count += 1
        print()  # 空行

    # 結果サマリー
    print("=" * 50)
    print(f"完了: {success_count}/{len(ISSUES)} issuesを作成しました。")

    return 0 if success_count == len(ISSUES) else 1


if __name__ == '__main__':
    exit(main())
