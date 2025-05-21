from typing import List, Dict, Any

class SFComparator:
    def __init__(self, dpa_sf: Dict[str, Any], gdpr_sf: Dict[str, Any]):
        self.dpa_sf = dpa_sf
        self.gdpr_sf = gdpr_sf

    def compare(self) -> List[str]:
        discrepancies = []
        for key in self.gdpr_sf.keys():
            if key not in self.dpa_sf:
                discrepancies.append(f"Missing key in DPA SF: {key}")
            elif self.dpa_sf[key] != self.gdpr_sf[key]:
                discrepancies.append(f"Discrepancy found for key '{key}': DPA SF value '{self.dpa_sf[key]}' does not match GDPR SF value '{self.gdpr_sf[key]}'")
        return discrepancies

    def is_compliant(self) -> bool:
        discrepancies = self.compare()
        return len(discrepancies) == 0

# Example usage:
# dpa_sf_example = {"action": "process", "actor": "data_controller", ...}
# gdpr_sf_example = {"action": "process", "actor": "data_controller", ...}
# comparator = SFComparator(dpa_sf_example, gdpr_sf_example)
# compliance_status = comparator.is_compliant()
# print("Compliance Status:", compliance_status)