import io
import re
import pandas as pd
import streamlit as st
import textstat

from services.simplification import simplify_at_level
from services.preservation import compare_clauses_weighted_with_equivalence
from services.summarization import summarize_with_metadata
from services.glossary import find_legal_terms

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

st.set_page_config(page_title='ClauseGuard', page_icon='🛡️', layout='wide')

def clean(text):
    return re.sub(r'\s+', ' ', text or '').strip()

def word_count(text):
    return len(re.findall(r'\b[\w\x27-]+\b', text or ''))

def reduction(original, simplified):
    a = word_count(original)
    b = word_count(simplified)
    return 0.0 if a == 0 else ((a - b) / a) * 100.0

def extract_pdf(data):
    if PdfReader is None:
        raise RuntimeError('pypdf is not installed')
    reader = PdfReader(io.BytesIO(data))
    return '\n'.join(page.extract_text() or '' for page in reader.pages)

def readability(text):
    text = clean(text)
    if not text:
        return {}
    return {
        'Flesch': round(textstat.flesch_reading_ease(text), 3),
        'FK': round(textstat.flesch_kincaid_grade(text), 3),
        'Fog': round(textstat.gunning_fog(text), 3),
        'ARI': round(textstat.automated_readability_index(text), 3)
    }

def analyze(text, level):
    original = clean(text)
    simplified, rules = simplify_at_level(original, level)
    preservation = compare_clauses_weighted_with_equivalence(original, simplified)
    return {
        'original': original,
        'simplified': simplified,
        'rules': rules,
        'preservation': preservation,
        'summary': summarize_with_metadata(simplified),
        'glossary': find_legal_terms(original),
        'original_readability': readability(original),
        'simplified_readability': readability(simplified)
    }

st.title('🛡️ ClauseGuard')
st.subheader('Explainable, Non-LLM Legal Text Simplification')
st.write('Controlled rule-based simplification with structured preservation checking.')
st.divider()

st.header('1. Upload Legal Document')
uploaded = st.file_uploader('Upload PDF or TXT', type=['pdf', 'txt'])
pasted = st.text_area('Or paste legal text', height=220)

source = ''

if uploaded is not None:
    if uploaded.name.lower().endswith('.pdf'):
        source = extract_pdf(uploaded.getvalue())
    else:
        source = uploaded.getvalue().decode('utf-8', errors='ignore')
elif pasted.strip():
    source = pasted

source = clean(source)

if source:
    st.success(f'Text loaded successfully — {word_count(source):,} words')

st.header('2. Understanding Level')
level = st.radio('Choose target level', ['Skilled', 'Intermediate', 'Basic'], horizontal=True)
level_info = {
    'Skilled': '6 approved rules',
    'Intermediate': '10 approved rules',
    'Basic': '14 approved rules'
}
st.info(level_info[level])

if st.button('🔍 Analyze & Simplify', type='primary', disabled=not bool(source)):
    try:
        st.session_state['clauseguard_result'] = analyze(source, level)
    except Exception as exc:
        st.error('ClauseGuard analysis failed')
        st.exception(exc)

if 'clauseguard_result' in st.session_state:
    result = st.session_state['clauseguard_result']
    preservation = result['preservation']
    st.divider()
    st.header('3. Results')

    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Original Words', f"{word_count(result['original']):,}")
    c2.metric('Simplified Words', f"{word_count(result['simplified']):,}")
    c3.metric('Reduction', f"{reduction(result['original'], result['simplified']):.2f}%")
    c4.metric('Preservation', f"{preservation['score']:.1f}/100")

    st.subheader('🛡️ Preservation Checker')
    p1, p2, p3 = st.columns(3)
    p1.write('**Meaning Status**')
    p1.write(preservation['status'])
    p2.write('**Risk Level**')
    p2.write(preservation['risk'])
    p3.write('**Changed Elements**')
    p3.write(preservation['changed_count'])
    st.caption('The score reflects implemented structured checks and is not a universal guarantee of legal correctness.')

    st.subheader('📄 Original vs Simplified')
    left, right = st.columns(2)
    with left:
        st.markdown('### Original')
        st.text_area('Original', result['original'], height=350, disabled=True, label_visibility='collapsed')
    with right:
        st.markdown(f"### {level}")
        st.text_area('Simplified', result['simplified'], height=350, disabled=True, label_visibility='collapsed')

    st.subheader('📝 Key Summary')
    st.write(result['summary']['summary'])

    st.subheader('📊 Readability')
    rows = []
    for metric in ['Flesch', 'FK', 'Fog', 'ARI']:
        rows.append({
            'Metric': metric,
            'Original': result['original_readability'].get(metric, 0),
            'Simplified': result['simplified_readability'].get(metric, 0)
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader('📚 Legal Glossary')
    if result['glossary']:
        st.dataframe(pd.DataFrame(result['glossary']), use_container_width=True, hide_index=True)
    else:
        st.info('No curated glossary terms detected.')

    st.subheader('⚙️ Applied Simplification Rules')
    if result['rules']:
        for rule in result['rules']:
            st.write('• ' + rule)
    else:
        st.write('No approved transformation was applicable.')

    st.subheader('🔎 Preservation Check Details')
    details = []
    for check in preservation['checks']:
        details.append({
            'Legal Element': check['check'],
            'Status': check['status'],
            'Risk': check['risk'],
            'Original': str(check['original']),
            'Simplified': str(check['simplified'])
        })
    st.dataframe(pd.DataFrame(details), use_container_width=True, hide_index=True)

    report = '\n'.join([
        'CLAUSEGUARD ANALYSIS REPORT',
        '',
        f"Level: {level}",
        f"Original Words: {word_count(result['original'])}",
        f"Simplified Words: {word_count(result['simplified'])}",
        f"Reduction: {reduction(result['original'], result['simplified']):.2f}%",
        f"Preservation Score: {preservation['score']}",
        f"Status: {preservation['status']}",
        f"Risk: {preservation['risk']}",
        '',
        'SUMMARY',
        result['summary']['summary'],
        '',
        'ORIGINAL',
        result['original'],
        '',
        'SIMPLIFIED',
        result['simplified']
    ])

    st.subheader('⬇️ Downloads')
    d1, d2, d3 = st.columns(3)
    d1.download_button('Download Original', result['original'].encode('utf-8'), 'clauseguard_original.txt', 'text/plain')
    d2.download_button('Download Simplified', result['simplified'].encode('utf-8'), 'clauseguard_simplified.txt', 'text/plain')
    d3.download_button('Download Report', report.encode('utf-8'), 'clauseguard_report.txt', 'text/plain')

st.divider()
st.caption('ClauseGuard | Explainable non-LLM legal text simplification and structured preservation checking')
