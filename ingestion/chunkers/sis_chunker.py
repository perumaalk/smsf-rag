# 2.1 SIS Chunker (ingestion/chunkers/sis_chunker.py)
import re
from llama_index.core import Document

SECTION_REGEX = re.compile(
    r"(s\s?\d+[A-Z]?)\s*(\([^)]+\))?",
    re.IGNORECASE
)

def chunk_sis_act(text: str, source: str) -> list[Document]:
    chunks = []
    matches = list(SECTION_REGEX.finditer(text))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        section_text = text[start:end].strip()
        section = match.group(1).replace(" ", "")
        subsection = match.group(2).strip("()") if match.group(2) else None

        doc = Document(
            text=section_text,
            metadata={
                "doc_type": "legislation",
                "act": "SIS Act 1993",
                "section": section.replace("s", ""),
                "subsection": subsection,
                "jurisdiction": "Australia",
                "source": source,
            },
            id_=f"sis_act_1993_{section}_{subsection or 'base'}"
        )

        chunks.append(doc)

    return chunks


