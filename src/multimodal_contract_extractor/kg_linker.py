"""KGLinker: Links extracted entities into a knowledge graph edge list.

Outputs a simple adjacency / edge list format compatible with
LegalEntityGraph from the Neuro-Symbolic-Law-Prover.

Edge schema:
  (source_node, relation, target_node, metadata)

Node types mirror LegalEntityGraph conventions:
  - ContractParty     → party entities
  - TemporalAnchor    → date/duration entities
  - MonetaryValue     → amount entities
  - Jurisdiction      → jurisdiction entities
  - DataCategory      → data_category entities
  - ContractClause    → clause nodes (central hub)

Relations:
  - IS_PARTY_TO       party → clause
  - HAS_PAYMENT_TERM  clause(payment) → amount
  - HAS_DEADLINE      clause → date
  - GOVERNED_BY       clause(liability/termination) → jurisdiction
  - COVERS_DATA       clause(data_protection) → data_category
  - HAS_LICENSE       clause(ip) → party (licensee)
  - DISCLOSES_TO      clause(confidentiality) → party (receiving party)
  - EFFECTIVE_DATE    clause → date
  - EXPIRES_ON        clause(termination) → date
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .clause_extractor import ExtractedClause
from .entity_extractor import ExtractedEntity


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class KGNode:
    """A node in the knowledge graph."""
    node_id: str
    node_type: str
    label: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class KGEdge:
    """A directed edge in the knowledge graph."""
    source: str        # node_id
    relation: str      # predicate
    target: str        # node_id
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContractKG:
    """A knowledge graph representation of a contract.

    Compatible with LegalEntityGraph from Neuro-Symbolic-Law-Prover.
    """
    nodes: list[KGNode] = field(default_factory=list)
    edges: list[KGEdge] = field(default_factory=list)

    def add_node(self, node: KGNode) -> None:
        # Avoid duplicates
        existing_ids = {n.node_id for n in self.nodes}
        if node.node_id not in existing_ids:
            self.nodes.append(node)

    def add_edge(self, edge: KGEdge) -> None:
        # Avoid exact duplicate edges
        existing = {(e.source, e.relation, e.target) for e in self.edges}
        if (edge.source, edge.relation, edge.target) not in existing:
            self.edges.append(edge)

    def to_adjacency_list(self) -> dict[str, list[dict]]:
        """Return adjacency list: {node_id: [{relation, target, weight}]}"""
        adj: dict[str, list[dict]] = {n.node_id: [] for n in self.nodes}
        for edge in self.edges:
            if edge.source in adj:
                adj[edge.source].append({
                    "relation": edge.relation,
                    "target": edge.target,
                    "weight": edge.weight,
                })
        return adj

    def to_edge_list(self) -> list[tuple[str, str, str]]:
        """Return simple (source, relation, target) triples."""
        return [(e.source, e.relation, e.target) for e in self.edges]

    def to_legal_entity_graph_dict(self) -> dict:
        """Serialize to a dict compatible with LegalEntityGraph.from_dict().

        Schema mirrors what Neuro-Symbolic-Law-Prover expects:
        {
            "entities": [...],
            "relations": [...],
        }
        """
        entities = [
            {
                "id": n.node_id,
                "type": n.node_type,
                "label": n.label,
                **n.properties,
            }
            for n in self.nodes
        ]
        relations = [
            {
                "source": e.source,
                "predicate": e.relation,
                "target": e.target,
                "weight": e.weight,
                **e.properties,
            }
            for e in self.edges
        ]
        return {"entities": entities, "relations": relations}

    def summary(self) -> str:
        node_types: dict[str, int] = {}
        for n in self.nodes:
            node_types[n.node_type] = node_types.get(n.node_type, 0) + 1
        rel_types: dict[str, int] = {}
        for e in self.edges:
            rel_types[e.relation] = rel_types.get(e.relation, 0) + 1

        lines = [
            f"ContractKG: {len(self.nodes)} nodes, {len(self.edges)} edges",
            "  Node types: " + ", ".join(f"{k}={v}" for k, v in sorted(node_types.items())),
            "  Relations:  " + ", ".join(f"{k}={v}" for k, v in sorted(rel_types.items())),
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Linker
# ---------------------------------------------------------------------------

# Maps clause type to the node_type label for the clause hub
_CLAUSE_NODE_TYPE = "ContractClause"

# Maps entity type to KG node type
_ENTITY_NODE_TYPES: dict[str, str] = {
    "party": "ContractParty",
    "date": "TemporalAnchor",
    "amount": "MonetaryValue",
    "jurisdiction": "Jurisdiction",
    "data_category": "DataCategory",
}

# Default relations from clause to entity, by (clause_type, entity_type)
_CLAUSE_ENTITY_RELATIONS: dict[tuple[str, str], str] = {
    ("payment", "party"): "IS_PARTY_TO",
    ("payment", "amount"): "HAS_PAYMENT_TERM",
    ("payment", "date"): "HAS_DEADLINE",
    ("payment", "jurisdiction"): "GOVERNED_BY",

    ("liability", "party"): "IS_PARTY_TO",
    ("liability", "amount"): "HAS_LIABILITY_CAP",
    ("liability", "jurisdiction"): "GOVERNED_BY",

    ("termination", "party"): "IS_PARTY_TO",
    ("termination", "date"): "EXPIRES_ON",
    ("termination", "jurisdiction"): "GOVERNED_BY",

    ("data_protection", "party"): "IS_PARTY_TO",
    ("data_protection", "data_category"): "COVERS_DATA",
    ("data_protection", "jurisdiction"): "GOVERNED_BY",
    ("data_protection", "date"): "RETENTION_PERIOD",

    ("ip", "party"): "HAS_LICENSE",
    ("ip", "amount"): "HAS_PAYMENT_TERM",
    ("ip", "date"): "HAS_DEADLINE",

    ("confidentiality", "party"): "DISCLOSES_TO",
    ("confidentiality", "date"): "HAS_DEADLINE",
    ("confidentiality", "jurisdiction"): "GOVERNED_BY",
}

_DEFAULT_PARTY_RELATION = "IS_PARTY_TO"
_DEFAULT_DATE_RELATION = "HAS_TEMPORAL_ANCHOR"
_DEFAULT_AMOUNT_RELATION = "HAS_MONETARY_VALUE"
_DEFAULT_JURISDICTION_RELATION = "GOVERNED_BY"
_DEFAULT_DATA_CAT_RELATION = "COVERS_DATA"


def _get_relation(clause_type: Optional[str], entity_type: str) -> str:
    if clause_type:
        rel = _CLAUSE_ENTITY_RELATIONS.get((clause_type, entity_type))
        if rel:
            return rel
    defaults = {
        "party": _DEFAULT_PARTY_RELATION,
        "date": _DEFAULT_DATE_RELATION,
        "amount": _DEFAULT_AMOUNT_RELATION,
        "jurisdiction": _DEFAULT_JURISDICTION_RELATION,
        "data_category": _DEFAULT_DATA_CAT_RELATION,
    }
    return defaults.get(entity_type, "RELATED_TO")


def _node_id(node_type: str, label: str) -> str:
    """Deterministic node id from type + label."""
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", label.strip().lower())
    return f"{node_type.lower()}:{safe[:50]}"


import re


class KGLinker:
    """Builds a ContractKG from extracted clauses and entities.

    Usage:
        linker = KGLinker()
        kg = linker.build(clauses, entities)
        print(kg.summary())
        edges = kg.to_edge_list()
    """

    def build(
        self,
        clauses: list[ExtractedClause],
        entities: list[ExtractedEntity],
        contract_id: str = "contract:main",
    ) -> ContractKG:
        """Build a ContractKG from clauses and entities.

        Args:
            clauses: Output of ClauseExtractor.extract()
            entities: Output of EntityExtractor.extract_from_clauses()
            contract_id: Identifier for the root contract node.

        Returns:
            A populated ContractKG.
        """
        kg = ContractKG()

        # Root contract node
        root_node = KGNode(
            node_id=contract_id,
            node_type="Contract",
            label="Contract",
        )
        kg.add_node(root_node)

        # Add clause nodes and connect to root
        clause_nodes: list[KGNode] = []
        for i, clause in enumerate(clauses):
            clause_id = f"clause:{clause.clause_type}:{i}"
            clause_node = KGNode(
                node_id=clause_id,
                node_type=_CLAUSE_NODE_TYPE,
                label=f"{clause.clause_type.upper()} clause",
                properties={
                    "clause_type": clause.clause_type,
                    "confidence": clause.confidence,
                    "text_snippet": clause.text[:120] + ("…" if len(clause.text) > 120 else ""),
                },
            )
            kg.add_node(clause_node)
            clause_nodes.append(clause_node)
            kg.add_edge(KGEdge(
                source=contract_id,
                relation="HAS_CLAUSE",
                target=clause_id,
                weight=clause.confidence,
            ))

        # Add entity nodes and link to relevant clause nodes
        # Group entities by clause type for efficient linking
        clause_type_to_nodes: dict[str, list[KGNode]] = {}
        for cn in clause_nodes:
            ct = cn.properties.get("clause_type", "")
            clause_type_to_nodes.setdefault(ct, []).append(cn)

        for entity in entities:
            node_type = _ENTITY_NODE_TYPES.get(entity.entity_type, "Entity")
            ent_id = _node_id(node_type, entity.value)
            ent_node = KGNode(
                node_id=ent_id,
                node_type=node_type,
                label=entity.value,
                properties={"entity_type": entity.entity_type},
            )
            kg.add_node(ent_node)

            # Link entity to the clause nodes it came from
            source_clause_nodes = []
            if entity.clause_type:
                source_clause_nodes = clause_type_to_nodes.get(entity.clause_type, [])

            if not source_clause_nodes:
                # Fall back: link to all clause nodes (global entity)
                source_clause_nodes = clause_nodes

            for cn in source_clause_nodes:
                relation = _get_relation(entity.clause_type, entity.entity_type)
                kg.add_edge(KGEdge(
                    source=cn.node_id,
                    relation=relation,
                    target=ent_id,
                ))

            # Also link parties directly to root contract node
            if entity.entity_type == "party":
                kg.add_edge(KGEdge(
                    source=contract_id,
                    relation="HAS_PARTY",
                    target=ent_id,
                ))

        return kg
