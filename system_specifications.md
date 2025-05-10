# 医療機器サイバーセキュリティ専門家システム 要求仕様書

## 1. システム概要

本システムは、医療機器のサイバーセキュリティに関する国際ガイドライン、実装技術、リスク評価をAIによって自動収集・分析・提案する専門家支援システムである。複数のエージェントが連携し、セキュリティ対策の可視化、実装補助、リスクアセスメントを提供する。

---

## 2. 要件一覧

### 2.1 機能要件

| 要件ID | 要件内容 |
|--------|----------|
| FR-001 | Webや規格ドキュメントから情報を収集し、全文検索可能な形式で保存できること。 |
| FR-002 | ドキュメントをセキュリティ対策分類（例：NIST CSF, IEC 62443）に整理できること。 |
| FR-003 | 分類された対策に基づき、関連技術や製品例を自動検索できること。 |
| FR-004 | ユーザーの状況をヒアリングし、各規格に対するリスクアセスメントを実施できること。 |
| FR-005 | 設計仕様と技術データを照合して、推奨技術を提示できること。 |

### 2.2 非機能要件

| 要件ID | 要件内容 |
|--------|----------|
| NFR-001 | すべての処理は週次で自動実行できること（例：GitHub Actions） |
| NFR-002 | 結果はトレーサブルに管理され、出典、発行日、信頼性が付与されていること。 |
| NFR-003 | システムはDockerコンテナで構成され、再現可能な形で動作すること。 |

---

## 3. サブシステム別要求

### 3.1 クローラー

- CR-001: FDA, NIST, PMDA等のWeb/PDF/HTMLから文書を自動取得できる。
- CR-002: MIME型でフィルタリング、重複排除できる。
- CR-003: 更新された文書のみ処理対象とする。

### 3.2 インデックスエンジン

- IX-001: 文書をセクション単位に分割し、ベクトル埋め込みを生成できる。
- IX-002: 言語情報とメタデータを添えて保存可能である。

### 3.3 ガイドラインエージェント

- GL-001: セキュリティ対策分類（例：NIST CSF, IEC 62443）を行える。
- GL-002: 各項目に対し、出典、地域、キーワード等のメタ情報を付与する。

### 3.4 アセスメントエージェント

- AS-001: ユーザーの回答とガイドラインの差異を自動抽出する。
- AS-002: 不足している対策について、リスクと推奨対策を提示する。

### 3.5 テックエージェント

- TC-001: 検索対象キーワードに対して、Tavily等でWeb検索を実行できる。
- TC-002: 検索結果に対し、技術名、URL、要約、出典を保存できる。

### 3.6 アーキエージェント

- AR-001: 入力された設計仕様に対して、準拠すべき対策と技術提案を行う。
- AR-002: 技術DBとガイドラインDBの両方を照合して提案根拠を示す。

---

# 医療機器サイバーセキュリティ専門家システム テストケース一覧

## 1. ガイドライン分類

| Test ID | 内容 | 入力 | 期待出力 |
|---------|------|------|----------|
| TC-GL-001 | NIST分類 | NIST SP800-53 PDF | Protect > Access Control |
| TC-GL-002 | メタ情報抽出 | FDA Guidance PDF | 出典: FDA、地域: US |

## 2. アセスメント

| Test ID | 内容 | 入力 | 期待出力 |
|---------|------|------|----------|
| TC-AS-001 | 不足対策判定 | ソフトウェア更新なし | Patch management 未対応 |
| TC-AS-002 | 推奨対策説明 | BLE通信使用 | 暗号通信の推奨, FIPS対応例 |

## 3. 技術検索

| Test ID | 内容 | 入力 | 期待出力 |
|---------|------|------|----------|
| TC-TC-001 | 検索成功 | Device authentication | FIDO2, TPM, OAuth2のURL付き結果 |

## 4. クローラー／インデックス

| Test ID | 内容 | 入力 | 期待出力 |
|---------|------|------|----------|
| TC-CR-001 | PDF取得 | https://www.nist.gov/ | PDF取得成功、MIME=application/pdf |
| TC-IX-001 | インデックス成功 | 新規PDF1件 | 分割数 > 0、ベクトルDBに追加済み |

---

# クローラー 詳細仕様書

## 1. 概要

クローラーは、医療機器のサイバーセキュリティに関する文書（ガイドライン、発表資料、脆弱性情報など）を、定期的に指定URLから取得し、構造化されたテキスト形式として保存・インデックス化する機能を提供する。対象はPDF, HTML, DOCXなどで、重複除外や更新検知も行う。


## 2. 入出力仕様

### 2.1 入力

| 項目 | 説明 |
|------|------|
| URLリスト | 対象のトップページまたは特定ファイルへのURL一覧（例：NIST, FDA） |
| MIMEフィルター | `["application/pdf", "text/html", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]` |
| 巡回深度 | デフォルト: 2階層（オプション） |
| クロール間隔 | 毎週（cronまたはGitHub Actions） |

### 2.2 出力

| フィールド名 | 型 | 説明 |
|--------------|----|------|
| `doc_id`     | str | 一意なID（ハッシュ） |
| `url`        | str | 元URL |
| `title`      | str | 文書タイトル（HTMLなら`<title>`, PDFは1ページ目） |
| `content`    | str | 抽出本文 |
| `source_type`| str | "PDF", "HTML", "DOCX"など |
| `downloaded_at` | datetime | ダウンロード日時 |
| `lang`       | str | 言語コード（自動判定） |


## 3. 処理フロー

### 3.1 擬似コード

```python
for url in seed_urls:
    page = fetch(url)
    for link in extract_links(page):
        if mime_type(link) in allowed_types:
            if not is_duplicate(link):
                content = extract_content(link)
                doc = {
                    "doc_id": hash(link),
                    "url": link,
                    "title": get_title(content),
                    "content": content,
                    "source_type": detect_type(link),
                    "downloaded_at": now(),
                    "lang": detect_language(content)
                }
                save_to_index(doc)
```

### 3.2 使用ライブラリ例
| 処理         | 使用ライブラリ                            |
|--------------|-------------------------------------------|
| HTML/PDF取得 | `requests`, `playwright`, `pdfminer.six`  |
| リンク抽出   | `beautifulsoup4`, `trafilatura`           |
| MIME判定     | `magic`, `mimetypes`                      |
| 言語判定     | `langdetect`, `fasttext`                  |
| データ保存   | `JSON`, `SQLite`, `LlamaIndex` など        |


### 4. テストケース一覧
| Test ID     | 内容               | 入力              | 期待出力               | 判定基準                             |
|-------------|--------------------|-------------------|------------------------|--------------------------------------|
| TC-CR-001   | PDF取得成功        | PDF URL           | content抽出済み        | contentが空でない                    |
| TC-CR-002   | HTML取得成功       | FDA HTMLページ     | title, content抽出     | `<title>`が正しく取得される         |
| TC-CR-003   | MIMEフィルタ機能   | 画像リンク含むページ | PDF/HTMLのみ取得       | 無関係ファイルが除外されている       |
| TC-CR-004   | 重複排除           | 同一URL 2回       | 1件のみ保存            | 重複はスキップされる                 |
| TC-CR-005   | 言語判定           | EN/JA混在ページ   | lang="en"/"ja"         | 言語が正しく推定される               |
| TC-CR-006   | クロール失敗処理   | 404ページ         | エラー記録             | 処理継続＋ログあり                   |


### 5. 今後の拡張案
PDF構造の章ごとの分割（ガイドライン分類用）

OpenGraph対応（title/description抽出精度向上）

クロール優先度制御（重要度の高いURLから巡回）


---

# インデックスエンジン 詳細仕様書

## 1. 概要

インデックスエンジンは、クローラーによって取得・抽出された医療機器関連の文書（PDF, HTMLなど）を、セクション単位に分割し、全文検索・類似検索を可能にするためのベクトル化とメタデータ付加を行う。ベクトル検索には FAISS や Weaviate を、LLMベースの処理には LlamaIndex を利用する。

## 2. 入出力仕様

### 2.1 入力

| フィールド | 型 | 説明 |
|------------|----|------|
| `doc_id`   | str | 文書の一意なID（クローラー出力） |
| `title`    | str | 文書タイトル |
| `content`  | str | 抽出本文 |
| `source_type` | str | PDF/HTML/DOCXなど |
| `lang`     | str | 言語コード（例：'en', 'ja'） |
| `downloaded_at` | datetime | ダウンロード日時 |

### 2.2 出力

| フィールド | 型 | 説明 |
|------------|-----|------|
| `node_id`  | str  | セクションごとの一意ID |
| `text_chunk` | str | 分割されたテキスト |
| `embedding`  | list[float] | ベクトル埋め込み（LLM由来） |
| `metadata`   | dict | `{"doc_id": ..., "title": ..., "section": ..., "lang": ...}` |


## 3. 処理フロー

### 3.1 処理ステップ

1. 文書のセクション分割（paragraph/chapter単位）
2. 言語ごとにLLM埋め込み（OpenAI Embeddings等）
3. セクションID生成（doc_id + セクション番号）
4. メタデータ付加
5. ベクトルストア（FAISSなど）に登録
6. インデックス更新（既存セクションは差し替え）

### 3.2 擬似コード

```python
for doc in raw_documents:
    sections = split_into_sections(doc["content"])
    for i, chunk in enumerate(sections):
        embedding = embed_model.get_embedding(chunk)
        node = {
            "node_id": f"{doc['doc_id']}_{i}",
            "text_chunk": chunk,
            "embedding": embedding,
            "metadata": {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "section": i,
                "lang": doc["lang"]
            }
        }
        vector_store.add(node)
```


### 4. 使用技術候補

| 処理           | 技術例                                                   |
|----------------|----------------------------------------------------------|
| セクション分割 | `LlamaIndex DocumentParser`, `spaCy`, `re`              |
| 埋め込み生成   | `OpenAI`, `Cohere`, `SentenceTransformer`               |
| ベクトルDB     | `FAISS`, `Weaviate`, `Chroma`, `LlamaIndex`             |
| ストレージ     | `SQLite`, `JSON`, `MongoDB`, `PostgreSQL`               |

### 5. テストケース一覧
| Test ID     | 内容               | 入力                        | 期待出力                    | 判定条件                              |
|-------------|--------------------|-----------------------------|-----------------------------|----------------------------------------|
| TC-IX-001   | 分割処理成功        | 長文テキスト                 | 複数チャンク                | 各チャンクが1000トークン以内           |
| TC-IX-002   | 埋め込み生成        | 英文セクション               | ベクトル（list[float]）     | 長さ512以上、非ゼロ                   |
| TC-IX-003   | メタデータ付与      | 入力文書                     | metadataにtitle/lang含む     | メタデータキーの存在                  |
| TC-IX-004   | ベクトル登録成功    | ベクトル・メタ付きチャンク   | ベクトルDBに追加済み         | ID指定検索で一致                      |
| TC-IX-005   | 言語判定対応        | 英語／日本語混在文書         | langフィールドあり           | 正確な言語推定                        |

### 6. 拡張案
セクションごとに見出しを抽出し section_title をメタ情報として追加

PDFのTOCを活用した構造化

日本語LLM（例：ELYZA, Cluana）への切り替え


---

# ガイドラインエージェント 詳細仕様書

## 1. 概要

ガイドラインエージェントは、インデックスエンジンによって構造化・ベクトル化された医療機器関連文書から、セキュリティ対策に関連する記述を抽出し、既存のフレームワーク（NIST CSF, IEC 62443, FDA等）に分類・整理する役割を担う。分類結果はガイドラインDBに保存され、アセスメントや技術提案の基盤となる。

---

## 2. 入出力仕様

### 2.1 入力

| フィールド | 型 | 説明 |
|------------|----|------|
| `text_chunk` | str | インデックスされたテキストセクション |
| `metadata`   | dict | 出典情報、タイトル、言語、文書種別など |

### 2.2 出力（ガイドラインDB形式）

| フィールド | 型 | 説明 |
|------------|-----|------|
| `guideline_id` | str | 一意なID（doc_id + section） |
| `category`     | str | セキュリティカテゴリ（例：Protect > Access Control） |
| `standard`     | str | 出典規格（例：NIST, FDA, PMDA） |
| `control_text` | str | 抽出されたセキュリティ要求文 |
| `keywords`     | list[str] | 重要語（例："SBOM", "secure boot"） |
| `source_url`   | str | 原文URL（または文書タイトル） |
| `region`       | str | 対象地域（例：US, JP, EU） |

---

## 3. 処理フロー

### 3.1 ステップ概要

1. 類似セクションの検索（例：`“Access Control”` に関するセクション群）
2. セキュリティ対策カテゴリとの関連度をLLMで分類
3. 抽出文に対して出典・地域・キーワードをメタ付加
4. ガイドラインDBへ構造化保存

### 3.2 擬似コード

```python
for node in index.search("security controls"):
    category = classify_control(node.text_chunk)
    keywords = extract_keywords(node.text_chunk)
    region = infer_region(node.metadata["source_url"])
    guideline_entry = {
        "guideline_id": node.node_id,
        "category": category,
        "standard": detect_standard(node.metadata),
        "control_text": node.text_chunk,
        "keywords": keywords,
        "source_url": node.metadata["source_url"],
        "region": region
    }
    guideline_db.insert(guideline_entry)
```

### 4. 使用技術・モデル例
| 処理             | 技術例                                                       |
|------------------|--------------------------------------------------------------|
| 分類             | `OpenAI GPT-4`, `Claude`, 自己教師付きLLM分類器             |
| キーワード抽出   | `spaCy`, `yake`, `re.findall(r"#?\w+")`                      |
| 地域・規格推定   | 文書URLや`title`の正規表現解析                               |
| 保存             | `SQLite`, `PostgreSQL`, `JSON`, `LlamaIndex StorageContext` |


### 5. テストケース一覧
| Test ID     | 内容             | 入力                                | 期待出力                      | 判定条件                            |
|-------------|------------------|-------------------------------------|-------------------------------|-------------------------------------|
| TC-GL-001   | 対策分類         | “All users must be authenticated…” | Protect > Access Control      | カテゴリが正しく分類される         |
| TC-GL-002   | 規格抽出         | URL中に“fda.gov”                    | standard=FDA                  | 規格名が正しく抽出される           |
| TC-GL-003   | 地域推定         | PMDA URL                            | region=JP                     | 対象地域が一致する                 |
| TC-GL-004   | キーワード抽出   | “must implement secure boot”       | ["secure boot"]               | 重要語が含まれている               |
| TC-GL-005   | 重複処理         | 同一セクション2回処理              | 1件のみDB登録                 | ID重複は無視される                 |

### 6. 分類カテゴリ候補（例）
NIST Cybersecurity Framework
Identify > Asset Management

Protect > Access Control

Protect > Data Security

Detect > Anomalies

Respond > Incident Response

IEC 62443
SR 1.x: Identification and authentication control

SR 2.x: Use control

SR 7.x: Resource availability

FDA
Secure design

Software Bill of Materials (SBOM)

Patch Management

Threat modeling

Logging/Audit



###########
# アーキテクチャ

```
+────────────────────────────────────────────────────────────────────────────+
|                          利用者インターフェース（UI）                    |
|  ┌────────────────────────────┐   ┌────────────────────────────┐         |
|  | セキュリティ対策検索画面   │   | リスクアセスメント入力画面 │         |
|  └────────────────────────────┘   └────────────────────────────┘         |
|                   ↓ フロントエンド（React/Vite）                        |
+────────────────────────────────────────────────────────────────────────────+
                                ↓ API呼び出し
+────────────────────────────────────────────────────────────────────────────+
|                        バックエンド（FastAPI）                           |
|                                                                            |
|  ┌──────────────┐ → ┌────────────────┐ → ┌────────────────────┐ → DB保存 |
|  | クローラー     │   | インデックス       │   | ガイド分類             │          |
|  | （週次実行）   │   | （ベクトル化）     │   | （NIST/IEC分類）       │          |
|  └──────────────┘   └────────────────┘   └────────────────────┘          |
|           ↑                              ↓                                 |
|     GitHub Actions               推論エンジン（OpenAI/LLM）              |
+────────────────────────────────────────────────────────────────────────────+
                                ↓
+────────────────────────────────────────────────────────────────────────────+
|                       データベース（SQLite/PostgreSQL）                  |
|  - 原文文書（PDF/HTML）                                                  |
|  - セクション単位のインデックス                                          |
|  - セキュリティ分類タグ                                                  |
|  - メタ情報（出典、発行日、分類）                                        |
+────────────────────────────────────────────────────────────────────────────+
```

## 🔧 技術構成（対応関係）
| 機能             | 技術候補・備考                                                    |
|------------------|---------------------------------------------------------------------|
| フロントエンド   | `React` + `Tailwind CSS` + Markdown表示                            |
| バックエンドAPI  | `FastAPI`（`JWT`認証含む）                                         |
| クローラー       | `Python` + `BeautifulSoup` / `PyMuPDF`                             |
| インデックスエンジン | `LlamaIndex` + `OpenAI` / `SentenceTransformers`              |
| 分類・要約       | `GPT-4`, `GPT-3.5`, `Claude` など（LLM推論）                        |
| 自動実行         | `GitHub Actions` または `cron`                                     |
| ストレージ       | `SQLite` / `PostgreSQL` / ファイルシステム                         |
| メタデータ付与   | `JSON-LD` またはカスタムスキーマ                                   |



