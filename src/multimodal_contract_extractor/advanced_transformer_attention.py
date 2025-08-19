"""
Advanced Transformer-based Attention Mechanisms for Legal Document Understanding

This module implements breakthrough Transformer attention mechanisms specifically designed 
for legal clause understanding and contract analysis. Novel contributions include:

1. Legal Domain-Aware Multi-Head Attention with jurisdictional context
2. Hierarchical Legal Attention across document semantic levels  
3. Temporal Legal Attention for contract evolution tracking
4. Cross-Document Attention for legal precedent integration
5. Causal Legal Attention for legal reasoning chain modeling
6. Sparse Legal Attention for long document processing efficiency

Theoretical Foundation:
- Transformer architecture with legal domain specialization
- Multi-scale attention mechanisms for hierarchical legal structures
- Temporal attention with legal precedence modeling
- Cross-modal attention for text-layout fusion
- Sparse attention patterns optimized for legal document structure

Academic Target: ACL/EMNLP - "Legal Domain-Specialized Transformer Attention Mechanisms"  
Performance Target: >20% improvement over standard BERT in legal clause classification
"""

from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class LegalAttentionType(Enum):
    """Types of legal-specialized attention mechanisms."""
    JURISDICTIONAL = "jurisdictional"  # Attention based on legal jurisdiction
    HIERARCHICAL = "hierarchical"  # Multi-level document hierarchy attention
    TEMPORAL = "temporal"  # Time-aware attention for contract evolution
    PRECEDENT = "precedent"  # Cross-document precedent attention
    CAUSAL = "causal"  # Causal reasoning chain attention
    SPARSE_LEGAL = "sparse_legal"  # Efficient attention for long legal documents
    CROSS_MODAL = "cross_modal"  # Text-layout-semantic fusion attention


class LegalSemanticLevel(Enum):
    """Hierarchical levels of legal semantic processing."""
    TOKEN = "token"  # Individual legal terms
    PHRASE = "phrase"  # Legal phrases and expressions
    CLAUSE = "clause"  # Individual contract clauses
    SECTION = "section"  # Document sections
    ARTICLE = "article"  # Major document articles
    DOCUMENT = "document"  # Entire legal document
    CORPUS = "corpus"  # Cross-document corpus level


class JurisdictionType(Enum):
    """Legal jurisdictions for context-aware processing."""
    COMMON_LAW = "common_law"  # Common law jurisdictions
    CIVIL_LAW = "civil_law"  # Civil law jurisdictions
    MIXED_LAW = "mixed_law"  # Mixed legal systems
    INTERNATIONAL = "international"  # International law
    FEDERAL = "federal"  # Federal jurisdiction
    STATE = "state"  # State/provincial jurisdiction
    LOCAL = "local"  # Local jurisdiction


@dataclass
class LegalToken:
    """Enhanced token representation for legal documents."""
    token_id: int
    text: str
    semantic_level: LegalSemanticLevel
    legal_category: Optional[str] = None  # e.g., "obligation", "right", "condition"
    jurisdiction_context: Optional[JurisdictionType] = None
    confidence: float = 1.0
    position_in_clause: Optional[int] = None
    temporal_context: Optional[float] = None  # Timestamp for temporal modeling
    embeddings: Optional[np.ndarray] = None

    def __post_init__(self):
        """Initialize token embeddings if not provided."""
        if self.embeddings is None:
            self.embeddings = np.random.randn(768) * 0.1  # BERT-like embedding size


@dataclass
class LegalAttentionHead:
    """Individual attention head with legal specialization."""
    head_id: int
    attention_type: LegalAttentionType
    embedding_dim: int = 768
    head_dim: int = 64
    dropout_rate: float = 0.1
    temperature: float = 1.0

    # Legal-specific parameters
    jurisdiction_weight: float = 0.1
    temporal_decay: float = 0.95
    hierarchy_bias: float = 0.05

    # Learned parameters
    W_q: Optional[np.ndarray] = None
    W_k: Optional[np.ndarray] = None
    W_v: Optional[np.ndarray] = None
    legal_bias: Optional[np.ndarray] = None

    def __post_init__(self):
        """Initialize attention parameters."""
        if self.W_q is None:
            self.W_q = np.random.randn(self.embedding_dim, self.head_dim) * 0.1
        if self.W_k is None:
            self.W_k = np.random.randn(self.embedding_dim, self.head_dim) * 0.1
        if self.W_v is None:
            self.W_v = np.random.randn(self.embedding_dim, self.head_dim) * 0.1
        if self.legal_bias is None:
            self.legal_bias = np.zeros(self.head_dim)


class JurisdictionalAttention:
    """
    Jurisdictional attention mechanism that adapts attention patterns 
    based on legal jurisdiction and regulatory context.
    """

    def __init__(self, embedding_dim: int = 768, num_jurisdictions: int = 10):
        self.embedding_dim = embedding_dim
        self.num_jurisdictions = num_jurisdictions

        # Jurisdiction-specific embeddings
        self.jurisdiction_embeddings = {
            jurisdiction: np.random.randn(embedding_dim) * 0.1
            for jurisdiction in JurisdictionType
        }

        # Learned jurisdiction attention weights
        self.jurisdiction_attention_matrix = np.random.randn(
            len(JurisdictionType), len(JurisdictionType)
        ) * 0.1

    def compute_jurisdictional_bias(self, tokens: List[LegalToken]) -> np.ndarray:
        """Compute attention bias based on jurisdictional context."""
        seq_len = len(tokens)
        bias_matrix = np.zeros((seq_len, seq_len))

        for i, token_i in enumerate(tokens):
            for j, token_j in enumerate(tokens):
                # Same jurisdiction gets positive bias
                if (token_i.jurisdiction_context is not None and
                    token_j.jurisdiction_context is not None):

                    if token_i.jurisdiction_context == token_j.jurisdiction_context:
                        bias_matrix[i, j] = 0.2  # Positive bias for same jurisdiction
                    else:
                        # Cross-jurisdiction bias based on legal compatibility
                        i_idx = list(JurisdictionType).index(token_i.jurisdiction_context)
                        j_idx = list(JurisdictionType).index(token_j.jurisdiction_context)
                        bias_matrix[i, j] = self.jurisdiction_attention_matrix[i_idx, j_idx]

        return bias_matrix

    def apply_jurisdictional_attention(self, attention_scores: np.ndarray,
                                     tokens: List[LegalToken]) -> np.ndarray:
        """Apply jurisdictional bias to attention scores."""
        jurisdictional_bias = self.compute_jurisdictional_bias(tokens)
        return attention_scores + jurisdictional_bias


class HierarchicalLegalAttention:
    """
    Hierarchical attention mechanism that processes legal documents at multiple 
    semantic levels with cross-level interaction.
    """

    def __init__(self, embedding_dim: int = 768, num_levels: int = 6):
        self.embedding_dim = embedding_dim
        self.num_levels = num_levels

        # Level-specific projection matrices
        self.level_projections = {}
        for level in LegalSemanticLevel:
            self.level_projections[level] = np.random.randn(embedding_dim, embedding_dim) * 0.1

        # Cross-level attention matrices
        self.cross_level_attention = np.random.randn(
            len(LegalSemanticLevel), len(LegalSemanticLevel)
        ) * 0.1

        # Hierarchical position encodings
        self.hierarchical_encodings = self._initialize_hierarchical_encodings()

    def _initialize_hierarchical_encodings(self) -> Dict[LegalSemanticLevel, np.ndarray]:
        """Initialize hierarchical position encodings for each semantic level."""
        encodings = {}

        for i, level in enumerate(LegalSemanticLevel):
            # Sinusoidal encoding with level-specific frequency
            encoding = np.zeros(self.embedding_dim)
            for pos in range(self.embedding_dim // 2):
                freq = 1.0 / (10000 ** ((2 * pos) / self.embedding_dim))
                encoding[2 * pos] = np.sin((i + 1) * freq)
                encoding[2 * pos + 1] = np.cos((i + 1) * freq)
            encodings[level] = encoding

        return encodings

    def compute_hierarchical_attention(self, tokens: List[LegalToken]) -> np.ndarray:
        """Compute attention weights considering hierarchical semantic structure."""
        seq_len = len(tokens)
        hierarchical_scores = np.zeros((seq_len, seq_len))

        for i, token_i in enumerate(tokens):
            for j, token_j in enumerate(tokens):
                # Get semantic levels
                level_i = token_i.semantic_level
                level_j = token_j.semantic_level

                # Cross-level attention based on hierarchical relationship
                level_i_idx = list(LegalSemanticLevel).index(level_i)
                level_j_idx = list(LegalSemanticLevel).index(level_j)

                cross_level_score = self.cross_level_attention[level_i_idx, level_j_idx]

                # Hierarchical distance penalty
                level_distance = abs(level_i_idx - level_j_idx)
                distance_penalty = np.exp(-0.1 * level_distance)

                hierarchical_scores[i, j] = cross_level_score * distance_penalty

        return hierarchical_scores

    def add_hierarchical_encodings(self, token_embeddings: List[np.ndarray],
                                 tokens: List[LegalToken]) -> List[np.ndarray]:
        """Add hierarchical position encodings to token embeddings."""
        enhanced_embeddings = []

        for embedding, token in zip(token_embeddings, tokens):
            level_encoding = self.hierarchical_encodings[token.semantic_level]
            enhanced_embedding = embedding + 0.1 * level_encoding
            enhanced_embeddings.append(enhanced_embedding)

        return enhanced_embeddings


class TemporalLegalAttention:
    """
    Temporal attention mechanism for tracking legal document evolution, 
    contract amendments, and temporal legal relationships.
    """

    def __init__(self, embedding_dim: int = 768, max_time_horizon: float = 365.0):
        self.embedding_dim = embedding_dim
        self.max_time_horizon = max_time_horizon  # days

        # Temporal encoding parameters
        self.temporal_encoding_dim = 128
        self.W_temporal = np.random.randn(self.temporal_encoding_dim, embedding_dim) * 0.1

        # Learned temporal decay parameters
        self.temporal_decay_rates = {
            'short_term': 0.1,    # Hours to days
            'medium_term': 0.01,  # Days to weeks
            'long_term': 0.001    # Weeks to months
        }

    def compute_temporal_encoding(self, timestamp: float) -> np.ndarray:
        """Compute temporal encoding for a given timestamp."""
        encoding = np.zeros(self.temporal_encoding_dim)

        # Normalize timestamp to [0, 1] range
        normalized_time = min(timestamp / (self.max_time_horizon * 24 * 3600), 1.0)

        # Sinusoidal temporal encoding
        for i in range(self.temporal_encoding_dim // 2):
            freq = 1.0 / (10000 ** (2 * i / self.temporal_encoding_dim))
            encoding[2 * i] = np.sin(normalized_time * freq)
            encoding[2 * i + 1] = np.cos(normalized_time * freq)

        return encoding

    def compute_temporal_attention_bias(self, tokens: List[LegalToken],
                                      current_time: float) -> np.ndarray:
        """Compute temporal attention bias based on token timestamps."""
        seq_len = len(tokens)
        temporal_bias = np.zeros((seq_len, seq_len))

        for i, token_i in enumerate(tokens):
            for j, token_j in enumerate(tokens):
                if (token_i.temporal_context is not None and
                    token_j.temporal_context is not None):

                    # Time difference in seconds
                    time_diff = abs(token_i.temporal_context - token_j.temporal_context)

                    # Temporal decay based on time difference
                    if time_diff < 3600:  # Same hour
                        decay_rate = self.temporal_decay_rates['short_term']
                    elif time_diff < 86400 * 7:  # Same week
                        decay_rate = self.temporal_decay_rates['medium_term']
                    else:  # Longer periods
                        decay_rate = self.temporal_decay_rates['long_term']

                    temporal_weight = np.exp(-decay_rate * time_diff)
                    temporal_bias[i, j] = temporal_weight

        return temporal_bias

    def apply_temporal_attention(self, attention_scores: np.ndarray,
                               tokens: List[LegalToken],
                               current_time: Optional[float] = None) -> np.ndarray:
        """Apply temporal attention bias to base attention scores."""
        if current_time is None:
            current_time = time.time()

        temporal_bias = self.compute_temporal_attention_bias(tokens, current_time)
        return attention_scores * (1.0 + 0.2 * temporal_bias)


class CrossDocumentPrecedentAttention:
    """
    Cross-document attention mechanism for integrating legal precedents
    and similar contract clauses from external documents.
    """

    def __init__(self, embedding_dim: int = 768, max_precedents: int = 100):
        self.embedding_dim = embedding_dim
        self.max_precedents = max_precedents

        # Precedent database (simplified in-memory storage)
        self.precedent_database = {}

        # Cross-document attention parameters
        self.W_precedent_query = np.random.randn(embedding_dim, embedding_dim) * 0.1
        self.W_precedent_key = np.random.randn(embedding_dim, embedding_dim) * 0.1
        self.precedent_similarity_threshold = 0.7

    def add_precedent(self, precedent_id: str, precedent_embedding: np.ndarray,
                     precedent_metadata: Dict[str, Any]):
        """Add legal precedent to the database."""
        self.precedent_database[precedent_id] = {
            'embedding': precedent_embedding,
            'metadata': precedent_metadata
        }

        # Maintain database size limit
        if len(self.precedent_database) > self.max_precedents:
            # Remove oldest precedent (simplified FIFO)
            oldest_key = next(iter(self.precedent_database))
            del self.precedent_database[oldest_key]

    def retrieve_relevant_precedents(self, query_embedding: np.ndarray,
                                   top_k: int = 10) -> List[Tuple[str, float, np.ndarray]]:
        """Retrieve most relevant precedents for a query embedding."""
        similarities = []

        query_normalized = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)

        for precedent_id, precedent_data in self.precedent_database.items():
            precedent_embedding = precedent_data['embedding']
            precedent_normalized = precedent_embedding / (np.linalg.norm(precedent_embedding) + 1e-8)

            similarity = np.dot(query_normalized, precedent_normalized)

            if similarity > self.precedent_similarity_threshold:
                similarities.append((precedent_id, similarity, precedent_embedding))

        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def compute_precedent_attention(self, token_embeddings: List[np.ndarray]) -> np.ndarray:
        """Compute attention weights incorporating relevant precedents."""
        seq_len = len(token_embeddings)
        precedent_attention = np.zeros((seq_len, seq_len))

        for i, embedding in enumerate(token_embeddings):
            # Query for relevant precedents
            relevant_precedents = self.retrieve_relevant_precedents(embedding, top_k=5)

            if relevant_precedents:
                # Compute attention bias based on precedent similarity
                precedent_bias = 0.0
                for _, similarity, _ in relevant_precedents:
                    precedent_bias += similarity
                precedent_bias /= len(relevant_precedents)

                # Apply precedent bias to attention weights
                for j in range(seq_len):
                    precedent_attention[i, j] = precedent_bias * 0.1

        return precedent_attention


class CausalLegalAttention:
    """
    Causal attention mechanism for modeling legal reasoning chains
    and cause-effect relationships in legal documents.
    """

    def __init__(self, embedding_dim: int = 768):
        self.embedding_dim = embedding_dim

        # Causal relationship indicators
        self.causal_indicators = {
            'cause': ['because', 'due to', 'as a result of', 'caused by', 'owing to'],
            'effect': ['therefore', 'thus', 'consequently', 'as a result', 'hence'],
            'condition': ['if', 'when', 'unless', 'provided that', 'subject to'],
            'exception': ['except', 'however', 'but', 'unless', 'save for']
        }

        # Causal attention masks
        self.causal_mask_types = {
            'forward_only': 'future_tokens_masked',
            'bidirectional': 'no_masking',
            'conditional': 'condition_dependent_masking'
        }

    def identify_causal_relationships(self, tokens: List[LegalToken]) -> List[Tuple[int, int, str]]:
        """Identify causal relationships between tokens."""
        causal_relationships = []

        for i, token in enumerate(tokens):
            token_text = token.text.lower()

            # Check for causal indicators
            for relationship_type, indicators in self.causal_indicators.items():
                for indicator in indicators:
                    if indicator in token_text:
                        # Look for related tokens in context window
                        context_window = 10
                        start_idx = max(0, i - context_window)
                        end_idx = min(len(tokens), i + context_window + 1)

                        for j in range(start_idx, end_idx):
                            if j != i:
                                causal_relationships.append((i, j, relationship_type))

        return causal_relationships

    def create_causal_attention_mask(self, tokens: List[LegalToken],
                                   mask_type: str = 'conditional') -> np.ndarray:
        """Create attention mask based on causal relationships."""
        seq_len = len(tokens)
        causal_mask = np.ones((seq_len, seq_len))

        if mask_type == 'forward_only':
            # Traditional causal mask (lower triangular)
            causal_mask = np.tril(causal_mask)
        elif mask_type == 'conditional':
            # Custom mask based on legal causal relationships
            causal_relationships = self.identify_causal_relationships(tokens)

            for i, j, relationship_type in causal_relationships:
                if relationship_type in ['cause', 'condition']:
                    # Cause/condition tokens can attend to effect tokens
                    causal_mask[i, j] = 1.0
                elif relationship_type == 'effect':
                    # Effect tokens have limited attention to future tokens
                    causal_mask[i, j] = 0.5

        return causal_mask

    def apply_causal_attention(self, attention_scores: np.ndarray,
                             tokens: List[LegalToken]) -> np.ndarray:
        """Apply causal attention masking to attention scores."""
        causal_mask = self.create_causal_attention_mask(tokens)

        # Apply mask (set masked positions to large negative value)
        masked_scores = attention_scores + (causal_mask - 1) * 1e9

        return masked_scores


class SparseLegalAttention:
    """
    Sparse attention mechanism optimized for long legal documents
    with legal structure-aware sparsity patterns.
    """

    def __init__(self, embedding_dim: int = 768, sparsity_ratio: float = 0.1):
        self.embedding_dim = embedding_dim
        self.sparsity_ratio = sparsity_ratio

        # Legal structure patterns for sparsity
        self.legal_attention_patterns = {
            'clause_local': 'attend_within_clause',
            'section_summary': 'attend_to_section_headers',
            'cross_reference': 'attend_to_references',
            'temporal_sequence': 'attend_to_temporal_neighbors'
        }

    def create_legal_sparsity_mask(self, tokens: List[LegalToken]) -> np.ndarray:
        """Create sparsity mask based on legal document structure."""
        seq_len = len(tokens)
        sparsity_mask = np.zeros((seq_len, seq_len))

        # Group tokens by clauses
        clause_groups = {}
        for i, token in enumerate(tokens):
            clause_pos = token.position_in_clause or 0
            if clause_pos not in clause_groups:
                clause_groups[clause_pos] = []
            clause_groups[clause_pos].append(i)

        # Apply attention patterns
        for i, token in enumerate(tokens):
            # 1. Local clause attention (always include)
            clause_pos = token.position_in_clause or 0
            if clause_pos in clause_groups:
                for j in clause_groups[clause_pos]:
                    sparsity_mask[i, j] = 1.0

            # 2. Cross-clause attention (sparse)
            for j, other_token in enumerate(tokens):
                if i != j and token.semantic_level == other_token.semantic_level:
                    # Same semantic level tokens can attend to each other
                    sparsity_mask[i, j] = 0.5

            # 3. Hierarchical attention (parent-child relationships)
            for j, other_token in enumerate(tokens):
                token_level_idx = list(LegalSemanticLevel).index(token.semantic_level)
                other_level_idx = list(LegalSemanticLevel).index(other_token.semantic_level)

                # Parent-child or child-parent relationships
                if abs(token_level_idx - other_level_idx) == 1:
                    sparsity_mask[i, j] = 0.8

        # Apply sparsity ratio by keeping only top-k connections
        for i in range(seq_len):
            row = sparsity_mask[i]
            k = max(1, int(seq_len * self.sparsity_ratio))
            top_k_indices = np.argsort(row)[-k:]

            # Zero out all but top-k connections
            sparse_row = np.zeros(seq_len)
            sparse_row[top_k_indices] = row[top_k_indices]
            sparsity_mask[i] = sparse_row

        return sparsity_mask

    def apply_sparse_attention(self, attention_scores: np.ndarray,
                             tokens: List[LegalToken]) -> np.ndarray:
        """Apply legal structure-aware sparse attention."""
        sparsity_mask = self.create_legal_sparsity_mask(tokens)

        # Apply sparsity mask
        sparse_attention = attention_scores * sparsity_mask

        return sparse_attention


class LegalMultiHeadAttention:
    """
    Advanced multi-head attention mechanism combining all legal-specialized 
    attention types for comprehensive legal document understanding.
    """

    def __init__(self, embedding_dim: int = 768, num_heads: int = 12,
                 dropout: float = 0.1):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.head_dim = embedding_dim // num_heads
        self.dropout = dropout

        # Initialize attention heads with different specializations
        self.attention_heads = self._initialize_specialized_heads()

        # Attention components
        self.jurisdictional_attention = JurisdictionalAttention(embedding_dim)
        self.hierarchical_attention = HierarchicalLegalAttention(embedding_dim)
        self.temporal_attention = TemporalLegalAttention(embedding_dim)
        self.precedent_attention = CrossDocumentPrecedentAttention(embedding_dim)
        self.causal_attention = CausalLegalAttention(embedding_dim)
        self.sparse_attention = SparseLegalAttention(embedding_dim)

        # Output projection
        self.W_o = np.random.randn(embedding_dim, embedding_dim) * 0.1

    def _initialize_specialized_heads(self) -> List[LegalAttentionHead]:
        """Initialize attention heads with different legal specializations."""
        heads = []
        attention_types = list(LegalAttentionType)

        for i in range(self.num_heads):
            attention_type = attention_types[i % len(attention_types)]
            head = LegalAttentionHead(
                head_id=i,
                attention_type=attention_type,
                embedding_dim=self.embedding_dim,
                head_dim=self.head_dim
            )
            heads.append(head)

        return heads

    async def forward(self, token_embeddings: List[np.ndarray],
                     tokens: List[LegalToken],
                     attention_mask: Optional[np.ndarray] = None) -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """Forward pass through legal multi-head attention."""

        seq_len = len(token_embeddings)
        if seq_len == 0:
            return [], {}

        # Convert to matrix form
        X = np.stack(token_embeddings)  # [seq_len, embedding_dim]

        # Compute base attention scores for all heads
        all_head_outputs = []
        attention_weights_by_head = {}

        for head in self.attention_heads:
            # Compute Q, K, V for this head
            Q = np.dot(X, head.W_q)  # [seq_len, head_dim]
            K = np.dot(X, head.W_k)  # [seq_len, head_dim]
            V = np.dot(X, head.W_v)  # [seq_len, head_dim]

            # Base attention scores
            attention_scores = np.dot(Q, K.T) / math.sqrt(self.head_dim)

            # Apply specialized attention based on head type
            if head.attention_type == LegalAttentionType.JURISDICTIONAL:
                attention_scores = self.jurisdictional_attention.apply_jurisdictional_attention(
                    attention_scores, tokens
                )
            elif head.attention_type == LegalAttentionType.HIERARCHICAL:
                hierarchical_bias = self.hierarchical_attention.compute_hierarchical_attention(tokens)
                attention_scores += hierarchical_bias
            elif head.attention_type == LegalAttentionType.TEMPORAL:
                attention_scores = self.temporal_attention.apply_temporal_attention(
                    attention_scores, tokens
                )
            elif head.attention_type == LegalAttentionType.PRECEDENT:
                precedent_bias = self.precedent_attention.compute_precedent_attention(token_embeddings)
                attention_scores += precedent_bias
            elif head.attention_type == LegalAttentionType.CAUSAL:
                attention_scores = self.causal_attention.apply_causal_attention(
                    attention_scores, tokens
                )
            elif head.attention_type == LegalAttentionType.SPARSE_LEGAL:
                attention_scores = self.sparse_attention.apply_sparse_attention(
                    attention_scores, tokens
                )

            # Apply attention mask if provided
            if attention_mask is not None:
                attention_scores += (attention_mask - 1) * 1e9

            # Softmax to get attention weights
            attention_weights = self._softmax(attention_scores)

            # Apply dropout (simulated)
            if self.dropout > 0:
                dropout_mask = np.random.binomial(1, 1 - self.dropout, attention_weights.shape)
                attention_weights = attention_weights * dropout_mask / (1 - self.dropout)

            # Compute attended output
            head_output = np.dot(attention_weights, V)  # [seq_len, head_dim]
            all_head_outputs.append(head_output)

            # Store attention weights for analysis
            attention_weights_by_head[f"head_{head.head_id}_{head.attention_type.value}"] = attention_weights

        # Concatenate all head outputs
        concatenated_output = np.concatenate(all_head_outputs, axis=1)  # [seq_len, embedding_dim]

        # Final output projection
        final_output = np.dot(concatenated_output, self.W_o)  # [seq_len, embedding_dim]

        # Convert back to list format
        output_embeddings = [final_output[i] for i in range(seq_len)]

        # Compute attention analysis metrics
        attention_analysis = self._analyze_attention_patterns(attention_weights_by_head, tokens)

        return output_embeddings, attention_analysis

    def _softmax(self, scores: np.ndarray) -> np.ndarray:
        """Apply softmax with numerical stability."""
        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        return exp_scores / (np.sum(exp_scores, axis=-1, keepdims=True) + 1e-8)

    def _analyze_attention_patterns(self, attention_weights: Dict[str, np.ndarray],
                                  tokens: List[LegalToken]) -> Dict[str, Any]:
        """Analyze attention patterns for legal insights."""
        analysis = {
            'attention_entropy': {},
            'legal_focus_patterns': {},
            'cross_jurisdictional_attention': 0.0,
            'temporal_attention_strength': 0.0,
            'hierarchical_attention_distribution': {}
        }

        for head_name, weights in attention_weights.items():
            # Compute attention entropy (measure of attention concentration)
            entropy_values = []
            for i in range(weights.shape[0]):
                row_entropy = -np.sum(weights[i] * np.log(weights[i] + 1e-8))
                entropy_values.append(row_entropy)
            analysis['attention_entropy'][head_name] = np.mean(entropy_values)

            # Legal focus patterns (attention to different legal categories)
            legal_categories = {}
            for i, token in enumerate(tokens):
                if token.legal_category:
                    if token.legal_category not in legal_categories:
                        legal_categories[token.legal_category] = 0.0
                    legal_categories[token.legal_category] += np.sum(weights[:, i])

            analysis['legal_focus_patterns'][head_name] = legal_categories

        # Cross-jurisdictional attention analysis
        cross_juris_attention = 0.0
        total_pairs = 0

        for i, token_i in enumerate(tokens):
            for j, token_j in enumerate(tokens):
                if (token_i.jurisdiction_context is not None and
                    token_j.jurisdiction_context is not None and
                    token_i.jurisdiction_context != token_j.jurisdiction_context):

                    # Average attention across all heads for this cross-jurisdictional pair
                    avg_attention = np.mean([weights[i, j] for weights in attention_weights.values()])
                    cross_juris_attention += avg_attention
                    total_pairs += 1

        if total_pairs > 0:
            analysis['cross_jurisdictional_attention'] = cross_juris_attention / total_pairs

        # Hierarchical attention distribution
        hierarchy_distribution = {}
        for level in LegalSemanticLevel:
            level_tokens = [i for i, token in enumerate(tokens) if token.semantic_level == level]
            if level_tokens:
                level_attention = 0.0
                count = 0
                for head_weights in attention_weights.values():
                    for i in level_tokens:
                        level_attention += np.sum(head_weights[i, :])
                        count += 1
                if count > 0:
                    hierarchy_distribution[level.value] = level_attention / count

        analysis['hierarchical_attention_distribution'] = hierarchy_distribution

        return analysis


class LegalTransformerLayer:
    """
    Complete transformer layer with legal-specialized attention and feed-forward networks.
    """

    def __init__(self, embedding_dim: int = 768, num_heads: int = 12,
                 ff_dim: int = 3072, dropout: float = 0.1):
        self.embedding_dim = embedding_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.dropout = dropout

        # Multi-head attention
        self.attention = LegalMultiHeadAttention(embedding_dim, num_heads, dropout)

        # Feed-forward network with legal domain specialization
        self.ff_W1 = np.random.randn(embedding_dim, ff_dim) * 0.1
        self.ff_W2 = np.random.randn(ff_dim, embedding_dim) * 0.1
        self.ff_b1 = np.zeros(ff_dim)
        self.ff_b2 = np.zeros(embedding_dim)

        # Legal domain-specific parameters
        self.legal_domain_weights = {
            'contract': np.random.randn(embedding_dim) * 0.1,
            'litigation': np.random.randn(embedding_dim) * 0.1,
            'regulation': np.random.randn(embedding_dim) * 0.1,
            'patent': np.random.randn(embedding_dim) * 0.1
        }

    async def forward(self, token_embeddings: List[np.ndarray],
                     tokens: List[LegalToken],
                     legal_domain: str = 'contract') -> Tuple[List[np.ndarray], Dict[str, Any]]:
        """Forward pass through legal transformer layer."""

        if not token_embeddings:
            return [], {}

        # Multi-head attention
        attended_embeddings, attention_analysis = await self.attention.forward(
            token_embeddings, tokens
        )

        # Residual connection and layer norm (simplified)
        attention_output = []
        for orig, attended in zip(token_embeddings, attended_embeddings):
            residual_output = orig + attended
            # Simple layer normalization
            mean = np.mean(residual_output)
            std = np.std(residual_output)
            normalized = (residual_output - mean) / (std + 1e-8)
            attention_output.append(normalized)

        # Feed-forward network
        ff_outputs = []
        for embedding in attention_output:
            # First linear transformation + ReLU
            hidden = np.maximum(0, np.dot(embedding, self.ff_W1) + self.ff_b1)

            # Apply dropout (simulated)
            if self.dropout > 0:
                dropout_mask = np.random.binomial(1, 1 - self.dropout, hidden.shape)
                hidden = hidden * dropout_mask / (1 - self.dropout)

            # Second linear transformation
            output = np.dot(hidden, self.ff_W2) + self.ff_b2

            # Legal domain adaptation
            if legal_domain in self.legal_domain_weights:
                domain_bias = self.legal_domain_weights[legal_domain]
                output = output + 0.1 * domain_bias

            ff_outputs.append(output)

        # Final residual connection and layer norm
        final_outputs = []
        for attention_out, ff_out in zip(attention_output, ff_outputs):
            final_output = attention_out + ff_out
            # Layer normalization
            mean = np.mean(final_output)
            std = np.std(final_output)
            normalized = (final_output - mean) / (std + 1e-8)
            final_outputs.append(normalized)

        return final_outputs, attention_analysis


class LegalTransformerModel:
    """
    Complete legal transformer model with multiple specialized layers
    for comprehensive legal document understanding.
    """

    def __init__(self, vocab_size: int = 30000, embedding_dim: int = 768,
                 num_layers: int = 12, num_heads: int = 12,
                 max_seq_length: int = 2048):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        self.num_heads = num_heads
        self.max_seq_length = max_seq_length

        # Token embeddings
        self.token_embeddings = np.random.randn(vocab_size, embedding_dim) * 0.1

        # Legal transformer layers
        self.layers = []
        for i in range(num_layers):
            layer = LegalTransformerLayer(embedding_dim, num_heads)
            self.layers.append(layer)

        # Output heads for different legal tasks
        self.task_heads = {
            'clause_classification': np.random.randn(embedding_dim, 20) * 0.1,  # 20 clause types
            'entity_extraction': np.random.randn(embedding_dim, 10) * 0.1,     # 10 entity types
            'relationship_detection': np.random.randn(embedding_dim, 15) * 0.1, # 15 relation types
            'risk_assessment': np.random.randn(embedding_dim, 5) * 0.1         # 5 risk levels
        }

    async def process_legal_document(self, token_ids: List[int],
                                   legal_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process legal document through the transformer model."""
        start_time = time.time()

        # Convert token IDs to LegalToken objects
        tokens = self._create_legal_tokens(token_ids, legal_metadata)

        # Get token embeddings
        token_embeddings = [self.token_embeddings[token_id] for token_id in token_ids]

        # Add legal hierarchical encodings
        hierarchical_attention = HierarchicalLegalAttention(self.embedding_dim)
        enhanced_embeddings = hierarchical_attention.add_hierarchical_encodings(
            token_embeddings, tokens
        )

        # Process through transformer layers
        current_embeddings = enhanced_embeddings
        layer_analyses = []

        for i, layer in enumerate(self.layers):
            layer_output, layer_analysis = await layer.forward(
                current_embeddings, tokens, legal_metadata.get('domain', 'contract')
            )
            current_embeddings = layer_output
            layer_analysis['layer_id'] = i
            layer_analyses.append(layer_analysis)

        # Apply task-specific heads
        task_outputs = {}
        for task_name, task_head in self.task_heads.items():
            # Pool sequence representations (simple mean pooling)
            if current_embeddings:
                pooled_representation = np.mean(current_embeddings, axis=0)
                task_logits = np.dot(pooled_representation, task_head)
                task_probs = self._softmax(task_logits)
                task_outputs[task_name] = {
                    'logits': task_logits,
                    'probabilities': task_probs,
                    'prediction': np.argmax(task_probs)
                }
            else:
                task_outputs[task_name] = {
                    'logits': np.zeros(task_head.shape[1]),
                    'probabilities': np.zeros(task_head.shape[1]),
                    'prediction': 0
                }

        processing_time = time.time() - start_time

        # Compute comprehensive analysis
        comprehensive_analysis = self._compute_comprehensive_analysis(
            layer_analyses, tokens, current_embeddings
        )

        return {
            'final_embeddings': current_embeddings,
            'task_predictions': task_outputs,
            'layer_analyses': layer_analyses,
            'comprehensive_analysis': comprehensive_analysis,
            'processing_metrics': {
                'processing_time': processing_time,
                'tokens_processed': len(tokens),
                'layers_processed': len(self.layers),
                'throughput': len(tokens) / processing_time if processing_time > 0 else 0
            }
        }

    def _create_legal_tokens(self, token_ids: List[int],
                           metadata: Dict[str, Any]) -> List[LegalToken]:
        """Create LegalToken objects from token IDs and metadata."""
        tokens = []

        # Extract jurisdiction and domain from metadata
        jurisdiction = metadata.get('jurisdiction', JurisdictionType.COMMON_LAW)
        if isinstance(jurisdiction, str):
            try:
                jurisdiction = JurisdictionType(jurisdiction)
            except ValueError:
                jurisdiction = JurisdictionType.COMMON_LAW

        for i, token_id in enumerate(token_ids):
            # Simulate token text (in real implementation, would use tokenizer)
            token_text = f"token_{token_id}"

            # Assign semantic levels based on position and patterns
            if i < len(token_ids) * 0.1:  # First 10% are likely document-level
                semantic_level = LegalSemanticLevel.DOCUMENT
            elif i < len(token_ids) * 0.3:  # Next 20% are sections
                semantic_level = LegalSemanticLevel.SECTION
            elif i < len(token_ids) * 0.7:  # Next 40% are clauses
                semantic_level = LegalSemanticLevel.CLAUSE
            else:  # Rest are tokens/phrases
                semantic_level = LegalSemanticLevel.TOKEN

            # Assign legal categories based on token patterns (simplified)
            legal_categories = ['obligation', 'right', 'condition', 'term', 'reference']
            legal_category = legal_categories[token_id % len(legal_categories)]

            token = LegalToken(
                token_id=i,
                text=token_text,
                semantic_level=semantic_level,
                legal_category=legal_category,
                jurisdiction_context=jurisdiction,
                position_in_clause=i % 50,  # Simplified clause positioning
                temporal_context=time.time() + i * 0.1  # Simulate temporal context
            )
            tokens.append(token)

        return tokens

    def _softmax(self, logits: np.ndarray) -> np.ndarray:
        """Apply softmax to logits."""
        exp_logits = np.exp(logits - np.max(logits))
        return exp_logits / np.sum(exp_logits)

    def _compute_comprehensive_analysis(self, layer_analyses: List[Dict[str, Any]],
                                      tokens: List[LegalToken],
                                      final_embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Compute comprehensive analysis of legal document processing."""

        analysis = {
            'attention_evolution': [],
            'legal_concept_emergence': {},
            'jurisdictional_consistency': 0.0,
            'hierarchical_understanding': {},
            'temporal_coherence': 0.0,
            'overall_legal_comprehension_score': 0.0
        }

        # Attention evolution across layers
        for layer_analysis in layer_analyses:
            layer_attention_summary = {}
            if 'attention_entropy' in layer_analysis:
                avg_entropy = np.mean(list(layer_analysis['attention_entropy'].values()))
                layer_attention_summary['average_entropy'] = avg_entropy

            if 'cross_jurisdictional_attention' in layer_analysis:
                layer_attention_summary['cross_jurisdictional'] = layer_analysis['cross_jurisdictional_attention']

            analysis['attention_evolution'].append(layer_attention_summary)

        # Legal concept emergence (track how embeddings change across layers)
        if final_embeddings:
            legal_categories = set(token.legal_category for token in tokens if token.legal_category)
            for category in legal_categories:
                category_embeddings = [
                    final_embeddings[i] for i, token in enumerate(tokens)
                    if token.legal_category == category and i < len(final_embeddings)
                ]
                if category_embeddings:
                    category_centroid = np.mean(category_embeddings, axis=0)
                    category_variance = np.mean([
                        np.linalg.norm(emb - category_centroid)
                        for emb in category_embeddings
                    ])
                    analysis['legal_concept_emergence'][category] = {
                        'centroid_magnitude': np.linalg.norm(category_centroid),
                        'concept_coherence': 1.0 / (1.0 + category_variance)
                    }

        # Hierarchical understanding
        hierarchical_scores = {}
        for level in LegalSemanticLevel:
            level_tokens = [i for i, token in enumerate(tokens) if token.semantic_level == level]
            if level_tokens and final_embeddings:
                level_embeddings = [final_embeddings[i] for i in level_tokens if i < len(final_embeddings)]
                if level_embeddings:
                    level_coherence = self._compute_embedding_coherence(level_embeddings)
                    hierarchical_scores[level.value] = level_coherence

        analysis['hierarchical_understanding'] = hierarchical_scores

        # Overall comprehension score
        comprehension_factors = []

        if analysis['attention_evolution']:
            avg_attention_entropy = np.mean([
                layer.get('average_entropy', 0) for layer in analysis['attention_evolution']
            ])
            comprehension_factors.append(1.0 / (1.0 + avg_attention_entropy))  # Lower entropy = better focus

        if analysis['legal_concept_emergence']:
            avg_concept_coherence = np.mean([
                concept['concept_coherence']
                for concept in analysis['legal_concept_emergence'].values()
            ])
            comprehension_factors.append(avg_concept_coherence)

        if hierarchical_scores:
            avg_hierarchical_understanding = np.mean(list(hierarchical_scores.values()))
            comprehension_factors.append(avg_hierarchical_understanding)

        if comprehension_factors:
            analysis['overall_legal_comprehension_score'] = np.mean(comprehension_factors)

        return analysis

    def _compute_embedding_coherence(self, embeddings: List[np.ndarray]) -> float:
        """Compute coherence score for a set of embeddings."""
        if len(embeddings) < 2:
            return 1.0

        # Compute pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                emb1 = embeddings[i] / (np.linalg.norm(embeddings[i]) + 1e-8)
                emb2 = embeddings[j] / (np.linalg.norm(embeddings[j]) + 1e-8)
                similarity = np.dot(emb1, emb2)
                similarities.append(similarity)

        return np.mean(similarities) if similarities else 0.0


# Factory functions for easy instantiation
def create_legal_transformer_model(vocab_size: int = 30000,
                                 embedding_dim: int = 768,
                                 num_layers: int = 6,
                                 num_heads: int = 12) -> LegalTransformerModel:
    """Create a legal transformer model with specified configuration."""
    return LegalTransformerModel(vocab_size, embedding_dim, num_layers, num_heads)


# Demonstration function
async def demonstrate_legal_transformer():
    """Demonstrate legal transformer capabilities."""
    # Create legal transformer model
    model = create_legal_transformer_model(num_layers=3)  # Smaller for demo

    # Sample token sequence (simulated)
    token_ids = list(range(50))  # 50 tokens

    # Legal metadata
    legal_metadata = {
        'domain': 'contract',
        'jurisdiction': 'common_law',
        'document_type': 'service_agreement',
        'complexity': 'moderate'
    }

    # Process through legal transformer
    results = await model.process_legal_document(token_ids, legal_metadata)

    logger.info("Legal Transformer Processing Results:")
    logger.info(f"Processing time: {results['processing_metrics']['processing_time']:.3f}s")
    logger.info(f"Tokens processed: {results['processing_metrics']['tokens_processed']}")
    logger.info(f"Legal comprehension score: {results['comprehensive_analysis']['overall_legal_comprehension_score']:.3f}")

    # Task predictions
    for task, prediction in results['task_predictions'].items():
        logger.info(f"{task} prediction: class {prediction['prediction']} (confidence: {np.max(prediction['probabilities']):.3f})")

    return results


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demonstrate_legal_transformer())
