"""Extract the supplied Line Boss DOCX in document order for implementation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def iter_blocks(document):
    body = document.element.body
    for child in body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)


source = Path(sys.argv[1]).resolve()
document = Document(source)
items = []
for index, block in enumerate(iter_blocks(document), 1):
    if isinstance(block, Paragraph):
        text = block.text.strip()
        if text:
            items.append(
                {
                    "order": index,
                    "kind": "paragraph",
                    "style": block.style.name if block.style else "",
                    "text": text,
                }
            )
    else:
        rows = []
        for row in block.rows:
            rows.append([cell.text.strip() for cell in row.cells])
        items.append({"order": index, "kind": "table", "rows": rows})

print(
    json.dumps(
        {
            "source": str(source),
            "sections": len(document.sections),
            "inline_shapes": len(document.inline_shapes),
            "items": items,
        },
        indent=2,
        ensure_ascii=False,
    )
)
