import re

LEGAL_GLOSSARY = {
    'jurisdiction': 'the legal authority or area where a court or law applies',
    'liability': 'legal responsibility for an act, loss, or damage',
    'breach': 'failure to follow a legal agreement or obligation',
    'indemnification': 'a duty to compensate another party for certain losses',
    'obligation': 'a legal duty or responsibility',
    'confidential': 'information that must be kept private',
    'termination': 'the ending of an agreement or legal relationship',
    'arbitration': 'a process where a neutral person resolves a dispute',
    'damages': 'money awarded or payable for harm or loss',
    'warranty': 'a promise or assurance about a product, service, or fact',
    'force majeure': 'an unusual event outside a party control',
    'lessee': 'the person or organization renting property',
    'lessor': 'the person or organization renting property to another',
    'party': 'a person or organization involved in the agreement',
    'parties': 'the people or organizations involved in the agreement',
}

def find_legal_terms(text):
    text = (text or '').lower()
    found = []
    for term, explanation in LEGAL_GLOSSARY.items():
        if re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text):
            found.append({
                'term': term,
                'explanation': explanation
            })
    return sorted(found, key=lambda x: x['term'])
