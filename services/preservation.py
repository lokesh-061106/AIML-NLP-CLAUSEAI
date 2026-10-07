import re

from collections import Counter

APPROVED_EQUIVALENCES = [('in accordance with', 'according to'), ('pursuant to', 'under'), ('notwithstanding', 'despite'), ('for the purpose of', 'to'), ('obtain', 'get'), ('provide', 'give'), ('in relation to', 'about'), ('prior to', 'before'), ('retain', 'keep'), ('in the event of', 'if'), ('terminate', 'end'), ('notify', 'inform'), ('in the event that', 'if'), ('terminated', 'ended')]

PRESERVATION_WEIGHTS = {'MODALITY': 5, 'NEGATION': 5, 'MONEY': 5, 'PERCENTAGES': 5, 'DATES': 5, 'DURATIONS': 4, 'CONDITIONS': 4, 'EXCEPTIONS': 4, 'NUMBERS': 4, 'LEGAL_TERMS': 2}

MODALITY_PATTERNS = {'mandatory': ['\\bshall\\b', '\\bmust\\b', '\\bis required to\\b', '\\bare required to\\b', '\\brequired\\b'], 'permission': ['\\bmay\\b', '\\bpermitted\\b', '\\bpermission\\b', '\\bauthorized\\b'], 'recommendation': ['\\bshould\\b', '\\brecommended\\b'], 'future': ['\\bwill\\b']}

NEGATION_PATTERNS = ['\\bnot\\b', '\\bno\\b', '\\bnever\\b', '\\bwithout\\b', '\\bprohibited\\b', '\\bforbidden\\b']

CONDITION_TERMS = ['if', 'unless', 'provided that', 'subject to', 'in the event', 'when', 'where']

EXCEPTION_TERMS = ['unless', 'except', 'subject to', 'provided that', 'notwithstanding']

LEGAL_TERMS = ['agreement', 'breach', 'confidential', 'obligation', 'obligations', 'party', 'parties', 'return', 'destroy', 'indemnification', 'jurisdiction', 'lessee', 'lessor', 'force majeure', 'liability', 'arbitration', 'warranty', 'damages', 'claims', 'losses']

def normalize_approved_legal_terms(text):
    """
    Normalize only approved ClauseGuard legal transformations.
    No general synonym matching is performed.
    """

    normalized = text or ""

    for original_term, replacement in APPROVED_EQUIVALENCES:

        pattern = (
            r"\b"
            + re.escape(original_term)
            + r"\b"
        )

        normalized = re.sub(
            pattern,
            replacement,
            normalized,
            flags=re.IGNORECASE
        )

    return normalized

def detect_modality(text):

    text = (text or "").lower()

    detected = []

    for category, patterns in MODALITY_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, text):

                detected.append(category)

                break

    return sorted(detected)

def detect_negation(text):

    text = (text or "").lower()

    detected = []

    for pattern in NEGATION_PATTERNS:

        if re.search(pattern, text):

            detected.append(pattern)

    return sorted(detected)

def detect_conditions(text):

    text = (text or "").lower()

    found = []

    for term in CONDITION_TERMS:

        if re.search(
            r"\b" + re.escape(term) + r"\b",
            text
        ):

            found.append(term)

    return sorted(set(found))

def detect_exceptions(text):

    text = (text or "").lower()

    found = []

    for term in EXCEPTION_TERMS:

        if re.search(
            r"\b" + re.escape(term) + r"\b",
            text
        ):

            found.append(term)

    return sorted(set(found))

def detect_legal_terms(text):

    text = (text or "").lower()

    found = []

    for term in LEGAL_TERMS:

        if re.search(
            r"\b" + re.escape(term) + r"\b",
            text
        ):

            found.append(term)

    return sorted(set(found))

def detect_money(text):

    pattern = re.compile(

        r"(?<!\w)"
        r"(?:"
        r"(?:[$₹€£]\s?\d[\d,]*(?:\.\d+)?)"
        r"|"
        r"(?:\d[\d,]*(?:\.\d+)?\s?"
        r"(?:USD|INR|EUR|GBP|"
        r"dollars?|rupees?|euros?|pounds?))"
        r")"
        r"(?!\w)",

        re.IGNORECASE

    )

    return sorted(
        pattern.findall(text or "")
    )

def detect_percentages(text):

    pattern = re.compile(
        r"\b\d+(?:\.\d+)?\s?%",
        re.IGNORECASE
    )

    return sorted(
        pattern.findall(text or "")
    )

def detect_dates(text):

    patterns = [

        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",

        r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",

        r"\b\d{1,2}\s+"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{4}\b",

        r"\b(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{1,2},\s+\d{4}\b",

    ]

    found = []

    for pattern in patterns:

        found.extend(
            re.findall(
                pattern,
                text or "",
                flags=re.IGNORECASE
            )
        )

    return sorted(set(found))

def detect_durations(text):

    pattern = re.compile(

        r"\b\d+(?:\.\d+)?\s+"
        r"(?:day|days|week|weeks|month|months|"
        r"year|years|hour|hours|minute|minutes)\b",

        re.IGNORECASE

    )

    return sorted(
        pattern.findall(text or "")
    )

def detect_numbers(text):

    text = text or ""

    masked = text

    special_values = (
        detect_money(masked)
        + detect_percentages(masked)
        + detect_dates(masked)
        + detect_durations(masked)
    )

    for value in special_values:

        masked = masked.replace(
            value,
            " "
        )

    numbers = re.findall(
        r"\b\d+(?:\.\d+)?\b",
        masked
    )

    return sorted(numbers)

def compare_values(
    original,
    simplified,
    check_name,
    risk="MEDIUM"
):

    original_counter = Counter(
        original
    )

    simplified_counter = Counter(
        simplified
    )

    status = "PRESERVED"

    missing = []

    if original_counter != simplified_counter:

        status = "CHANGED"

        for item, count in (
            original_counter
            - simplified_counter
        ).items():

            missing.extend(
                [item] * count
            )

    return {

        "check": check_name,

        "original": original,

        "simplified": simplified,

        "missing":
            missing if missing else None,

        "status": status,

        "risk":
            risk if status == "CHANGED"
            else "LOW",

    }

def compare_modality(
    original,
    simplified
):

    original_modality = detect_modality(
        original
    )

    simplified_modality = detect_modality(
        simplified
    )

    result = {

        "check": "MODALITY",

        "original":
            original_modality,

        "simplified":
            simplified_modality,

        "missing":
            None,

        "status":
            "PRESERVED",

        "risk":
            "LOW",

    }

    if (
        not original_modality
        and
        not simplified_modality
    ):
        return result

    if (
        Counter(original_modality)
        ==
        Counter(simplified_modality)
    ):
        return result

    original_mandatory = (
        "mandatory"
        in original_modality
    )

    simplified_mandatory = (
        "mandatory"
        in simplified_modality
    )

    original_permission = (
        "permission"
        in original_modality
    )

    simplified_permission = (
        "permission"
        in simplified_modality
    )

    if (

        (
            original_mandatory
            and
            simplified_permission
        )

        or

        (
            original_permission
            and
            simplified_mandatory
        )

    ):

        result["status"] = "CHANGED"
        result["risk"] = "HIGH"

        return result

    result["status"] = "CHANGED"
    result["risk"] = "MEDIUM"

    return result

def compare_negation(
    original,
    simplified
):

    original_negation = bool(
        detect_negation(original)
    )

    simplified_negation = bool(
        detect_negation(simplified)
    )

    result = {

        "check":
            "NEGATION",

        "original":
            original_negation,

        "simplified":
            simplified_negation,

        "missing":
            None,

        "status":
            "PRESERVED",

        "risk":
            "LOW",

    }

    if (
        original_negation
        != simplified_negation
    ):

        result["status"] = "CHANGED"
        result["risk"] = "HIGH"

    return result

def calculate_weighted_preservation_score(
    results
):

    total_weight = 0

    preserved_weight = 0

    for result in results:

        check_name = result["check"]

        weight = PRESERVATION_WEIGHTS.get(
            check_name,
            1
        )

        total_weight += weight

        if (
            result["status"]
            ==
            "PRESERVED"
        ):

            preserved_weight += weight

    if total_weight == 0:

        return 100.0

    return round(

        (
            preserved_weight
            /
            total_weight
        )
        * 100,

        2

    )

def compare_clauses_weighted(
    original,
    simplified
):

    results = []

    results.append(
        compare_modality(
            original,
            simplified
        )
    )

    results.append(
        compare_negation(
            original,
            simplified
        )
    )

    results.append(
        compare_values(
            detect_money(original),
            detect_money(simplified),
            "MONEY",
            risk="HIGH"
        )
    )

    results.append(
        compare_values(
            detect_percentages(original),
            detect_percentages(simplified),
            "PERCENTAGES",
            risk="HIGH"
        )
    )

    results.append(
        compare_values(
            detect_dates(original),
            detect_dates(simplified),
            "DATES",
            risk="HIGH"
        )
    )

    results.append(
        compare_values(
            detect_durations(original),
            detect_durations(simplified),
            "DURATIONS",
            risk="HIGH"
        )
    )

    results.append(
        compare_values(
            detect_numbers(original),
            detect_numbers(simplified),
            "NUMBERS",
            risk="HIGH"
        )
    )

    results.append(
        compare_values(
            detect_conditions(original),
            detect_conditions(simplified),
            "CONDITIONS",
            risk="MEDIUM"
        )
    )

    results.append(
        compare_values(
            detect_exceptions(original),
            detect_exceptions(simplified),
            "EXCEPTIONS",
            risk="HIGH"
        )
    )

    results.append(
        compare_values(
            detect_legal_terms(original),
            detect_legal_terms(simplified),
            "LEGAL_TERMS",
            risk="HIGH"
        )
    )

    score = (
        calculate_weighted_preservation_score(
            results
        )
    )

    high_risk_count = sum(

        1

        for result in results

        if (
            result["status"]
            ==
            "CHANGED"

            and

            result["risk"]
            ==
            "HIGH"
        )

    )

    medium_risk_count = sum(

        1

        for result in results

        if (
            result["status"]
            ==
            "CHANGED"

            and

            result["risk"]
            ==
            "MEDIUM"
        )

    )

    changed_count = sum(

        1

        for result in results

        if (
            result["status"]
            ==
            "CHANGED"
        )

    )

    if high_risk_count > 0:

        overall_risk = "HIGH"

        preservation_status = (
            "Potential Meaning Change"
        )

    elif medium_risk_count > 0:

        overall_risk = "MEDIUM"

        preservation_status = (
            "Review Required"
        )

    else:

        overall_risk = "LOW"

        preservation_status = (
            "Meaning Preserved"
        )

    return {

        "results":
            results,

        "checks":
            results,

        "preservation_score":
            score,

        "score":
            score,

        "preservation_status":
            preservation_status,

        "status":
            preservation_status,

        "overall_risk":
            overall_risk,

        "risk":
            overall_risk,

        "high_risk_count":
            high_risk_count,

        "medium_risk_count":
            medium_risk_count,

        "changed_count":
            changed_count,

    }

def compare_clauses_weighted_with_equivalence(
    original,
    simplified
):

    original_normalized = (
        normalize_approved_legal_terms(
            original
        )
    )

    simplified_normalized = (
        normalize_approved_legal_terms(
            simplified
        )
    )

    result = compare_clauses_weighted(
        original_normalized,
        simplified_normalized
    )

    result["original_text"] = original

    result["simplified_text"] = simplified

    result["normalized_original"] = (
        original_normalized
    )

    result["normalized_simplified"] = (
        simplified_normalized
    )

    return result
