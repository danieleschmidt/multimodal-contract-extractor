"""Language detection and OCR configuration for multi-language document support."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LanguageConfig:
    """Configuration for language-specific OCR processing."""

    code: str  # ISO 639-1 language code
    name: str  # Human-readable language name
    tesseract_code: str  # Tesseract language code
    script: str  # Writing script (latin, cyrillic, chinese, etc.)
    reading_direction: str  # ltr (left-to-right) or rtl (right-to-left)
    confidence_threshold: float  # Minimum confidence for this language
    preprocessing_options: Dict[str, str]  # Additional OCR options


# Supported languages with their configurations
SUPPORTED_LANGUAGES = {
    "en": LanguageConfig(
        code="en",
        name="English",
        tesseract_code="eng",
        script="latin",
        reading_direction="ltr",
        confidence_threshold=0.7,
        preprocessing_options={"psm": "6"}
    ),
    "es": LanguageConfig(
        code="es",
        name="Spanish",
        tesseract_code="spa",
        script="latin",
        reading_direction="ltr",
        confidence_threshold=0.7,
        preprocessing_options={"psm": "6"}
    ),
    "fr": LanguageConfig(
        code="fr",
        name="French",
        tesseract_code="fra",
        script="latin",
        reading_direction="ltr",
        confidence_threshold=0.7,
        preprocessing_options={"psm": "6"}
    ),
    "de": LanguageConfig(
        code="de",
        name="German",
        tesseract_code="deu",
        script="latin",
        reading_direction="ltr",
        confidence_threshold=0.7,
        preprocessing_options={"psm": "6"}
    ),
    "ja": LanguageConfig(
        code="ja",
        name="Japanese",
        tesseract_code="jpn",
        script="mixed",  # Japanese uses multiple scripts
        reading_direction="ltr",
        confidence_threshold=0.65,  # Lower threshold for Japanese
        preprocessing_options={"psm": "6", "oem": "1"}
    ),
    "zh": LanguageConfig(
        code="zh",
        name="Chinese (Simplified)",
        tesseract_code="chi_sim",
        script="chinese",
        reading_direction="ltr",
        confidence_threshold=0.65,  # Lower threshold for Chinese
        preprocessing_options={"psm": "6", "oem": "1"}
    ),
    "zh-tw": LanguageConfig(
        code="zh-tw",
        name="Chinese (Traditional)",
        tesseract_code="chi_tra",
        script="chinese",
        reading_direction="ltr",
        confidence_threshold=0.65,
        preprocessing_options={"psm": "6", "oem": "1"}
    ),
}


def detect_document_language(text_sample: str) -> Tuple[str, float]:
    """
    Detect the primary language of a document from a text sample.
    
    Args:
        text_sample: Sample text extracted from the document
        
    Returns:
        Tuple of (language_code, confidence_score)
    """
    if not text_sample or len(text_sample.strip()) < 10:
        return "en", 0.5  # Default to English with low confidence

    # Simple heuristic-based language detection
    # In production, you might want to use a proper language detection library

    # Character set analysis
    text_sample = text_sample.lower().strip()

    # Japanese detection (Hiragana, Katakana, Kanji)
    if re.search(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text_sample):
        return "ja", _calculate_script_confidence(text_sample, "japanese")

    # Chinese detection (CJK ideographs)
    if re.search(r'[\u4e00-\u9fff]', text_sample):
        # Simple heuristic to distinguish simplified vs traditional
        simplified_chars = len(re.findall(r'[\u4e00-\u9fa5]', text_sample))
        traditional_chars = len(re.findall(r'[\u9fa6-\u9fff]', text_sample))

        if traditional_chars > simplified_chars * 0.1:
            return "zh-tw", _calculate_script_confidence(text_sample, "chinese")
        else:
            return "zh", _calculate_script_confidence(text_sample, "chinese")

    # European language detection based on character frequency and common words
    language_scores = {}

    # Spanish indicators
    spanish_indicators = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'está', 'ser', 'están', 'muy', 'más', 'todo', 'pero', 'ya', 'tiene', 'han', 'fue', 'este', 'fue', 'sí', 'como', 'hace', 'dice', 'dos', 'antes', 'cada', 'años', 'hasta', 'desde', 'vamos', 'durante', 'pueden', 'nuevo', 'estos', 'otras', 'parte', 'hace', 'tiempo', 'día', 'año', 'bien', 'días', 'vida', 'vez', 'caso', 'mismo', 'ninguna', 'trabajo', 'país', 'hombre', 'último', 'hacia', 'así', 'menos', 'mejor', 'mucho', 'siempre', 'cualquier', 'bueno', 'mayor', 'poco', 'manera', 'grupo', 'ciertos', 'nuestro', 'lugar', 'grandes', 'gobierno', 'general', 'partido', 'número', 'mercado', 'historia', 'cualquier', 'cambio', 'persona', 'programa', 'datos', 'razón', 'millones', 'sitio', 'través', 'desarrollo', 'proceso', 'empresa', 'calidad', 'internacional', 'cuestión', 'sociedad', 'resultado', 'medio', 'sistema', 'problema', 'forma', 'momento', 'ciudad', 'servicio', 'mesa', 'mesa', 'medida', 'precio', 'acuerdo', 'conocer', 'control', 'agua', 'mundo', 'guerra', 'muerte', 'fuerza', 'niño', 'mujer', 'casa', 'hora', 'proyecto', 'libro', 'política', 'cuerpo', 'educación', 'ejemplo', 'tecnología', 'sector', 'recursos', 'medios', 'objetivo', 'oportunidad', 'realidad', 'ñ']
    language_scores['es'] = _calculate_word_frequency_score(text_sample, spanish_indicators)

    # French indicators
    french_indicators = ['le', 'de', 'et', 'être', 'à', 'il', 'avoir', 'ne', 'je', 'son', 'que', 'se', 'qui', 'ce', 'dans', 'en', 'du', 'elle', 'au', 'de', 'le', 'tout', 'le', 'pour', 'par', 'sur', 'faire', 'sont', 'avec', 'ils', 'nous', 'sa', 'une', 'son', 'cette', 'leurs', 'mais', 'ou', 'lui', 'bien', 'temps', 'très', 'où', 'sans', 'autre', 'comme', 'notre', 'deux', 'peut', 'ces', 'plus', 'après', 'sous', 'leur', 'aussi', 'encore', 'entre', 'moins', 'même', 'beaucoup', 'depuis', 'contre', 'jusqu', 'toujours', 'pendant', 'avant', 'quelque', 'celui', 'alors', 'grand', 'autre', 'chaque', 'ainsi', 'dont', 'nouveau', 'année', 'jour', 'homme', 'vie', 'fois', 'temps', 'main', 'part', 'france', 'état', 'pays', 'monde', 'travail', 'groupe', 'service', 'ville', 'famille', 'enfant', 'femme', 'problème', 'moment', 'eau', 'développement', 'gouvernement', 'programme', 'système', 'société', 'entreprise', 'place', 'économie', 'niveau', 'recherche', 'milieu', 'formation', 'europe', 'politique', 'région', 'qualité', 'question', 'personne', 'marché', 'public', 'projet', 'international', 'français', 'mesure', 'guerre', 'histoire', 'situation', 'droit', 'rapport', 'point', 'culture', 'information', 'prix', 'action', 'équipe', 'maison', 'école', 'centre', 'nombre', 'livre', 'page', 'santé', 'effort', 'voie', 'commune', 'ordre', 'force', 'résultat', 'cause', 'effet', 'terme', 'à', 'é', 'è', 'ç']
    language_scores['fr'] = _calculate_word_frequency_score(text_sample, french_indicators)

    # German indicators
    german_indicators = ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als', 'auch', 'es', 'an', 'werden', 'aus', 'er', 'hat', 'dass', 'sie', 'nach', 'wird', 'bei', 'einer', 'um', 'am', 'sind', 'noch', 'wie', 'einem', 'über', 'einen', 'so', 'zum', 'war', 'haben', 'nur', 'oder', 'aber', 'vor', 'zur', 'bis', 'mehr', 'durch', 'man', 'sein', 'wurde', 'sei', 'ins', 'zeit', 'sehr', 'wenn', 'kann', 'schon', 'gegen', 'nach', 'vom', 'heute', 'jahr', 'jahren', 'deutschland', 'menschen', 'welt', 'weg', 'leben', 'arbeit', 'kinder', 'frau', 'staat', 'geld', 'land', 'wasser', 'tage', 'entwicklung', 'prozent', 'haus', 'regierung', 'politik', 'gesellschaft', 'wirtschaft', 'woche', 'unternehmen', 'stadt', 'familie', 'sicherheit', 'europa', 'information', 'gruppe', 'system', 'ende', 'geschichte', 'problem', 'service', 'bereich', 'grund', 'stelle', 'markt', 'qualität', 'projekt', 'bildung', 'control', 'recht', 'produkt', 'region', 'programm', 'interesse', 'frage', 'öffentlich', 'international', 'zentrum', 'ziel', 'kosten', 'wissenschaft', 'kultur', 'chance', 'deutschland', 'ä', 'ö', 'ü', 'ß']
    language_scores['de'] = _calculate_word_frequency_score(text_sample, german_indicators)

    # English indicators (default)
    english_indicators = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'contract', 'agreement', 'party', 'shall', 'clause', 'terms', 'conditions', 'obligations', 'rights', 'liability', 'termination', 'breach', 'damages', 'consideration', 'payment', 'compensation', 'confidential', 'disclosure', 'proprietary', 'intellectual', 'property', 'jurisdiction', 'governing', 'law', 'dispute', 'resolution', 'arbitration', 'mediation', 'court', 'enforce', 'binding', 'executed', 'signed', 'dated', 'effective', 'performance', 'delivery', 'services', 'goods', 'materials', 'specifications', 'warranty', 'guarantee', 'indemnify', 'hold', 'harmless', 'attorney', 'fees', 'costs', 'expenses', 'notice', 'written', 'consent', 'approval', 'reasonable', 'commercial', 'efforts', 'force', 'majeure']
    language_scores['en'] = _calculate_word_frequency_score(text_sample, english_indicators)

    # Find the language with the highest score
    if not language_scores:
        return "en", 0.5

    best_language = max(language_scores.keys(), key=lambda k: language_scores[k])
    confidence = min(language_scores[best_language] / 100.0, 1.0)  # Normalize to 0-1

    # Ensure minimum confidence
    if confidence < 0.3:
        return "en", 0.5  # Default to English with low confidence

    return best_language, confidence


def _calculate_word_frequency_score(text: str, indicators: List[str]) -> float:
    """Calculate a frequency score based on language indicators."""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0

    matches = sum(1 for word in words if word in indicators)
    return (matches / len(words)) * 100


def _calculate_script_confidence(text: str, script: str) -> float:
    """Calculate confidence based on script character frequency."""
    if script == "japanese":
        # Count Japanese characters
        jp_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]', text))
        total_chars = len(re.findall(r'[^\s\d\W]', text))
        return min(jp_chars / max(total_chars, 1), 1.0)

    elif script == "chinese":
        # Count Chinese characters
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(re.findall(r'[^\s\d\W]', text))
        return min(cn_chars / max(total_chars, 1), 1.0)

    return 0.8  # Default confidence


def get_language_config(language_code: str) -> Optional[LanguageConfig]:
    """Get language configuration for a given language code."""
    return SUPPORTED_LANGUAGES.get(language_code)


def get_supported_languages() -> Dict[str, LanguageConfig]:
    """Get all supported language configurations."""
    return SUPPORTED_LANGUAGES.copy()


def get_tesseract_language_string(language_codes: List[str]) -> str:
    """
    Get Tesseract language string for multiple languages.
    
    Args:
        language_codes: List of language codes to combine
        
    Returns:
        Tesseract-compatible language string (e.g., "eng+spa+fra")
    """
    tesseract_codes = []
    for code in language_codes:
        config = get_language_config(code)
        if config:
            tesseract_codes.append(config.tesseract_code)

    return "+".join(tesseract_codes) if tesseract_codes else "eng"


def is_language_supported(language_code: str) -> bool:
    """Check if a language is supported."""
    return language_code in SUPPORTED_LANGUAGES


def get_ocr_config_for_language(language_code: str) -> Dict[str, str]:
    """Get OCR configuration options for a specific language."""
    config = get_language_config(language_code)
    if config:
        return config.preprocessing_options.copy()
    return {"psm": "6"}  # Default configuration
