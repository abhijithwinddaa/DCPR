import os
import json
import sys
from app.core.config import settings

# Add workspace root folder to sys.path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from knowledge.rule_engine import RuleEngine

class RuleEngineService:
    """
    Service to run the deterministic zoning calculator and trace generator.
    """
    _engine_instance = None
    _contract_data = None

    @classmethod
    def get_contract_data(cls) -> dict:
        """Loads and caches the rule contract schema from the JSON file."""
        if cls._contract_data is not None:
            return cls._contract_data

        # Paths to search for contract
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        paths_to_try = [
            os.path.join(settings.STORAGE_DIR, "rule_engine_contract.json"),
            os.path.join(project_root, "knowledge", "graphs", "rule_engine_contract.json")
        ]

        for path in paths_to_try:
            if os.path.exists(path):
                print(f"[RuleEngineService] Loading rule contract from {path}...")
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        cls._contract_data = json.load(f)
                    return cls._contract_data
                except Exception as e:
                    print(f"Error loading contract from {path}: {e}")

        # Fallback empty structure
        print("Warning: Rule engine contract JSON not found. Starting with empty rules.")
        cls._contract_data = {}
        return cls._contract_data

    @classmethod
    def get_engine(cls) -> RuleEngine:
        """Retrieves or creates the global RuleEngine instance."""
        if cls._engine_instance is None:
            contract = cls.get_contract_data()
            cls._engine_instance = RuleEngine(contract)
        else:
            # Refresh contract if it was empty initially and has been populated since
            if not cls._contract_data:
                cls._contract_data = cls.get_contract_data()
                cls._engine_instance.contract_data = cls._contract_data
        return cls._engine_instance

    @classmethod
    def evaluate(cls, scheme_id: str, inputs: dict) -> dict:
        """
        Executes AST evaluation for the scheme and compiles eligibility,
        FSI, BUA, and rule trace outputs.
        """
        engine = cls.get_engine()
        
        # Format the scheme_id (e.g. "33(9)" or "dcpr:scheme:33-9")
        clean_scheme_id = scheme_id
        if scheme_id == "dcpr:scheme:33-9":
            clean_scheme_id = "33(9)"
            
        print(f"[RuleEngineService] Evaluating rules for scheme: {clean_scheme_id}")
        return engine.evaluate(clean_scheme_id, inputs)
