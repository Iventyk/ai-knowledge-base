from src.tasks.celery import celery_app


@celery_app.task
def process_document_task(document_id: str):
    print(f"Processing document {document_id}")
