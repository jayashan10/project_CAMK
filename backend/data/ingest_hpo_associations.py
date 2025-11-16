"""
HPO Association Data Ingestion Script

Processes downloaded HPO association files from HPO browser
and converts them into knowledge graph seed data format.
"""
import csv
from pathlib import Path
from typing import List, Dict, Tuple


def parse_hpo_phenotype_file(file_path: Path) -> List[Dict[str, str]]:
    """
    Parse HPO phenotype association file (tab-separated).
    
    Expected format:
    id\tname
    HP:0003115\tAbnormal EKG
    ...
    """
    phenotypes = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read first line to get headers
        header_line = f.readline().strip()
        headers = [h.strip() for h in header_line.split('\t')]
        
        # Read remaining lines
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                phenotypes.append({
                    'hpo_id': parts[0].strip(),
                    'term': parts[1].strip(),
                    'feature_key': _generate_feature_key(parts[1].strip())
                })
    
    return phenotypes


def parse_disease_association_file(file_path: Path) -> List[Dict[str, str]]:
    """
    Parse disease association file (tab-separated).
    
    Expected format:
    id\tname
    OMIM:310200\tDuchenne muscular dystrophy
    ...
    """
    diseases = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip header line
        f.readline()
        
        # Read remaining lines
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) >= 2:
                diseases.append({
                    'disease_id': parts[0].strip(),
                    'name': parts[1].strip()
                })
    
    return diseases


def _generate_feature_key(term_name: str) -> str:
    """
    Generate a feature key from HPO term name.
    Converts to lowercase, replaces spaces with underscores.
    """
    return term_name.lower().replace(' ', '_').replace('-', '_').replace(',', '')


def calculate_specificity_score(hpo_id: str, term: str, disease_code: str) -> float:
    """
    Calculate specificity score for a phenotype-disease association.
    
    Higher scores indicate more specific/diagnostic features.
    This is a simplified version - in production would use
    frequency data from HPO disease annotations.
    """
    # Highly specific features for DMD/BMD
    highly_specific = [
        'gowers sign',
        'calf muscle pseudohypertrophy',
        'absent muscle dystrophin expression',
        'x-linked inheritance'
    ]
    
    # Moderately specific features
    moderately_specific = [
        'proximal muscle weakness',
        'progressive muscle weakness',
        'dilated cardiomyopathy',
        'respiratory insufficiency',
        'loss of ambulation'
    ]
    
    # Less specific (common across many neuromuscular diseases)
    less_specific = [
        'muscle weakness',
        'elevated circulating creatine kinase',
        'myopathy',
        'hypotonia'
    ]
    
    term_lower = term.lower()
    
    if any(specific in term_lower for specific in highly_specific):
        return 0.9
    elif any(specific in term_lower for specific in moderately_specific):
        return 0.7
    elif any(specific in term_lower for specific in less_specific):
        return 0.4
    else:
        return 0.5  # Default moderate specificity


def convert_to_seed_data_format(
    phenotypes: List[Dict[str, str]],
    disease_code: str = "DMD"
) -> List[Dict]:
    """
    Convert parsed phenotypes to seed_data.py format.
    """
    seed_phenotypes = []
    
    for pheno in phenotypes:
        seed_phenotypes.append({
            'feature_key': pheno['feature_key'],
            'hpo_id': pheno['hpo_id'],
            'term': pheno['term'],
            'specificity': calculate_specificity_score(
                pheno['hpo_id'],
                pheno['term'],
                disease_code
            )
        })
    
    return seed_phenotypes


def main():
    """
    Main ingestion function.
    """
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data'
    
    # Parse phenotype associations
    phenotype_file = data_dir / 'phenotypes_for_NCBIGene_1756'
    if phenotype_file.exists():
        phenotypes = parse_hpo_phenotype_file(phenotype_file)
        print(f"Parsed {len(phenotypes)} phenotypes from {phenotype_file.name}")
        
        # Convert to seed data format
        seed_phenotypes = convert_to_seed_data_format(phenotypes, disease_code="DMD")
        
        # Print first 10 as example
        print("\nFirst 10 phenotypes:")
        for p in seed_phenotypes[:10]:
            print(f"  {p['hpo_id']}: {p['term']} (specificity: {p['specificity']})")
        
        return seed_phenotypes
    else:
        print(f"Error: {phenotype_file} not found")
        return []


if __name__ == '__main__':
    main()

