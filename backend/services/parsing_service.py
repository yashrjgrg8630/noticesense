import re

def clean_extracted_text(raw_text: str) -> str:
    """
    Cleans raw OCR text by removing page headers, excess whitespace,
    and noisy OCR garbage lines based on character heuristics.
    """
    lines = raw_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
            
        # 1. Remove obvious page headers/footers
        if re.search(r'(?:---\s*Page\s*\d+\s*---|^\s*Page\s*\d+\s*$)', stripped, re.IGNORECASE):
            continue
            
        # 2. Filter lines with very low alphabetical ratio (OCR garbage)
        alpha_count = sum(c.isalpha() for c in stripped)
        if len(stripped) > 10 and alpha_count / len(stripped) < 0.3:
            continue
            
        # 3. Remove repeated institution address footers or known garbage
        if re.search(r'(?:Telephone\s*No|Tel\s*No|Fax\s*No|Email|Website)\s*[\.:].*', stripped, re.IGNORECASE):
            continue
            
        if "Foreign Exchange Department, Central Office" in stripped or "Shahid Bhagat Singh Road" in stripped:
            continue
            
        cleaned_lines.append(stripped)
        
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Remove multiple spaces/newlines
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    cleaned_text = re.sub(r'[ \t]{2,}', ' ', cleaned_text)
    
    return cleaned_text.strip()

def determine_document_type(cleaned_text: str) -> str:
    """
    Dynamically identifies the document type based on keywords.
    """
    text_upper = cleaned_text.upper()
    first_part = text_upper[:1500]
    
    if "COURT" in first_part and ("ORDER" in first_part or "VS." in first_part or "HEARING" in first_part):
        return "Court Notice"
    elif "RESERVE BANK" in first_part or "RBI" in first_part or "CIRCULAR" in first_part or "REGULATION" in first_part:
        return "Regulatory Circular"
    elif "NOTICE" in first_part and ("LEGAL" in first_part or "ACT" in first_part):
        return "Legal Notice"
    elif "SYLLABUS" in first_part or "COURSE" in first_part or "SEMESTER" in first_part or "UNIVERSITY" in first_part:
        return "Academic Document"
        
    return "unknown"

def extract_regulatory_legal_data(cleaned_text: str, doc_type: str) -> dict:
    """
    Extracts structured fields for regulatory, legal, and court notices.
    """
    data = {
        "document_type": doc_type,
        "issuing_authority": None,
        "reference_number": None,
        "date": None,
        "subject_line": None,
        "legal_references": [],
        "effective_date": None,
        "signatory_details": None,
        "raw_cleaned_text": cleaned_text
    }
    
    # Issuing Authority
    from_match = re.search(r'(?:From|Issued by|Authority|By order of)\s*[:-]\s*(.+?)(?=\n|$)', cleaned_text, re.IGNORECASE)
    if from_match:
        data["issuing_authority"] = from_match.group(1).strip()
    elif "RESERVE BANK OF INDIA" in cleaned_text.upper():
        data["issuing_authority"] = "RESERVE BANK OF INDIA"
        
    # Circular/Notification/Reference Number
    ref_match = re.search(r'(?:Ref\.?\s*No\.?|Reference|File\.?\s*No\.?|No\.?|Circular No\.?|[A-Z]{2,4}/\d{4}-\d{2}/\d+)\b(.*?)', cleaned_text, re.IGNORECASE)
    rbi_match = re.search(r'([A-Z]{3,4}/\d{4}-\d{2}/\d+)', cleaned_text)
    if rbi_match:
         data["reference_number"] = rbi_match.group(1).strip()
    elif ref_match:
        data["reference_number"] = ref_match.group(1).strip().split('\n')[0][:100]
        
    # Date — capture full rest-of-line after "Date:" or "Dated:" (handles spaces in dates)
    date_match = re.search(r'(?:Date|Dated)\s*[:-]\s*([^\n]{4,40})', cleaned_text, re.IGNORECASE)
    if not date_match:
        # Full written date: "March 15, 2026" / "15 March 2026"
        date_match = re.search(
            r'\b((?:\d{1,2}(?:st|nd|rd|th)?\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b',
            cleaned_text, re.IGNORECASE)
    if not date_match:
        # Numeric: 15/03/2026 or 15-03-2026 or 15.03.2026
        date_match = re.search(r'\b(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4})\b', cleaned_text)
    if date_match:
        try:
            raw_date = date_match.group(1).strip()
            # Strip ordinal suffixes (1st, 2nd, 3rd, 15th → 15)
            raw_date = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', raw_date, flags=re.IGNORECASE)
            # Trim any trailing junk after the year
            raw_date = re.sub(r'(\d{4}).*', r'\1', raw_date).strip()
            data["date"] = raw_date
        except IndexError:
            data["date"] = date_match.group(0).strip()

            
    # Subject
    salutation_match = re.search(r'(?:Madam\s*/\s*Sir|Dear\s+Sir|Dear\s+Madam|Sir\s*/\s*Madam|Sir,|Madam,)\s*\n+(.+?)(?=\n\n|\n[A-Z0-9])', cleaned_text, re.IGNORECASE | re.DOTALL)
    if salutation_match:
        subj = salutation_match.group(1).strip()
        data["subject_line"] = re.sub(r'\s+', ' ', subj)[:500]
    else:
        subject_match = re.search(r'(?:Subject|Sub\.?|Ref\.?)\s*[:-]?\s*(.+?)(?=\n\s*\n|\Z)', cleaned_text, re.IGNORECASE | re.DOTALL)
        if subject_match:
            subj = subject_match.group(1).strip()
            data["subject_line"] = re.sub(r'\s+', ' ', subj)[:500]
        else:
            fallback_subject = re.search(r'Reporting under.*?Borrowing \(ECB\)', cleaned_text, re.IGNORECASE | re.DOTALL)
            if fallback_subject:
                 subj = fallback_subject.group(0).strip()
                 data["subject_line"] = re.sub(r'\s+', ' ', subj)
             
    # Normalize text for multi-line regex matching (remove mid-sentence newlines)
    normalized_text = re.sub(r'(?<!\n)\n(?!\n)', ' ', cleaned_text)
             
    # Referenced Acts or Sections
    acts_matches = re.finditer(r'([A-Z][a-zA-Z\s]+Act(?:,\s*\d{4})?)', normalized_text)
    for match in acts_matches:
        act = match.group(1).strip()
        act = re.sub(r'\s+', ' ', act)  # Clean internal spaces
        if act not in data["legal_references"] and len(act.split()) > 1:
            data["legal_references"].append(act)
            
    sections_matches = re.finditer(r'(?:section|sections)\s+(\d+(?:\(\d+[a-zA-Z]*\))?(?:,\s*\d+(?:\(\d+[a-zA-Z]*\))?)*)', normalized_text, re.IGNORECASE)
    for match in sections_matches:
         sec = f"Section(s) {match.group(1).strip()}"
         if sec not in data["legal_references"]:
             data["legal_references"].append(sec)

    # Effective Date
    effective_match = re.search(r'(?:come into force|effective|applicable)\s+(?:with|from|on)\s+(.+?)(?=\.|and|\n)', cleaned_text, re.IGNORECASE)
    if effective_match:
        data["effective_date"] = effective_match.group(1).strip()
        
    # Signatory details
    signatory_match = re.search(r'(?:Yours faithfully|Sincerely|Sd/-)[,\s]*\n+.*?\(?([A-Za-z\s\.]+)\)?', cleaned_text, re.IGNORECASE)
    if signatory_match:
        data["signatory_details"] = signatory_match.group(1).strip()
        
    return data

def extract_unknown_data(cleaned_text: str, doc_type: str) -> dict:
    """
    Extracts generic fields if document type is unknown or academic.
    Uses generic structure exactly as requested.
    """
    # If the document is academic, we simply treat it as unknown/generic
    # as all syllabus-specific logic must be removed.
    data = {
        "document_type": doc_type if doc_type == "unknown" else "unknown",
        "issuer": None,
        "reference_number": None,
        "date": None,
        "subject": None,
        "raw_cleaned_text": cleaned_text
    }
    
    # Generic extraction attempts
    date_match = re.search(r'\b(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b', cleaned_text)
    if date_match:
        data["date"] = date_match.group(1).strip()
        
    ref_match = re.search(r'(?:Ref|No|ID)[\.\s:-]+([A-Za-z0-9/-]+)', cleaned_text, re.IGNORECASE)
    if ref_match:
         data["reference_number"] = ref_match.group(1).strip()
         
    return data

def extract_structured_data(cleaned_text: str) -> dict:
    """
    Main router for extracting structured data based on document type.
    """
    doc_type = determine_document_type(cleaned_text)
    
    # Process supported legal/regulatory entities, fallback to pure generic schema
    if doc_type in ["Regulatory Circular", "Legal Notice", "Court Notice"]:
        return extract_regulatory_legal_data(cleaned_text, doc_type)
    else:
        return extract_unknown_data(cleaned_text, doc_type)

def process_and_structure_document(raw_text: str) -> tuple[dict, str]:
    """
    Master function to clean text and extract info to dict.
    Returns: (structured_dict, cleaned_text_string)
    """
    cleaned_txt = clean_extracted_text(raw_text)
    structured_data = extract_structured_data(cleaned_txt)
    
    return structured_data, cleaned_txt
