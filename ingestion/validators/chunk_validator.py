# 2.2 Validation Rules (ingestion/validators/chunk_validator.py)
def validate_sis_chunks(chunks):
    for c in chunks:
        if len(c.text) > 3500:
            raise ValueError(f"Oversized chunk: {c.id_}")
        if "section" not in c.metadata:
            raise ValueError(f"Missing section metadata: {c.id_}")