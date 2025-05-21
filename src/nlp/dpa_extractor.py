from transformers import T5Tokenizer, T5ForConditionalGeneration
import re

class DPAExtractor:
    def __init__(self, model_name='t5-base'):
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)

    def extract_semantic_frame(self, dpa_text):
        input_text = f"extract semantic frame: {dpa_text}"
        input_ids = self.tokenizer.encode(input_text, return_tensors='pt')
        output_ids = self.model.generate(input_ids)
        semantic_frame = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return self.parse_semantic_frame(semantic_frame)

    def parse_semantic_frame(self, semantic_frame):
        # Placeholder for parsing logic
        # This should convert the semantic frame string into a structured format
        return semantic_frame

    def extract_metadata(self, dpa_text):
        metadata = {}
        metadata['contact_info'] = self.extract_contact_info(dpa_text)
        # Add more metadata extraction as needed
        return metadata

    def extract_contact_info(self, text):
        phone_pattern = r'\+?\d[\d -]{8,12}\d'
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phones = re.findall(phone_pattern, text)
        emails = re.findall(email_pattern, text)
        return {'phones': phones, 'emails': emails}