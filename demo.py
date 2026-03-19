#!/usr/bin/env python3
"""Demo: VLM-based Contract Extraction Pipeline

Processes a hardcoded sample contract:
  1. ContractParser  → raw text
  2. ClauseExtractor → typed clauses
  3. EntityExtractor → named entities
  4. KGLinker        → knowledge graph edges

No file upload or external model required.
"""

import json
import sys
from pathlib import Path

# Make sure the package is importable when run from repo root
sys.path.insert(0, str(Path(__file__).parent / "src"))

from multimodal_contract_extractor.contract_parser import ContractParser
from multimodal_contract_extractor.clause_extractor import ClauseExtractor
from multimodal_contract_extractor.entity_extractor import EntityExtractor
from multimodal_contract_extractor.kg_linker import KGLinker


# ---------------------------------------------------------------------------
# Sample contract text (hardcoded — no file upload needed)
# ---------------------------------------------------------------------------

SAMPLE_CONTRACT = """
SERVICE AGREEMENT

This Service Agreement ("Agreement") is entered into as of January 15, 2024,
by and between Acme Technologies Inc. ("Service Provider") and Global Industries Ltd.
("Client"), collectively referred to as the "Parties".

PAYMENT TERMS

The Client shall pay to the Service Provider a monthly service fee of $15,000 USD,
payable within 30 days of invoice date. In the event of late payment, interest shall
accrue at the rate of 1.5% per month on all overdue amounts. The purchase price for
professional services shall be invoiced on a Net 30 basis.

LIMITATION OF LIABILITY

In no event shall either party be liable to the other for any consequential, incidental,
indirect, or punitive damages arising out of or related to this Agreement. The total
liability of the Service Provider under this Agreement shall not exceed the total fees
paid by the Client in the 12 months preceding the claim. Each party shall indemnify,
defend and hold harmless the other party from any third-party claims arising from its
own gross negligence or willful misconduct.

TERMINATION

Either party may terminate this Agreement for convenience upon 90 days written notice
to the other party. This Agreement may be terminated for cause if either party materially
breaches any provision and fails to cure such breach within 30 days of receiving notice
of the breach. Upon termination, all confidential information must be returned or destroyed.
The Agreement shall expire on December 31, 2026.

DATA PROTECTION

The Service Provider shall process personal data on behalf of the Client solely in
accordance with the Client's instructions and this Data Processing Agreement (DPA).
The Service Provider shall implement appropriate technical and organisational measures
to protect personal data against unauthorized access, including contact details, email
addresses, IP addresses, and behavioral data. This Agreement is governed by the
requirements of the General Data Protection Regulation (GDPR). Data retention periods
shall not exceed 7 years from the date of collection. Any cross-border data transfer
shall be subject to Standard Contractual Clauses (SCCs).

INTELLECTUAL PROPERTY

All intellectual property, including copyrights, patents, and trade secrets, developed
by the Service Provider in connection with this Agreement shall be subject to a
non-exclusive license granted to the Client. The Client shall own all work product
created as work for hire under this Agreement. The Licensor retains all moral rights
in any licensed materials.

CONFIDENTIALITY

Each party (the "Receiving Party") agrees to hold the other party's (the "Disclosing Party")
proprietary information and trade secrets in strict confidence and not to disclose such
confidential information to any third party without prior written consent. This non-disclosure
obligation shall survive for 5 years after the termination of this Agreement. All
confidential treatment shall be governed by the laws of England and Wales, and any disputes
shall be subject to the exclusive jurisdiction of the courts of England and Wales.

GOVERNING LAW

This Agreement shall be governed by and construed in accordance with the laws of
New York State, without regard to its conflict of law provisions. Any disputes arising
under this Agreement shall be resolved by the courts of New York.
"""


def main():
    print("=" * 70)
    print("MULTIMODAL CONTRACT EXTRACTOR — Demo Pipeline")
    print("=" * 70)
    print()

    # Step 1: Parse
    print("STEP 1: ContractParser")
    print("-" * 40)
    parser = ContractParser()
    print(f"  Capabilities: {parser.capabilities()}")
    text = parser.parse_text(SAMPLE_CONTRACT)
    print(f"  Extracted {len(text)} characters of text")
    print()

    # Step 2: Extract clauses
    print("STEP 2: ClauseExtractor")
    print("-" * 40)
    clause_extractor = ClauseExtractor()
    clauses = clause_extractor.extract(text)
    print(f"  Found {len(clauses)} clauses:")
    for i, clause in enumerate(clauses):
        snippet = clause.text[:80].replace("\n", " ").strip()
        print(f"  [{i}] {clause.clause_type:20s}  conf={clause.confidence:.2f}  \"{snippet}…\"")
        if clause.matched_keywords:
            print(f"       keywords: {', '.join(clause.matched_keywords[:5])}")
    print()

    # Step 3: Extract entities
    print("STEP 3: EntityExtractor")
    print("-" * 40)
    entity_extractor = EntityExtractor()
    entities = entity_extractor.extract_from_clauses(clauses)
    print(f"  Found {len(entities)} entities:")
    by_type: dict = {}
    for ent in entities:
        by_type.setdefault(ent.entity_type, []).append(ent)
    for etype, ents in sorted(by_type.items()):
        print(f"  [{etype}]")
        for e in ents[:8]:  # show up to 8 per type
            print(f"    · {e.value}  (from: {e.clause_type})")
    print()

    # Step 4: Build KG
    print("STEP 4: KGLinker")
    print("-" * 40)
    linker = KGLinker()
    kg = linker.build(clauses, entities)
    print(f"  {kg.summary()}")
    print()

    print("  Edge list (source → relation → target):")
    for src, rel, tgt in kg.to_edge_list()[:30]:  # show first 30
        print(f"    {src}  →[{rel}]→  {tgt}")
    total_edges = len(kg.to_edge_list())
    if total_edges > 30:
        print(f"    ... and {total_edges - 30} more edges")
    print()

    # Output JSON for downstream consumption
    print("  LegalEntityGraph-compatible JSON (first 500 chars):")
    leg_dict = kg.to_legal_entity_graph_dict()
    leg_json = json.dumps(leg_dict, indent=2)
    print("  " + leg_json[:500].replace("\n", "\n  ") + "…")
    print()

    # Save full output
    output_path = Path(__file__).parent / "demo_output.json"
    output_path.write_text(json.dumps(leg_dict, indent=2))
    print(f"  Full KG saved to: {output_path}")
    print()

    print("=" * 70)
    print("Pipeline complete. Feed demo_output.json to Neuro-Symbolic-Law-Prover.")
    print("See: https://github.com/danieleschmidt/neuro-symbolic-law-prover")
    print("=" * 70)


if __name__ == "__main__":
    main()
