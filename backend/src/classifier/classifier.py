import os
import re
import logging
import json
from typing import List, Dict, Any
import openai
from openai import OpenAI

from datetime import datetime
from dotenv import load_dotenv

from .models import ClassificationConfig, KeywordExtractionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
logger.info("Loading environment variables from .env file")
if os.getenv("OPENROUTER_API_KEY"):
    openai.api_type = "openrouter"
    openai.api_key = os.getenv("OPENROUTER_API_KEY")
    API_URL = "https://openrouter.ai/api/v1"
    MODEL = "deepseek/deepseek-chat-v3-0324:free"
    logger.info(f"Using OpenRouter model: {MODEL}")
else:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai.api_type = "openai"
    API_URL = "https://api.openai.com/v1"
    MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logger.info(f"Using OpenAI model: {MODEL}")

if not openai.api_key:
    logger.warning("API_KEY environment variable not set")

client = OpenAI(
    api_key=openai.api_key,
    base_url=API_URL,
)

max_document_size = os.getenv("MAX_DOCUMENT_SIZE", 4000)


class DocumentClassifier:
    """医療機器サイバーセキュリティドキュメント分類器"""

    def __init__(self):
        """分類器の初期化"""
        self.openai_model = MODEL
#        self.api_key = os.getenv("OPENAI_API_KEY")

        self.nist_categories = {
            "ID": "Identify（特定）",
            "PR": "Protect（防御）",
            "DE": "Detect（検知）",
            "RS": "Respond（対応）",
            "RC": "Recover（復旧）"
        }

        self.iec_categories = {
            "FR1": "Identification and authentication control（識別と認証制御）",
            "FR2": "Use control（使用制御）",
            "FR3": "System integrity（システム完全性）",
            "FR4": "Data confidentiality（データ機密性）",
            "FR5": "Restricted data flow（制限されたデータフロー）",
            "FR6": "Timely response to events（イベントへのタイムリーな対応）",
            "FR7": "Resource availability（リソース可用性）"
        }

    def classify_document(self, document_text: str, config: ClassificationConfig) -> Dict[str, Any]:
        """ドキュメントをNISTとIECフレームワークに基づいて分類"""
        frameworks = config.frameworks
        result = {
            "timestamp": datetime.now().isoformat(),
            "frameworks": {},
            "keywords": [],
            "summary": "",
            "intermediate_results": {}  # 中間結果を保存するための新しいフィールド
        }

        intermediate_results = {}

        for framework in frameworks:
            if framework == "NIST_CSF":
                nist_result = self._classify_nist(document_text)
                result["frameworks"]["NIST_CSF"] = nist_result
                intermediate_results["NIST_CSF_raw"] = nist_result  # 中間結果を保存
            elif framework == "IEC_62443":
                iec_result = self._classify_iec(document_text)
                result["frameworks"]["IEC_62443"] = iec_result
                intermediate_results["IEC_62443_raw"] = iec_result  # 中間結果を保存

        keywords = self._extract_keywords(document_text, config.keyword_config)
        result["keywords"] = keywords
        intermediate_results["keywords_raw"] = keywords  # 中間結果を保存

        summary = self._summarize_document(document_text)
        result["summary"] = summary
        intermediate_results["summary_raw"] = summary  # 中間結果を保存

        result["intermediate_results"] = intermediate_results

        return result

    def _classify_nist(self, document_text: str) -> Dict[str, Any]:
        """NISTサイバーセキュリティフレームワークに基づいて分類"""
        prompt = f"""
        あなたは医療機器サイバーセキュリティの専門家です。
        以下のテキストを分析し、NISTサイバーセキュリティフレームワークのカテゴリに分類してください。

        NISTカテゴリ:
        - ID: Identify（特定）- 資産管理、ビジネス環境、ガバナンス、リスク評価、リスク管理戦略
        - PR: Protect（防御）- アクセス制御、意識向上とトレーニング、データセキュリティ、情報保護プロセス、保守、保護技術
        - DE: Detect（検知）- 異常とイベント、継続的なセキュリティモニタリング、検出プロセス
        - RS: Respond（対応）- 対応計画、コミュニケーション、分析、緩和、改善
        - RC: Recover（復旧）- 復旧計画、改善、コミュニケーション

        テキスト:
        {document_text[:max_document_size]}

        各カテゴリの関連度を0から10の数値で評価し、最も関連性の高いカテゴリを特定してください。
        また、その判断理由を簡潔に説明してください。

        以下のJSON形式で回答してください。有効なJSONのみを返してください。
        特に余分なテキスト、説明、コンマの使用に注意してください:
        {{
            "categories": {{
                "ID": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "PR": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "DE": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "RS": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "RC": {{
                    "score": 0,
                    "reason": "理由"
                }}
            }},
            "primary_category": "最も関連性の高いカテゴリコード",
            "explanation": "全体的な分析と判断理由の要約"
        }}

        必ず有効なJSON形式で回答してください。余分なテキストや改行を含めないでください。
        """

        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "あなたは医療機器サイバーセキュリティの専門家です。有効なJSON形式でのみ回答してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content
            match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.S)
            json_text = match.group(1) if match else raw
            result = json.loads(json_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"NIST分類JSON解析エラー: {str(e)}")
            logger.error(
                f"レスポンス内容: {response.choices[0].message.content if 'response' in locals() and hasattr(response, 'choices') else 'レスポンスなし'}"
            )
            return {
                "categories": {
                    "ID": {"score": 0, "reason": "JSON解析エラー"},
                    "PR": {"score": 0, "reason": "JSON解析エラー"},
                    "DE": {"score": 0, "reason": "JSON解析エラー"},
                    "RS": {"score": 0, "reason": "JSON解析エラー"},
                    "RC": {"score": 0, "reason": "JSON解析エラー"}
                },
                "primary_category": "エラー",
                "explanation": f"JSON解析中にエラーが発生しました: {str(e)}"
            }
        except Exception as e:
            logger.error(f"NIST分類エラー: {str(e)}")
            return {
                "categories": {
                    "ID": {"score": 0, "reason": "分類エラー"},
                    "PR": {"score": 0, "reason": "分類エラー"},
                    "DE": {"score": 0, "reason": "分類エラー"},
                    "RS": {"score": 0, "reason": "分類エラー"},
                    "RC": {"score": 0, "reason": "分類エラー"}
                },
                "primary_category": "エラー",
                "explanation": f"分類処理中にエラーが発生しました: {str(e)}"
            }

    def _classify_iec(self, document_text: str) -> Dict[str, Any]:
        """IEC 62443に基づいて分類"""
        prompt = f"""
        あなたは医療機器サイバーセキュリティの専門家です。
        以下のテキストを分析し、IEC 62443の基本要件（Foundational Requirements）に分類してください。

        IEC 62443の基本要件:
        - FR1: Identification and authentication control（識別と認証制御）
        - FR2: Use control（使用制御）
        - FR3: System integrity（システム完全性）
        - FR4: Data confidentiality（データ機密性）
        - FR5: Restricted data flow（制限されたデータフロー）
        - FR6: Timely response to events（イベントへのタイムリーな対応）
        - FR7: Resource availability（リソース可用性）

        テキスト:
        {document_text[:max_document_size]}

        各基本要件の関連度を0から10の数値で評価し、最も関連性の高い要件を特定してください。
        また、その判断理由を簡潔に説明してください。

        以下のJSON形式で回答してください。有効なJSONのみを返してください。特に余分なテキスト、説明、コンマの使用に注意してください:
        {{
            "requirements": {{
                "FR1": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "FR2": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "FR3": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "FR4": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "FR5": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "FR6": {{
                    "score": 0,
                    "reason": "理由"
                }},
                "FR7": {{
                    "score": 0,
                    "reason": "理由"
                }}
            }},
            "primary_requirement": "最も関連性の高い要件コード",
            "explanation": "全体的な分析と判断理由の要約"
        }}

        必ず有効なJSON形式で回答してください。余分なテキストや改行を含めないでください。
        """

        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "あなたは医療機器サイバーセキュリティの専門家です。有効なJSON形式でのみ回答してください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            raw = response.choices[0].message.content
            match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.S)
            json_text = match.group(1) if match else raw
            result = json.loads(json_text)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"IEC分類JSON解析エラー: {str(e)}")
            logger.error(f"レスポンス内容: {response.choices[0].message.content if 'response' in locals() and hasattr(response, 'choices') else 'レスポンスなし'}")
            return {
                "requirements": {
                    "FR1": {"score": 0, "reason": "JSON解析エラー"},
                    "FR2": {"score": 0, "reason": "JSON解析エラー"},
                    "FR3": {"score": 0, "reason": "JSON解析エラー"},
                    "FR4": {"score": 0, "reason": "JSON解析エラー"},
                    "FR5": {"score": 0, "reason": "JSON解析エラー"},
                    "FR6": {"score": 0, "reason": "JSON解析エラー"},
                    "FR7": {"score": 0, "reason": "JSON解析エラー"}
                },
                "primary_requirement": "エラー",
                "explanation": f"JSON解析中にエラーが発生しました: {str(e)}"
            }
        except Exception as e:
            logger.error(f"IEC分類エラー: {str(e)}")
            return {
                "requirements": {
                    "FR1": {"score": 0, "reason": "分類エラー"},
                    "FR2": {"score": 0, "reason": "分類エラー"},
                    "FR3": {"score": 0, "reason": "分類エラー"},
                    "FR4": {"score": 0, "reason": "分類エラー"},
                    "FR5": {"score": 0, "reason": "分類エラー"},
                    "FR6": {"score": 0, "reason": "分類エラー"},
                    "FR7": {"score": 0, "reason": "分類エラー"}
                },
                "primary_requirement": "エラー",
                "explanation": f"分類処理中にエラーが発生しました: {str(e)}"
            }

    def _extract_keywords(self, document_text: str, config: KeywordExtractionConfig) -> List[Dict[str, Any]]:
        """セキュリティキーワードの抽出"""
        prompt = f"""
        あなたは医療機器サイバーセキュリティの専門家です。
        以下のテキストから医療機器のサイバーセキュリティに関連する重要なキーワードを抽出してください。

        テキスト:
        {document_text[:max_document_size]}


        以下の条件を満たすキーワードを抽出してください:
        - 医療機器のサイバーセキュリティに関連していること
        - 重要度が高いこと
        - 最低{config.min_keyword_length}文字以上であること
        - 最大{config.max_keywords}個まで

        各キーワードについて、重要度（1-10）と簡単な説明を付けてください。

        以下のJSON形式で回答してください:
        {{
            "keywords": [
                {{
                    "keyword": "キーワード1",
                    "importance": 1-10,
                    "description": "説明"
                }},
                ...
            ]
        }}
        """

        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "あなたは医療機器サイバーセキュリティの専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content
            match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.S)
            json_text = match.group(1) if match else raw
            result = json.loads(json_text)
            return result.get("keywords", [])
        except Exception as e:
            logger.error(f"キーワード抽出エラー: {str(e)}")
            return [{"keyword": "エラー", "importance": 0, "description": f"キーワード抽出中にエラーが発生しました: {str(e)}"}]

    def _summarize_document(self, document_text: str) -> str:
        """ドキュメントの要約"""
        prompt = f"""
        あなたは医療機器サイバーセキュリティの専門家です。
        以下のテキストを医療機器のサイバーセキュリティの観点から要約してください。

        テキスト:
        {document_text[:max_document_size]}

        以下の点に注目して要約してください:
        - 主要なセキュリティ対策や推奨事項
        - 重要なリスクや脅威
        - 規制やコンプライアンスに関する情報
        - 実装に関する具体的なガイダンス

        400字程度で簡潔に要約してください。
        """

        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは医療機器サイバーセキュリティの専門家です。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=500
            )

            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"要約エラー: {str(e)}")
            return f"要約中にエラーが発生しました: {str(e)}"
