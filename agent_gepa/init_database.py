import json
import os

DATA_FILE = 'pdf_metadata.json'

initial_data = {
    "version": 1,
    "created_by": "init_database.py",
    "documents": []
}

if os.path.exists(DATA_FILE):
    print(f"⚠️  {DATA_FILE} ya existe, no se sobrescribirá.")
else:
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=2)
    print(f"✅ {DATA_FILE} creado con estructura mínima.")
