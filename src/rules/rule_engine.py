from typing import List, Dict, Any
import json

class RuleEngine:
    requirement_keywords = {
        "Identity and contact details of the controller": [
            "controller", "data controller", "contact", "contact details", "contact information", "name", "address", "email", "phone", "telephone", "reach us", "get in touch", "contact person", "representative"
        ],
        "Purpose of processing": [
            "purpose", "why", "reason", "objective", "we process", "used for", "processing for", "in order to", "aim", "goal"
        ],
        "Legal basis for processing": [
            "legal basis", "lawful basis", "consent", "contract", "legal obligation", "legitimate interest", "vital interest", "public task", "compliance with law", "required by law", "statutory"
        ],
        "Categories of personal data": [
            "categories", "types of data", "personal data", "data collected", "we collect", "information we collect", "data we process", "data category", "data type"
        ],
        "Recipients of personal data": [
            "recipient", "third party", "third parties", "shared with", "disclose", "provided to", "transferred to", "who receives", "who may access", "partners", "vendors"
        ],
        "Retention period": [
            "retention", "how long", "storage period", "kept for", "deleted after", "stored for", "retained for", "archived for", "duration", "period of storage"
        ],
        "Rights of the data subject": [
            "right", "access", "rectification", "erasure", "object", "portability", "complaint", "restrict processing", "withdraw consent", "data subject rights", "your rights", "request information", "correct your data", "delete your data", "oppose processing", "file a complaint", "how to exercise your rights", "right to lodge a complaint", "right to data portability", "right to restrict processing", "right to withdraw consent", "exercise your rights", "request access", "request correction", "request deletion", "object to processing", "contact us to exercise your rights", "request a copy", "ask for your data", "make a request", "privacy rights", "access your information", "correct your information", "erase your information", "object to our processing", "lodge a complaint", "supervisory authority", "regulator", "data protection authority", "contact the regulator", "contact the authority"
        ],
        "Source of the personal data": [
            "source", "obtained from", "collected from", "where we get", "how we obtain", "origin of data", "provided by", "supplied by", "received from", "where your data comes from", "how we receive your data", "third party source", "external source", "from other sources", "we receive your data from", "we get your data from", "data is provided by", "data is supplied by", "data is received from", "data comes from", "data is collected from", "third party", "external source", "from third parties"
        ],
        "Processing must be lawful and fair": [
            "lawful", "fair", "legal", "compliant", "in accordance with the law", "fairly processed", "lawfully processed"
        ],
        "Data subject must be informed about the processing": [
            "inform", "notified", "told", "aware", "provided with information", "informed about", "transparency", "explained to you"
        ],
        "Legal basis must be established": [
            "legal basis", "lawful basis", "established", "basis for processing", "justification", "grounds for processing"
        ],
        "Appropriate technical and organizational measures must be implemented": [
            "security", "encryption", "access control", "technical measure", "organizational measure", "protection", "safeguard", "secure", "data breach", "security policy", "security controls", "staff training", "penetration testing", "firewall", "antivirus", "risk management"
        ],
        "Risk assessment must be conducted": [
            "risk assessment", "risk analysis", "risk management", "risk evaluation", "risk review", "risk mitigation", "risk identified", "risk handled", "risk register", "risk process", "risk procedures", "risk control", "risk monitoring", "risk policy", "risk audit", "security risk", "data protection impact assessment", "DPIA", "impact assessment", "security review", "security audit", "risk review", "risk evaluation", "risk mitigation", "risk control", "risk monitoring", "risk policy", "risk audit", "security risk", "risk process", "risk procedures", "risk register", "risk handled", "risk identified", "risk management process", "risk assessment process", "risk analysis process"
        ]
    }

    def __init__(self, rules_file: str):
        self.rules = self.load_rules(rules_file)

    def load_rules(self, rules_file: str) -> List[Dict[str, Any]]:
        with open(rules_file, 'r') as file:
            return json.load(file)

    def validate(self, extracted_data: Dict[str, Any]) -> List[str]:
        violations = []
        requirement_keywords = self.requirement_keywords
        # DEBUG: Print extracted obligations and text for analysis
        print('Extracted obligations:', extracted_data.get('obligations', []))
        print('Extracted text:', extracted_data.get('text', '')[:2000])  # Print first 2000 chars
        # Support both old and new rule formats
        if isinstance(self.rules, dict) and 'rules' in self.rules:
            rules = self.rules['rules']
        else:
            rules = self.rules
        for rule in rules:
            # If rule has 'field', use enhanced logic
            if 'field' in rule or 'keywords' in rule or 'min_count' in rule:
                if not self.check_rule(rule, extracted_data):
                    violations.append(rule.get('description', str(rule)))
            # If rule has 'requirements', check each requirement using keywords
            elif 'requirements' in rule:
                for req in rule['requirements']:
                    found = False
                    keywords = requirement_keywords.get(req, [])
                    # Check in obligations and text fields
                    for field in ['obligations', 'text']:
                        items = extracted_data.get(field, [])
                        if isinstance(items, str):
                            items = [items]
                        # Flexible: match any keyword for the requirement
                        for item in items:
                            item_lower = str(item).lower()
                            if req.lower() in item_lower:
                                found = True
                                break
                            if any(kw in item_lower for kw in keywords):
                                found = True
                                break
                        if found:
                            break
                    if not found:
                        violations.append(f"Missing: {req} ({rule.get('id', '')})")
        return violations

    def check_rule(self, rule: Dict[str, Any], extracted_data: Dict[str, Any]) -> bool:
        # Enhanced rule checking logic
        # Example rule: {"field": "parties", "min_count": 1, "description": "At least one party (ORG or PERSON) must be identified."}
        field = rule.get("field")
        min_count = rule.get("min_count", 1)
        keywords = rule.get("keywords", [])
        # Check for required field with minimum count
        if field and field in extracted_data:
            if isinstance(extracted_data[field], list) and len(extracted_data[field]) < min_count:
                return False
        # Check for required keywords in obligations or text
        if keywords:
            found = False
            for kw in keywords:
                if any(kw.lower() in str(item).lower() for item in extracted_data.get(field, [])):
                    found = True
                    break
            if not found:
                return False
        return True

    def check_dpa(self, extracted_data: dict) -> list:
        """Validate DPA extracted data against rules (for compatibility with main.py)."""
        return self.validate(extracted_data)

    def check_privacy_policy(self, extracted_data: dict) -> list:
        """Validate privacy policy extracted data against rules (for compatibility with app.py and main.py)."""
        return self.validate(extracted_data)

# Example usage:
# rule_engine = RuleEngine('src/rules/gdpr_rules.json')
# violations = rule_engine.validate(extracted_data)