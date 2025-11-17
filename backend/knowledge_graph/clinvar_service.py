"""
ClinVar variant annotation service.

Supplements Monarch and clinical_data.py with:
- Clinical significance for point mutations (multi-lab consensus)
- Review status and confidence metrics
- Additional phenotype associations for LAMA2/CAPN3

Note: This service is SUPPLEMENTARY. The clinical_data.py remains the authoritative
source for reading frame predictions and FDA therapy eligibility, which are essential
for DMD vs BMD distinction and treatment decisions.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class ClinVarService:
    """
    Query ClinVar for variant clinical significance using NCBI E-utilities API.

    Features:
    - Rate limiting (10 req/sec with API key, 3 req/sec without)
    - 30-day cache to minimize API calls
    - HGVS-based variant lookups
    - Gene-based variant searches
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 days

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: str = ".clinvar_cache",
        rate_limit: Optional[int] = None
    ):
        """
        Initialize ClinVar service.

        Args:
            api_key: NCBI API key (get from https://www.ncbi.nlm.nih.gov/account/).
                If None, will check NCBI_API_KEY environment variable.
            cache_dir: Directory for caching API responses.
            rate_limit: Maximum requests per second. If None, auto-detects based on
                API key (10/sec with key, 3/sec without).
        """
        self.api_key = api_key or os.getenv("NCBI_API_KEY")

        # Auto-detect rate limit based on API key availability
        if rate_limit is None:
            self.rate_limit = 10 if self.api_key else 3
        else:
            self.rate_limit = rate_limit

        self.last_request_time = 0

        # Set up cache directory
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        logger.info(
            f"ClinVar service initialized (rate limit: {self.rate_limit} req/sec, "
            f"cache: {self.cache_dir}, API key: {'yes' if self.api_key else 'no'})"
        )

    def _rate_limit(self):
        """Enforce rate limiting to respect NCBI API guidelines."""
        elapsed = time.time() - self.last_request_time
        min_interval = 1.0 / self.rate_limit

        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.json"

    def _read_cache(self, cache_key: str) -> Optional[Dict]:
        """Read from cache if available and not expired."""
        cache_file = self._get_cache_path(cache_key)

        if not cache_file.exists():
            return None

        # Check if cache is expired
        age = time.time() - cache_file.stat().st_mtime
        if age > self.CACHE_TTL_SECONDS:
            logger.debug(f"Cache expired for {cache_key} (age: {age / 86400:.1f} days)")
            return None

        try:
            data = json.loads(cache_file.read_text())
            logger.debug(f"Cache hit for {cache_key}")
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Cache read error for {cache_key}: {e}")
            return None

    def _write_cache(self, cache_key: str, data: Dict):
        """Write data to cache."""
        cache_file = self._get_cache_path(cache_key)
        try:
            cache_file.write_text(json.dumps(data, indent=2))
            logger.debug(f"Cache written for {cache_key}")
        except OSError as e:
            logger.warning(f"Cache write error for {cache_key}: {e}")

    def _api_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Make an API request to NCBI E-utilities.

        Args:
            endpoint: E-utilities endpoint (esearch.fcgi, esummary.fcgi, etc.)
            params: Query parameters

        Returns:
            JSON response or None if request fails
        """
        self._rate_limit()

        # Add API key if available
        if self.api_key:
            params = {**params, 'api_key': self.api_key}

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"ClinVar API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"ClinVar API response not valid JSON: {e}")
            return None

    def get_variant_by_hgvs(
        self,
        hgvs_expression: str,
        gene: str
    ) -> Optional[Dict]:
        """
        Fetch ClinVar data for a variant by HGVS expression.

        Args:
            hgvs_expression: HGVS variant notation (e.g., "c.5021del", "p.Arg1234*")
            gene: Gene symbol (e.g., "DMD", "LAMA2")

        Returns:
            Dict with clinical significance, review status, phenotypes, or None if not found.
            Example:
            {
                "variation_id": "VCV000123456",
                "clinical_significance": "Pathogenic",
                "review_status": "criteria provided, multiple submitters",
                "phenotypes": ["Duchenne muscular dystrophy"],
                "gene_symbol": "DMD",
                "hgvs": "c.5021del",
                "submitter_count": 5
            }
        """
        # Generate cache key
        cache_key = hashlib.md5(f"{gene}:{hgvs_expression}".encode()).hexdigest()

        # Check cache
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached

        # Search for variant
        search_query = f"{gene}[gene] AND {hgvs_expression}[variant name]"
        logger.info(f"Searching ClinVar for: {search_query}")

        search_result = self._api_request(
            "esearch.fcgi",
            {
                'db': 'clinvar',
                'term': search_query,
                'retmode': 'json',
                'retmax': 1  # We expect one specific variant
            }
        )

        if not search_result or 'esearchresult' not in search_result:
            logger.warning(f"No search results for {gene}:{hgvs_expression}")
            return None

        id_list = search_result['esearchresult'].get('idlist', [])
        if not id_list:
            logger.info(f"No ClinVar variants found for {gene}:{hgvs_expression}")
            # Cache negative result
            self._write_cache(cache_key, {})
            return None

        # Fetch variant details
        variant_id = id_list[0]
        summary_result = self._api_request(
            "esummary.fcgi",
            {
                'db': 'clinvar',
                'id': variant_id,
                'retmode': 'json'
            }
        )

        if not summary_result or 'result' not in summary_result:
            logger.warning(f"Failed to fetch summary for variant ID {variant_id}")
            return None

        # Extract variant data
        variant_data = summary_result['result'].get(variant_id, {})

        # Parse clinical significance
        clin_sig = variant_data.get('clinical_significance', {})

        result = {
            'variation_id': variant_id,
            'clinical_significance': clin_sig.get('description', 'Unknown'),
            'review_status': clin_sig.get('review_status', 'Unknown'),
            'gene_symbol': gene,
            'hgvs': hgvs_expression,
            'variant_name': variant_data.get('title', ''),
            'phenotypes': self._extract_phenotypes(variant_data),
            'submitter_count': len(variant_data.get('supporting_submissions', {}).get('rcv', [])),
        }

        # Cache result
        self._write_cache(cache_key, result)

        return result

    def search_variants_by_gene(
        self,
        gene_symbol: str,
        variant_type: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search ClinVar for all variants in a gene.

        Args:
            gene_symbol: Gene symbol (e.g., "DMD", "LAMA2", "CAPN3")
            variant_type: Optional filter by variant type (e.g., "deletion", "missense")
            max_results: Maximum number of variants to return

        Returns:
            List of variant dictionaries with basic information
        """
        # Build search query
        query_parts = [f"{gene_symbol}[gene]"]
        if variant_type:
            query_parts.append(f"{variant_type}[variant type]")
        search_query = " AND ".join(query_parts)

        # Generate cache key
        cache_key = hashlib.md5(f"search:{search_query}:{max_results}".encode()).hexdigest()

        # Check cache
        cached = self._read_cache(cache_key)
        if cached is not None:
            return cached.get('variants', [])

        logger.info(f"Searching ClinVar for variants: {search_query}")

        # Search for variant IDs
        search_result = self._api_request(
            "esearch.fcgi",
            {
                'db': 'clinvar',
                'term': search_query,
                'retmode': 'json',
                'retmax': max_results
            }
        )

        if not search_result or 'esearchresult' not in search_result:
            logger.warning(f"No search results for {search_query}")
            return []

        id_list = search_result['esearchresult'].get('idlist', [])
        if not id_list:
            logger.info(f"No ClinVar variants found for {search_query}")
            self._write_cache(cache_key, {'variants': []})
            return []

        logger.info(f"Found {len(id_list)} variants, fetching summaries...")

        # Fetch summaries (batch up to 100 at a time)
        variants = []
        for i in range(0, len(id_list), 100):
            batch_ids = id_list[i:i+100]

            summary_result = self._api_request(
                "esummary.fcgi",
                {
                    'db': 'clinvar',
                    'id': ','.join(batch_ids),
                    'retmode': 'json'
                }
            )

            if not summary_result or 'result' not in summary_result:
                logger.warning(f"Failed to fetch summaries for batch {i//100 + 1}")
                continue

            # Parse each variant
            for vid in batch_ids:
                variant_data = summary_result['result'].get(vid, {})
                if not variant_data:
                    continue

                # Extract germline classification (contains clinical significance)
                germline = variant_data.get('germline_classification', {})

                # Extract variant type from obj_type or variation_set
                variant_type = variant_data.get('obj_type', 'Unknown')
                if variant_type == 'Unknown':
                    variation_set = variant_data.get('variation_set', [{}])
                    if variation_set:
                        variant_type = variation_set[0].get('variant_type', 'Unknown')

                # Extract gene symbol from genes array
                genes = variant_data.get('genes', [])
                gene_sym = genes[0].get('symbol', gene_symbol) if genes else gene_symbol

                # Extract genomic location
                variation_set = variant_data.get('variation_set', [{}])
                location = {}
                if variation_set and variation_set[0].get('variation_loc'):
                    loc = variation_set[0]['variation_loc'][0]
                    location = {
                        'chromosome': loc.get('chr', ''),
                        'start': loc.get('start', ''),
                        'stop': loc.get('stop', ''),
                        'assembly': loc.get('assembly_name', ''),
                    }

                # Extract phenotypes from trait_set
                phenotypes = []
                trait_set = germline.get('trait_set', [])
                for trait in trait_set:
                    trait_name = trait.get('trait_name', '')
                    if trait_name:
                        phenotypes.append(trait_name)

                variants.append({
                    'variation_id': vid,
                    'clinvar_accession': variant_data.get('accession', ''),
                    'variant_name': variant_data.get('title', ''),
                    'clinical_significance': germline.get('description', 'Not provided'),
                    'review_status': germline.get('review_status', 'Not provided'),
                    'last_evaluated': germline.get('last_evaluated', 'Not provided'),
                    'gene_symbol': gene_sym,
                    'variant_type': variant_type,
                    'chromosome': location.get('chromosome', ''),
                    'position_start': location.get('start', ''),
                    'position_stop': location.get('stop', ''),
                    'assembly': location.get('assembly', ''),
                    'phenotypes': phenotypes,
                })

        logger.info(f"Retrieved {len(variants)} variant summaries")

        # Cache results
        self._write_cache(cache_key, {'variants': variants})

        return variants

    def enrich_variant_annotation(self, variant_dict: Dict) -> Dict:
        """
        Enrich a variant annotation with ClinVar data.

        This method supplements existing variant data from clinical_data.py or Monarch
        with ClinVar's clinical significance, without overwriting critical fields like
        reading_frame or eligible_treatments.

        Args:
            variant_dict: Existing variant annotation (from clinical_data.py or Monarch)

        Returns:
            Enriched variant dict with ClinVar data added (original dict is NOT modified)
        """
        enriched = variant_dict.copy()

        # Try to get HGVS expression and gene from variant dict
        hgvs = variant_dict.get('hgvs') or variant_dict.get('variant_name')
        gene = variant_dict.get('gene') or variant_dict.get('gene_symbol')

        if not hgvs or not gene:
            logger.debug(f"Cannot enrich variant: missing HGVS or gene")
            return enriched

        # Query ClinVar
        clinvar_data = self.get_variant_by_hgvs(hgvs, gene)

        if not clinvar_data:
            logger.debug(f"No ClinVar data found for {gene}:{hgvs}")
            return enriched

        # Add ClinVar data WITHOUT overwriting critical fields
        enriched['clinvar_id'] = clinvar_data.get('variation_id')
        enriched['clinvar_significance'] = clinvar_data.get('clinical_significance')
        enriched['clinvar_review_status'] = clinvar_data.get('review_status')

        # Optionally merge phenotypes (if not already present)
        if 'phenotypes' not in enriched:
            enriched['phenotypes'] = clinvar_data.get('phenotypes', [])

        logger.info(f"Enriched variant {gene}:{hgvs} with ClinVar data")

        return enriched

    def _extract_phenotypes(self, variant_data: Dict) -> List[str]:
        """Extract phenotype names from ClinVar variant data."""
        phenotypes = []

        # Try various fields where phenotypes might be stored
        if 'phenotype_list' in variant_data:
            for pheno in variant_data['phenotype_list']:
                if isinstance(pheno, dict) and 'trait' in pheno:
                    phenotypes.append(pheno['trait'])

        if 'trait_set' in variant_data:
            for trait in variant_data['trait_set']:
                if isinstance(trait, dict) and 'trait_name' in trait:
                    phenotypes.append(trait['trait_name'])

        return list(set(phenotypes))  # Remove duplicates
