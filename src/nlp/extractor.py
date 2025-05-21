from transformers import T5Tokenizer, T5ForConditionalGeneration
import spacy
import re
import logging
from typing import List, Dict, Tuple

class PrivacyPolicyExtractor:
    def __init__(self):
        self.tokenizer = T5Tokenizer.from_pretrained("t5-base")
        self.model = T5ForConditionalGeneration.from_pretrained("t5-base")
        self.nlp = spacy.load("en_core_web_sm")

    def extract_data_practices(self, text):
        input_text = f"extract data practices: {text}"
        input_ids = self.tokenizer.encode(input_text, return_tensors="pt")
        output_ids = self.model.generate(input_ids)
        extracted_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return extracted_text

    def split_into_sections(self, text: str) -> Dict[str, str]:
        """
        Splits the document into sections based on common header patterns.
        Returns a dict: {section_header: section_text}
        """
        section_pattern = re.compile(r"(^\d+\.\s+.+$|^[A-Z][A-Za-z\s]{3,}:$|^[A-Z][A-Za-z\s]{3,}$)", re.MULTILINE)
        matches = list(section_pattern.finditer(text))
        sections = {}
        if not matches:
            return {"Full Document": text}
        for i, match in enumerate(matches):
            start = match.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            header = match.group().strip()
            body = text[start:end].strip()
            sections[header] = body
        return sections

    def extract_lists_and_tables(self, text: str) -> List[str]:
        """
        Extracts bullet/numbered lists and simple tables from text.
        Returns a list of string representations.
        """
        lines = text.split('\n')
        lists = []
        current_list = []
        for line in lines:
            if re.match(r"^\s*[-*•\d+.]", line):
                current_list.append(line.strip())
            else:
                if current_list:
                    lists.append('\n'.join(current_list))
                    current_list = []
        if current_list:
            lists.append('\n'.join(current_list))
        # Table-like: lines with repeated delimiters
        for line in lines:
            if line.count('|') >= 2 or line.count('\t') >= 2:
                lists.append(line.strip())
        return lists

    def semantic_match(self, sentence: str, requirements: List[str], threshold: float = 0.78) -> List[Tuple[str, float]]:
        """
        Returns a list of (requirement, similarity) for requirements above threshold.
        """
        doc1 = self.nlp(sentence)
        matches = []
        for req in requirements:
            doc2 = self.nlp(req)
            sim = doc1.similarity(doc2)
            if sim >= threshold:
                matches.append((req, sim))
        return matches

    def extract(self, text, gdpr_requirements: List[str] = None, debug: bool = False):
        doc = self.nlp(text)
        parties = set()
        obligations = set()
        section_matches = {}
        # Extract parties using named entities (ORG, PERSON, etc.)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PERSON"]:
                parties.add(ent.text)
        # Section/paragraph extraction
        sections = self.split_into_sections(text)
        for header, body in sections.items():
            section_doc = self.nlp(body)
            for sent in section_doc.sents:
                # Obligations
                for token in sent:
                    if token.lemma_.lower() in {"must", "shall", "should", "required", "obligated", "agree", "consent", "process", "collect", "use", "share", "store", "protect", "retain", "disclose"}:
                        obligations.add(sent.text.strip())
                        break
                # Semantic similarity to requirements
                if gdpr_requirements:
                    matches = self.semantic_match(sent.text, gdpr_requirements)
                    if matches:
                        section_matches[sent.text] = matches
                        if debug:
                            logging.info(f"[GDPR Match] Section '{header}': '{sent.text}' -> {matches}")
        # Extract lists/tables
        lists_tables = []
        for header, body in sections.items():
            lists_tables.extend(self.extract_lists_and_tables(body))
        if debug:
            logging.info(f"[DEBUG] Extracted sections: {list(sections.keys())}")
            logging.info(f"[DEBUG] Extracted lists/tables: {lists_tables}")
            logging.info(f"[DEBUG] Section matches: {section_matches}")
        return {
            'text': self.extract_data_practices(text),
            'uri': 'http://example.org/document',
            'type': 'privacy_policy',
            'parties': list(parties),
            'obligations': list(obligations),
            'sections': sections,
            'lists_tables': lists_tables,
            'section_matches': section_matches
        }

class DPAExtractor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def extract_semantic_frames(self, text):
        doc = self.nlp(text)
        semantic_frames = []
        for sent in doc.sents:
            frame = self._extract_frame_from_sentence(sent)
            if frame:
                semantic_frames.append(frame)
        return semantic_frames

    def extract(self, text):
        doc = self.nlp(text)
        parties = set()
        obligations = set()
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PERSON"]:
                parties.add(ent.text)
        obligation_verbs = {"must", "shall", "should", "required", "obligated", "agree", "consent", "process", "collect", "use", "share", "store", "protect", "retain", "disclose"}
        for sent in doc.sents:
            for token in sent:
                if token.lemma_.lower() in obligation_verbs:
                    obligations.add(sent.text.strip())
                    break
        return {
            'text': text,
            'uri': 'http://example.org/document',
            'type': 'dpa',
            'parties': list(parties),
            'obligations': list(obligations)
        }

def extract_email_addresses(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(email_pattern, text)

def extract_phone_numbers(text):
    phone_pattern = r'\+?\d[\d -]{8,12}\d'
    return re.findall(phone_pattern, text)