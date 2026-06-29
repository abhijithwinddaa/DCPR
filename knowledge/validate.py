import sys
import os
import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

def validate_yaml(schema_path, target_path):
    print(f"Validating {target_path} against {schema_path}...")
    
    if not os.path.exists(schema_path):
        print(f"Error: Schema file {schema_path} not found.")
        return False
        
    if not os.path.exists(target_path):
        print(f"Error: Target file {target_path} not found.")
        return False
        
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading schema YAML: {e}")
        return False
        
    try:
        with open(target_path, 'r', encoding='utf-8') as f:
            target = yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading target YAML: {e}")
        return False
        
    # JSON schema expects JSON-compatible types. 
    # Python-yaml parses dates as datetime.date objects, which jsonschema doesn't recognize as strings.
    # We must recursively convert dates/datetimes to string representations.
    def serialize_dates(data):
        import datetime
        if isinstance(data, dict):
            return {k: serialize_dates(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [serialize_dates(x) for x in data]
        elif isinstance(data, (datetime.date, datetime.datetime)):
            return data.isoformat()
        return data

    target_serialized = serialize_dates(target)
    
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(target_serialized), key=lambda e: e.path)
    
    if not errors:
        print("Success: YAML is valid!")
        return True
    else:
        print(f"Validation failed with {len(errors)} error(s):")
        for i, error in enumerate(errors, 1):
            path = " -> ".join([str(p) for p in error.path]) if error.path else "root"
            print(f"\n[{i}] Error at path '{path}':")
            print(f"    Message: {error.message}")
            print(f"    Validator: {error.validator}")
            print(f"    Schema path: {list(error.schema_path)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        schema = "knowledge/schemas/canonical-knowledge-model.schema.yaml"
        target = "knowledge/instruments/dcpr-2034/schemes/33-9.yaml"
        print(f"Usage: python validate.py [schema_path] [target_path]")
        print(f"Using defaults: schema={schema}, target={target}")
    else:
        schema = sys.argv[1]
        target = sys.argv[2]
        
    success = validate_yaml(schema, target)
    sys.exit(0 if success else 1)
