"""
Generate formatted DMD phenotypes for seed_data.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from ingest_hpo_associations import parse_hpo_phenotype_file, convert_to_seed_data_format

project_root = Path(__file__).parent.parent.parent
data_dir = project_root / 'data'

phenotypes = parse_hpo_phenotype_file(data_dir / 'phenotypes_for_NCBIGene_1756')
seed_phenotypes = convert_to_seed_data_format(phenotypes, 'DMD')

# Format as Python dict list
output = '        "phenotypes": [\n'
for p in seed_phenotypes:
    output += '            {\n'
    output += f'                "feature_key": "{p["feature_key"]}",\n'
    output += f'                "hpo_id": "{p["hpo_id"]}",\n'
    output += f'                "term": "{p["term"]}",\n'
    output += f'                "specificity": {p["specificity"]},\n'
    output += '            },\n'
output += '        ],'

print(output)

