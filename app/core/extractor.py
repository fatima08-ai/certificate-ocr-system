import re

def extract_fields(raw_text: str) -> dict:
    """Parse structured fields out of raw OCR text using pattern matching."""

    fields = {
        "candidate_name": None,
        "certificate_title": None,
        "organization": None,
        "issue_date": None,
        "certificate_number": None,
    }

    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    title_keywords = ["certificate", "achievement", "completion", "certifies"]

    date_match = re.search(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', raw_text)
    if date_match:
        fields["issue_date"] = date_match.group()

    cert_id_match = re.search(r'\b[A-Z0-9]{2,8}(?:-[A-Z0-9]{2,8}){1,3}\b', raw_text)
    if cert_id_match:
        fields["certificate_number"] = cert_id_match.group()

    for line in lines:
        if any(keyword in line.lower() for keyword in title_keywords):
            cleaned = re.sub(r'^[^A-Za-z]*', '', line)
            fields["certificate_title"] = cleaned
            break

    for i, line in enumerate(lines):
        if "certifies that" in line.lower() and i + 1 < len(lines):
            fields["candidate_name"] = lines[i + 1]
        if "completed" in line.lower() and i + 1 < len(lines):
            fields["certificate_title"] = lines[i + 1]

    if lines and not any(keyword in lines[0].lower() for keyword in title_keywords):
        fields["organization"] = lines[0]

    return fields