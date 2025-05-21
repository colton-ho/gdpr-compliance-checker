import os
from nlp.extractor import PrivacyPolicyExtractor, DPAExtractor
from rules.rule_engine import RuleEngine
from kg.kg_builder import KnowledgeGraphBuilder
from workflow.orchestrator import Orchestrator
from utils.logger import setup_logger
import config

def main():
    # Set up logging
    logger = setup_logger()

    # Initialize the compliance checker components
    privacy_policy_extractor = PrivacyPolicyExtractor()
    dpa_extractor = DPAExtractor()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(base_dir, "rules", "gdpr_rules.json")
    ontology_path = os.path.join(base_dir, "kg", "ontology", "smashhitcore.owl")
    rule_engine = RuleEngine(rules_path)
    kg_builder = KnowledgeGraphBuilder(ontology_path)
    orchestrator = Orchestrator(rules_path, ontology_path)

    logger.info("Starting GDPR Compliance Checker...")

    # Load documents and resources
    documents = orchestrator.load_documents(config.DOCUMENT_PATHS)

    # Process each document
    for document in documents:
        extracted_data = None
        compliance_results = None
        if document.type == 'privacy_policy':
            extracted_data = privacy_policy_extractor.extract(document.content)
            compliance_results = rule_engine.check_privacy_policy(extracted_data)
        elif document.type == 'dpa':
            extracted_data = dpa_extractor.extract(document.content)
            compliance_results = rule_engine.check_dpa(extracted_data)
        if extracted_data is not None:
            # If extracted_data is a list (e.g., from DPAExtractor), process each item
            if isinstance(extracted_data, list):
                for item in extracted_data:
                    kg = kg_builder.build_kg(item)
                    compliance_status = orchestrator.verify_compliance(kg)
                    orchestrator.generate_report(compliance_results, compliance_status)
            else:
                kg = kg_builder.build_kg(extracted_data)
                compliance_status = orchestrator.verify_compliance(kg)
                orchestrator.generate_report(compliance_results, compliance_status)

    logger.info("GDPR Compliance Checker completed.")

if __name__ == "__main__":
    main()