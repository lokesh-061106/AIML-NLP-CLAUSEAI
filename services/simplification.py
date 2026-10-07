import re

APPROVED_RULES = [('in accordance with', 'according to'), ('pursuant to', 'under'), ('notwithstanding', 'despite'), ('for the purpose of', 'to'), ('obtain', 'get'), ('provide', 'give'), ('in relation to', 'about'), ('prior to', 'before'), ('retain', 'keep'), ('in the event of', 'if'), ('terminate', 'end'), ('notify', 'inform'), ('in the event that', 'if'), ('terminated', 'ended')]

GRADED_RULES = {'Skilled': [('in accordance with', 'according to'), ('pursuant to', 'under'), ('notwithstanding', 'despite'), ('for the purpose of', 'to'), ('obtain', 'get'), ('provide', 'give')], 'Intermediate': [('in accordance with', 'according to'), ('pursuant to', 'under'), ('notwithstanding', 'despite'), ('for the purpose of', 'to'), ('obtain', 'get'), ('provide', 'give'), ('in relation to', 'about'), ('prior to', 'before'), ('retain', 'keep'), ('in the event of', 'if')], 'Basic': [('in accordance with', 'according to'), ('pursuant to', 'under'), ('notwithstanding', 'despite'), ('for the purpose of', 'to'), ('obtain', 'get'), ('provide', 'give'), ('in relation to', 'about'), ('prior to', 'before'), ('retain', 'keep'), ('in the event of', 'if'), ('terminate', 'end'), ('notify', 'inform'), ('in the event that', 'if'), ('terminated', 'ended')]}

def apply_rule(
    text,
    original_term,
    replacement
):

    pattern = (
        r"\b"
        + re.escape(original_term)
        + r"\b"
    )

    return re.sub(
        pattern,
        replacement,
        text,
        flags=re.IGNORECASE
    )

def simplify_at_level(
    text,
    level
):

    if level not in GRADED_RULES:

        raise ValueError(
            f"Invalid level: {level}. "
            f"Use Skilled, Intermediate, or Basic."
        )

    current_text = text

    applied_rules = []

    for (
        original_term,
        replacement
    ) in GRADED_RULES[level]:

        candidate = apply_rule(
            current_text,
            original_term,
            replacement
        )

        if candidate != current_text:

            applied_rules.append(
                f"{original_term} -> {replacement}"
            )

            current_text = candidate

    return (
        current_text,
        applied_rules
    )


def preservation_aware_simplify(text, level, max_attempts=3):
    from services.preservation import compare_clauses_weighted_with_equivalence

    if level not in GRADED_RULES:
        raise ValueError(f'Invalid level: {level}')

    current = text or ''
    accepted = []
    rejected = []
    attempts = 0

    for old, new in GRADED_RULES[level]:

        candidate = apply_rule(current, old, new)

        if candidate == current:
            continue

        if attempts >= max_attempts:
            break

        attempts += 1

        check = compare_clauses_weighted_with_equivalence(
            text,
            candidate
        )

        if check['risk'] == 'LOW':
            current = candidate
            accepted.append(f'{old} -> {new}')
        else:
            rejected.append({
                'rule': f'{old} -> {new}',
                'risk': check['risk'],
                'status': check['status']
            })

    final_check = compare_clauses_weighted_with_equivalence(
        text,
        current
    )

    return {
        'simplified': current,
        'accepted_rules': accepted,
        'rejected_rules': rejected,
        'attempts': attempts,
        'final_check': final_check
    }

