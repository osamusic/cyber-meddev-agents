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

# Load environment variables
load_dotenv()
logger.info("Loading environment variables from .env file")

# Configure OpenAI or OpenRouter
if os.getenv("OPENROUTER_API_KEY"):
    openai.api_type = "openrouter"
    openai.api_key = os.getenv("OPENROUTER_API_KEY")
    API_URL = "https://openrouter.ai/api/v1"
    MODEL = "deepseek/deepseek-r1:free"
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

# Maximum size of document text to send in prompts
max_document_size = int(os.getenv("MAX_DOCUMENT_SIZE", 3000))


def normalize_json(raw: str) -> str:
    """
    Extract only the valid JSON part from a JSON-like string and correct duplicated braces.
    """
    try:
        # Extract only the JSON substring
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("Braces not found")
        json_candidate = raw[start:end]
        # If there are duplicate closing braces '}}' at the end, reduce to one
        json_candidate = re.sub(r"\}\s*\}\s*$", "}", json_candidate)
        return json_candidate
    except Exception as e:
        logger.error(f"JSON normalization error: {str(e)}")
        return raw  # Return as is if normalization fails


class DocumentClassifier:
    """Medical Device Cybersecurity Document Classifier"""

    def __init__(self):
        """Initialize the classifier."""
        self.openai_model = MODEL

        # NIST CSF categories
        self.nist_categories = {
            "ID": "Identify",
            "PR": "Protect",
            "DE": "Detect",
            "RS": "Respond",
            "RC": "Recover"
        }

        # IEC 62443 Foundational Requirements
        self.iec_categories = {
            "FR1": "Identification and authentication control",
            "FR2": "Use control",
            "FR3": "System integrity",
            "FR4": "Data confidentiality",
            "FR5": "Restricted data flow",
            "FR6": "Timely response to events",
            "FR7": "Resource availability"
        }

    def classify_document(self, document_text: str, config: ClassificationConfig) -> Dict[str, Any]:
        """
        Classify the document based on NIST CSF and IEC 62443 frameworks,
        extract security requirements, and identify keywords.
        """
        result: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "frameworks": {},
            "requirements": [],
            "keywords": []
        }

        # Extract security requirements
        requirements_list = self._extract_document(document_text)
        result["requirements"] = requirements_list

        # Prepare text for framework classification
        requirements_text = ""
        if requirements_list:
            requirements_text = "\n".join([
                f"{item.get('id', i + 1)}. [{item.get('type', 'Mandatory')}] {item.get('text', '')}"
                for i, item in enumerate(requirements_list)
            ])

        # Classify against NIST CSF
        result["frameworks"]["NIST_CSF"] = self._classify_nist(requirements_text or document_text)

        # Classify against IEC 62443
        result["frameworks"]["IEC_62443"] = self._classify_iec(requirements_text or document_text)

        # Extract keywords
        result["keywords"] = self._extract_keywords(requirements_text or document_text, config.keyword_config)

        return result

    def _classify_nist(self, document_text: str) -> Dict[str, Any]:
        """Classify text according to the NIST Cybersecurity Framework."""
        prompt = f"""
            You are an expert in medical device cybersecurity.
            Analyze the following text and classify it into the NIST Cybersecurity Framework categories in English.

            NIST Categories:
            - ID: Identify (Asset Management, Business Environment, Governance, Risk Assessment, Risk Management Strategy)
            - PR: Protect (Access Control, Awareness and Training, Data Security, Information Protection Processes and Procedures, Maintenance, Protective Technology)
            - DE: Detect (Anomalies and Events, Continuous Security Monitoring, Detection Processes)
            - RS: Respond (Response Planning, Communications, Analysis, Mitigation, Improvements)
            - RC: Recover (Recovery Planning, Improvements, Communications)

            Text:
            {document_text[:max_document_size]}

            Please respond with valid JSON only, without any extra text or line breaks, in the following format:
            {{
                "categories": {{
                    "ID": {{ "score": 0, "reason": "reason" }},
                    "PR": {{ "score": 0, "reason": "reason" }},
                    "DE": {{ "score": 0, "reason": "reason" }},
                    "RS": {{ "score": 0, "reason": "reason" }},
                    "RC": {{ "score": 0, "reason": "reason" }}
                }},
                "primary_category": "MostRelevantCategoryCode",
                "explanation": "Summary of analysis and reasoning"
            }}
            """
        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert in medical device cybersecurity. Please respond only in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            json_text = normalize_json(response.choices[0].message.content)
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"NIST classification JSON parse error: {str(e)}")
            return {
                "categories": {k: {"score": 0, "reason": "Parse error"} for k in self.nist_categories},
                "primary_category": "Error",
                "explanation": f"An error occurred during JSON parsing: {str(e)}"
            }
        except Exception as e:
            logger.error(f"NIST classification error: {str(e)}")
            return {
                "categories": {k: {"score": 0, "reason": "Classification error"} for k in self.nist_categories},
                "primary_category": "Error",
                "explanation": f"An error occurred during classification: {str(e)}"
            }

    def _classify_iec(self, document_text: str) -> Dict[str, Any]:
        """Classify text according to IEC 62443 Foundational Requirements."""
        prompt = f"""
            You are an expert in medical device cybersecurity.
            Analyze the following text and classify it into the IEC 62443 Foundational Requirements in English.

            IEC 62443 Foundational Requirements:
            - FR1: Identification and authentication control
            - FR2: Use control
            - FR3: System integrity
            - FR4: Data confidentiality
            - FR5: Restricted data flow
            - FR6: Timely response to events
            - FR7: Resource availability

            Text:
            {document_text[:max_document_size]}

            Please respond with valid JSON only, without any extra text or line breaks, in the following format:
            {{
                "requirements": {{
                    "FR1": {{ "score": 0, "reason": "reason" }},
                    "FR2": {{ "score": 0, "reason": "reason" }},
                    "FR3": {{ "score": 0, "reason": "reason" }},
                    "FR4": {{ "score": 0, "reason": "reason" }},
                    "FR5": {{ "score": 0, "reason": "reason" }},
                    "FR6": {{ "score": 0, "reason": "reason" }},
                    "FR7": {{ "score": 0, "reason": "reason" }}
                }},
                "primary_requirement": "MostRelevantRequirementCode",
                "explanation": "Summary of analysis and reasoning"
            }}
            """
        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert in medical device cybersecurity. Please respond only in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            json_text = normalize_json(response.choices[0].message.content)
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"IEC classification JSON parse error: {str(e)}")
            return {
                "requirements": {k: {"score": 0, "reason": "Parse error"} for k in self.iec_categories},
                "primary_requirement": "Error",
                "explanation": f"An error occurred during JSON parsing: {str(e)}"
            }
        except Exception as e:
            logger.error(f"IEC classification error: {str(e)}")
            return {
                "requirements": {k: {"score": 0, "reason": "Classification error"} for k in self.iec_categories},
                "primary_requirement": "Error",
                "explanation": f"An error occurred during classification: {str(e)}"
            }

    def _extract_document(self, document_text: str) -> List[Dict[str, Any]]:
        """Extract security requirements from the document text."""
        prompt = f"""
            You are an expert in medical device cybersecurity.
            The text below contains “Recommendations” and “Mandatory requirements (Obligations)” related to security measures.
            From this text, extract the security **requirements (security measures)** and list them in the following format:
            - Specify whether each requirement is “Mandatory” or “Recommended”
            - Summarize the original point concisely (not a direct quote, but as a structured requirement statement)
            Text:
            {document_text[:max_document_size]}
            Please respond in the following JSON format. Return only valid JSON:

            {{
                "requirements": [
                    {{
                        "id": 1,
                        "type": "Mandatory",
                        "text": "Use multi-factor authentication for user authentication"
                    }},
                    {{
                        "id": 2,
                        "type": "Recommended",
                        "text": "Install a firewall on external interfaces"
                    }},
                    {{
                        "id": 3,
                        "type": "Mandatory",
                        "text": "Store logs in a tamper-evident format"
                    }}
                ]
            }}
            """
        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert in medical device cybersecurity."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            json_text = normalize_json(response.choices[0].message.content)
            result = json.loads(json_text)
            return result.get("requirements", [])
        except Exception as e:
            logger.error(f"Requirement extraction error: {str(e)}")
            return []

    def _extract_keywords(self, document_text: str, config: KeywordExtractionConfig) -> List[Dict[str, Any]]:
        """Extract critical security keywords related to medical device cybersecurity."""
        prompt = f"""
            You are an expert in medical device cybersecurity.
            Extract important keywords related to medical device cybersecurity from the text below.

            Text:
            {document_text[:max_document_size]}

            Extract keywords that meet the following criteria:
            - Related to medical device cybersecurity
            - High importance
            - At least {config.min_keyword_length} characters long
            - Up to {config.max_keywords} keywords

            For each keyword, include importance (1-10) and a brief description.

            Please respond in the following JSON format. Return only valid JSON, without extra text or commas:

            {{
                "keywords": [
                    {{
                        "keyword": "keyword1",
                        "importance": 10,
                        "description": "Description"
                    }}
                ]
            }}
            """
        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert in medical device cybersecurity. Please respond only in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            json_text = normalize_json(response.choices[0].message.content)
            result = json.loads(json_text)
            return result.get("keywords", [])
        except Exception as e:
            logger.error(f"Keyword extraction error: {str(e)}")
            return [{"keyword": "error", "importance": 0, "description": f"An error occurred during keyword extraction: {str(e)}"}]
