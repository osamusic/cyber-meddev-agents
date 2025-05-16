from langchain.prompts import PromptTemplate
from typing import List

# Prompt templates for DocumentClassifier

NIST_TEMPLATE = """
You are an expert in medical device cybersecurity.
Analyze the following text and classify it into the NIST Cybersecurity Framework categories in English.

NIST Categories:
- ID: Identify (Asset Management, Business Environment, Governance, Risk Assessment, Risk Management Strategy)
- PR: Protect (Access Control, Awareness and Training, Data Security, Information Protection Processes and Procedures, Maintenance, Protective Technology)
- DE: Detect (Anomalies and Events, Continuous Security Monitoring, Detection Processes)
- RS: Respond (Response Planning, Communications, Analysis, Mitigation, Improvements)
- RC: Recover (Recovery Planning, Improvements, Communications)

Text:
{text}

Please respond with valid JSON only, in the format:
{{
    "categories": {{"ID": {{"score": 0, "reason": ""}}, "PR": {{"score": 0, "reason": ""}}, "DE": {{"score": 0, "reason": ""}}, "RS": {{"score": 0, "reason": ""}}, "RC": {{"score": 0, "reason": ""}}}},
    "primary_category": "",
    "explanation": ""
}}"""

IEC_TEMPLATE = """
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
{text}

Please respond with valid JSON only, in the format:
{{
    "requirements": {{"FR1": {{"score": 0, "reason": ""}}, "FR2": {{"score": 0, "reason": ""}}, "FR3": {{"score": 0, "reason": ""}}, "FR4": {{"score": 0, "reason": ""}}, "FR5": {{"score": 0, "reason": ""}}, "FR6": {{"score": 0, "reason": ""}}, "FR7": {{"score": 0, "reason": ""}}}},
    "primary_requirement": "",
    "explanation": ""
}}"""

EXTRACT_TEMPLATE = """
You are an expert in medical device cybersecurity.
The text below contains “Recommendations” and “Mandatory requirements (Obligations)” related to security measures.

Text:
{text}

Extract security requirements from this text and list them as structured items.
Respond in JSON:
{{
  "requirements": [{{"id": 1, "type": "", "text": ""}}]
}}"""

KEYWORDS_TEMPLATE = """
You are an expert in medical device cybersecurity.
Extract important keywords related to medical device cybersecurity from the text below.
At least {min_length} characters long, up to {max_kws} keywords.

Text:
{text}

Respond in JSON:
{{
  "keywords": [{{"keyword": "", "importance": 0, "description": ""}}]
}}"""

# Factory for PromptTemplate instances


def build_prompt(input_vars: List[str], template: str) -> PromptTemplate:
    """Helper to create a PromptTemplate with given variables and template text."""
    return PromptTemplate(input_variables=input_vars, template=template)


# Pre-built PromptTemplate objects
nist_prompt = build_prompt(["text"], NIST_TEMPLATE)
iec_prompt = build_prompt(["text"], IEC_TEMPLATE)
extract_prompt = build_prompt(["text"], EXTRACT_TEMPLATE)
keywords_prompt = build_prompt(["text", "min_length", "max_kws"], KEYWORDS_TEMPLATE)
