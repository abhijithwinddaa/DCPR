import os
import sys
import shutil
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.db_service import DBService
from app.services.graph_service import GraphService

# Add workspace root directory (4 levels up) to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from knowledge.pipeline.ingestor import Ingestor
from knowledge.pipeline.normalizer import Normalizer
from knowledge.pipeline.parsers import SemanticParser
from knowledge.pipeline.reference_resolver import ReferenceResolver
from knowledge.pipeline.exporter import Exporter
from knowledge.graph_builder.generator import GraphGenerator
from app.db.neo4j_conn import neo4j_db

def generate_rule_engine_contract_from_graph(G, scheme_id):
    """
    Constructs the exact Rule Engine data contract structure for a scheme.
    Matches the original run_graph_builder.py logic.
    """
    citation = G.nodes[scheme_id].get("citation", scheme_id.split(":")[-1])
    contract = {
        "scheme_id": citation,
        "scheme_uri": scheme_id,
        "conditions": [],
        "formulae": [],
        "tables": [],
        "definitions": [],
        "references": [],
        "inputs": [],
        "outputs": [],
        "facts": []
    }
    
    # Collect direct children
    for v in G.successors(scheme_id):
        if v not in G:
            continue
        label = G.nodes[v].get("label")
        properties = {k: val for k, val in G.nodes[v].items() if k != "label"}
        properties["id"] = v
        
        if label == "Condition":
            contract["conditions"].append(properties)
        elif label == "Formula":
            contract["formulae"].append(properties)
            # Find lookup tables connected to this formula
            for fv in G.successors(v):
                if fv in G and G.nodes[fv].get("label") == "Table":
                    t_props = {tk: tv for tk, tv in G.nodes[fv].items() if tk != "label"}
                    t_props["id"] = fv
                    if t_props not in contract["tables"]:
                        contract["tables"].append(t_props)
        elif label == "Table":
            if properties not in contract["tables"]:
                contract["tables"].append(properties)
        elif label == "Definition":
            contract["definitions"].append(properties)
        elif label == "Reference":
            contract["references"].append(properties)
        elif label == "InputParameter":
            contract["inputs"].append(properties)
        elif label == "OutputParameter":
            contract["outputs"].append(properties)
        elif label == "Fact":
            contract["facts"].append(properties)
            
    return contract

class IngestionService:
    """
    Coordinates PDF layouts OCR parsing, CKM validation, Postgres persistence,
    and Graph loader synchronization.
    """

    @staticmethod
    def process_pdf(db: Session, version_id: str, file_path: str, page_range_str: str = "188-197") -> bool:
        """
        Runs the complete extraction pipeline, saves output to relational schemas,
        updates version status, and populates the graph database.
        """
        try:
            print(f"[IngestionService] Starting ingestion pipeline for version {version_id}...")
            DBService.update_version_status(db, version_id, "PROCESSING")

            # Parse page range
            pages = IngestionService._parse_page_range(page_range_str)
            print(f"[IngestionService] Extracted page range: {pages}")

            # 1. Ingest PDF & Extract Page IR (L0/L1)
            release_id = f"dcpr2034:extraction:{version_id}"
            ingestor = Ingestor(file_path, release_id)
            page_docs = ingestor.ingest(pages)
            if not page_docs:
                raise ValueError("PDF text extraction returned no pages.")

            # 2. Text/AST Normalization (L2)
            normalizer = Normalizer()
            normalized_pages = normalizer.normalize(page_docs)

            # 3. Extract Canonical Knowledge Model candidates (L3)
            parser = SemanticParser(release_id)
            raw_package = parser.parse(normalized_pages)

            # 4. Resolve References and Precedences (L4)
            resolver = ReferenceResolver()
            resolved_package = resolver.resolve(raw_package)

            # 5. Export to Canonical Folder Layout (L5)
            knowledge_output_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "knowledge"
            )
            exporter = Exporter(knowledge_output_path)
            exporter.export(resolved_package)

            # 6. Save package components to SQL database (PostgreSQL/SQLite)
            entities_to_save = IngestionService._map_package_to_entities(resolved_package)
            DBService.save_knowledge_entities(db, version_id, entities_to_save)

            # 7. Generate & Load Graph Nodes/Edges
            generator = GraphGenerator(input_dir=knowledge_output_path)
            nodes, relationships, metadata = generator.extract()
            GraphService.load_graph_data(nodes, relationships, metadata)

            # 8. Generate and save the Rule Engine Contract
            neo4j_db.connect()
            contract_path_dest = os.path.join(settings.STORAGE_DIR, "rule_engine_contract.json")
            contract_path_know = os.path.join(knowledge_output_path, "graphs", "rule_engine_contract.json")
            
            contracts = {}
            if neo4j_db.use_fallback:
                G = neo4j_db.nx_graph
                schemes = [n for n in G.nodes() if G.nodes[n].get("label") == "Scheme"]
                for scheme_id in schemes:
                    citation = G.nodes[scheme_id].get("citation", scheme_id)
                    contracts[citation] = generate_rule_engine_contract_from_graph(G, scheme_id)
            else:
                # Retrieve from Neo4j (We emulate using active driver or query)
                # For safety, compile from the local NetworkX graph we just saved
                # (which represents the exact Neo4j state since they are synced)
                # Seed load a networkx helper
                from knowledge.graph_builder.loader import GraphLoader
                loader = GraphLoader(base_output_path=knowledge_output_path)
                G = loader.load(nodes, relationships, metadata)
                schemes = [n for n in G.nodes() if G.nodes[n].get("label") == "Scheme"]
                for scheme_id in schemes:
                    citation = G.nodes[scheme_id].get("citation", scheme_id)
                    contracts[citation] = generate_rule_engine_contract_from_graph(G, scheme_id)

            # Save contract to both knowledge and storage directory
            os.makedirs(os.path.dirname(contract_path_dest), exist_ok=True)
            os.makedirs(os.path.dirname(contract_path_know), exist_ok=True)
            for path in (contract_path_dest, contract_path_know):
                with open(path, "w", encoding="utf-8") as f:
                    import json
                    json.dump(contracts, f, indent=2, sort_keys=False)
            
            # Clear rule engine service cached contract so it reloads the new one
            from app.services.rule_engine_service import RuleEngineService
            RuleEngineService._contract_data = None
            RuleEngineService._engine_instance = None

            # Mark version as completed
            DBService.update_version_status(db, version_id, "COMPLETED")
            print(f"[IngestionService] Pipeline completed successfully for version {version_id}!")
            return True

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[IngestionService] Ingestion failed: {e}\n{error_trace}")
            DBService.update_version_status(db, version_id, "FAILED", error_log=f"{e}\n{error_trace}")
            return False

    @staticmethod
    def process_pdf_background(version_id: str, file_path: str, page_range_str: str = "188-197"):
        """Background-safe wrapper that creates its own DB session."""
        from app.db.postgres import get_sessionmaker
        SessionLocal = get_sessionmaker()
        db = SessionLocal()
        try:
            IngestionService.process_pdf(db, version_id, file_path, page_range_str)
        finally:
            db.close()

    @staticmethod
    def _parse_page_range(pages_str: str):
        """Parses range strings like '188-197' or returns None for 'all' pages."""
        if not pages_str or str(pages_str).strip().lower() in ["all", "none", "*", ""]:
            return None
        pages = set()
        for part in str(pages_str).split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                start, end = part.split('-')
                pages.update(range(int(start), int(end) + 1))
            else:
                pages.add(int(part))
        return sorted(list(pages)) if pages else None

    @staticmethod
    def _map_package_to_entities(package: dict) -> list[dict]:
        """Maps resolved package lists into standard relational DB entity row dicts."""
        entities = []
        today = date.today()

        # 1. Scheme/Regulation entities
        for ent in package.get("entities", []):
            ent_type = ent.get("type", "REGULATION")
            label = "SCHEME" if ent_type == "SCHEME" or "scheme" in ent.get("id", "") else "REGULATION"
            entities.append({
                "entity_uri": ent.get("id"),
                "entity_label": label,
                "normalized_citation": ent.get("normalized_citation", ent.get("citation", "")),
                "entity_data": ent,
                "effective_period_start": today
            })

        # 2. Conditions
        for cond in package.get("conditions", []):
            entities.append({
                "entity_uri": cond.get("id"),
                "entity_label": "FACT",  # Conditions map to FACT constraints
                "normalized_citation": cond.get("phase", "APPLICABILITY"),
                "entity_data": cond,
                "effective_period_start": today
            })

        # 3. Facts
        for fact in package.get("facts", []):
            entities.append({
                "entity_uri": fact.get("id"),
                "entity_label": "FACT",
                "normalized_citation": fact.get("concept_type_id", ""),
                "entity_data": fact,
                "effective_period_start": today
            })

        # 4. Formulae
        for form in package.get("formulae", []):
            entities.append({
                "entity_uri": form.get("id"),
                "entity_label": "FORMULA",
                "normalized_citation": form.get("output_id", ""),
                "entity_data": form,
                "effective_period_start": today
            })

        # 5. Tables
        for table in package.get("tables", []):
            entities.append({
                "entity_uri": table.get("id"),
                "entity_label": "TABLE",
                "normalized_citation": table.get("title", ""),
                "entity_data": table,
                "effective_period_start": today
            })

        # 6. Definitions
        for defn in package.get("definitions", []):
            entities.append({
                "entity_uri": defn.get("id"),
                "entity_label": "DEFINITION",
                "normalized_citation": defn.get("term", ""),
                "entity_data": defn,
                "effective_period_start": today
            })

        # Deduplicate entities by entity_uri to prevent UNIQUE constraint database crashes
        seen_uris = set()
        deduplicated_entities = []
        for ent in entities:
            uri = ent.get("entity_uri")
            if uri not in seen_uris:
                seen_uris.add(uri)
                deduplicated_entities.append(ent)
        
        return deduplicated_entities
