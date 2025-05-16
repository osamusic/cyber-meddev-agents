import os
import re
import logging
import json
from typing import List, Dict, Any

from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnableSequence
from langchain.schema import AIMessage

from datetime import datetime
from dotenv import load_dotenv

from .models import ClassificationConfig, KeywordExtractionConfig
from .prompt import nist_prompt, iec_prompt, extract_prompt, keywords_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Loading environment variables from .env file")

# Determine model provider
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "false").lower() == "true"
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
API_TEMPERATURE = float(os.getenv("API_TEMPERATURE", 0.1))

# API Keys and Endpoints
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")

# Maximum text size for prompts
max_document_size = int(os.getenv("MAX_DOCUMENT_SIZE", 3000))


def get_chat_model():
    """Factory to return the appropriate chat model based on configuration."""
    if USE_OPENROUTER:
        logger.info("Using OpenRouter provider for LLM")
        return ChatOpenAI(
            model_name=MODEL_NAME,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base=OPENROUTER_API_BASE,
            temperature=API_TEMPERATURE
        )
    logger.info("Using OpenAI provider for LLM")
    return ChatOpenAI(
        model_name=MODEL_NAME,
        openai_api_key=OPENAI_API_KEY,
        temperature=API_TEMPERATURE
    )


# Initialize LangChain Chat model
document_chat_model = get_chat_model()


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

    # Use class-level model attribute to ensure availability
    model = document_chat_model

    def classify_document(self, document_text: str, config: ClassificationConfig) -> Dict[str, Any]:
        result = {"timestamp": datetime.now().isoformat(), "frameworks": {}, "requirements": [], "keywords": []}

        # Extract security requirements
        reqs = self._extract_document(document_text)
        result["requirements"] = reqs

        # Prepare text for classification and keyword extraction
        text_for_fw = "\n".join([f"{r['id']}. [{r['type']}] {r['text']}" for r in reqs]) or document_text

        # Classify into frameworks
        result["frameworks"]["NIST_CSF"] = self._classify_nist(text_for_fw)
        result["frameworks"]["IEC_62443"] = self._classify_iec(text_for_fw)

        # Extract keywords using the provided KeywordExtractionConfig
        result["keywords"] = self._extract_keywords(text_for_fw, config.keyword_config)

        return result

    def _classify_nist(self, document_text: str) -> Dict[str, Any]:
        prompt_text = document_text[:max_document_size]
        sequence = RunnableSequence(nist_prompt, self.model)
        raw = sequence.invoke({"text": prompt_text})
        if isinstance(raw, AIMessage):
            raw = raw.content
        try:
            return json.loads(normalize_json(raw))
        except Exception as e:
            logger.error(f"NIST parse error: {e}")
            return {}

    def _classify_iec(self, document_text: str) -> Dict[str, Any]:
        prompt_text = document_text[:max_document_size]
        sequence = RunnableSequence(iec_prompt, self.model)
        raw = sequence.invoke({"text": prompt_text})
        if isinstance(raw, AIMessage):
            raw = raw.content
        try:
            return json.loads(normalize_json(raw))
        except Exception as e:
            logger.error(f"IEC parse error: {e}")
            return {}

    def _extract_document(self, document_text: str) -> List[Dict[str, Any]]:
        prompt_text = document_text[:max_document_size]
        sequence = RunnableSequence(extract_prompt, self.model)
        raw = sequence.invoke({"text": prompt_text})
        if isinstance(raw, AIMessage):
            raw = raw.content
        try:
            data = json.loads(normalize_json(raw))
            return data.get("requirements", [])
        except Exception as e:
            logger.error(f"Extract error: {e}")
            return []

    def _extract_keywords(self, document_text: str, keyword_config: KeywordExtractionConfig) -> List[Dict[str, Any]]:
        prompt_text = document_text[:max_document_size]
        sequence = RunnableSequence(keywords_prompt, self.model)
        raw = sequence.invoke({"text": prompt_text, "min_length": keyword_config.min_keyword_length, "max_kws": keyword_config.max_keywords})
        if isinstance(raw, AIMessage):
            raw = raw.content
        try:
            data = json.loads(normalize_json(raw))
            return data.get("keywords", [])
        except Exception as e:
            logger.error(f"Keywords error: {e}")
            return []
