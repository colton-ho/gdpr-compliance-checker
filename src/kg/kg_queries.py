from rdflib import Graph, Namespace, URIRef

# Define namespaces
GDPR = Namespace("http://example.org/gdpr#")
LEGAL = Namespace("http://example.org/legal#")

class KGQueries:
    def __init__(self, graph_path):
        self.graph = Graph()
        self.graph.parse(graph_path)

    def get_compliance_status(self, document_uri):
        query = f"""
        PREFIX gdpr: <{GDPR}>
        PREFIX legal: <{LEGAL}>
        
        SELECT ?status
        WHERE {{
            <{document_uri}> legal:hasComplianceStatus ?status .
        }}
        """
        results = self.graph.query(query)
        return [str(row.status) for row in results]

    def get_obligations(self, party_uri):
        query = f"""
        PREFIX gdpr: <{GDPR}>
        PREFIX legal: <{LEGAL}>
        
        SELECT ?obligation
        WHERE {{
            <{party_uri}> legal:hasObligation ?obligation .
        }}
        """
        results = self.graph.query(query)
        return [str(row.obligation) for row in results]

    def check_contract_validity(self, contract_uri):
        query = f"""
        PREFIX gdpr: <{GDPR}>
        PREFIX legal: <{LEGAL}>
        
        SELECT ?validity
        WHERE {{
            <{contract_uri}> legal:hasValidity ?validity .
        }}
        """
        results = self.graph.query(query)
        return [str(row.validity) for row in results]