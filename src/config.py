# Configuration settings for the GDPR Compliance Checker application

import os

# Base directory for the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths to resources
RESOURCE_PATH = os.path.join(BASE_DIR, 'resources')
DATASET_PATH = os.path.join(RESOURCE_PATH, 'datasets')
LEGAL_ENTITIES_PATH = os.path.join(RESOURCE_PATH, 'legal_entities.py')

# Paths to NLP models and configurations
NLP_MODEL_PATH = os.path.join(BASE_DIR, 'nlp', 'models')
GDPR_RULES_PATH = os.path.join(BASE_DIR, 'rules', 'gdpr_rules.json')
GDPR_SF_TEMPLATES_PATH = os.path.join(BASE_DIR, 'semantic', 'gdpr_sf_templates.json')

# Paths to documents
DOCUMENT_PATHS = [
    os.path.join(BASE_DIR, 'src', 'resources', 'datasets', 'opp-115_sample.json'),
    os.path.join(BASE_DIR, 'src', 'resources', 'datasets', 'dpa_samples.json')
]

# Logging configuration
LOGGING_LEVEL = 'INFO'
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Scheduler settings
SCHEDULER_INTERVAL = 60  # in seconds for automated checks

# Other parameters
MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5 MB limit for document processing

# Web interface instructions
WEB_INSTRUCTIONS = """
To use the web interface:
1. Install dependencies: pip install -r requirements.txt
2. Run: python src/app.py
3. Open your browser and go to http://127.0.0.1:5000/
4. Paste your document, select type, and check compliance.
"""
