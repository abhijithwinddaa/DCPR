import os
import sys
import argparse

# Ensure parent directory is in sys.path so we can import knowledge.pipeline
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.pipeline.ingestor import Ingestor
from knowledge.pipeline.normalizer import Normalizer
from knowledge.pipeline.parsers import SemanticParser
from knowledge.pipeline.reference_resolver import ReferenceResolver
from knowledge.pipeline.exporter import Exporter
from knowledge.pipeline.report_generator import ReportGenerator

def parse_args():
    parser = argparse.ArgumentParser(description="DCPR Knowledge Ingestion & Extraction Pipeline")
    parser.add_argument("--pdf", type=str, default="MUMBAI-DCPR.pdf", help="Path to the DCPR source PDF")
    parser.add_argument("--pages", type=str, default="188-197", help="Page range to process (e.g., 188-197)")
    parser.add_argument("--output", type=str, default="knowledge", help="Base output directory")
    parser.add_argument("--release-id", type=str, default="dcpr2034:33-9:extraction-v1", help="ID of the knowledge release package")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=== DCPR KNOWLEDGE EXTRACTION PIPELINE ===")
    print(f"Source PDF:   {args.pdf}")
    print(f"Page Range:   {args.pages}")
    print(f"Output Base:  {args.output}")
    print(f"Release ID:   {args.release_id}")
    print("==========================================")

    # 1. Ingest PDF & Extract Page IR (L0/L1)
    ingestor = Ingestor(args.pdf, args.release_id)
    pages_to_process = parse_page_range(args.pages)
    
    print("\n--- Step 1: Ingesting PDF ---")
    page_docs = ingestor.ingest(pages_to_process)
    if not page_docs:
        print("Ingestion failed. Exiting.")
        sys.exit(1)

    # 2. Text/AST Normalization (L2)
    print("\n--- Step 2: Normalizing text and structure ---")
    normalizer = Normalizer()
    normalized_pages = normalizer.normalize(page_docs)

    # 3. Extract Canonical Knowledge Model candidates (L3)
    print("\n--- Step 3: Extracting regulatory elements ---")
    parser = SemanticParser(args.release_id)
    raw_package = parser.parse(normalized_pages)

    # 4. Resolve References and Precedences (L4)
    print("\n--- Step 4: Resolving cross-references ---")
    resolver = ReferenceResolver()
    resolved_package = resolver.resolve(raw_package)

    # 5. Export to Canonical Folder Layout (L5)
    print("\n--- Step 5: Exporting packages ---")
    exporter = Exporter(args.output)
    exported_paths = exporter.export(resolved_package)

    # 6. Generate Validation & Reference Reports
    print("\n--- Step 6: Generating pipeline reports ---")
    report_gen = ReportGenerator(args.output)
    report_gen.generate(resolved_package, exported_paths)

    print("\nPipeline execution complete! All reports generated successfully.")

def parse_page_range(pages_str):
    """Parses a page range string like '188-197' or '1,3,5' into a set of 1-indexed page integers."""
    pages = set()
    for part in pages_str.split(','):
        if '-' in part:
            start, end = part.split('-')
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(part))
    return sorted(list(pages))

if __name__ == "__main__":
    main()
