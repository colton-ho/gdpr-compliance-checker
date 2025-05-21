import json
import os
from nlp.extractor import PrivacyPolicyExtractor, DPAExtractor
from rules.rule_engine import RuleEngine
from semantic.sf_comparator import SFComparator
from kg.kg_builder import KnowledgeGraphBuilder
from utils.logger import setup_logger

class Orchestrator:
    def __init__(self, rules_path, ontology_path):
        self.logger = setup_logger()
        self.privacy_policy_extractor = PrivacyPolicyExtractor()
        self.dpa_extractor = DPAExtractor()
        self.rule_engine = RuleEngine(rules_path)
        # Load semantic frames
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dpa_sf_path = os.path.join(base_dir, "..", "semantic", "dpa_sf.json")
        gdpr_sf_path = os.path.join(base_dir, "..", "semantic", "gdpr_sf.json")
        with open(dpa_sf_path, "r") as f:
            dpa_sf = json.load(f)
        with open(gdpr_sf_path, "r") as f:
            gdpr_sf = json.load(f)
        self.sf_comparator = SFComparator(dpa_sf, gdpr_sf)
        self.kg_builder = KnowledgeGraphBuilder(ontology_path)

    def load_documents(self, document_paths):
        """Load documents from the given list of file paths. Assumes each document is a text file and infers type from filename."""
        documents = []
        for path in document_paths:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Infer document type from filename
            if 'privacy' in os.path.basename(path).lower():
                doc_type = 'privacy_policy'
            elif 'dpa' in os.path.basename(path).lower():
                doc_type = 'dpa'
            else:
                doc_type = 'unknown'
            # Create a simple object with .content and .type
            doc = type('Document', (object,), {'content': content, 'type': doc_type})()
            documents.append(doc)
        return documents

    def process_document(self, document):
        self.logger.info("Starting document processing.")
        
        if self.is_privacy_policy(document):
            self.logger.info("Processing Privacy Policy.")
            extracted_data = self.privacy_policy_extractor.extract(document)
            compliance_results = self.rule_engine.check_privacy_policy_compliance(extracted_data)
        elif self.is_dpa(document):
            self.logger.info("Processing Data Processing Agreement.")
            extracted_data = self.dpa_extractor.extract(document)
            compliance_results = self.sf_comparator.compare_with_gdpr(extracted_data)
        else:
            self.logger.warning("Document type not recognized.")
            return None
        
        self.logger.info("Document processing completed.")
        return compliance_results

    def is_privacy_policy(self, document):
        # Logic to determine if the document is a Privacy Policy
        return "Privacy Policy" in document

    def is_dpa(self, document):
        # Logic to determine if the document is a DPA
        return "Data Processing Agreement" in document

    def verify_compliance(self, kg):
        """Basic compliance check: require at least one party and one obligation in the KG."""
        parties = list(kg.subjects(predicate=self.kg_builder.namespace.hasParty))
        obligations = list(kg.subjects(predicate=self.kg_builder.namespace.hasObligation))
        compliant = bool(parties) and bool(obligations)
        return {
            'compliant': compliant,
            'parties_found': len(parties),
            'obligations_found': len(obligations),
            'details': 'At least one party and one obligation required.'
        }

    def generate_report(self, compliance_results, compliance_status):
        """Stub for report generation. Prints results for now."""
        print("Compliance Results:", compliance_results)
        print("Compliance Status:", compliance_status)

    def run(self, documents):
        results = []
        for document in documents:
            result = self.process_document(document)
            results.append(result)
        return results