# 医療機器サイバーセキュリティ専門家システム

医療機器のサイバーセキュリティに関する情報を自動収集・分析・提案するAI支援システムです。

## システム概要

- 医療機器サイバーセキュリティに関するガイドライン、技術情報、リスク評価を自動収集・分析
- 複数のエージェント（クローラー、インデックス、ガイドライン分類、アセスメント、テック、アーキ）が連携
- フロントエンド（React/Vite）とバックエンド（FastAPI）の構成
- SQLiteによるデータ保存

## ディレクトリ構造

```
cyber-meddev-agents/
├── backend/              # バックエンドアプリケーション（FastAPI）
│   ├── src/              # ソースコード
│   │   ├── admin/        # 管理者機能
│   │   ├── auth/         # 認証機能
│   │   ├── crawler/      # クローラーモジュール
│   │   ├── db/           # データベース関連
│   │   ├── guidelines/   # ガイドライン管理
│   │   ├── indexer/      # インデックスエンジン
│   │   └── main.py       # メインアプリケーション
│   ├── Dockerfile        # バックエンド用Dockerfile
│   └── requirements.txt  # Pythonパッケージ依存関係
├── frontend/             # フロントエンドアプリケーション（React/Vite）
│   ├── src/              # ソースコード
│   │   ├── api/          # APIクライアント
│   │   ├── components/   # Reactコンポーネント
│   │   ├── contexts/     # Reactコンテキスト
│   │   ├── App.jsx       # メインアプリケーション
│   │   └── main.jsx      # エントリーポイント
│   ├── Dockerfile        # フロントエンド用Dockerfile
│   └── package.json      # NPMパッケージ依存関係
├── docker-compose.yml    # Docker Compose設定
└── README.md             # このファイル
```

## 機能一覧

### バックエンド

- **認証システム**: JWT認証によるユーザー管理
- **クローラー**: FDA, NIST, PMDAからのドキュメント収集
- **インデックスエンジン**: LlamaIndexによるベクトル検索
- **ガイドライン管理**: ガイドラインの検索・フィルタリング
- **管理者機能**: ユーザー管理、ドキュメント管理

### フロントエンド

- **認証画面**: ログイン・登録
- **ガイドライン一覧**: 検索・フィルタリング機能
- **ガイドライン詳細**: 詳細表示
- **管理者ダッシュボード**: システム統計情報
- **管理者機能**: ユーザー管理、ドキュメント管理

## セットアップ方法

### 環境変数

`.env`ファイルをプロジェクトルートに作成し、以下の環境変数を設定してください：

```
OPENAI_API_KEY=your_openai_api_key
```

### Dockerを使用する場合

```bash
# リポジトリをクローン
git clone https://github.com/osamusic/cyber-meddev-agents.git
cd cyber-meddev-agents

# Docker Composeでビルド・起動
docker-compose up --build
```

### 手動セットアップ

#### バックエンド

```bash
cd backend

# 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate  # Windowsの場合: .venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# サーバーを起動
uvicorn src.main:app --reload
```

#### フロントエンド

```bash
cd frontend

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev
```

## アクセス方法

- バックエンドAPI: http://localhost:8000
- フロントエンド: http://localhost:5173
- API ドキュメント: http://localhost:8000/docs

## 開発者向け情報

### バックエンド開発

- FastAPIフレームワークを使用
- SQLAlchemyによるORMマッピング
- LlamaIndexによるベクトル検索
- OpenAI APIによる埋め込み生成

### フロントエンド開発

- React/Viteフレームワークを使用
- Tailwind CSSによるスタイリング
- React Router Domによるルーティング
- Axiosによる非同期API通信
