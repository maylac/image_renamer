# Image Renamer - Backlog

改善項目のリストです。各項目はGitHub issueとして登録することを推奨します。

## 🎯 機能追加 (Features)

### 1. プログレスバーの追加
**優先度**: 高
**ラベル**: `enhancement`, `good first issue`

**概要**:
大量のファイルを処理する際に、進捗状況を可視化するプログレスバーを追加する。

**動機**:
- 現在は処理状況が分かりにくい
- ユーザーが処理完了までの時間を見積もれない
- 大規模なディレクトリ処理時に不安を感じる

**実装案**:
- `tqdm` ライブラリを使用
- 処理済みファイル数 / 総ファイル数を表示
- 推定残り時間を表示
- `--quiet` オプションで無効化可能

**参考コード**:
```python
from tqdm import tqdm
for file in tqdm(files, desc="Processing"):
    # process file
```

---

### 2. 並列処理による高速化
**優先度**: 中
**ラベル**: `enhancement`, `performance`

**概要**:
マルチプロセッシングを利用して、ファイル処理を並列化し高速化する。

**動機**:
- EXIF読み取りはI/O待ちが多い
- マルチコアCPUを活用できていない
- 大量ファイル処理時のパフォーマンス向上

**実装案**:
- `multiprocessing.Pool` または `concurrent.futures.ProcessPoolExecutor` を使用
- `--workers N` オプションでワーカー数を指定可能（デフォルト: CPU数）
- dry-runモードでも並列化を適用

**注意点**:
- ログ出力の順序が変わる可能性
- エラーハンドリングを適切に行う
- プログレスバーとの統合を考慮

---

### 3. 設定ファイルのサポート
**優先度**: 中
**ラベル**: `enhancement`, `configuration`

**概要**:
YAMLまたはJSON形式の設定ファイルで、デフォルト設定を管理できるようにする。

**動機**:
- 毎回コマンドライン引数を指定するのが面倒
- プロジェクトごとに設定を保存したい
- 環境変数よりも管理しやすい

**実装案**:
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

---

### 4. Undo/ロールバック機能
**優先度**: 中
**ラベル**: `enhancement`, `feature`

**概要**:
実行した操作を元に戻すためのundo/ロールバック機能を追加する。

**動機**:
- 誤った操作を元に戻したい
- バックアップを取らずに実行した場合のリカバリー
- 安心して--forceオプションを使いたい

**実装案**:
1. 操作履歴を `.image-renamer-history.json` に保存
   ```json
   {
     "timestamp": "2025-01-15T10:30:00",
     "operation": "rename",
     "changes": [
       {"from": "IMG_1234.jpg", "to": "20250115_0001_iPhone.jpg"}
     ]
   }
   ```

2. 新しいコマンド `undo` を追加
   ```bash
   python rename_images.py undo  # 直前の操作を戻す
   python rename_images.py undo --all  # 全ての操作を戻す
   python rename_images.py undo --list  # 操作履歴を表示
   ```

3. 履歴の保持期間を設定可能（デフォルト: 30日）

**注意点**:
- ディスク容量を消費する
- ファイルが削除されている場合は復元不可
- dry-runモードでは履歴を保存しない

---

### 5. 重複ファイル検出機能
**優先度**: 低
**ラベル**: `enhancement`, `feature`

**概要**:
同一内容のファイルを検出し、処理方法を選択できるようにする。

**動機**:
- 同じ写真が複数のフォルダに散在している
- ストレージの無駄を削減したい
- 重複ファイルをマージしたい

**実装案**:
1. ハッシュ値（SHA256）で重複を検出
2. 重複処理のオプション:
   - `--duplicates skip`: 重複をスキップ（デフォルト）
   - `--duplicates keep-newest`: 最新のファイルを保持
   - `--duplicates keep-oldest`: 最古のファイルを保持
   - `--duplicates interactive`: 都度確認

3. 重複レポートの出力:
   ```
   重複ファイル検出:
   グループ1 (SHA256: abc123...):
     - /path/to/file1.jpg (2023-01-01, 2.5MB)
     - /path/to/file2.jpg (2023-01-02, 2.5MB)
   ```

**パフォーマンス考慮**:
- ファイルサイズが同じものだけハッシュ計算
- 最初の数KBだけ比較してから完全ハッシュ

---

### 6. カスタムファイル名パターンのサポート
**優先度**: 中
**ラベル**: `enhancement`, `feature`

**概要**:
ユーザーが自由にファイル名のパターンをカスタマイズできるようにする。

**動機**:
- 現在のフォーマット `YYYYMMDD_####_DeviceName.ext` が固定
- ユーザーごとに好みのフォーマットがある
- プロジェクトごとに異なる命名規則を使いたい

**実装案**:

パターン指定方法:
```bash
python rename_images.py /path/to/images \
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

例:
```
{date:%Y-%m-%d}_{time:%H-%M-%S}_{device}
→ 2025-01-15_14-30-45_iPhone

{year}/{month}/{date}_{seq:05d}
→ 2025/01/20250115_00001

vacation_{date}_{original}
→ vacation_20250115_IMG_1234
```

**バリデーション**:
- パターンが一意性を保証するか検証
- 不正な文字が含まれていないか確認

---

### 7. インタラクティブモード
**優先度**: 低
**ラベル**: `enhancement`, `ux`

**概要**:
ファイル処理前にプレビューを表示し、確認を求めるインタラクティブモードを追加。

**実装案**:
```bash
python rename_images.py /path/to/images --interactive
```

出力例:
```
以下のファイルをリネームします:
1. IMG_1234.jpg → 20250115_0001_iPhone.jpg
2. IMG_5678.jpg → 20250115_0002_iPhone.jpg
3. ...

続行しますか? (y/n/s=選択):
```

オプション:
- `y`: 全て実行
- `n`: キャンセル
- `s`: 個別に選択
- `p`: パターンで選択（正規表現）

---

## 🧪 テスト (Testing)

### 8. テストカバレッジの向上
**優先度**: 高
**ラベル**: `testing`, `good first issue`

**概要**:
テストカバレッジを向上させ、エッジケースをカバーする。

**現状**:
- 基本的な動作はテスト済み
- エッジケースやエラーケースのテストが不足

**追加すべきテスト**:

**rename_images.py**:
- [ ] 巨大ファイル（>100MB）の処理
- [ ] 特殊文字を含むファイル名
- [ ] シンボリックリンクの処理
- [ ] 読み取り専用ファイル
- [ ] 10000件以上の連番処理
- [ ] タイムゾーンが異なるEXIF日時
- [ ] 壊れたEXIFデータ

**organize_files.py**:
- [ ] 深い階層のディレクトリ処理
- [ ] ディスク容量不足のケース
- [ ] ネットワークドライブでの動作

**utils.py**:
- [ ] ExifToolがインストールされていない場合
- [ ] ExifToolのバージョン違いによる動作確認
- [ ] 異なるOSでの動作確認

**目標**:
- カバレッジ: 90%以上
- 全ての公開関数に対するテスト

---

### 9. 統合テストの追加
**優先度**: 中
**ラベル**: `testing`, `ci/cd`

**概要**:
実際のExifToolを使用した統合テストを追加する。

**動機**:
- 現在のテストは全てExifToolをモック化
- 実際のExifToolとの互換性が保証されていない
- ExifToolのバージョンアップ時の影響が分からない

**実装案**:
1. テスト用の実画像ファイルを `tests/fixtures/` に配置
2. 実際にExifToolを呼び出すテストを作成
3. CI/CDでExifToolをインストールして実行

テスト対象:
- [ ] JPEGファイル（各種カメラメーカー）
- [ ] HEICファイル（iPhone）
- [ ] RAWファイル（CR2, NEF, ARW）
- [ ] 動画ファイル（MP4, MOV）
- [ ] ExifToolのバージョン違いによる動作確認

**注意**:
- テストファイルはサイズを最小限に（各ファイル<100KB）
- 著作権フリーの画像を使用
- Git LFSの使用を検討

---

### 10. パフォーマンステストの追加
**優先度**: 低
**ラベル**: `testing`, `performance`

**概要**:
パフォーマンスの劣化を検出するためのベンチマークテストを追加。

**実装案**:
- `pytest-benchmark` を使用
- 1000ファイル、10000ファイルでの処理時間を計測
- CI/CDで定期的に実行し、パフォーマンスの推移を記録

---

## 📚 ドキュメント (Documentation)

### 11. CI/CDバッジとサンプル画像の追加
**優先度**: 高
**ラベル**: `documentation`, `good first issue`

**概要**:
READMEにCI/CDステータスバッジと、使用例の画像を追加する。

**追加内容**:

**1. バッジ**:
```markdown
[![Tests](https://github.com/maylac/image_renamer/actions/workflows/test.yml/badge.svg)](https://github.com/maylac/image_renamer/actions/workflows/test.yml)
[![Docker](https://github.com/maylac/image_renamer/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/maylac/image_renamer/actions/workflows/docker-publish.yml)
[![codecov](https://codecov.io/gh/maylac/image_renamer/branch/main/graph/badge.svg)](https://codecov.io/gh/maylac/image_renamer)
```

**2. 使用例のスクリーンショット**:
- Before/Afterの比較画像
- コマンド実行時の出力例
- dry-runモードの出力例

**3. 使用例のGIF動画（オプション）**:
- 実際の操作を録画したGIF

**ツール**:
- スクリーンショット: `asciinema` でターミナル録画
- GIF生成: `asciinema2gif` または `terminalizer`

---

### 12. コントリビューションガイドの作成
**優先度**: 中
**ラベル**: `documentation`

**概要**:
`CONTRIBUTING.md` を作成し、コントリビューターのためのガイドを整備する。

**内容**:
- 開発環境のセットアップ手順
- コーディング規約
- テストの実行方法
- PRの作成方法
- コミットメッセージの規約

---

### 13. APIドキュメントの生成
**優先度**: 低
**ラベル**: `documentation`

**概要**:
Sphinxを使用してAPIドキュメントを自動生成する。

**実装案**:
- `sphinx-autodoc` で docstring から自動生成
- GitHub Pages でホスティング
- CI/CDで自動デプロイ

---

## 🛠️ 開発体験 (DevEx)

### 14. pre-commitフックの設定
**優先度**: 高
**ラベル**: `devex`, `good first issue`

**概要**:
コード品質を保つためのpre-commitフックを設定する。

**実装内容**:

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

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

**セットアップ手順を README.md に追加**:
```bash
# 開発者向けセットアップ
pip install pre-commit
pre-commit install
```

---

### 15. Makefileまたはタスクランナーの追加
**優先度**: 中
**ラベル**: `devex`, `good first issue`

**概要**:
一般的な開発タスクを簡単に実行できるようにする。

**実装案**:

`Makefile`:
```makefile
.PHONY: test lint format clean install dev-install

test:
	pytest -v

test-cov:
	pytest --cov=. --cov-report=html

lint:
	flake8 *.py
	mypy *.py

format:
	black *.py
	isort *.py

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov
	find . -name "*.pyc" -delete

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install
```

または `pyproject.toml` + `taskipy`:
```toml
[tool.taskipy.tasks]
test = "pytest -v"
test-cov = "pytest --cov=. --cov-report=html"
lint = "flake8 *.py && mypy *.py"
format = "black *.py && isort *.py"
```

---

### 16. 型ヒントの完全化
**優先度**: 中
**ラベル**: `devex`, `code-quality`

**概要**:
全ての関数に型ヒントを追加し、mypyでの型チェックを有効にする。

**現状**:
- 一部の関数に型ヒントがある
- 戻り値の型が指定されていない関数がある
- mypyの厳格モードが無効

**実装案**:
1. 全ての関数に型ヒントを追加
2. `mypy.ini` または `pyproject.toml` で厳格モードを有効化:
   ```ini
   [mypy]
   python_version = 3.9
   warn_return_any = True
   warn_unused_configs = True
   disallow_untyped_defs = True
   ```
3. CI/CDでmypyチェックを実行

---

## ⚡ パフォーマンス (Performance)

### 17. EXIF読み取りのキャッシング
**優先度**: 低
**ラベル**: `performance`

**概要**:
同じファイルのEXIF情報を複数回読み取らないようにキャッシュする。

**実装案**:
- `functools.lru_cache` を使用
- ファイルのパスとmtimeをキーにする
- メモリ使用量を考慮してキャッシュサイズを制限

---

### 18. バッチ処理の最適化
**優先度**: 低
**ラベル**: `performance`

**概要**:
ExifToolを複数ファイルに対してバッチで実行し、起動オーバーヘッドを削減する。

**実装案**:
- ExifToolのバッチモード（`-@` オプション）を使用
- 一度に100ファイルずつ処理
- パフォーマンステストで効果を測定

---

## 🔒 セキュリティ (Security)

### 19. セキュリティスキャンの追加
**優先度**: 中
**ラベル**: `security`, `ci/cd`

**概要**:
依存関係の脆弱性を検出するセキュリティスキャンを追加する。

**実装案**:
- `safety` または `pip-audit` を使用
- CI/CDで定期的に実行
- 依存関係の更新を自動化（Dependabot）

---

### 20. コマンドインジェクション対策の強化
**優先度**: 高
**ラベル**: `security`

**概要**:
ExifTool実行時のコマンドインジェクション対策を強化する。

**現状**:
- `subprocess.run()` で `check=True` を使用
- ファイルパスのバリデーションが不十分

**実装案**:
1. ファイルパスのサニタイズを強化
2. 許可されていない文字を含むパスを拒否
3. ExifToolの出力を厳密にバリデーション

---

## まとめ

### 優先度別

**高優先度** (すぐに取り組むべき):
1. プログレスバーの追加
2. テストカバレッジの向上
3. CI/CDバッジとサンプル画像の追加
4. pre-commitフックの設定
5. コマンドインジェクション対策の強化

**中優先度** (次のフェーズで実装):
6. 並列処理による高速化
7. 設定ファイルのサポート
8. Undo/ロールバック機能
9. カスタムファイル名パターンのサポート
10. 統合テストの追加
11. コントリビューションガイドの作成
12. Makefileまたはタスクランナーの追加
13. 型ヒントの完全化
14. セキュリティスキャンの追加

**低優先度** (余裕があれば実装):
15. 重複ファイル検出機能
16. インタラクティブモード
17. パフォーマンステストの追加
18. APIドキュメントの生成
19. EXIF読み取りのキャッシング
20. バッチ処理の最適化

### 初心者向け (good first issue):
- プログレスバーの追加
- テストカバレッジの向上
- CI/CDバッジとサンプル画像の追加
- pre-commitフックの設定
- Makefileまたはタスクランナーの追加
