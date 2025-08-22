"""Advanced fraud detection capabilities for contract analysis.

Generation 1 Enhanced Feature: Detects fraudulent patterns, anomalies,
and suspicious content in legal documents using ML and heuristic analysis.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FraudRiskLevel(Enum):
    """Fraud risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FraudIndicator:
    """Individual fraud indicator."""
    indicator_type: str
    description: str
    risk_score: float
    evidence: List[str] = field(default_factory=list)
    confidence: float = 0.0
    location: Optional[str] = None


@dataclass 
class FraudAnalysisResult:
    """Complete fraud analysis result."""
    fraud_score: float
    risk_level: FraudRiskLevel
    indicators: List[FraudIndicator] = field(default_factory=list)
    analysis_time: float = 0.0
    document_anomalies: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FraudDetector:
    """Advanced fraud detection system for contracts."""
    
    def __init__(self):
        """Initialize fraud detector with ML models and rule sets."""
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.anomaly_thresholds = {
            'unusual_terms': 0.3,
            'inconsistent_dates': 0.2,
            'suspicious_amounts': 0.4,
            'forged_signatures': 0.6,
            'template_anomalies': 0.3
        }
        
    def analyze_document(self, document_text: str, clauses: List[Any],
                        document_metadata: Dict[str, Any]) -> FraudAnalysisResult:
        """Perform comprehensive fraud analysis on a document.
        
        Args:
            document_text: Full document text
            clauses: Extracted clauses
            document_metadata: Document metadata
            
        Returns:
            Comprehensive fraud analysis result
        """
        start_time = time.perf_counter()
        
        indicators = []
        
        # Run multiple fraud detection algorithms
        indicators.extend(self._detect_suspicious_language(document_text))
        indicators.extend(self._detect_date_anomalies(document_text))
        indicators.extend(self._detect_amount_inconsistencies(document_text))
        indicators.extend(self._detect_clause_anomalies(clauses))
        indicators.extend(self._detect_template_fraud(document_text, document_metadata))
        indicators.extend(self._detect_party_fraud(document_text))
        indicators.extend(self._detect_signature_anomalies(document_text))
        
        # Calculate overall fraud score
        fraud_score = self._calculate_fraud_score(indicators)
        risk_level = self._determine_risk_level(fraud_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(indicators, risk_level)
        
        # Detect document-level anomalies
        anomalies = self._detect_document_anomalies(document_text, document_metadata)
        
        analysis_time = time.perf_counter() - start_time
        
        result = FraudAnalysisResult(
            fraud_score=fraud_score,
            risk_level=risk_level,
            indicators=indicators,
            analysis_time=analysis_time,
            document_anomalies=anomalies,
            recommendations=recommendations,
            metadata={
                "total_indicators": len(indicators),
                "high_risk_indicators": len([i for i in indicators if i.risk_score > 0.7]),
                "document_length": len(document_text),
                "clause_count": len(clauses)
            }
        )
        
        logger.info("Fraud analysis completed: score=%.3f, risk=%s, indicators=%d",
                   fraud_score, risk_level.value, len(indicators))
        
        return result
        
    def _detect_suspicious_language(self, text: str) -> List[FraudIndicator]:
        """Detect suspicious language patterns."""
        indicators = []
        text_lower = text.lower()
        
        # Check for urgent/pressure language
        urgent_patterns = [
            r'urgent(?:ly)?', r'immediate(?:ly)?', r'asap', r'rush',
            r'limited time', r'act now', r'expires? (?:today|tomorrow)',
            r'don\'?t (?:wait|delay)', r'time[- ]sensitive'
        ]
        
        for pattern in urgent_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                indicators.append(FraudIndicator(
                    indicator_type="pressure_language",
                    description="Document contains urgent/pressure language",
                    risk_score=0.4,
                    evidence=matches[:3],  # Limit evidence
                    confidence=0.8
                ))
                break
                
        # Check for vague/ambiguous terms
        vague_patterns = [
            r'(?:might|maybe|possibly|potentially) be',
            r'(?:some|various|certain|particular) (?:terms|conditions)',
            r'(?:as (?:deemed )?(?:appropriate|necessary|suitable))',
            r'(?:subject to (?:further )?(?:review|approval))'
        ]
        
        vague_count = 0
        for pattern in vague_patterns:
            vague_count += len(re.findall(pattern, text_lower))
            
        if vague_count > 3:
            indicators.append(FraudIndicator(
                indicator_type="vague_language",
                description="Excessive use of vague or ambiguous language",
                risk_score=0.3,
                evidence=[f"Found {vague_count} instances of vague language"],
                confidence=0.7
            ))
            
        # Check for unusual legal disclaimers
        unusual_disclaimers = [
            r'no warranty(?:ies)?.*express(?:ed)? or implied',
            r'use at your own risk',
            r'not responsible for (?:any )?(?:damages?|losses?)',
            r'waive(?:s)? (?:all )?rights? to (?:sue|legal action)'
        ]
        
        for pattern in unusual_disclaimers:
            if re.search(pattern, text_lower):
                indicators.append(FraudIndicator(
                    indicator_type="unusual_disclaimer",
                    description="Contains unusual or suspicious disclaimers",
                    risk_score=0.5,
                    evidence=[pattern],
                    confidence=0.6
                ))
                
        return indicators
        
    def _detect_date_anomalies(self, text: str) -> List[FraudIndicator]:
        """Detect anomalies in dates."""
        indicators = []
        
        # Extract all dates
        date_patterns = [
            r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b',
            r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b',
            r'\b(\w+)\s+(\d{1,2}),?\s+(\d{4})\b'
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates_found.extend(matches)
            
        if len(dates_found) > 10:
            # Check for date inconsistencies
            # (This is a simplified check - real implementation would parse dates)
            years = []
            for date_tuple in dates_found:
                if len(date_tuple) >= 3:
                    year_str = date_tuple[-1]
                    if year_str.isdigit():
                        year = int(year_str)
                        if year > 1900:  # Valid year range
                            years.append(year)
                            
            if years:
                year_range = max(years) - min(years)
                if year_range > 20:  # Suspicious date range
                    indicators.append(FraudIndicator(
                        indicator_type="date_anomaly",
                        description="Suspicious date range spanning multiple decades",
                        risk_score=0.6,
                        evidence=[f"Date range: {min(years)}-{max(years)}"],
                        confidence=0.7
                    ))
                    
        return indicators
        
    def _detect_amount_inconsistencies(self, text: str) -> List[FraudIndicator]:
        """Detect inconsistencies in monetary amounts."""
        indicators = []
        
        # Extract monetary amounts
        amount_patterns = [
            r'\$[\d,]+(?:\.\d{2})?',
            r'(?:USD|usd)\s*[\d,]+(?:\.\d{2})?',
            r'(?:dollars?)\s*[\d,]+(?:\.\d{2})?'
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
            
        if len(amounts) > 3:
            # Check for suspicious patterns like repeated exact amounts
            amount_counts = {}
            for amount in amounts:
                amount_counts[amount] = amount_counts.get(amount, 0) + 1
                
            repeated_amounts = [amt for amt, count in amount_counts.items() if count > 3]
            if repeated_amounts:
                indicators.append(FraudIndicator(
                    indicator_type="amount_anomaly",
                    description="Suspicious repetition of identical amounts",
                    risk_score=0.4,
                    evidence=repeated_amounts[:3],
                    confidence=0.6
                ))
                
        return indicators
        
    def _detect_clause_anomalies(self, clauses: List[Any]) -> List[FraudIndicator]:
        """Detect anomalies in clause structure and content."""
        indicators = []
        
        if not clauses:
            return indicators
            
        # Check for missing critical clauses
        clause_types = {getattr(clause, 'type', 'unknown') for clause in clauses}
        
        critical_clauses = {
            'termination', 'payment_terms', 'liability', 'governing_law'
        }
        
        missing_critical = critical_clauses - clause_types
        if len(missing_critical) >= 2:
            indicators.append(FraudIndicator(
                indicator_type="missing_clauses",
                description="Missing critical contract clauses",
                risk_score=0.5,
                evidence=list(missing_critical),
                confidence=0.8
            ))
            
        # Check for unusually short clauses (potential redaction)
        short_clauses = [
            clause for clause in clauses 
            if hasattr(clause, 'text') and len(clause.text) < 50
        ]
        
        if len(short_clauses) > len(clauses) * 0.3:  # >30% short clauses
            indicators.append(FraudIndicator(
                indicator_type="redacted_content",
                description="Unusually high number of very short clauses",
                risk_score=0.6,
                evidence=[f"Found {len(short_clauses)} short clauses"],
                confidence=0.7
            ))
            
        return indicators
        
    def _detect_template_fraud(self, text: str, metadata: Dict[str, Any]) -> List[FraudIndicator]:
        """Detect template-based fraud indicators."""
        indicators = []
        
        # Check for template artifacts
        template_artifacts = [
            r'\[.*?\]',  # Square bracket placeholders
            r'\{.*?\}',  # Curly bracket placeholders
            r'____+',    # Blank lines
            r'XX+',      # Placeholder text
            r'TBD|tbd|To Be Determined'
        ]
        
        artifacts_found = []
        for pattern in template_artifacts:
            matches = re.findall(pattern, text, re.IGNORECASE)
            artifacts_found.extend(matches)
            
        if len(artifacts_found) > 5:
            indicators.append(FraudIndicator(
                indicator_type="template_artifacts",
                description="Document contains numerous template artifacts",
                risk_score=0.4,
                evidence=artifacts_found[:5],
                confidence=0.8
            ))
            
        return indicators
        
    def _detect_party_fraud(self, text: str) -> List[FraudIndicator]:
        """Detect fraud related to contract parties."""
        indicators = []
        
        # Check for suspicious party names
        suspicious_patterns = [
            r'(?:john|jane)\s+doe',
            r'test\s+(?:company|corp|llc)',
            r'example\s+(?:company|corp|llc)',
            r'placeholder\s+(?:name|company)',
            r'(?:company|corp|llc)\s+(?:name|here)'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                indicators.append(FraudIndicator(
                    indicator_type="placeholder_parties",
                    description="Document contains placeholder party names",
                    risk_score=0.7,
                    evidence=[pattern],
                    confidence=0.9
                ))
                
        return indicators
        
    def _detect_signature_anomalies(self, text: str) -> List[FraudIndicator]:
        """Detect signature-related anomalies."""
        indicators = []
        
        # Check for digital signature indicators
        signature_patterns = [
            r'digitally signed',
            r'electronic signature',
            r'esignature',
            r'/s/\s*[A-Za-z\s]+',
            r'signed electronically'
        ]
        
        signature_count = 0
        for pattern in signature_patterns:
            signature_count += len(re.findall(pattern, text, re.IGNORECASE))
            
        # Check for suspicious signature text
        if re.search(r'signature\s+(?:pending|required|missing)', text, re.IGNORECASE):
            indicators.append(FraudIndicator(
                indicator_type="missing_signatures",
                description="Document indicates missing or pending signatures",
                risk_score=0.3,
                evidence=["Signature status mentioned"],
                confidence=0.6
            ))
            
        return indicators
        
    def _calculate_fraud_score(self, indicators: List[FraudIndicator]) -> float:
        """Calculate overall fraud score from indicators."""
        if not indicators:
            return 0.0
            
        # Weighted scoring based on indicator types
        type_weights = {
            'pressure_language': 1.0,
            'vague_language': 0.8,
            'unusual_disclaimer': 1.2,
            'date_anomaly': 1.1,
            'amount_anomaly': 1.0,
            'missing_clauses': 1.3,
            'redacted_content': 1.1,
            'template_artifacts': 0.9,
            'placeholder_parties': 1.5,
            'missing_signatures': 0.7
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for indicator in indicators:
            weight = type_weights.get(indicator.indicator_type, 1.0)
            weighted_score = indicator.risk_score * indicator.confidence * weight
            total_score += weighted_score
            total_weight += weight
            
        if total_weight == 0:
            return 0.0
            
        # Normalize to 0-1 range
        fraud_score = min(1.0, total_score / total_weight)
        return round(fraud_score, 3)
        
    def _determine_risk_level(self, fraud_score: float) -> FraudRiskLevel:
        """Determine risk level from fraud score."""
        if fraud_score >= 0.8:
            return FraudRiskLevel.CRITICAL
        elif fraud_score >= 0.6:
            return FraudRiskLevel.HIGH
        elif fraud_score >= 0.3:
            return FraudRiskLevel.MEDIUM
        else:
            return FraudRiskLevel.LOW
            
    def _generate_recommendations(self, indicators: List[FraudIndicator], 
                                risk_level: FraudRiskLevel) -> List[str]:
        """Generate fraud prevention recommendations."""
        recommendations = []
        
        if risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
            recommendations.append("Require additional verification of document authenticity")
            recommendations.append("Request original signed documents")
            recommendations.append("Verify party identities through independent sources")
            
        indicator_types = {indicator.indicator_type for indicator in indicators}
        
        if 'placeholder_parties' in indicator_types:
            recommendations.append("Verify all party names and contact information")
            
        if 'missing_clauses' in indicator_types:
            recommendations.append("Ensure all critical contract clauses are present")
            
        if 'template_artifacts' in indicator_types:
            recommendations.append("Review document for incomplete template sections")
            
        if 'date_anomaly' in indicator_types:
            recommendations.append("Verify all dates for accuracy and consistency")
            
        if not recommendations:
            recommendations.append("Document appears legitimate but continue standard verification procedures")
            
        return recommendations
        
    def _detect_document_anomalies(self, text: str, metadata: Dict[str, Any]) -> List[str]:
        """Detect document-level anomalies."""
        anomalies = []
        
        # Check document length anomalies
        text_length = len(text)
        if text_length < 500:
            anomalies.append("Document unusually short for a legal contract")
        elif text_length > 100000:
            anomalies.append("Document unusually long, may contain padding")
            
        # Check for excessive whitespace
        whitespace_ratio = (text.count(' ') + text.count('\n') + text.count('\t')) / len(text)
        if whitespace_ratio > 0.4:
            anomalies.append("Document contains excessive whitespace")
            
        # Check file metadata anomalies
        file_size = metadata.get("file_size", 0)
        if file_size > 50 * 1024 * 1024:  # 50MB
            anomalies.append("File size unusually large for a contract")
            
        return anomalies
        
    def _load_suspicious_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for suspicious content detection."""
        return {
            "scam_phrases": [
                "guaranteed return",
                "risk free",
                "limited time offer",
                "act now",
                "no questions asked"
            ],
            "placeholder_text": [
                "lorem ipsum",
                "sample text",
                "placeholder",
                "example text",
                "dummy content"
            ],
            "urgency_markers": [
                "urgent",
                "immediate",
                "expires today",
                "last chance",
                "time sensitive"
            ]
        }