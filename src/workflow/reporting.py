from datetime import datetime
import json

class ComplianceReport:
    def __init__(self, document_name, compliance_status, findings, recommendations):
        self.document_name = document_name
        self.compliance_status = compliance_status
        self.findings = findings
        self.recommendations = recommendations
        self.timestamp = datetime.now().isoformat()

    def generate_report(self):
        report = {
            "document_name": self.document_name,
            "compliance_status": self.compliance_status,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp
        }
        return report

    def save_report(self, file_path):
        report = self.generate_report()
        with open(file_path, 'w') as report_file:
            json.dump(report, report_file, indent=4)

def create_compliance_report(document_name, compliance_status, findings, recommendations, output_path):
    report = ComplianceReport(document_name, compliance_status, findings, recommendations)
    report.save_report(output_path)