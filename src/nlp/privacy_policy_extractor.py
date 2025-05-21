from transformers import T5Tokenizer, T5ForConditionalGeneration
import re

class PrivacyPolicyExtractor:
    def __init__(self, model_name='t5-base'):
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)

    def extract_data_practices(self, text):
        input_text = f"extract data practices: {text}"
        input_ids = self.tokenizer.encode(input_text, return_tensors='pt')
        output_ids = self.model.generate(input_ids)
        extracted_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return self._parse_extracted_text(extracted_text)

    def _parse_extracted_text(self, extracted_text):
        practices = []
        # Simple regex to find data practices in the extracted text
        for line in extracted_text.split('\n'):
            match = re.search(r'(.*?)(?=\.)', line)
            if match:
                practices.append(match.group(0).strip())
        return practices

    def extract_metadata(self, text):
        metadata = {}
        # Example regex patterns for extracting metadata
        patterns = {
            'email': r'[\w\.-]+@[\w\.-]+',
            'phone': r'\+?\d[\d -]{8,12}\d',
            'address': r'\d+\s[A-z]+\s[A-z]+'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                metadata[key] = match.group(0)
        return metadata
