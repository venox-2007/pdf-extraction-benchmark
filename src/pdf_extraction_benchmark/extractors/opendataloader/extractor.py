\"\"\"opendataloader extractor adapter (placeholder).\"\"\"

from __future__ import annotations

from pathlib import Path

from pdf_extraction_benchmark.interfaces.base_extractor import BaseExtractor
from pdf_extraction_benchmark.models.extraction_result import ExtractionMetadata, ExtractionResult


class OpendataloaderExtractor(BaseExtractor):
    \"\"\"Placeholder adapter for the opendataloader backend.\"\"\"

    tool_name = \"opendataloader\"

    def extract(self, pdf_path: Path) -> list[ExtractionResult]:
        \"\"\"Return placeholder page results for the given PDF file.\"\"\"
        result = ExtractionResult(
            tool_name=self.tool_name,
            page_number=1,
            extracted_text=\"\",
            metadata=ExtractionMetadata(source_file=pdf_path.name, extra={\"status\": \"not_implemented\"}),
        )
        return [result]
