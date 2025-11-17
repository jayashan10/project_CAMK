"""
Google Gemini File Search RAG service for clinical guidelines.

This module provides a RAG (Retrieval-Augmented Generation) service using Google's
Gemini File Search API to retrieve evidence-based recommendations from clinical
guidelines for muscular dystrophy diagnoses.

Features:
- Upload clinical guideline PDFs with rich metadata
- Semantic search over guidelines using Gemini embeddings
- Extract evidence-based recommendations with citations
- Support for disease-specific and general clinical queries
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Try to import google genai (optional dependency)
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class GuidanceEvidence:
    """Evidence passage retrieved from clinical guideline."""

    recommendation: str  # The recommendation text (synthesized by Gemini)
    source: str  # Guideline title/name
    evidence_level: Optional[str] = None  # Level A/B/C if available
    citation: str = ""  # File URI or reference
    confidence: float = 1.0  # Rank-based confidence score
    chunk_id: Optional[str] = None  # Grounding chunk identifier
    retrieved_text: Optional[str] = None  # Actual text passage retrieved from guideline


class GeminiFileSearchService:
    """
    RAG service for clinical guideline retrieval using Gemini File Search API.

    This service uploads clinical guidelines as PDFs and enables semantic search
    for evidence-based treatment recommendations and diagnostic protocols.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini File Search service.

        Args:
            api_key: Google Gemini API key. If None, reads from GOOGLE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")

        if not self.api_key:
            logger.warning(
                "No Gemini API key found (GOOGLE_API_KEY or GOOGLE_GEMINI_API_KEY). "
                "RAG service will be disabled."
            )
            self.client = None
            self.store = None
            return

        try:
            self.client = genai.Client(api_key=self.api_key)
            self.store = None  # Will be set during initialize_store()
            self._file_display_names = {}  # Cache: file_id -> display_name
            logger.info("Gemini File Search service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None
            self.store = None
            self._file_display_names = {}

    def initialize_store(self, store_name: str = "md_clinical_guidelines") -> bool:
        """
        Initialize or retrieve existing File Search store.

        Args:
            store_name: Display name for the File Search store.

        Returns:
            True if successful, False otherwise.
        """
        if not self.client:
            logger.warning("Gemini client not initialized; cannot create store")
            return False

        try:
            # Try to find existing store
            stores = list(self.client.file_search_stores.list())

            # Use the LAST (most recent) available store or create a new one
            if stores:
                self.store = stores[-1]  # Use last store (most recently created)
                logger.info(f"Using existing File Search store: {self.store.name}")

                # Populate file display name cache
                self._populate_file_cache()

                return True

            # Create new store if not found (using correct API with config)
            self.store = self.client.file_search_stores.create(
                config={'display_name': store_name}
            )
            logger.info(f"Created new File Search store: {store_name} ({self.store.name})")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize File Search store: {e}")
            self.client = None
            self.store = None
            return False

    def upload_guideline(
        self, file_path: str, metadata: Optional[Dict] = None, display_name: Optional[str] = None
    ) -> bool:
        """
        Upload clinical guideline PDF to File Search store.

        Args:
            file_path: Path to guideline PDF file.
            metadata: Optional metadata dict. Example:
                {
                    "disease_code": "DMD",
                    "guideline_type": "management",
                    "publication_year": 2018,
                    "evidence_level": "Level_A"
                }
            display_name: Optional display name for the file. If None, uses filename.

        Returns:
            True if upload successful, False otherwise.
        """
        if not self.client or not self.store:
            logger.warning("Gemini client/store not initialized; skipping upload")
            return False

        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return False

        try:
            file_name = display_name or Path(file_path).name

            # Step 1: Upload file via Files API first
            import time
            uploaded_file = self.client.files.upload(
                file=file_path,
                config={'display_name': file_name}
            )

            logger.info(f"📤 File uploaded: {file_name} ({uploaded_file.name})")

            # Step 2: Convert metadata to Gemini format for import_file
            custom_metadata = []
            if metadata:
                for key, value in metadata.items():
                    if isinstance(value, str):
                        custom_metadata.append({"key": key, "string_value": value})
                    elif isinstance(value, (int, float)):
                        custom_metadata.append({"key": key, "numeric_value": float(value)})
                    elif isinstance(value, bool):
                        custom_metadata.append({"key": key, "string_value": str(value)})

            # Step 3: Import file into File Search store
            # Note: custom_metadata not supported in current Python SDK
            # Try using config parameter instead
            try:
                operation = self.client.file_search_stores.import_file(
                    file_search_store_name=self.store.name,
                    file_name=uploaded_file.name,
                    config={'custom_metadata': custom_metadata} if custom_metadata else {}
                )
            except TypeError:
                # Fallback: import without metadata
                logger.warning("Custom metadata not supported in Python SDK, importing without metadata")
                operation = self.client.file_search_stores.import_file(
                    file_search_store_name=self.store.name,
                    file_name=uploaded_file.name
                )

            # Wait for import to complete
            max_wait = 60  # 60 seconds timeout
            wait_time = 0
            while not operation.done and wait_time < max_wait:
                time.sleep(2)
                operation = self.client.operations.get(operation)
                wait_time += 2

            if not operation.done:
                logger.warning(f"Import operation still pending after {max_wait}s for {file_name}")
                return False

            logger.info(f"✅ Imported guideline: {file_name}")
            if metadata:
                logger.info(f"   Metadata attached: {metadata}")
            return True

        except Exception as e:
            logger.error(f"Failed to upload {file_path}: {e}")
            return False

    def search_guidelines(
        self,
        query: str,
        disease_code: Optional[str] = None,
        metadata_filter: Optional[str] = None,
        max_results: int = 5,
    ) -> List[GuidanceEvidence]:
        """
        Search clinical guidelines for evidence-based recommendations.

        Args:
            query: Search query (e.g., "corticosteroid therapy recommendations").
            disease_code: Optional disease code to filter results (e.g., "DMD").
            metadata_filter: Optional metadata filter expression (e.g., 'disease_code="DMD"').
            max_results: Maximum number of evidence passages to return.

        Returns:
            List of GuidanceEvidence objects with recommendations and citations.
        """
        if not self.client or not self.store:
            logger.warning("Gemini client/store not initialized; returning empty results")
            return []

        try:
            # Build query with disease context
            if disease_code and disease_code not in query:
                full_query = f"For {disease_code}: {query}"
            else:
                full_query = query

            # Automatically add disease code filter if provided and no metadata filter given
            if disease_code and not metadata_filter:
                metadata_filter = f'disease_code="{disease_code}"'

            # Configure search using correct API with metadata filter
            from google.genai import types

            # Build file search config with optional metadata filter
            file_search_config = types.FileSearch(
                file_search_store_names=[self.store.name]
            )

            # Add metadata filter if provided
            if metadata_filter:
                file_search_config = types.FileSearch(
                    file_search_store_names=[self.store.name],
                    metadata_filter=metadata_filter
                )

            config = types.GenerateContentConfig(
                tools=[
                    types.Tool(file_search=file_search_config)
                ]
            )

            # Generate response
            logger.info("=" * 80)
            logger.info(f"📝 RAG QUERY: '{full_query}'")
            if metadata_filter:
                logger.info(f"🔍 FILTER: {metadata_filter}")
            logger.info("=" * 80)

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",  # Use File Search compatible model
                contents=full_query,
                config=config,
            )

            # Log the synthesized response
            response_text = response.text if hasattr(response, "text") else ""
            logger.info(f"💬 GEMINI RESPONSE ({len(response_text)} chars):")
            logger.info(f"   {response_text[:300]}...")  # First 300 chars
            logger.info("-" * 80)

            # Extract evidence passages
            evidence_list = self._extract_evidence_from_response(response, max_results)

            # Log retrieved evidence details
            logger.info(f"📚 Retrieved {len(evidence_list)} evidence passages from guidelines:")
            for i, evidence in enumerate(evidence_list[:3], 1):  # Show first 3
                logger.info(f"   {i}. Source: {evidence.source}")
                logger.info(f"      Confidence: {evidence.confidence}")
                logger.info(f"      Text: {evidence.retrieved_text[:100] if evidence.retrieved_text else 'N/A'}...")
            logger.info("=" * 80)
            return evidence_list

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []

    def _extract_evidence_from_response(
        self, response, max_results: int = 5
    ) -> List[GuidanceEvidence]:
        """
        Extract evidence passages from Gemini response with grounding metadata.

        Args:
            response: Gemini API response object.
            max_results: Maximum number of evidence items to extract.

        Returns:
            List of GuidanceEvidence objects.
        """
        evidence_list = []

        # Get main recommendation text
        recommendation_text = response.text if hasattr(response, "text") else ""

        # Try to access grounding metadata from candidates[0] (correct location)
        grounding = None
        if hasattr(response, "candidates") and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata"):
                grounding = candidate.grounding_metadata
                logger.info(f"Found grounding_metadata in candidates[0]")
            else:
                logger.warning(f"No grounding_metadata in candidate. Available attributes: {dir(candidate)}")

        # Fallback: check response directly (older API)
        if not grounding and hasattr(response, "grounding_metadata"):
            grounding = response.grounding_metadata
            logger.info(f"Found grounding_metadata in response (legacy)")

        # If no grounding metadata found, return basic response
        if not grounding:
            logger.warning("No grounding metadata found in response")
            if recommendation_text:
                evidence_list.append(
                    GuidanceEvidence(
                        recommendation=recommendation_text,
                        source="Gemini (no specific guideline cited)",
                        confidence=0.5,
                    )
                )
            return evidence_list
        chunks = grounding.grounding_chunks if hasattr(grounding, "grounding_chunks") else []
        supports = grounding.grounding_supports if hasattr(grounding, "grounding_supports") else []

        if not chunks:
            logger.warning("No grounding chunks found in response")
            return evidence_list

        # Track seen chunks to avoid duplicates
        seen_chunks = set()
        all_chunks_info = []  # Collect all chunk information
        all_sources = set()
        all_evidence_levels = set()

        # Process grounding supports (links text segments to source chunks)
        for support_idx, support in enumerate(supports[:max_results]):
            if not hasattr(support, "grounding_chunk_indices"):
                continue

            for chunk_idx in support.grounding_chunk_indices:
                if chunk_idx >= len(chunks) or chunk_idx in seen_chunks:
                    continue

                seen_chunks.add(chunk_idx)
                chunk = chunks[chunk_idx]

                # Extract source information from chunk (it's an object, not dict)
                # Check for retrieved_context attribute (File Search chunks)
                source_title = "Unknown guideline"
                source_uri = ""
                chunk_text = ""

                if hasattr(chunk, "retrieved_context"):
                    retrieved = chunk.retrieved_context
                    if hasattr(retrieved, "title"):
                        source_title = retrieved.title
                    if hasattr(retrieved, "uri"):
                        source_uri = retrieved.uri
                    if hasattr(retrieved, "text"):
                        chunk_text = retrieved.text

                # Fallback: check chunk attributes directly
                if source_title == "Unknown guideline":
                    source_title = getattr(chunk, "title", "Unknown guideline")
                if not source_uri:
                    source_uri = getattr(chunk, "uri", "")
                if not chunk_text:
                    chunk_text = getattr(chunk, "text", "")

                chunk_id = getattr(chunk, "id", f"chunk_{chunk_idx}")

                # Try to get proper display name from file metadata
                # Try both source_uri and source_title (which might be the file ID)
                display_name = self._get_file_display_name(source_uri) or self._get_file_display_name(source_title)
                if display_name:
                    source_title = display_name
                else:
                    # Use source_title or source_uri as fallback (don't skip the chunk!)
                    if source_title and source_title != "Unknown guideline":
                        logger.debug(f"Using source_title as fallback for chunk {chunk_idx}: {source_title}")
                    elif source_uri:
                        source_title = f"Guideline (ID: {source_uri.split('/')[-1]})"
                        logger.debug(f"Using source_uri as fallback for chunk {chunk_idx}: {source_uri}")
                    else:
                        source_title = f"Clinical Guideline {chunk_idx + 1}"
                        logger.debug(f"Using generic name for chunk {chunk_idx}")

                # Log chunk structure for debugging
                logger.debug(f"Chunk {chunk_idx}: title={source_title}, uri={source_uri}")

                # Extract evidence level from chunk text
                evidence_level = self._extract_evidence_level_from_text(chunk_text)
                if evidence_level:
                    all_evidence_levels.add(evidence_level)

                # Store chunk info (only if we have a valid display name)
                all_sources.add(source_title)
                all_chunks_info.append({
                    "text": chunk_text,
                    "source": source_title,
                    "uri": source_uri,
                    "chunk_id": chunk_id,
                    "evidence_level": evidence_level,
                })

        # Return MULTIPLE results: first with full synthesis, rest with just snippets
        if all_chunks_info:
            for idx, chunk_info in enumerate(all_chunks_info[:max_results]):
                # First result: Show full Gemini synthesis + first snippet
                # Subsequent results: Show "Additional evidence" + their snippets
                if idx == 0:
                    # First result with full Gemini answer
                    recommendation = recommendation_text
                    source_display = chunk_info['source']
                    confidence = 1.0
                else:
                    # Subsequent results - just show source without repeating the synthesis
                    recommendation = f"Supporting evidence from {chunk_info['source']}"
                    source_display = chunk_info['source']
                    confidence = 1.0 - (idx * 0.05)  # Slight decrease per position

                evidence = GuidanceEvidence(
                    recommendation=recommendation,
                    source=source_display,
                    evidence_level=chunk_info.get('evidence_level'),
                    citation=f"Retrieved from: {chunk_info['source']}",
                    confidence=max(confidence, 0.7),  # Minimum 0.7
                    chunk_id=chunk_info.get('chunk_id'),
                    retrieved_text=chunk_info['text'],  # Individual snippet
                )
                evidence_list.append(evidence)

        # If no grounded evidence found but we have text, return ungrounded result
        if not evidence_list and recommendation_text:
            evidence_list.append(
                GuidanceEvidence(
                    recommendation=recommendation_text,
                    source="Gemini synthesis (multiple guidelines)",
                    confidence=0.6,
                )
            )

        return evidence_list[:max_results]

    def _populate_file_cache(self):
        """Populate the file display name cache from uploaded files."""
        if not self.client:
            return

        try:
            file_pager = self.client.files.list()
            for file_obj in file_pager:
                # Get file ID (e.g., "files/abc123")
                file_id = file_obj.name if hasattr(file_obj, "name") else None
                if not file_id:
                    continue

                # Extract short ID (e.g., "abc123" from "files/abc123")
                short_id = file_id.split("/")[-1] if "/" in file_id else file_id

                # Get display name
                display_name = None
                if hasattr(file_obj, "display_name") and file_obj.display_name:
                    display_name = file_obj.display_name

                # Cache both formats
                if display_name:
                    self._file_display_names[file_id] = display_name  # files/abc123 -> name
                    self._file_display_names[short_id] = display_name  # abc123 -> name

            logger.debug(f"Cached display names for {len(self._file_display_names) // 2} files")

        except Exception as e:
            logger.warning(f"Failed to populate file cache: {e}")

    def _get_file_display_name(self, file_uri: str) -> Optional[str]:
        """
        Get the proper display name for a file from its URI.

        Args:
            file_uri: File URI (e.g., "files/abc123" or just "abc123")

        Returns:
            Display name of the file, or None if not found.
        """
        if not file_uri:
            return None

        # Check cache first
        if file_uri in self._file_display_names:
            return self._file_display_names[file_uri]

        # Try extracting short ID if it's a full URI
        if "/" in file_uri:
            short_id = file_uri.split("/")[-1]
            if short_id in self._file_display_names:
                return self._file_display_names[short_id]

        # Fallback: Try direct API call (slower)
        if self.client:
            try:
                file_id = file_uri if "/" in file_uri else f"files/{file_uri}"
                file_obj = self.client.files.get(name=file_id)
                if hasattr(file_obj, "display_name") and file_obj.display_name:
                    # Cache it for next time
                    self._file_display_names[file_uri] = file_obj.display_name
                    return file_obj.display_name
            except Exception as e:
                logger.debug(f"Could not get display name for {file_uri}: {e}")

        return None

    def _extract_evidence_level_from_text(self, text: str) -> Optional[str]:
        """
        Extract evidence level (A/B/C) from text content.

        Args:
            text: Text content to search for evidence level.

        Returns:
            Evidence level string (e.g., "Level A") or None.
        """
        if not text:
            return None

        chunk_text = text

        # Look for common evidence level patterns
        patterns = [
            r"Level\s+([ABC])",
            r"Grade\s+([ABC])",
            r"Strength\s+([ABC])",
            r"Evidence\s+level\s+([ABC])",
        ]

        for pattern in patterns:
            match = re.search(pattern, chunk_text, re.IGNORECASE)
            if match:
                return f"Level {match.group(1).upper()}"

        return None

    def list_uploaded_files(self) -> List[Dict]:
        """
        List all documents uploaded to the File Search store.

        Returns:
            List of file information dictionaries with name, id, create_time, and size.
        """
        if not self.client or not self.store:
            logger.warning("Client or store not initialized")
            return []

        try:
            # Use the Files API to list all files
            # The file_search_stores.documents API is not well documented,
            # so we'll list files directly from the Files API
            logger.info(f"Listing files in File Search store: {self.store.name}")

            all_files = []
            page_token = None

            try:
                # List files from the Files API - returns a Pager object
                file_pager = self.client.files.list()

                # Iterate over the pager
                for file_obj in file_pager:
                    # Extract file information
                    file_info = {
                        "name": file_obj.display_name if hasattr(file_obj, 'display_name') and file_obj.display_name else file_obj.name,
                        "id": file_obj.name,  # Full resource name (e.g., "files/abc123")
                        "create_time": str(file_obj.create_time) if hasattr(file_obj, 'create_time') else None,
                    }

                    # Add size if available
                    if hasattr(file_obj, 'size_bytes'):
                        file_info["size_bytes"] = file_obj.size_bytes

                    # Add MIME type if available
                    if hasattr(file_obj, 'mime_type'):
                        file_info["mime_type"] = file_obj.mime_type

                    all_files.append(file_info)

            except Exception as e:
                logger.error(f"Error listing files: {e}")
                import traceback
                logger.debug(traceback.format_exc())

            logger.info(f"Found {len(all_files)} uploaded files")

            # If we found files, return them
            if all_files:
                return all_files

            # Fallback: Return store info
            logger.warning("No files found, returning store info as fallback")
            store_info = self.client.file_search_stores.get(name=self.store.name)
            file_count = getattr(store_info, 'file_count', 0)

            return [{
                "name": f"File Search Store ({file_count} files)",
                "id": self.store.name,
                "file_count": file_count,
            }]

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            import traceback
            logger.error(traceback.format_exc())

            # Final fallback
            return [{
                "name": "File Search Store",
                "id": self.store.name if self.store else "unknown",
                "error": str(e),
            }]

    def delete_file(self, file_name: str) -> bool:
        """
        Delete a file from the File Search store.

        Args:
            file_name: Name/ID of the file to delete.

        Returns:
            True if successful, False otherwise.
        """
        if not self.client or not self.store:
            return False

        try:
            self.client.files.delete(name=file_name)
            logger.info(f"Deleted file: {file_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {file_name}: {e}")
            return False
