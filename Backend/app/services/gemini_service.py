import re
import json
import logging
from typing import List, Dict, Any
from google import genai
from app.config import get_settings

logger = logging.getLogger("skillsetu.gemini_service")

def clean_json_markdown(text: str) -> str:
    """Removes ```json ... ``` code fence markers and trims surrounding whitespace."""
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return text.strip()

def generate_fallback_mcqs(competency_area: str, title: str) -> List[Dict[str, Any]]:
    """
    Generates domain-aware fallback MCQs for MoSPI statistical competencies if AI service is unavailable.
    Guarantees demo readiness under all conditions.
    """
    logger.info(f"Generating domain fallback MCQs for competency: {competency_area}")
    
    comp_lower = competency_area.lower()
    
    if "survey" in comp_lower or "design" in comp_lower:
        return [
            {
                "question": "What is the primary objective of pre-testing a questionnaire in survey design?",
                "options": [
                    "To estimate total survey budget",
                    "To identify ambiguous questions and field response difficulties",
                    "To train enumerators on coding responses",
                    "To calculate final sample size weights"
                ],
                "correct_index": 1,
                "explanation": "Pre-testing identifies confusing terminology, questionnaire routing issues, and respondent burden prior to full deployment."
            },
            {
                "question": "Which type of question bias occurs when respondents answer in a manner to be viewed favorably?",
                "options": [
                    "Recall Bias",
                    "Social Desirability Bias",
                    "Selection Bias",
                    "Non-response Bias"
                ],
                "correct_index": 1,
                "explanation": "Social desirability bias leads respondents to over-report good behavior and under-report undesirable traits."
            },
            {
                "question": "In structured survey instruments, what does a filter/skip question control?",
                "options": [
                    "Data encryption protocols",
                    "Flow of questions based on respondent eligibility",
                    "Geographic stratification boundaries",
                    "Post-stratification weighting adjustments"
                ],
                "correct_index": 1,
                "explanation": "Filter questions direct respondents past irrelevant questions based on prior answers."
            },
            {
                "question": "What is non-sampling error in statistical surveys?",
                "options": [
                    "Error arising purely from taking a sample instead of census",
                    "Errors occurring during data collection, entry, or non-response",
                    "Mathematical rounding error in variance calculation",
                    "Standard error of the population mean"
                ],
                "correct_index": 1,
                "explanation": "Non-sampling errors occur due to human mistakes, measurement errors, non-response, or bad data entry."
            },
            {
                "question": "Which method is best suited for reducing respondent fatigue in long statistical schedules?",
                "options": [
                    "Increasing total question count",
                    "Questionnaire split-module modularization",
                    "Mandatory strict timed responses",
                    "Eliminating skip patterns"
                ],
                "correct_index": 1,
                "explanation": "Modularizing schedules into shorter sub-sections prevents fatigue and maintains response accuracy."
            }
        ]
    elif "field" in comp_lower or "data collection" in comp_lower:
        return [
            {
                "question": "In CAPI (Computer-Assisted Personal Interviewing), what is real-time validation checks used for?",
                "options": [
                    "Preventing out-of-range numerical entries at time of survey",
                    "Speeding up hardware processor speeds",
                    "Creating paper backups automatically",
                    "Calculating final GDP metrics"
                ],
                "correct_index": 0,
                "explanation": "CAPI real-time validation catches range errors and logical contradictions immediately in the field."
            },
            {
                "question": "What is the primary role of a primary sampling unit (PSU) field supervisor?",
                "options": [
                    "Writing federal legislation",
                    "Re-interviewing a subsample for quality verification",
                    "Designing statistical software code",
                    "Selling survey publications"
                ],
                "correct_index": 1,
                "explanation": "Field supervisors conduct spot checks and re-interviews to verify data authenticity."
            },
            {
                "question": "When encountering a closed household during enumeration, what is standard protocol?",
                "options": [
                    "Immediately replace with next-door neighbor without recording",
                    "Make required repeat visits at different time slots before replacement",
                    "Fabricate household responses",
                    "Cancel the entire sample block"
                ],
                "correct_index": 1,
                "explanation": "Protocol requires scheduled revisit attempts to minimize non-response bias."
            },
            {
                "question": "Which metadata field is essential for verifying CAPI field enumeration locations?",
                "options": [
                    "Device Wi-Fi password",
                    "GPS coordinates & interview timestamp",
                    "Monitor screen resolution",
                    "Battery consumption level"
                ],
                "correct_index": 1,
                "explanation": "GPS coordinates and timestamps ensure auditability of enumerator field visits."
            },
            {
                "question": "What does unit non-response refer to in data collection?",
                "options": [
                    "A respondent skipping one optional question",
                    "Entire selected unit/household failing to participate",
                    "A server breakdown during transfer",
                    "Translation errors in questionnaire"
                ],
                "correct_index": 1,
                "explanation": "Unit non-response occurs when no data is gathered from an eligible sampled unit."
            }
        ]
    else:
        return [
            {
                "question": f"Based on the material '{title}', what is a fundamental statistical rule for data reliability?",
                "options": [
                    "Ignoring outlier values completely",
                    "Ensuring representative sampling and minimal measurement error",
                    "Relying solely on convenience sampling",
                    "Falsifying missing records"
                ],
                "correct_index": 1,
                "explanation": "Representative sampling and error reduction form the cornerstone of statistical reliability."
            },
            {
                "question": "What is the key indicator of statistical variance in a dataset?",
                "options": [
                    "The spread of data points relative to the mean",
                    "The color formatting of the data table",
                    "The speed of database queries",
                    "The total number of survey pages"
                ],
                "correct_index": 0,
                "explanation": "Variance measures how far numbers in a data set are spread out from their average value."
            },
            {
                "question": "Why is data anonymization mandatory in official statistics?",
                "options": [
                    "To save storage disk space",
                    "To protect respondent confidentiality and legal compliance",
                    "To accelerate machine learning training speed",
                    "To hide survey mistakes"
                ],
                "correct_index": 1,
                "explanation": "Official statistical protocols mandate respondent privacy protection."
            },
            {
                "question": "What does a confidence interval of 95% signify?",
                "options": [
                    "95% of survey questions were answered correctly",
                    "If sampling is repeated, 95% of intervals will contain true population parameter",
                    "The survey cost is 95% under budget",
                    "95 respondents were sampled in total"
                ],
                "correct_index": 1,
                "explanation": "A 95% confidence interval estimates population parameters under repeated sampling."
            },
            {
                "question": "In statistical analysis, what is a primary source of data?",
                "options": [
                    "Data collected directly from respondents first-hand",
                    "Data copied from third-party blogs",
                    "Extrapolated predictions from synthetic models",
                    "Historical textbooks published 50 years ago"
                ],
                "correct_index": 0,
                "explanation": "Primary data is original data gathered specifically for the research purpose at hand."
            }
        ]

async def generate_mcqs_from_text(text: str, competency_area: str, title: str, num_questions: int = 5) -> List[Dict[str, Any]]:
    """
    Calls Google Gemini API (google-genai SDK) to generate structured MCQs from provided material text.
    GAP FIX #3: Migrated from deprecated google-generativeai to google-genai package.
    Falls back to domain-specific questions if API call fails or key is unconfigured.
    """
    settings = get_settings()
    
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("mock_"):
        logger.info("No valid GEMINI_API_KEY found. Utilizing domain fallback generator.")
        return generate_fallback_mcqs(competency_area, title)
        
    try:
        # GAP FIX #3: Use the current google-genai client API (replaces deprecated google-generativeai)
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""
You are an expert assessment generator for India's Official Statistical System (MoSPI capacity building).
Analyze the following learning material tagged with the competency area '{competency_area}' and title '{title}'.

Generate exactly {num_questions} high-quality multiple-choice questions (MCQs) testing understanding of the core concepts in the text.

Return ONLY a valid JSON array of objects, with NO markdown formatting around it, matching this schema:
[
  {{
    "question": "Detailed question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Brief clear explanation of why this answer is correct."
  }}
]

Important rules:
1. 'correct_index' must be an integer between 0 and 3 corresponding to the correct option index.
2. 'options' must be a list of exactly 4 distinct strings.
3. Do not include markdown code block syntax like ```json.

Learning Material:
\"\"\"
{text[:4000]}
\"\"\"
"""
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        cleaned_text = clean_json_markdown(response.text)
        
        parsed_mcqs = json.loads(cleaned_text)
        
        # Validate schema structure
        if isinstance(parsed_mcqs, list) and len(parsed_mcqs) > 0:
            valid_mcqs = []
            for item in parsed_mcqs:
                if "question" in item and "options" in item and "correct_index" in item:
                    valid_mcqs.append({
                        "question": str(item["question"]),
                        "options": [str(opt) for opt in item["options"][:4]],
                        "correct_index": int(item["correct_index"]),
                        "explanation": str(item.get("explanation", ""))
                    })
            if len(valid_mcqs) > 0:
                logger.info(f"Successfully generated {len(valid_mcqs)} MCQs via Gemini API.")
                return valid_mcqs

        logger.warning("Gemini response parsing returned invalid structure. Falling back.")
        return generate_fallback_mcqs(competency_area, title)
        
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}. Falling back to domain MCQ generator.")
        return generate_fallback_mcqs(competency_area, title)
