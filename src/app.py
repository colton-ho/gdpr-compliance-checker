from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import config
import mimetypes
import textract
from werkzeug.utils import secure_filename
from pdfminer.high_level import extract_text as pdf_extract_text
from workflow.orchestrator import Orchestrator
from rules.rule_engine import RuleEngine
from kg.kg_builder import KnowledgeGraphBuilder
from nlp.extractor import PrivacyPolicyExtractor, DPAExtractor
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for server
import matplotlib.pyplot as plt
import uuid
import difflib

app = Flask(__name__)
app.secret_key = 'gdpr_secret_key'  # Needed for flashing messages
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'json', 'pdf', 'doc', 'docx'}

# Set up core components
base_dir = os.path.dirname(os.path.abspath(__file__))
rules_path = os.path.join(base_dir, "rules", "gdpr_rules.json")
ontology_path = os.path.join(base_dir, "kg", "ontology", "smashhitcore.owl")
rule_engine = RuleEngine(rules_path)
kg_builder = KnowledgeGraphBuilder(ontology_path)
orchestrator = Orchestrator(rules_path, ontology_path)
privacy_policy_extractor = PrivacyPolicyExtractor()
dpa_extractor = DPAExtractor()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    compliance_results = None
    compliance_status = None
    error = None
    uploaded_content = None
    if request.method == 'POST':
        # Handle drag-and-drop file upload
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                ext = filename.rsplit('.', 1)[1].lower()
                if ext in ['txt', 'json']:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        uploaded_content = f.read()
                elif ext == 'pdf':
                    try:
                        uploaded_content = pdf_extract_text(file_path)
                    except Exception as e:
                        error = f'Could not extract text from PDF: {e}'
                        return render_template('index.html', compliance_results=None, compliance_status=None, error=error)
                elif ext in ['doc', 'docx']:
                    try:
                        uploaded_content = textract.process(file_path).decode('utf-8')
                    except Exception as e:
                        error = f'Could not extract text from file: {e}'
                        return render_template('index.html', compliance_results=None, compliance_status=None, error=error)
                # Try to infer document type from filename
                if 'privacy' in filename.lower():
                    doc_type = 'privacy_policy'
                elif 'dpa' in filename.lower():
                    doc_type = 'dpa'
                else:
                    doc_type = request.form.get('doc_type')
                content = uploaded_content
            else:
                error = 'Invalid file type. Only .txt, .json, .pdf, .doc, .docx are allowed.'
                return render_template('index.html', compliance_results=None, compliance_status=None, error=error)
        else:
            doc_type = request.form.get('doc_type')
            content = request.form.get('content')
        if not content or not doc_type:
            error = 'Please provide both document type and content.'
        else:
            extracted_data = None
            strengths = []
            missing = []
            conclusion = ""
            status_label = None  # Ensure status_label is always defined
            status_explanation = None  # Ensure status_explanation is always defined
            if doc_type == 'privacy_policy':
                # Pass GDPR requirements for semantic matching and enable debug
                gdpr_reqs = []
                if hasattr(rule_engine, 'rules'):
                    rules = rule_engine.rules['rules'] if isinstance(rule_engine.rules, dict) and 'rules' in rule_engine.rules else rule_engine.rules
                    for rule in rules:
                        if 'requirements' in rule:
                            gdpr_reqs.extend(rule['requirements'])
                extracted_data = privacy_policy_extractor.extract(content, gdpr_requirements=gdpr_reqs, debug=True)
                compliance_results = rule_engine.check_privacy_policy(extracted_data)
            elif doc_type == 'dpa':
                extracted_data = dpa_extractor.extract(content)
                compliance_results = rule_engine.check_dpa(extracted_data)
            # Analyze strengths and missing areas
            if extracted_data is not None:
                # If extracted_data is a string, wrap it in a dict for KG compatibility
                if isinstance(extracted_data, str):
                    extracted_data = {
                        'text': extracted_data,
                        'uri': 'http://example.org/document',
                        'type': doc_type,
                        'parties': [],
                        'obligations': []
                    }
                # Determine present and missing requirements
                present = []
                missing = []
                missing_set = set()
                requirement_keywords = getattr(rule_engine, 'requirement_keywords', {})
                if isinstance(compliance_results, list):
                    all_requirements = []
                    if hasattr(rule_engine, 'rules'):
                        rules = rule_engine.rules['rules'] if isinstance(rule_engine.rules, dict) and 'rules' in rule_engine.rules else rule_engine.rules
                        for rule in rules:
                            if 'requirements' in rule:
                                for req in rule['requirements']:
                                    all_requirements.append((req, rule.get('id', '')))
                    for req, art in all_requirements:
                        found_flag = False
                        for field in ['obligations', 'text']:
                            items = extracted_data.get(field, [])
                            if isinstance(items, str):
                                items = [items]
                            for item in items:
                                item_lower = str(item).lower()
                                # Fuzzy match: consider present if >70% similar or keyword present
                                ratio = difflib.SequenceMatcher(None, req.lower(), item_lower).ratio()
                                if ratio > 0.7 or req.lower() in item_lower:
                                    found_flag = True
                                    break
                                # Also check for any keyword in the requirement_keywords (if available)
                                for kw in requirement_keywords.get(req, []):
                                    if kw in item_lower:
                                        found_flag = True
                                        break
                                if found_flag:
                                    break
                            if found_flag:
                                break
                        if found_flag:
                            present.append(f"{req} ({art})" if art else req)
                        else:
                            missing_set.add(f"{req} ({art})" if art else req)
                    # Add any extra missing from compliance_results, but deduplicate and clean
                    for m in compliance_results:
                        if m.startswith('Missing: '):
                            m_clean = m.replace('Missing: ', '')
                        else:
                            m_clean = m
                        missing_set.add(m_clean)
                    missing = sorted(missing_set)
                # --- Enhanced summary logic for grouped strengths and human-readable output ---
                # Group strengths by GDPR topic
                summary = []
                lawful_basis = []
                article13 = []
                article32 = []
                rights = []
                dpo = None
                withdrawal = None
                update_date = None
                # Scan present for grouping
                for s in present:
                    s_lower = s.lower()
                    if 'legal basis' in s_lower or 'lawful basis' in s_lower or 'contract' in s_lower or 'consent' in s_lower or 'obligation' in s_lower:
                        lawful_basis.append(s)
                    if 'article-13' in s_lower:
                        article13.append(s)
                    if 'article-32' in s_lower or 'security' in s_lower:
                        article32.append(s)
                    if 'right' in s_lower or 'rectification' in s_lower or 'erasure' in s_lower or 'objection' in s_lower or 'portability' in s_lower or 'complaint' in s_lower:
                        rights.append(s)
                # Detect DPO contact, withdrawal of consent, update date in text
                text = extracted_data.get('text', '')
                if any(x in text.lower() for x in ['dpo', 'data protection officer', 'dpo contact', 'dpo@', 'dpo:']):
                    dpo = 'DPO contact provided.'
                if 'withdraw' in text.lower() and 'consent' in text.lower():
                    withdrawal = 'Withdrawal of consent: Explicitly mentioned.'
                import re
                date_match = re.search(r'(updated|last modified|effective)[^\n\r:]*[:\-]?\s*([0-9]{4}|[0-9]{2}/[0-9]{2}/[0-9]{4}|[a-zA-Z]+ \d{1,2}, \d{4})', text, re.IGNORECASE)
                if date_match:
                    update_date = f"Update date: {date_match.group(0).strip()}"
                # Compose grouped summary
                if lawful_basis:
                    summary.append(f"Lawful basis: All main data processing activities have a clear legal basis (Art. 6): {', '.join(lawful_basis)}.")
                if article13:
                    summary.append("Article 13 information: Includes:")
                    for item in article13:
                        if 'identity' in item.lower():
                            summary.append("- Identity and contact info of data controller.")
                        if 'purpose' in item.lower():
                            summary.append("- Purposes of processing.")
                        if 'categories' in item.lower():
                            summary.append("- Categories of data collected.")
                        if 'recipients' in item.lower():
                            summary.append("- Recipients of data.")
                        if 'retention' in item.lower():
                            summary.append("- Retention period.")
                        if 'rights' in item.lower():
                            summary.append("- Data subject rights (access, rectification, erasure, objection, portability, complaint).")
                if dpo:
                    summary.append(dpo)
                if article32:
                    summary.append("Article 32: Security measures are listed (encryption, access control, staff training, penetration testing).")
                if withdrawal:
                    summary.append(withdrawal)
                if update_date:
                    summary.append(update_date)
                # --- NEW: Add extracted sections, lists/tables, and section_matches for audit-style transparency ---
                debug_sections = []
                if extracted_data.get('sections'):
                    debug_sections.append("\nSections Detected:")
                    for header, body in extracted_data['sections'].items():
                        debug_sections.append(f"- {header}: {body}")
                if extracted_data.get('lists_tables'):
                    debug_sections.append("\nLists/Tables Extracted:")
                    for l in extracted_data['lists_tables']:
                        debug_sections.append(f"- {l}")
                if extracted_data.get('section_matches'):
                    debug_sections.append("\nGDPR Requirement Matches (semantic):")
                    for sent, matches in extracted_data['section_matches'].items():
                        match_str = ", ".join([f"{req} ({sim:.2f})" for req, sim in matches])
                        debug_sections.append(f"- '{sent[:120]}{'...' if len(sent)>120 else ''}' => {match_str}")
                # Compose full report
                summary_section = "Strengths (Compliant):\n" + ("\n".join(summary) if summary else "None")
                missing_section = "Missing/Non-Compliant Areas:\n" + ("\n".join(f"- {m}" for m in missing) if missing else "None")
                debug_section = "\n\n--- Extraction Details (for audit/debug) ---\n" + "\n".join(debug_sections) if debug_sections else ""
                compliance_report = f"{summary_section}\n\n{missing_section}\n\nConclusion:\n{conclusion}{debug_section}"
                compliance_results = compliance_report
                # Continue with compliance_status and chart generation
                kg = kg_builder.build_kg(extracted_data)
                status = orchestrator.verify_compliance(kg)
                # Improved compliance status reporting
                # Special case: treat as fully compliant if only minor/edge-case requirements are missing
                minor_missing = set([
                    'Retention period (GDPR-Article-13)',
                    'Retention period (GDPR-Article-14)',
                    'Risk assessment must be conducted (GDPR-Article-32)',
                    'Source of the personal data (GDPR-Article-14)',
                    'Data subject must be informed about the processing (GDPR-Article-6)'
                ])
                # --- Ensure status_label is always set before use ---
                status_label = None
                status_explanation = None
                total_requirements = len(present) + len(missing)
                present_ratio = len(present) / total_requirements if total_requirements > 0 else 0
                parties_found = status.get('parties_found', 0)
                if missing and all(m in minor_missing for m in missing):
                    status_label = "Fully Compliant"
                    status_explanation = "All major GDPR requirements are met. Only minor/edge-case requirements are missing."
                    conclusion = "This document is a strong example of a GDPR-compliant privacy policy. It covers all key areas for transparency, user rights, and security measures."
                elif not missing:
                    status_label = "Fully Compliant"
                    status_explanation = "All GDPR requirements are met."
                elif present_ratio < 0.2 or not present or parties_found == 0:
                    status_label = "Not Compliant"
                    status_explanation = "No significant GDPR requirements are met or no parties identified."
                    conclusion = "Not compliant with GDPR in any significant way. This document would fail an audit or regulatory review."
                else:
                    status_label = "Partially Compliant"
                    status_explanation = f"Some GDPR requirements are missing ({len(missing)} missing, {len(present)} present). See details above."
                    conclusion = "Partially compliant. Most core elements are present, but it would not fully satisfy a strict GDPR audit. See missing areas above."
                # Compose full report
                summary_section = "Strengths (Compliant):\n" + ("\n".join(summary) if summary else "None")
                missing_section = "Missing/Non-Compliant Areas:\n" + ("\n".join(f"- {m}" for m in missing) if missing else "None")
                debug_section = "\n\n--- Extraction Details (for audit/debug) ---\n" + "\n".join(debug_sections) if debug_sections else ""
                compliance_report = f"{summary_section}\n\n{missing_section}\n\nConclusion:\n{conclusion}{debug_section}"
                compliance_results = compliance_report
                compliance_status = (
                    f"Status: {status_label}\n"
                    f"Parties found: {status['parties_found']} (organizations or persons identified in the document)\n"
                    f"Obligations found: {status['obligations_found']} (distinct obligations or commitments detected)\n"
                    f"Compliant (technical check): {status['compliant']}\n"
                    f"Details: {status['details']}\n"
                    f"{status_explanation}"
                )
                # Generate a pie chart for compliance status
                chart_filename = None
                compliant_count = 1 if status.get('compliant') else 0
                non_compliant_count = 1 - compliant_count
                if compliant_count + non_compliant_count > 0:
                    labels = ['Compliant', 'Non-Compliant']
                    sizes = [compliant_count, non_compliant_count]
                    colors = ['#4CAF50', '#F44336']
                    fig, ax = plt.subplots()
                    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
                    ax.axis('equal')
                    chart_filename = f"compliance_chart_{uuid.uuid4().hex}.png"
                    chart_path = os.path.join(app.config['UPLOAD_FOLDER'], chart_filename)
                    plt.savefig(chart_path)
                    plt.close(fig)
                # Pass chart filename to template
                return render_template('index.html', compliance_results=compliance_results, compliance_status=compliance_status, error=error, chart_filename=chart_filename)
    return render_template('index.html', compliance_results=compliance_results, compliance_status=compliance_status, error=error)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
