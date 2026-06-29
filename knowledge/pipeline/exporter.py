import os
import yaml

class Exporter:
    """
    Exporter handles writing the compiled package and individual components
    to the target folder structure.
    """
    def __init__(self, base_output_path="knowledge"):
        self.base_path = base_output_path
        # Standard folders
        self.folders = {
            "regulations": os.path.join(self.base_path, "regulations"),
            "schemes": os.path.join(self.base_path, "schemes"),
            "appendices": os.path.join(self.base_path, "appendices"),
            "definitions": os.path.join(self.base_path, "definitions"),
            "compiled": os.path.join(self.base_path, "instruments", "dcpr-2034", "schemes")
        }

    def _ensure_dirs(self):
        """Ensures all target directories exist."""
        for path in self.folders.values():
            os.makedirs(path, exist_ok=True)

    def export(self, package_dict):
        """
        Exports the parsed package components.
        Returns a dict of file paths written.
        """
        self._ensure_dirs()
        exported_paths = {}

        # 1. Export the complete schema-conforming package (release)
        package_id = package_dict["package"]["package_id"].replace(":", "_")
        compiled_path = os.path.join(self.folders["compiled"], "33-9.yaml")
        
        with open(compiled_path, "w", encoding="utf-8") as f:
            yaml.dump(package_dict, f, default_flow_style=False, sort_keys=False)
        exported_paths["compiled_package"] = compiled_path
        print(f"Exported compiled package to: {compiled_path}")

        # 2. Export Scheme-specific YAML
        scheme_path = os.path.join(self.folders["schemes"], "33-9.yaml")
        # Save just the Scheme entities and binding details
        scheme_data = {
            "schema_version": "dcpr-knowledge-model/v1",
            "package_metadata": package_dict["package"],
            "entities": [e for e in package_dict["entities"] if e["type"] == "SCHEME"],
            "facts": package_dict["facts"],
            "formulae": package_dict["formulae"],
            "tables": package_dict["tables"],
            "conditions": package_dict["conditions"],
            "inputs": package_dict["inputs"],
            "outputs": package_dict["outputs"]
        }
        with open(scheme_path, "w", encoding="utf-8") as f:
            yaml.dump(scheme_data, f, default_flow_style=False, sort_keys=False)
        exported_paths["scheme"] = scheme_path
        print(f"Exported scheme file to: {scheme_path}")

        # 3. Export Definitions YAML
        if package_dict["definitions"]:
            definitions_path = os.path.join(self.folders["definitions"], "33-9-definitions.yaml")
            definitions_data = {
                "schema_version": "dcpr-knowledge-model/v1",
                "definitions": package_dict["definitions"]
            }
            with open(definitions_path, "w", encoding="utf-8") as f:
                yaml.dump(definitions_data, f, default_flow_style=False, sort_keys=False)
            exported_paths["definitions"] = definitions_path
            print(f"Exported definitions file to: {definitions_path}")

        # 4. Export Regulations (provisional if any regulation is extracted)
        reg_entities = [e for e in package_dict["entities"] if e["type"] == "REGULATION"]
        if reg_entities:
            reg_path = os.path.join(self.folders["regulations"], "regulations.yaml")
            with open(reg_path, "w", encoding="utf-8") as f:
                yaml.dump({"entities": reg_entities}, f, default_flow_style=False, sort_keys=False)
            exported_paths["regulations"] = reg_path
            print(f"Exported regulations file to: {reg_path}")

        # 5. Export Appendices (if any)
        app_entities = [e for e in package_dict["entities"] if e["type"] == "APPENDIX"]
        if app_entities:
            app_path = os.path.join(self.folders["appendices"], "appendices.yaml")
            with open(app_path, "w", encoding="utf-8") as f:
                yaml.dump({"entities": app_entities}, f, default_flow_style=False, sort_keys=False)
            exported_paths["appendices"] = app_path
            print(f"Exported appendices file to: {app_path}")

        return exported_paths
