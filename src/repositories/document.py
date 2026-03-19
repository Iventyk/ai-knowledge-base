from sqlalchemy.orm import Session
from src.db.models.document import Document


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str) -> Document:
        document = Document(name=name)
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def get_all(self):
        return self.session.query(Document).all()

    def delete(self, document: Document):
        self.session.delete(document)
        self.session.commit()
