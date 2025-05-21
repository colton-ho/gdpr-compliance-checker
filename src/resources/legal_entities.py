from dataclasses import dataclass

@dataclass
class LegalEntity:
    name: str
    address: str
    contact_email: str
    contact_phone: str
    role: str  # e.g., Data Controller, Data Processor

    def __post_init__(self):
        # Validate email and phone format if necessary
        pass

class LegalEntityRegistry:
    def __init__(self):
        self.entities = []

    def add_entity(self, entity: LegalEntity):
        self.entities.append(entity)

    def get_entity_by_name(self, name: str):
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None

    def list_entities(self):
        return self.entities

    def remove_entity(self, name: str):
        self.entities = [entity for entity in self.entities if entity.name != name]