#!/usr/bin/env python3
"""
Terragon Autonomous Value Discovery Engine
Advanced SDLC optimization and continuous value discovery system
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
try:
    import yaml
except ImportError:
    # Fallback YAML parser for environments without PyYAML
    class SimpleYamlLoader:
        @staticmethod
        def safe_load(content):
            # Simple YAML-like parser for basic config
            if isinstance(content, str):
                lines = content.strip().split('\n')
            else:
                lines = content.read().strip().split('\n')
            
            result = {}
            current_section = result
            section_stack = [result]
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Handle indentation for nested structures
                    indent_level = (len(line) - len(line.lstrip())) // 2
                    
                    # Adjust section stack based on indentation
                    while len(section_stack) > indent_level + 1:
                        section_stack.pop()
                    
                    current_section = section_stack[-1]
                    
                    # Parse value
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '').isdigit():
                        value = float(value)
                    elif value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    current_section[key] = value
                    
                    # If this might be a section header, prepare for nesting
                    if not value or (isinstance(value, str) and not value.strip()):
                        current_section[key] = {}
                        section_stack.append(current_section[key])
            
            return result
    
    yaml = SimpleYamlLoader()

@dataclass
class ValueItem:
    """Represents a discovered value delivery opportunity"""
    id: str
    title: str
    description: str
    category: str
    type: str
    
    # Scoring components
    wsjf_score: float
    ice_score: float
    technical_debt_score: float
    composite_score: float
    
    # Estimation and tracking
    estimated_effort_hours: float
    confidence: float
    risk_level: str
    priority: str
    
    # Context
    files_affected: List[str]
    dependencies: List[str]
    source: str
    discovered_at: str
    
    # Execution tracking
    status: str = "discovered"
    assigned_to: str = "autonomous"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ValueDiscoveryEngine:
    """Advanced value discovery and prioritization engine"""
    
    def __init__(self, config_path: str = ".terragon/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.metrics = {"discoveries": 0, "completions": 0, "value_delivered": 0}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load Terragon configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Configure logging for value discovery"""
        logger = logging.getLogger("terragon.value_discovery")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def discover_opportunities(self) -> List[ValueItem]:
        """Main discovery orchestration"""
        self.logger.info("🔍 Starting autonomous value discovery...")
        
        opportunities = []
        
        # Multi-source signal harvesting
        git_signals = await self._analyze_git_history()
        static_signals = await self._run_static_analysis()
        security_signals = await self._scan_security_vulnerabilities()
        performance_signals = await self._analyze_performance_metrics()
        dependency_signals = await self._check_dependency_updates()
        
        # Combine all signals
        all_signals = (
            git_signals + static_signals + security_signals + 
            performance_signals + dependency_signals
        )
        
        # Score and prioritize
        for signal in all_signals:
            item = self._create_value_item(signal)
            if item and item.composite_score >= self.config["scoring"]["thresholds"]["minScore"]:
                opportunities.append(item)
        
        # Sort by composite score
        opportunities.sort(key=lambda x: x.composite_score, reverse=True)
        
        self.logger.info(f"📊 Discovered {len(opportunities)} value opportunities")
        return opportunities
    
    async def _analyze_git_history(self) -> List[Dict[str, Any]]:
        """Extract value signals from Git history"""
        signals = []
        
        try:
            # Find TODO/FIXME/HACK comments in commits
            result = subprocess.run([
                "git", "log", "--grep=TODO\\|FIXME\\|HACK\\|temporary\\|quick fix",
                "-i", "--oneline", "-20"
            ], capture_output=True, text=True, cwd=".")
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    signals.append({
                        "type": "technical_debt",
                        "source": "git_history", 
                        "description": f"Technical debt from commit: {line}",
                        "urgency": "medium",
                        "effort": 2.0
                    })
            
            # Analyze file churn vs complexity
            churn_result = subprocess.run([
                "git", "log", "--name-only", "--pretty=format:", "--since=30.days.ago"
            ], capture_output=True, text=True, cwd=".")
            
            file_changes = {}
            for line in churn_result.stdout.strip().split('\n'):
                if line and line.endswith('.py'):
                    file_changes[line] = file_changes.get(line, 0) + 1
            
            # High-churn files are refactoring candidates
            for file_path, change_count in file_changes.items():
                if change_count > 10:  # High churn threshold
                    signals.append({
                        "type": "refactoring",
                        "source": "git_churn",
                        "description": f"High-churn file needs refactoring: {file_path}",
                        "files": [file_path],
                        "urgency": "medium",
                        "effort": 4.0
                    })
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Git analysis failed: {e}")
        
        return signals
    
    async def _run_static_analysis(self) -> List[Dict[str, Any]]:
        """Run static analysis tools for code quality signals"""
        signals = []
        
        try:
            # Run ruff for code quality issues
            result = subprocess.run([
                "ruff", "check", ".", "--format=json"
            ], capture_output=True, text=True, cwd=".")
            
            if result.stdout:
                issues = json.loads(result.stdout)
                for issue in issues[:10]:  # Limit to top issues
                    signals.append({
                        "type": "code_quality",
                        "source": "ruff",
                        "description": f"Code quality issue: {issue.get('message', 'Unknown')}",
                        "files": [issue.get('filename', '')],
                        "urgency": "low",
                        "effort": 0.5
                    })
            
            # Run mypy for type checking
            mypy_result = subprocess.run([
                "mypy", "src/", "--json-report", "/tmp/mypy_report"
            ], capture_output=True, text=True, cwd=".")
            
            if mypy_result.returncode != 0:
                signals.append({
                    "type": "type_safety",
                    "source": "mypy",
                    "description": "Type checking improvements needed",
                    "urgency": "medium",
                    "effort": 3.0
                })
                
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.logger.warning(f"Static analysis failed: {e}")
        
        return signals
    
    async def _scan_security_vulnerabilities(self) -> List[Dict[str, Any]]:
        """Scan for security vulnerabilities"""
        signals = []
        
        try:
            # Run safety check
            result = subprocess.run([
                "safety", "check", "--json"
            ], capture_output=True, text=True, cwd=".")
            
            if result.stdout:
                vulnerabilities = json.loads(result.stdout)
                for vuln in vulnerabilities:
                    signals.append({
                        "type": "security_vulnerability",
                        "source": "safety",
                        "description": f"Security vulnerability: {vuln.get('advisory', 'Unknown')}",
                        "urgency": "high",
                        "effort": 1.0,
                        "security_boost": True
                    })
            
            # Run bandit security scan
            bandit_result = subprocess.run([
                "bandit", "-r", "src/", "-f", "json"
            ], capture_output=True, text=True, cwd=".")
            
            if bandit_result.stdout:
                try:
                    bandit_data = json.loads(bandit_result.stdout)
                    for issue in bandit_data.get("results", [])[:5]:
                        signals.append({
                            "type": "security_issue",
                            "source": "bandit",
                            "description": f"Security issue: {issue.get('test_name', 'Unknown')}",
                            "files": [issue.get('filename', '')],
                            "urgency": "high",
                            "effort": 1.5,
                            "security_boost": True
                        })
                except json.JSONDecodeError:
                    pass
                    
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Security scan failed: {e}")
        
        return signals
    
    async def _analyze_performance_metrics(self) -> List[Dict[str, Any]]:
        """Analyze performance metrics and bottlenecks"""
        signals = []
        
        # Check for large files that might need optimization
        try:
            result = subprocess.run([
                "find", ".", "-name", "*.py", "-size", "+1k", "-exec", "wc", "-l", "{}", "+"
            ], capture_output=True, text=True, cwd=".")
            
            for line in result.stdout.strip().split('\n')[-10:]:  # Last 10 largest
                if line and 'total' not in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        line_count, file_path = parts[0], parts[1]
                        if int(line_count) > 200:  # Large file threshold
                            signals.append({
                                "type": "performance_optimization",
                                "source": "file_size_analysis",
                                "description": f"Large file may need optimization: {file_path} ({line_count} lines)",
                                "files": [file_path],
                                "urgency": "medium",
                                "effort": 3.0
                            })
                            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Performance analysis failed: {e}")
        
        return signals
    
    async def _check_dependency_updates(self) -> List[Dict[str, Any]]:
        """Check for dependency updates"""
        signals = []
        
        try:
            # Check for outdated packages
            result = subprocess.run([
                "pip", "list", "--outdated", "--format=json"
            ], capture_output=True, text=True, cwd=".")
            
            if result.stdout:
                outdated = json.loads(result.stdout)
                for package in outdated[:5]:  # Top 5 outdated packages
                    signals.append({
                        "type": "dependency_update",
                        "source": "pip_outdated",
                        "description": f"Update {package['name']} from {package['version']} to {package['latest_version']}",
                        "urgency": "low",
                        "effort": 1.0
                    })
                    
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            self.logger.warning(f"Dependency check failed: {e}")
        
        return signals
    
    def _create_value_item(self, signal: Dict[str, Any]) -> Optional[ValueItem]:
        """Convert signal to scored value item"""
        try:
            # Calculate WSJF components
            urgency_map = {"high": 10, "medium": 6, "low": 3}
            type_business_value = {
                "security_vulnerability": 10,
                "security_issue": 8,
                "performance_optimization": 7,
                "technical_debt": 5,
                "code_quality": 4,
                "dependency_update": 3,
                "refactoring": 6,
                "type_safety": 5
            }
            
            urgency = urgency_map.get(signal.get("urgency", "low"), 3)
            business_value = type_business_value.get(signal.get("type", ""), 3)
            effort = signal.get("effort", 2.0)
            
            # WSJF = (Business Value + Urgency + Risk Reduction) / Effort
            wsjf_score = (business_value + urgency + 3) / max(effort, 0.5)
            
            # ICE = Impact * Confidence * Ease
            impact = business_value
            confidence = 8  # Default confidence
            ease = max(10 - effort, 1)
            ice_score = impact * confidence * ease
            
            # Technical debt score
            debt_score = business_value * urgency if "debt" in signal.get("type", "") else 0
            
            # Apply boosts
            composite_score = (
                self.config["scoring"]["weights"]["advanced"]["wsjf"] * wsjf_score +
                self.config["scoring"]["weights"]["advanced"]["ice"] * ice_score / 100 +
                self.config["scoring"]["weights"]["advanced"]["technicalDebt"] * debt_score
            )
            
            # Security boost
            if signal.get("security_boost", False):
                composite_score *= self.config["scoring"]["thresholds"]["securityBoost"]
            
            return ValueItem(
                id=f"{signal.get('type', 'unknown')}-{int(time.time())}",
                title=signal.get("description", "Unknown opportunity")[:50],
                description=signal.get("description", "No description"),
                category=signal.get("type", "unknown"),
                type=signal.get("source", "unknown"),
                wsjf_score=round(wsjf_score, 2),
                ice_score=round(ice_score, 2),
                technical_debt_score=round(debt_score, 2),
                composite_score=round(composite_score, 2),
                estimated_effort_hours=effort,
                confidence=0.8,
                risk_level=signal.get("urgency", "low"),
                priority="high" if composite_score > 50 else "medium" if composite_score > 20 else "low",
                files_affected=signal.get("files", []),
                dependencies=[],
                source=signal.get("source", "unknown"),
                discovered_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create value item: {e}")
            return None
    
    def save_metrics(self, opportunities: List[ValueItem]) -> None:
        """Save discovery metrics"""
        metrics_path = Path(".terragon/value-metrics.json")
        metrics_path.parent.mkdir(exist_ok=True)
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_opportunities": len(opportunities),
            "high_priority": len([o for o in opportunities if o.priority == "high"]),
            "medium_priority": len([o for o in opportunities if o.priority == "medium"]),
            "low_priority": len([o for o in opportunities if o.priority == "low"]),
            "categories": {},
            "top_opportunities": [o.to_dict() for o in opportunities[:10]]
        }
        
        # Category breakdown
        for opp in opportunities:
            metrics["categories"][opp.category] = metrics["categories"].get(opp.category, 0) + 1
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        self.logger.info(f"💾 Metrics saved to {metrics_path}")

async def main():
    """Main entry point for value discovery"""
    try:
        engine = ValueDiscoveryEngine()
        opportunities = await engine.discover_opportunities()
        engine.save_metrics(opportunities)
        
        if opportunities:
            top_item = opportunities[0]
            print(f"🎯 Next Best Value Item: {top_item.title}")
            print(f"   Score: {top_item.composite_score}")
            print(f"   Effort: {top_item.estimated_effort_hours}h")
            print(f"   Priority: {top_item.priority}")
        else:
            print("✅ No immediate value opportunities discovered")
            
    except Exception as e:
        logging.error(f"Value discovery failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))