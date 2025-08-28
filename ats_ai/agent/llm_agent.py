import json
import os
import re

from dotenv import load_dotenv
from langchain_community.document_loaders import PyMuPDFLoader
from openai import OpenAI
from pydantic import BaseModel

from ats_ai.agent.prompts import (
    RESUME_PARSE_PROMPT,
    calculate_weighted_score_and_status,
    get_dynamic_evaluation_prompt,
)

"""
    Using LLM chaining workflow to parse, evaluate, and validate resume and given job description
    to create a robust and accurate assessment of a candidate.
    1. extract_resume_info : extract_resume_info()
    2. evaluate_resume_against_jd : evaluate_resume_against_jd()
    3. Combined Evaluation Agent: combined_parse_evaluate()
"""

load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Define structured schema for parsed resume info
class ParsedResume(BaseModel):
    Name: str
    Contact_Details: dict
    Github_Repo: str
    LinkedIn: str
    Education: list
    Professional_Experience: list
    Projects: list
    Certifications: list
    Programming_Language: list[str]
    Frameworks: list[str]
    Technologies: list[str]


class ResumeEvaluation(BaseModel):
    Evaluation_Summary: dict
    Strengths_and_Weaknesses: dict
    Skill_Analysis: dict
    Key_Considerations: dict


def load_pdf_text(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return " ".join(page.page_content for page in pages)


def extract_json_block(text: str) -> dict:
    # Find JSON-like object
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise json.JSONDecodeError("No JSON object found", text, 0)

    raw_json = match.group()
    return json.loads(raw_json)


async def extract_resume_info(raw_resume_text: str):
    """Parse information from resume into JSON"""
    prompt = RESUME_PARSE_PROMPT.format(raw_resume_text=raw_resume_text)

    response = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.0)

    return extract_json_block(response.choices[0].message.content)


#
# # new added
# def get_experience_from_jd_json(jd_json: dict) -> float:
#     """Extract minimum required experience directly from JD JSON field"""
#
#     # Debug: Print the entire JD JSON structure
#     print("=== DEBUG: JD JSON KEYS ===")
#     print("Available keys:", list(jd_json.keys()))
#     print("=== END DEBUG ===")
#
#     # Check if Minimum_Experience exists (exact spelling)
#     if "Minimum_Experience" in jd_json:
#         value = jd_json["Minimum_Experience"]
#         print(f"Found 'Minimum_Experience' with value: '{value}' (type: {type(value)})")
#
#         # Handle different data types
#         if isinstance(value, (int, float)):
#             return float(value)
#         elif isinstance(value, str):
#             # Parse string like "5+ years", "3-5 years", "5", etc.
#             if value.strip().lower() in ["na", "n/a", "", "none", "not specified"]:
#                 return 0.0
#
#             # Try to extract number from string
#             import re
#
#             # Look for just numbers first
#             number_match = re.search(r"(\d+(?:\.\d+)?)", value.strip())
#             if number_match:
#                 return float(number_match.group(1))
#
#             # If no number found, return 0
#             return 0.0
#     else:
#         print("'Minimum_Experience' key not found in JD JSON")
#
#         # Check for similar keys (case variations, typos)
#         for key in jd_json.keys():
#             if "experience" in key.lower() or "minimum" in key.lower():
#                 print(f"Found similar key: '{key}' with value: '{jd_json[key]}'")
#
#     # Fallback
#     return 0.0
#
#
# def calculate_total_experience_years(professional_experience):
#     """
#     Calculate total years of experience from professional experience list
#     Handles various date formats and overlapping positions
#     """
#     if not professional_experience or len(professional_experience) == 0:
#         return 0.0
#
#     experience_periods = []
#     current_year = datetime.now().year
#     current_month = datetime.now().month
#
#     print(f"DEBUG: Current date: {current_month}/{current_year}")
#     print(f"DEBUG: Processing {len(professional_experience)} experience entries")
#
#     for i, exp in enumerate(professional_experience):
#         if isinstance(exp, dict):
#             duration = exp.get("Duration", "")
#             company = exp.get("Company", "Unknown")
#             role = exp.get("Role", "Unknown")
#         elif isinstance(exp, str):
#             duration = exp
#             company = "Unknown"
#             role = "Unknown"
#         else:
#             continue
#
#         if not duration or duration.strip().lower() in ["na", "n/a", ""]:
#             continue
#
#         print(f"DEBUG: Entry {i + 1} - {role} at {company}")
#         print(f"DEBUG: Duration string: '{duration}'")
#
#         # Parse duration string
#         # duration_years = parse_duration_to_years(duration, current_year, current_month)
#         duration_years = parse_duration_to_years(duration, current_year, current_month, "auto")
#         print(f"DEBUG: Parsed years: {duration_years}")
#
#         if duration_years > 0:
#             experience_periods.append(duration_years)
#
#             # Calculate total experience from earliest start to latest end
#             # Smart overlap detection and calculation
#             # Month-level overlap detection
#             if experience_periods:
#                 # Parse actual month ranges for overlap detection
#                 # Parse actual month ranges for overlap detection
#                 month_ranges = []
#                 has_present = False
#
#                 for exp in professional_experience:
#                     duration = exp.get("Duration", "") if isinstance(exp, dict) else str(exp)
#                     duration_lower = duration.lower()
#
#                     # Check for Present
#                     if "present" in duration_lower or "current" in duration_lower:
#                         has_present = True
#
#                     # Parse MM/DD/YYYY - MM/DD/YYYY format (your main format)
#                     range_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})\s*(?:[-–—]|to)\s*(\d{1,2})/(\d{1,2})/(\d{4})", duration_lower)
#                     if range_match:
#                         start_month, start_year = int(range_match.group(1)), int(range_match.group(3))
#                         end_month, end_year = int(range_match.group(4)), int(range_match.group(6))
#                         month_ranges.append(((start_year, start_month), (end_year, end_month)))
#                     # Parse MM/YYYY - MM/YYYY format
#                     elif re.search(r"(\d{1,2})/(\d{4})\s*(?:[-–—]|to)\s*(\d{1,2})/(\d{4})", duration_lower):
#                         range_match = re.search(r"(\d{1,2})/(\d{4})\s*(?:[-–—]|to)\s*(\d{1,2})/(\d{4})", duration_lower)
#                         start_month, start_year = int(range_match.group(1)), int(range_match.group(2))
#                         end_month, end_year = int(range_match.group(3)), int(range_match.group(4))
#                         month_ranges.append(((start_year, start_month), (end_year, end_month)))
#                     # Parse Present cases
#                     elif "present" in duration_lower:
#                         present_match = re.search(r"(\d{1,2})/(?:\d{1,2}/)?(\d{4})", duration_lower)
#                         if present_match:
#                             start_month = int(present_match.group(1))
#                             start_year = int(present_match.group(2))
#                             month_ranges.append(((start_year, start_month), (current_year, current_month)))
#
#                 # Check for month-level overlaps
#                 has_month_overlap = False
#                 for i in range(len(month_ranges)):
#                     for j in range(i + 1, len(month_ranges)):
#                         start1, end1 = month_ranges[i]
#                         start2, end2 = month_ranges[j]
#
#                         # Check if periods overlap: start1 <= end2 and start2 <= end1
#                         # if start1 <= end2 and start2 <= end1:
#                         #     has_month_overlap = True
#                         #     break
#                         # Convert to comparable format (year, month) for precise overlap detection
#                         start1_val = start1[0] * 12 + start1[1]
#                         end1_val = end1[0] * 12 + end1[1]
#                         start2_val = start2[0] * 12 + start2[1]
#                         end2_val = end2[0] * 12 + end2[1]
#
#                         # TRUE overlap: periods actually share working time (not just adjacent)
#                         overlap_start = max(start1_val, start2_val)
#                         overlap_end = min(end1_val, end2_val)
#
#                         if overlap_start < overlap_end:  # Changed from <= to < for true overlap
#                             overlap_months = overlap_end - overlap_start
#                             print(f"DEBUG: TRUE overlap found: {overlap_months} months")
#                             has_month_overlap = True
#                             break
#                     if has_month_overlap:
#                         break
#
#                 if has_month_overlap:
#                     # True overlap: use timeline from earliest to latest
#                     all_years = []
#                     for exp in professional_experience:
#                         duration = exp.get("Duration", "") if isinstance(exp, dict) else str(exp)
#                         years_found = re.findall(r"\b(20\d{2}|19\d{2})\b", duration)
#                         all_years.extend(int(y) for y in years_found)
#
#                     earliest_year = min(all_years)
#                     if has_present:
#                         total_years = current_year - earliest_year
#                     else:
#                         latest_year = max(all_years)
#                         total_years = latest_year - earliest_year + 1
#                     print(f"DEBUG: Month-level overlap detected, timeline: {total_years} years")
#                 else:
#                     # No overlap: sum individual periods
#                     total_years = sum(experience_periods)
#                     print(f"DEBUG: No month overlap, summing: {total_years} years")
#             else:
#                 total_years = 0.0
#
#     print(f"DEBUG: Individual periods: {experience_periods}")
#     print(f"DEBUG: Calculated total (overlap-adjusted): {total_years}")
#
#     return round(total_years, 1)
#
#
# def parse_duration_to_years(duration_str, current_year, current_month, date_format="MM/DD/YYYY"):
#     """
#     Enhanced parser for duration strings with better handling of explicit durations
#     FIXED: Better Present calculation and month handling
#     """
#     duration_str = duration_str.strip()
#     original_duration = duration_str  # Keep original for debugging
#     duration_str = duration_str.lower()
#
#     print(f"DEBUG: Parsing duration: '{original_duration}'")
#     # Auto-detect date format if needed
#     if date_format == "auto":
#         # Look for clear indicators to determine format
#         if re.search(r"\b(1[3-9]|[2-3]\d)/\d{1,2}/\d{4}\b", original_duration):  # Day > 12 in first position
#             date_format = "DD/MM/YYYY"
#             print("DEBUG: Auto-detected DD/MM/YYYY format")
#         elif re.search(r"\b\d{1,2}/(1[3-9]|[2-3]\d)/\d{4}\b", original_duration):  # Day > 12 in second position
#             date_format = "MM/DD/YYYY"
#             print("DEBUG: Auto-detected MM/DD/YYYY format")
#         else:
#             date_format = "MM/DD/YYYY"  # Default to US format
#             print("DEBUG: Using default MM/DD/YYYY format")
#
#     # PRIORITY 1: Handle explicit durations in parentheses first (most reliable)
#     # Pattern: "06/2025 - Present (0.4 years)" or "07/2022 - 05/2025 (2.9 years)"
#     explicit_years = re.search(r"\((\d+(?:\.\d+)?)\s*years?\)", duration_str)
#     if explicit_years:
#         years = float(explicit_years.group(1))
#         print(f"DEBUG: Found explicit years in parentheses: {years}")
#         return years
#
#     explicit_months = re.search(r"\((\d+(?:\.\d+)?)\s*months?\)", duration_str)
#     if explicit_months:
#         months = float(explicit_months.group(1))
#         years = months / 12.0
#         print(f"DEBUG: Found explicit months in parentheses: {months} -> {years} years")
#         return years
#
#     present_patterns = [
#         # "06/2025 to Present/Current", "10/2018 - Present" etc.
#         r"(\d{1,2})/(\d{4})\s*(?:[-–—]|to)\s*(?:present|current)",
#         r"(\w+)\s+(\d{4})\s*(?:[-–—]|to)\s*(?:present|current)",
#         # Handle MM/DD/YYYY format for Present
#         r"(\d{1,2})/(\d{1,2})/(\d{4})\s*(?:[-–—]|to)\s*(?:present|current)",
#     ]
#
#     for pattern in present_patterns:
#         match = re.search(pattern, duration_str)
#         if match:
#             if len(match.groups()) == 3:  # MM/DD/YYYY - Present format
#                 if date_format == "DD/MM/YYYY":
#                     start_day = int(match.group(1))
#                     start_month = int(match.group(2))
#                 else:  # MM/DD/YYYY (default)
#                     start_month = int(match.group(1))
#                     start_day = int(match.group(2))
#                 start_year = int(match.group(3))
#                 print(f"DEBUG: Detected full date format for Present: {start_month}/{start_day}/{start_year}")
#             elif "/" in pattern:
#                 start_month = int(match.group(1))
#                 start_year = int(match.group(2))
#
#             else:
#                 start_month_str = match.group(1)
#                 start_year = int(match.group(2))
#
#                 # Convert month name to number
#                 month_map = {
#                     "jan": 1,
#                     "january": 1,
#                     "feb": 2,
#                     "february": 2,
#                     "mar": 3,
#                     "march": 3,
#                     "apr": 4,
#                     "april": 4,
#                     "may": 5,
#                     "jun": 6,
#                     "june": 6,
#                     "jul": 7,
#                     "july": 7,
#                     "aug": 8,
#                     "august": 8,
#                     "sep": 9,
#                     "september": 9,
#                     "oct": 10,
#                     "october": 10,
#                     "nov": 11,
#                     "november": 11,
#                     "dec": 12,
#                     "december": 12,
#                 }
#                 start_month = month_map.get(start_month_str.lower()[:3], 1)
#
#             total_months = (current_year - start_year) * 12 + (current_month - start_month)
#
#             # Add 1 to include the current month
#             total_months += 1
#
#             years = max(total_months / 12.0, 0)
#
#             print(f"DEBUG: Present calculation - Start: {start_month}/{start_year}, Current: {current_month}/{current_year}")
#             print(f"DEBUG: Years diff: {current_year - start_year}, Months diff: {current_month - start_month}")
#             print(f"DEBUG: Total months (including current): {total_months}, Years: {years}")
#             return years
#
#     # PRIORITY 3: Handle completed date ranges - IMPROVED
#     completed_patterns = [
#         # "11/01/2011 - 09/30/2022" (MM/DD/YYYY - MM/DD/YYYY format)
#         r"(\d{1,2})/(\d{1,2})/(\d{4})\s*(?:[-–—]|to)\s*(\d{1,2})/(\d{1,2})/(\d{4})",
#         # "07/2022 - 05/2025", "08/2016 - 10/2018", "07/2022 to 05/2025" (MM/YYYY - MM/YYYY format)
#         r"(\d{1,2})/(\d{4})\s*(?:[-–—]|to)\s*(\d{1,2})/(\d{4})",
#         # "June 2012 - March 2021" (Month YYYY - Month YYYY format)
#         r"(\w+)\s+(\d{4})\s*(?:[-–—]|to)\s*(\w+)\s+(\d{4})",
#     ]
#
#     for pattern in completed_patterns:
#         match = re.search(pattern, duration_str)
#         if match:
#             if "/" in pattern and len(match.groups()) == 6:  # MM/DD/YYYY format
#                 if date_format == "DD/MM/YYYY":
#                     # start_day = int(match.group(1))
#                     start_month = int(match.group(2))
#                     # end_day = int(match.group(4))
#                     end_month = int(match.group(5))
#                 else:  # MM/DD/YYYY (default)
#                     start_month = int(match.group(1))
#                     # start_day = int(match.group(2))
#                     end_month = int(match.group(4))
#                     # end_day = int(match.group(5))
#                 start_year = int(match.group(3))
#                 end_year = int(match.group(6))
#             elif "/" in pattern and len(match.groups()) == 4:  # MM/YYYY format
#                 # existing MM/YYYY logic stays the same # MM/YYYY format
#                 start_month = int(match.group(1))
#                 start_year = int(match.group(2))
#                 end_month = int(match.group(3))
#                 end_year = int(match.group(4))
#             else:  # Month YYYY format
#                 start_month_str = match.group(1)
#                 start_year = int(match.group(2))
#                 end_month_str = match.group(3)
#                 end_year = int(match.group(4))
#
#                 month_map = {
#                     "jan": 1,
#                     "january": 1,
#                     "feb": 2,
#                     "february": 2,
#                     "mar": 3,
#                     "march": 3,
#                     "apr": 4,
#                     "april": 4,
#                     "may": 5,
#                     "jun": 6,
#                     "june": 6,
#                     "jul": 7,
#                     "july": 7,
#                     "aug": 8,
#                     "august": 8,
#                     "sep": 9,
#                     "september": 9,
#                     "oct": 10,
#                     "october": 10,
#                     "nov": 11,
#                     "november": 11,
#                     "dec": 12,
#                     "december": 12,
#                 }
#                 start_month = month_map.get(start_month_str.lower()[:3], 1)
#                 end_month = month_map.get(end_month_str.lower()[:3], 1)
#
#             # Calculate total months including both start and end months
#             total_months = (end_year - start_year) * 12 + (end_month - start_month) + 1
#             years = max(total_months / 12.0, 0)
#
#             print(f"DEBUG: Date range calculation - Start: {start_month}/{start_year}, End: {end_month}/{end_year}")
#             print(f"DEBUG: Total months (inclusive): {total_months}, Years: {years}")
#             return years
#
#     # # PRIORITY 4: Simple year ranges like "2023 - 2024"
#     # year_range = re.search(r"(\d{4})\s*(?:[-–—]|to)\s*(\d{4})", duration_str)
#     # PRIORITY 4: Simple year ranges like "2023 - 2024"
#     year_range = re.search(r"(\d{4})\s*(?:[-–—]|to)\s*(\d{4})", duration_str)
#     if year_range:
#         start_year = int(year_range.group(1))
#         end_year = int(year_range.group(2))
#         years = max(end_year - start_year, 0)  # Remove +1 for more realistic calculation
#         print(f"DEBUG: Year range: {start_year}-{end_year} -> {years} years")
#         return years
#
#     # FALLBACK: Only as last resort and with better validation
#     print(f"DEBUG: No date patterns matched, trying fallback extraction for: '{original_duration}'")
#
#     # Look for reasonable year numbers but NOT part of dates
#     # Avoid matching things like "06/2025" by requiring word boundaries or specific contexts
#     fallback_patterns = [
#         r"\b(\d+(?:\.\d+)?)\s*years?\b",  # "3.5 years", "2 years"
#         r"\b(\d+(?:\.\d+)?)\s*yrs?\b",  # "3 yrs", "2.5 yr"
#     ]
#
#     for pattern in fallback_patterns:
#         matches = re.findall(pattern, duration_str)
#         if matches:
#             for num_str in matches:
#                 val = float(num_str)
#                 if 0.1 <= val <= 50:  # Reasonable range for years
#                     print(f"DEBUG: Fallback found explicit years mention: {val}")
#                     return val
#
#     # If still no match, look for month mentions
#     month_patterns = [
#         r"\b(\d+(?:\.\d+)?)\s*months?\b",
#         r"\b(\d+(?:\.\d+)?)\s*mos?\b",
#     ]
#
#     for pattern in month_patterns:
#         matches = re.findall(pattern, duration_str)
#         if matches:
#             for num_str in matches:
#                 val = float(num_str)
#                 if 1 <= val <= 600:  # 1 month to 50 years in months
#                     years = val / 12.0
#                     print(f"DEBUG: Fallback found months: {val} -> {years} years")
#                     return years
#
#     print(f"DEBUG: No valid duration found in: '{original_duration}'")
#     return 0.0
#
#
# # Test function to verify the fix
# def test_experience_calculation():
#     """Test function to verify the experience calculation"""
#     test_experiences = [
#         {
#             "Duration": "11/2021 – Present",
#             "Company": "Digital Banking Platform (Confidential)",
#             "Role": "Technical Program Manager",
#             "Experience": "Ongoing (~46 months ≈ 3 years 10 months as of Aug 2025)",
#             "Highlights": [
#                 "Led a $25M portfolio, managing digital banking platform and transaction processing initiatives.",
#                 "Oversaw multiple cross-functional teams (80+ resources) to ensure successful delivery."
#             ],
#         },
#         {
#             "Duration": "01/2019 – 11/2021",
#             "Company": "Intuitive Surgical",
#             "Role": "Senior Technical Program Manager",
#             "Experience": "35 months ≈ 2 years 11 months",
#             "Highlights": [
#                 "Spearheaded a $20M ERP modernization program implementing SAP S/4 HANA.",
#                 "Managed global teams (50+ resources) across multiple regions."
#             ],
#         },
#         {
#             "Duration": "12/2017 – 01/2019",
#             "Company": "Charter Communication",
#             "Role": "Senior Technical Delivery Program Manager",
#             "Experience": "14 months ≈ 1 year 2 months",
#             "Highlights": [
#                 "Directed end-to-end delivery of large-scale, cross-functional technology integration.",
#                 "Oversaw billing system migration combining Oracle BRM with in-house build system."
#             ],
#         },
#         {
#             "Duration": "01/2017 – 12/2017",
#             "Company": "Comcast",
#             "Role": "Senior Technical Program Manager",
#             "Experience": "12 months ≈ 1 year",
#             "Highlights": [
#                 "Led a $15M cloud migration project for digital applications.",
#                 "Optimized financial operations and reporting with a 50+ resource team."
#             ],
#         },
#         {
#             "Duration": "01/2016 – 12/2016",
#             "Company": "LexisNexis",
#             "Role": "Technical Program Manager",
#             "Experience": "12 months ≈ 1 year",
#             "Highlights": [
#                 "Managed end-to-end delivery of Tibco middleware migration to SOA Oracle.",
#                 "Coordinated across 8 business units with 40+ resources."
#             ],
#         }
#     ]
#
#
#
#     total_years = calculate_total_experience_years(test_experiences)
#     print(f"\nFINAL RESULT: Total Experience = {total_years} years")
#     return total_years
#
#
# experience = test_experience_calculation()
# print(f"The calculated experience is: {experience}")
#
#
# def extract_jd_required_experience(jd_json):
#     """
#     Extract required experience from JD JSON in various formats
#     Returns minimum required years as float
#     """
#
#     # Check various possible keys where experience might be stored
#     possible_keys = ["minimum_experience", "Minimum_Experience"]
#
#     experience_text = ""
#
#     # Search through different sections of JD
#     for key in possible_keys:
#         if key in jd_json:
#             value = jd_json[key]
#             if isinstance(value, str):
#                 experience_text += " " + value.lower()
#             elif isinstance(value, list):
#                 experience_text += " " + " ".join([str(item).lower() for item in value])
#             elif isinstance(value, dict):
#                 for subkey, subvalue in value.items():
#                     if "experience" in subkey.lower():
#                         experience_text += " " + str(subvalue).lower()
#
#     # Also check in job description text if available
#     if "job_description" in jd_json:
#         experience_text += " " + str(jd_json["job_description"]).lower()
#
#     if "description" in jd_json:
#         experience_text += " " + str(jd_json["description"]).lower()
#
#     # Parse experience requirements from text
#     return parse_experience_requirement(experience_text)
#
#
# def parse_experience_requirement(text):
#     """
#     Parse experience requirement text and extract minimum years
#     """
#     import re
#
#     text = text.lower().strip()
#     if not text:
#         return 0.0
#
#     # Patterns to match experience requirements
#     patterns = [
#         # "5+ years", "5 + years", "minimum 5 years"
#         r"(?:minimum|min|at least|atleast)\s*(\d+)(?:\+|\s*plus)?\s*years?",
#         r"(\d+)\s*\+\s*years?",
#         r"(\d+)\s*plus\s*years?",
#         # "5-7 years", "5 to 7 years"
#         r"(\d+)(?:\s*[-–]\s*\d+|\s+to\s+\d+)\s*years?",
#         # "5 years experience"
#         r"(\d+)\s*years?\s*(?:of\s*)?(?:experience|exp)",
#         # "experience: 5 years"
#         r"experience:?\s*(\d+)\s*years?",
#         # Handle ranges like "2-3 years" - take the minimum
#         r"(\d+)[-–](\d+)\s*years?",
#     ]
#
#     for pattern in patterns:
#         matches = re.findall(pattern, text)
#         if matches:
#             # Take the first match (usually the minimum requirement)
#             if isinstance(matches[0], tuple):
#                 # For range patterns, take the minimum
#                 return float(min(matches[0]))
#             else:
#                 return float(matches[0])
#
#     # Fallback: look for any mention of years
#     year_matches = re.findall(r"(\d+)\s*years?", text)
#     if year_matches:
#         # Return the smallest reasonable number (likely minimum requirement)
#         years = [float(y) for y in year_matches if 1 <= float(y) <= 20]
#         if years:
#             return min(years)
#
#     return 0.0


async def combined_parse_evaluate(resume_data: str, job_description: dict, weightage_config=None):
    """
    Parse and Evaluate Candidate resume with Job Description with custom weightage
    Enhanced with experience years calculation and qualification logic
    - returns Dict[str, Any]: JSON object containing evaluation and parsed result
    """
    # Use default weightage if not provided
    if weightage_config is None:
        from pydantic import BaseModel

        class DefaultWeightageConfig(BaseModel):
            experience_weight: float = 0.3
            skills_weight: float = 0.4
            education_weight: float = 0.1
            projects_weight: float = 0.2

        weightage_config = DefaultWeightageConfig()

    # Generate enhanced prompt with experience calculation
    prompt = get_dynamic_evaluation_prompt(resume_data, job_description, weightage_config)

    response = openai_client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], temperature=0.0, top_p=0.9)

    print("=== RAW RESPONSE ===")
    print(response.choices[0].message.content)
    print("=== END RAW RESPONSE ===")

    # Parse the initial response to get individual scores and experience data
    parsed_response = extract_json_block(response.choices[0].message.content)

    print("=== PARSED RESPONSE ===")
    print(json.dumps(parsed_response, indent=2))
    print("=== END PARSED RESPONSE ===")
    # After line where you get parsed_response, add this:
    if "Parsed_Resume" in parsed_response:
        professional_exp = parsed_response["Parsed_Resume"].get("Professional_Experience", [])
        calculated_total_exp = 0.0

        for exp in professional_exp:
            if isinstance(exp, dict):
                duration_str = exp.get("Duration", "")
                # Look for pattern like "(0.5 years)" in duration string
                if "(" in duration_str and "years)" in duration_str:
                    try:
                        start_idx = duration_str.find("(") + 1
                        end_idx = duration_str.find(" years)")
                        years_value = float(duration_str[start_idx:end_idx])
                        calculated_total_exp += years_value
                    except (ValueError, IndexError):
                        continue
        calculated_total_exp = round(calculated_total_exp, 1)
        print(f"Calculated total experience: {calculated_total_exp}")

    # Extract experience information from LLM response and validate with our functions
    try:
        if "Evaluation" in parsed_response:
            evaluation = parsed_response["Evaluation"]

            # GET LLM'S DIRECT MATCH PERCENTAGE - ADD THIS LINE
            llm_match_percentage = evaluation.get("Match_Percentage", None)

            # Get LLM's calculation
            # evaluation.get("Total_Experience_Years", 0.0)
            # llm_jd_required_experience = evaluation.get("JD_Required_Experience_Years", 0.0)

            experience_score = evaluation["Experience_Score"]
            skills_score = evaluation["Skills_Score"]
            education_score = evaluation["Education_Score"]
            projects_score = evaluation["Projects_Score"]

            # Use LLM calculated experience values directly
            # candidate_total_experience = evaluation.get("Total_Experience_Years", 0.0)
            # With this:
            candidate_total_experience = calculated_total_exp if calculated_total_exp > 0 else evaluation.get("Total_Experience_Years", 0.0)
            jd_required_experience = evaluation.get("JD_Required_Experience_Years", 0.0)

        else:
            # Fallback to our own calculations if LLM didn't provide experience data
            print("LLM didn't provide experience data, calculating ourselves...")
            llm_match_percentage = None  # ADD THIS LINE
            candidate_total_experience = 0.0
            # jd_required_experience = extract_jd_required_experience(job_description)
            experience_score = parsed_response.get("Experience_Score", 0.0)
            skills_score = parsed_response.get("Skills_Score", 0.0)
            education_score = parsed_response.get("Education_Score", 0.0)
            projects_score = parsed_response.get("Projects_Score", 0.0)

            # Try to calculate from parsed resume if available
            if "Parsed_Resume" in parsed_response:
                parsed_response["Parsed_Resume"].get("Professional_Experience", [])
                # candidate_total_experience = calculate_total_experience_years(resume_experience)

    except KeyError as e:
        print(f"KeyError accessing scores: {e}")
        print(f"Available keys in parsed_response: {list(parsed_response.keys())}")

        # Fallback values with our own calculations
        llm_match_percentage = None  # ADD THIS LINE
        candidate_total_experience = 0.0
        # jd_required_experience = get_experience_from_jd_json(job_description)
        experience_score = 0.0
        skills_score = 0.0
        education_score = 0.0
        projects_score = 0.0
    # Determine if projects are valid based on parsed resume data
    try:
        if "Parsed_Resume" in parsed_response:
            projects = parsed_response["Parsed_Resume"].get("Projects", [])
        else:
            projects = parsed_response.get("Projects", [])
    except (KeyError, TypeError):
        projects = []

    # Check if projects are valid
    has_valid_projects = False
    if projects and len(projects) > 0:
        if isinstance(projects[0], dict):
            # Dictionary format: {"Title": "...", "Description": "..."}
            first_project = projects[0]
            title = first_project.get("Title", first_project.get("Project_Name", ""))
            description = first_project.get("Description", first_project.get("Project_Description", ""))
            has_valid_projects = title not in ["NA", "N/A", "", None] and description not in ["NA", "N/A", "", None] and len(str(description)) > 10
        elif isinstance(projects[0], str):
            # String format: direct project names
            has_valid_projects = projects[0] not in ["NA", "N/A", "", None] and len(projects[0]) > 10

    # Use enhanced calculation that includes experience years comparison
    calculation_result = calculate_weighted_score_and_status(
        experience_score=experience_score,
        skills_score=skills_score,
        education_score=education_score,
        projects_score=projects_score,
        candidate_total_experience_years=candidate_total_experience,
        jd_required_experience_years=jd_required_experience,
        has_valid_projects=has_valid_projects,
        experience_weight=weightage_config.experience_weight,
        skills_weight=weightage_config.skills_weight,
        education_weight=weightage_config.education_weight,
        projects_weight=weightage_config.projects_weight,
        llm_match_percentage=llm_match_percentage,
    )
    # Create a standardized response structure
    if "Evaluation" not in parsed_response:
        # If the response doesn't have the nested structure, create it
        evaluation_data = {
            "Total_Experience_Years": candidate_total_experience,
            "JD_Required_Experience_Years": jd_required_experience,
            "Experience_Score": experience_score,
            "Skills_Score": skills_score,
            "Education_Score": education_score,
            "Projects_Score": projects_score,
            "Overall_Weighted_Score": calculation_result["overall_weighted_score"],
            "Match_Percentage": calculation_result["match_percentage"],
            "Qualification Status": calculation_result["qualification_status"],
            "Pros": parsed_response.get("Pros", []),
            "Cons": parsed_response.get("Cons", []),
            "Skills Match": parsed_response.get("Skills Match", parsed_response.get("Skills_Match", [])),
            "Required_Skills_Missing_from_Resume": parsed_response.get("Required_Skills_Missing_from_Resume", []),
            "Extra skills": parsed_response.get("Extra skills", parsed_response.get("Extra_Skills", [])),
            "Summary": parsed_response.get("Summary", ""),
        }

        # Create the standardized response structure
        standardized_response = {"Evaluation": evaluation_data, "Parsed_Resume": parsed_response.get("Parsed_Resume", {})}

        return standardized_response
    else:
        # Update the existing nested structure with calculated values and experience info
        parsed_response["Evaluation"]["Total_Experience_Years"] = candidate_total_experience
        parsed_response["Evaluation"]["JD_Required_Experience_Years"] = jd_required_experience
        parsed_response["Evaluation"]["Overall_Weighted_Score"] = calculation_result["overall_weighted_score"]
        parsed_response["Evaluation"]["Match_Percentage"] = calculation_result["match_percentage"]
        parsed_response["Evaluation"]["Qualification Status"] = calculation_result["qualification_status"]

        return parsed_response
