from rdflib import Graph, URIRef, Literal, Namespace

class KnowledgeGraphBuilder:
    def __init__(self, ontology_path):
        self.graph = Graph()
        self.ontology_path = ontology_path
        self.namespace = Namespace("http://example.org/")

    def load_ontology(self):
        self.graph.parse(self.ontology_path)

    def add_document(self, document_uri, document_type, parties, obligations):
        doc_node = URIRef(document_uri)
        self.graph.add((doc_node, self.namespace.type, Literal(document_type)))

        for party in parties:
            party_node = URIRef(party)
            self.graph.add((doc_node, self.namespace.hasParty, party_node))

        for obligation in obligations:
            obligation_node = URIRef(obligation)
            self.graph.add((doc_node, self.namespace.hasObligation, obligation_node))

    def save_graph(self, output_path):
        self.graph.serialize(destination=output_path, format='turtle')

    def query_graph(self, query):
        return self.graph.query(query)

    def build_kg(self, extracted_data):
        """Builds the knowledge graph from extracted data."""
        self.load_ontology()
        document_uri = extracted_data.get('uri', 'http://example.org/document')
        document_type = extracted_data.get('type', 'Unknown')
        parties = extracted_data.get('parties', [])
        obligations = extracted_data.get('obligations', [])
        self.add_document(document_uri, document_type, parties, obligations)
        return self.graph