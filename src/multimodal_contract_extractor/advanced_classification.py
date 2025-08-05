"""Advanced clause classification system for specialized contract types."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ContractType:
    """Definition of a contract type with its characteristics."""

    name: str
    category: str
    required_clauses: List[str]
    optional_clauses: List[str]
    keywords: List[str]
    confidence_threshold: float = 0.7


@dataclass
class ClauseClassification:
    """Result of advanced clause classification."""

    clause_type: str
    confidence: float
    contract_types: List[str]  # Which contract types this clause is relevant for
    legal_significance: str  # high, medium, low
    keywords_matched: List[str]
    context_indicators: List[str]


# Enhanced contract type definitions
CONTRACT_TYPES = {
    "licensing_agreement": ContractType(
        name="Licensing Agreement",
        category="intellectual_property",
        required_clauses=["licensing", "intellectual_property", "payment_terms", "termination"],
        optional_clauses=["liability", "governing_law", "dispute_resolution"],
        keywords=["license", "licensing", "intellectual property", "patent", "trademark",
                 "copyright", "royalty", "exclusive", "non-exclusive", "territory", "field of use"],
        confidence_threshold=0.75
    ),
    "merger_acquisition": ContractType(
        name="Merger & Acquisition Agreement",
        category="corporate",
        required_clauses=["merger_acquisition", "purchase_price", "closing_conditions", "representations"],
        optional_clauses=["indemnification", "termination", "governing_law"],
        keywords=["merger", "acquisition", "purchase", "buy", "acquire", "consolidation",
                 "due diligence", "closing", "purchase price", "stock purchase", "asset purchase"],
        confidence_threshold=0.8
    ),
    "trade_agreement": ContractType(
        name="International Trade Agreement",
        category="commercial",
        required_clauses=["trade_agreement", "payment_terms", "delivery_terms", "customs"],
        optional_clauses=["force_majeure", "governing_law", "dispute_resolution"],
        keywords=["trade", "import", "export", "customs", "tariff", "international trade",
                 "incoterms", "letter of credit", "bill of lading", "freight"],
        confidence_threshold=0.7
    ),
    "employment_agreement": ContractType(
        name="Employment Agreement",
        category="employment",
        required_clauses=["payment_terms", "termination", "confidentiality"],
        optional_clauses=["non_compete", "benefits", "governing_law"],
        keywords=["employment", "employee", "employer", "salary", "wages", "benefits",
                 "vacation", "sick leave", "termination", "resignation"],
        confidence_threshold=0.7
    ),
    "nda": ContractType(
        name="Non-Disclosure Agreement",
        category="confidentiality",
        required_clauses=["confidentiality", "term_duration", "governing_law"],
        optional_clauses=["liability", "dispute_resolution"],
        keywords=["non-disclosure", "nda", "confidential", "proprietary", "trade secret",
                 "confidential information"],
        confidence_threshold=0.8
    ),
    "service_agreement": ContractType(
        name="Service Agreement",
        category="commercial",
        required_clauses=["services", "payment_terms", "termination"],
        optional_clauses=["liability", "indemnification", "governing_law"],
        keywords=["service", "services", "consulting", "professional services", "deliverables",
                 "scope of work", "statement of work"],
        confidence_threshold=0.7
    ),
    "lease_agreement": ContractType(
        name="Lease Agreement",
        category="real_estate",
        required_clauses=["lease_terms", "payment_terms", "property_description"],
        optional_clauses=["termination", "maintenance", "governing_law"],
        keywords=["lease", "rent", "tenant", "landlord", "property", "premises",
                 "rental", "lease term"],
        confidence_threshold=0.75
    ),
}

# Advanced clause type definitions with specialized keywords
ADVANCED_CLAUSE_KEYWORDS = {
    # Licensing-specific clauses
    "licensing": {
        "en": ["license", "licensing", "grant", "intellectual property", "patent rights",
               "trademark license", "copyright license", "exclusive license", "non-exclusive license",
               "field of use", "territory", "sublicense", "royalty", "license fee"],
        "es": ["licencia", "concesión", "propiedad intelectual", "derechos de patente",
               "licencia de marca", "derechos de autor", "licencia exclusiva", "territorio"],
        "fr": ["licence", "concession", "propriété intellectuelle", "droits de brevet",
               "licence de marque", "droit d'auteur", "licence exclusive", "territoire"],
        "de": ["lizenz", "gewährung", "geistiges eigentum", "patentrechte",
               "markenlizenz", "urheberrecht", "exklusive lizenz", "gebiet"],
        "ja": ["ライセンス", "許諾", "知的財産", "特許権", "商標ライセンス", "著作権",
               "独占ライセンス", "領域", "使用料"],
        "zh": ["许可", "授权", "知识产权", "专利权", "商标许可", "版权", "独占许可", "领域", "使用费"],
    },
    "merger_acquisition": {
        "en": ["merger", "acquisition", "purchase", "buy", "acquire", "consolidation",
               "due diligence", "closing", "purchase price", "stock purchase", "asset purchase",
               "representations and warranties", "indemnification", "earnout", "escrow"],
        "es": ["fusión", "adquisición", "compra", "adquirir", "consolidación",
               "diligencia debida", "cierre", "precio de compra", "garantías"],
        "fr": ["fusion", "acquisition", "achat", "acquérir", "consolidation",
               "diligence raisonnable", "clôture", "prix d'achat", "garanties"],
        "de": ["fusion", "übernahme", "kauf", "erwerben", "konsolidierung",
               "due diligence", "abschluss", "kaufpreis", "garantien"],
        "ja": ["合併", "買収", "取得", "統合", "デューデリジェンス", "クロージング",
               "買収価格", "表明保証"],
        "zh": ["合并", "收购", "购买", "获得", "整合", "尽职调查", "交割", "购买价格", "陈述保证"],
    },
    "trade_agreement": {
        "en": ["trade", "import", "export", "customs", "tariff", "international trade",
               "incoterms", "letter of credit", "bill of lading", "freight", "shipping",
               "customs clearance", "trade finance", "documentary credit"],
        "es": ["comercio", "importación", "exportación", "aduanas", "aranceles",
               "comercio internacional", "carta de crédito", "conocimiento de embarque"],
        "fr": ["commerce", "importation", "exportation", "douanes", "tarifs",
               "commerce international", "lettre de crédit", "connaissement"],
        "de": ["handel", "import", "export", "zoll", "tarife", "internationaler handel",
               "akkreditiv", "konnossement"],
        "ja": ["貿易", "輸入", "輸出", "関税", "通商", "信用状", "船荷証券", "国際貿易"],
        "zh": ["贸易", "进口", "出口", "关税", "商贸", "信用证", "提单", "国际贸易"],
    },
    # Enhanced existing clause types
    "intellectual_property": {
        "en": ["intellectual property", "ip", "patent", "trademark", "copyright", "trade secret",
               "proprietary", "invention", "design", "know-how", "confidential information"],
        "es": ["propiedad intelectual", "patente", "marca", "derechos de autor", "secreto comercial"],
        "fr": ["propriété intellectuelle", "brevet", "marque", "droit d'auteur", "secret commercial"],
        "de": ["geistiges eigentum", "patent", "marke", "urheberrecht", "geschäftsgeheimnis"],
        "ja": ["知的財産", "特許", "商標", "著作権", "営業秘密", "機密情報"],
        "zh": ["知识产权", "专利", "商标", "版权", "商业秘密", "机密信息"],
    },
    "purchase_price": {
        "en": ["purchase price", "consideration", "payment", "price", "cost", "fee",
               "amount", "sum", "total", "earnout", "adjustment", "escrow"],
        "es": ["precio de compra", "contraprestación", "pago", "precio", "costo", "importe"],
        "fr": ["prix d'achat", "contrepartie", "paiement", "prix", "coût", "montant"],
        "de": ["kaufpreis", "gegenleistung", "zahlung", "preis", "kosten", "betrag"],
        "ja": ["購入価格", "対価", "支払い", "価格", "費用", "金額"],
        "zh": ["购买价格", "对价", "支付", "价格", "费用", "金额"],
    },
    "closing_conditions": {
        "en": ["closing conditions", "conditions precedent", "closing", "completion",
               "satisfaction of conditions", "regulatory approval", "shareholder approval"],
        "es": ["condiciones de cierre", "condiciones precedentes", "cierre", "aprobación"],
        "fr": ["conditions de clôture", "conditions préalables", "clôture", "approbation"],
        "de": ["abschlussbedingungen", "voraussetzungen", "abschluss", "genehmigung"],
        "ja": ["クロージング条件", "前提条件", "完了", "承認"],
        "zh": ["交割条件", "先决条件", "交割", "批准"],
    },
    "representations": {
        "en": ["representations", "warranties", "representations and warranties", "covenants",
               "accuracy", "completeness", "material adverse change", "disclosure"],
        "es": ["declaraciones", "garantías", "manifestaciones", "convenios"],
        "fr": ["déclarations", "garanties", "affirmations", "engagements"],
        "de": ["zusicherungen", "garantien", "gewährleistungen", "verpflichtungen"],
        "ja": ["表明", "保証", "表明保証", "誓約"],
        "zh": ["陈述", "保证", "陈述保证", "承诺"],
    },
    "indemnification": {
        "en": ["indemnification", "indemnify", "hold harmless", "defense", "losses",
               "damages", "claims", "liabilities", "expenses", "costs"],
        "es": ["indemnización", "indemnizar", "eximir", "defensa", "pérdidas", "reclamaciones"],
        "fr": ["indemnisation", "indemniser", "dégager", "défense", "pertes", "réclamations"],
        "de": ["entschädigung", "entschädigen", "schadlos halten", "verteidigung", "verluste"],
        "ja": ["補償", "賠償", "免責", "防御", "損失", "請求"],
        "zh": ["赔偿", "补偿", "免责", "辩护", "损失", "索赔"],
    },
    "force_majeure": {
        "en": ["force majeure", "act of god", "natural disaster", "war", "terrorism",
               "government action", "unforeseeable circumstances", "beyond control"],
        "es": ["fuerza mayor", "caso fortuito", "desastre natural", "guerra", "acción gubernamental"],
        "fr": ["force majeure", "cas fortuit", "catastrophe naturelle", "guerre", "action gouvernementale"],
        "de": ["höhere gewalt", "naturkatastrophe", "krieg", "terrorismus", "regierungshandlung"],
        "ja": ["不可抗力", "天災", "戦争", "テロ", "政府の行為"],
        "zh": ["不可抗力", "天灾", "战争", "恐怖主义", "政府行为"],
    },
}


def classify_clause_advanced(clause_text: str, clause_type: str, language_code: str = "en") -> ClauseClassification:
    """
    Perform advanced classification of a clause with legal significance assessment.
    
    Args:
        clause_text: The text content of the clause
        clause_type: The basic clause type detected
        language_code: Language of the document
        
    Returns:
        Advanced classification results
    """
    # Analyze keywords matched
    keywords_matched = []
    context_indicators = []

    # Check for advanced clause-specific keywords
    if clause_type in ADVANCED_CLAUSE_KEYWORDS:
        lang_keywords = ADVANCED_CLAUSE_KEYWORDS[clause_type].get(language_code,
                                                                 ADVANCED_CLAUSE_KEYWORDS[clause_type]["en"])

        for keyword in lang_keywords:
            if keyword.lower() in clause_text.lower():
                keywords_matched.append(keyword)

    # Determine contract types this clause is relevant for
    relevant_contract_types = []
    for contract_id, contract_type in CONTRACT_TYPES.items():
        if clause_type in contract_type.required_clauses or clause_type in contract_type.optional_clauses:
            relevant_contract_types.append(contract_id)

    # Assess legal significance based on clause type and content
    legal_significance = _assess_legal_significance(clause_type, clause_text, keywords_matched)

    # Calculate confidence based on keyword matches and context
    confidence = _calculate_advanced_confidence(clause_text, clause_type, keywords_matched, language_code)

    # Extract context indicators
    context_indicators = _extract_context_indicators(clause_text, clause_type)

    return ClauseClassification(
        clause_type=clause_type,
        confidence=confidence,
        contract_types=relevant_contract_types,
        legal_significance=legal_significance,
        keywords_matched=keywords_matched,
        context_indicators=context_indicators
    )


def identify_contract_type(clauses: List[Tuple[str, str]]) -> Dict[str, float]:
    """
    Identify the most likely contract type based on detected clauses.
    
    Args:
        clauses: List of (clause_type, clause_text) tuples
        
    Returns:
        Dictionary of contract_type -> confidence_score
    """
    contract_scores = {}
    clause_types_present = [clause[0] for clause in clauses]

    for contract_id, contract_type in CONTRACT_TYPES.items():
        score = 0.0

        # Score based on required clauses present
        required_present = sum(1 for clause in contract_type.required_clauses
                             if clause in clause_types_present)
        required_score = (required_present / len(contract_type.required_clauses)) * 0.7

        # Score based on optional clauses present
        optional_present = sum(1 for clause in contract_type.optional_clauses
                             if clause in clause_types_present)
        optional_score = (optional_present / max(len(contract_type.optional_clauses), 1)) * 0.3

        # Bonus for contract-specific keywords in any clause text
        keyword_bonus = 0.0
        for _, clause_text in clauses:
            for keyword in contract_type.keywords:
                if keyword.lower() in clause_text.lower():
                    keyword_bonus += 0.05  # Small bonus per keyword match

        total_score = required_score + optional_score + min(keyword_bonus, 0.2)  # Cap keyword bonus
        contract_scores[contract_id] = min(total_score, 1.0)

    return contract_scores


def _assess_legal_significance(clause_type: str, clause_text: str, keywords_matched: List[str]) -> str:
    """Assess the legal significance of a clause."""
    # High significance clause types
    high_significance = {
        "liability", "indemnification", "termination", "governing_law",
        "dispute_resolution", "merger_acquisition", "licensing", "representations"
    }

    # Medium significance clause types
    medium_significance = {
        "payment_terms", "confidentiality", "intellectual_property",
        "trade_agreement", "closing_conditions"
    }

    if clause_type in high_significance:
        return "high"
    elif clause_type in medium_significance:
        return "medium"
    else:
        # Additional analysis based on content
        high_risk_terms = ["indemnify", "liable", "damages", "breach", "terminate",
                          "penalty", "forfeit", "void", "null"]

        if any(term in clause_text.lower() for term in high_risk_terms):
            return "high"
        elif len(keywords_matched) > 3:  # Many specific terms indicate importance
            return "medium"
        else:
            return "low"


def _calculate_advanced_confidence(clause_text: str, clause_type: str,
                                 keywords_matched: List[str], language_code: str) -> float:
    """Calculate confidence score for advanced clause classification."""
    base_confidence = 0.6

    # Bonus for keyword matches
    keyword_bonus = min(len(keywords_matched) * 0.05, 0.2)

    # Bonus for clause length (more context usually means better detection)
    length_bonus = min(len(clause_text) / 1000, 0.1)

    # Language-specific adjustment
    language_adjustment = 0.0
    if language_code in ["ja", "zh", "zh-tw"]:  # More complex scripts
        language_adjustment = -0.05
    elif language_code in ["es", "fr", "de"]:  # Related to English
        language_adjustment = 0.02

    # Clause type specific adjustments
    type_adjustments = {
        "licensing": 0.05,  # Usually well-defined
        "merger_acquisition": 0.1,  # Very specific terminology
        "trade_agreement": 0.03,  # Standard terms
    }

    type_bonus = type_adjustments.get(clause_type, 0.0)

    final_confidence = base_confidence + keyword_bonus + length_bonus + language_adjustment + type_bonus
    return min(max(final_confidence, 0.0), 1.0)


def _extract_context_indicators(clause_text: str, clause_type: str) -> List[str]:
    """Extract context indicators that help identify clause significance."""
    indicators = []

    # Legal action terms
    legal_terms = re.findall(r'\b(?:shall|must|will|may|cannot|prohibited|required|obligated)\b',
                           clause_text, re.IGNORECASE)
    indicators.extend([f"legal_obligation: {term}" for term in set(legal_terms)])

    # Financial terms
    financial_terms = re.findall(r'\$[\d,]+(?:\.\d{2})?', clause_text)
    if financial_terms:
        indicators.append(f"financial_amount: {len(financial_terms)} amounts")

    # Time periods
    time_terms = re.findall(r'\b\d+\s*(?:days?|weeks?|months?|years?)\b', clause_text, re.IGNORECASE)
    if time_terms:
        indicators.append(f"time_period: {len(time_terms)} periods")

    # Percentages
    percentages = re.findall(r'\b\d+%\b', clause_text)
    if percentages:
        indicators.append(f"percentage: {len(percentages)} values")

    # Geographic references
    geo_terms = re.findall(r'\b(?:jurisdiction|territory|country|state|province|region)\b',
                          clause_text, re.IGNORECASE)
    if geo_terms:
        indicators.append(f"geographic: {len(set(geo_terms))} references")

    return indicators


def get_contract_type_definition(contract_type_id: str) -> Optional[ContractType]:
    """Get the definition of a specific contract type."""
    return CONTRACT_TYPES.get(contract_type_id)


def get_all_contract_types() -> Dict[str, ContractType]:
    """Get all available contract type definitions."""
    return CONTRACT_TYPES.copy()


def is_specialized_contract_type(contract_type_id: str) -> bool:
    """Check if a contract type is one of the specialized types (licensing, M&A, trade)."""
    specialized_types = {"licensing_agreement", "merger_acquisition", "trade_agreement"}
    return contract_type_id in specialized_types
