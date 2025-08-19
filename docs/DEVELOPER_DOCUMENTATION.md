# Developer Documentation
## Advanced Multimodal Contract Extractor - Development Guide

**Version**: 4.0.0  
**Last Updated**: 2025-01-24  
**Target Audience**: Software Developers, Contributors, Maintainers  

---

## 📋 Table of Contents

1. [Development Setup](#development-setup)
2. [Code Architecture](#code-architecture)
3. [Testing Guide](#testing-guide)
4. [Contributing Guidelines](#contributing-guidelines)
5. [Code Style & Standards](#code-style--standards)
6. [Debugging & Profiling](#debugging--profiling)
7. [Performance Optimization](#performance-optimization)
8. [Extension Development](#extension-development)
9. [Troubleshooting](#troubleshooting)

---

## 🛠️ Development Setup

### Prerequisites

#### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10/11 with WSL2
- **Python**: 3.9 - 3.11 (3.10 recommended)
- **Git**: 2.25+
- **Docker**: 20.10+ (optional but recommended)
- **Node.js**: 16+ (for web interface development)

#### Hardware Requirements

**Minimum Development Setup:**
- 8 GB RAM
- 4 CPU cores
- 50 GB free disk space
- Internet connection for model downloads

**Recommended Development Setup:**
- 16 GB RAM
- 8 CPU cores
- 100 GB SSD storage
- GPU with 8+ GB VRAM (for research algorithm development)

### Quick Setup

#### 1. Clone and Environment Setup

```bash
# Clone the repository
git clone https://github.com/your-org/multimodal-contract-extractor.git
cd multimodal-contract-extractor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev,test,research]"

# Install pre-commit hooks
pre-commit install

# Verify installation
python -c "import multimodal_contract_extractor; print('Installation successful!')"
```

#### 2. Configure Development Environment

```bash
# Copy configuration template
cp config.example.yml config.development.yml

# Set environment variables
cat > .env << EOF
ENVIRONMENT=development
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///dev.db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
OPENAI_API_KEY=your-openai-key-here
HUGGINGFACE_TOKEN=your-hf-token-here
EOF

# Initialize development database
python scripts/init_dev_db.py

# Download required models
python scripts/download_models.py --development
```

#### 3. Development Services

```bash
# Start development services with Docker
docker-compose -f docker-compose.dev.yml up -d

# Or manually start services
# PostgreSQL
docker run --name postgres-dev -e POSTGRES_PASSWORD=dev -p 5432:5432 -d postgres:15

# Redis
docker run --name redis-dev -p 6379:6379 -d redis:7-alpine

# Start development server
python -m multimodal_contract_extractor.dev_server
```

### IDE Configuration

#### VS Code Setup

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".mypy_cache": true,
        ".pytest_cache": true,
        "htmlcov": true
    }
}
```

Create `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Debug API Server",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/api/app.py",
            "console": "integratedTerminal",
            "env": {
                "ENVIRONMENT": "development",
                "LOG_LEVEL": "DEBUG"
            }
        },
        {
            "name": "Python: Debug CLI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/extract.py",
            "args": ["--file", "test_contract.pdf", "--debug"],
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Run Tests",
            "type": "python",
            "request": "launch",
            "module": "pytest",
            "args": ["tests/", "-v"],
            "console": "integratedTerminal"
        }
    ]
}
```

#### PyCharm Setup

1. **Project Interpreter**: Set to `./venv/bin/python`
2. **Code Style**: Import `.editorconfig` settings
3. **Testing Framework**: Configure pytest as default test runner
4. **Git Integration**: Enable version control integration
5. **Docker Integration**: Configure Docker support for containerized development

### Development Workflow

#### Daily Development Routine

```bash
# 1. Start development session
source venv/bin/activate
export ENVIRONMENT=development

# 2. Update dependencies
pip install -e ".[dev,test,research]"

# 3. Run pre-commit checks
pre-commit run --all-files

# 4. Run tests
pytest tests/ -v --cov=src/

# 5. Start development server
python -m multimodal_contract_extractor.dev_server

# 6. Work on features...

# 7. Before committing
make lint
make test
make type-check
```

#### Git Workflow

```bash
# Feature development
git checkout -b feature/new-algorithm
git add .
git commit -m "feat: implement new legal reasoning algorithm"
git push origin feature/new-algorithm

# Create pull request through GitHub/GitLab interface

# After review and merge
git checkout main
git pull origin main
git branch -d feature/new-algorithm
```

---

## 🏗️ Code Architecture

### Project Structure

```
multimodal-contract-extractor/
├── src/                              # Source code
│   ├── api/                         # REST API implementation
│   │   ├── app.py                   # FastAPI application
│   │   ├── routes.py                # API route handlers
│   │   └── middleware.py            # Custom middleware
│   ├── multimodal_contract_extractor/  # Core library
│   │   ├── __init__.py              # Package initialization
│   │   ├── document.py              # Document processing
│   │   ├── extraction.py            # Core extraction logic
│   │   ├── config.py                # Configuration management
│   │   ├── novel_research_algorithms.py  # Research algorithms
│   │   ├── graph_neural_networks.py # GNN implementation
│   │   ├── advanced_transformer_attention.py  # Transformer attention
│   │   ├── federated_legal_learning.py  # Federated learning
│   │   ├── causal_inference_legal.py # Causal inference
│   │   ├── advanced_multimodal_fusion.py  # Multimodal fusion
│   │   ├── enterprise_*.py          # Enterprise reliability modules
│   │   └── generation4_*.py         # Generation 4 optimization
│   ├── models/                      # Data models
│   │   ├── contract.py              # Contract model
│   │   ├── clause.py                # Clause model
│   │   └── processing.py            # Processing models
│   ├── services/                    # Business logic services
│   │   ├── processing_service.py    # Document processing service
│   │   └── validation_service.py    # Validation service
│   └── database/                    # Database layer
│       ├── connection.py            # Database connections
│       ├── repositories.py          # Data repositories
│       └── cache_manager.py         # Cache management
├── tests/                           # Test suite
│   ├── unit/                        # Unit tests
│   ├── integration/                 # Integration tests
│   ├── e2e/                         # End-to-end tests
│   └── fixtures/                    # Test fixtures
├── docs/                            # Documentation
├── scripts/                         # Utility scripts
├── k8s/                            # Kubernetes manifests
├── monitoring/                      # Monitoring configuration
└── web_app.py                       # Streamlit web interface
```

### Core Components

#### Document Processing Pipeline

```python
class DocumentProcessor:
    """Core document processing pipeline."""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.ocr_engine = OCREngine(config.ocr_settings)
        self.text_extractor = TextExtractor(config.extraction_settings)
        self.preprocessor = DocumentPreprocessor(config.preprocessing_settings)
        
        # Research algorithms
        self.gnn_analyzer = GraphNeuralNetworkAnalyzer(config.gnn_settings)
        self.transformer_attention = AdvancedTransformerAttention(config.attention_settings)
        self.causal_engine = CausalInferenceEngine(config.causal_settings)
        self.multimodal_fusion = MultimodalFusionEngine(config.fusion_settings)
    
    async def process_document(self, document: RawDocument) -> ProcessedDocument:
        """Process document through complete pipeline."""
        
        # Stage 1: Document ingestion and preprocessing
        preprocessed_doc = await self.preprocessor.preprocess(document)
        
        # Stage 2: Text and visual feature extraction
        text_features = await self.text_extractor.extract_text(preprocessed_doc)
        visual_features = await self.ocr_engine.extract_visual_features(preprocessed_doc)
        
        # Stage 3: Multimodal fusion
        fused_features = await self.multimodal_fusion.fuse_features(
            text_features, visual_features
        )
        
        # Stage 4: Graph construction and GNN analysis
        graph = await self.gnn_analyzer.construct_legal_graph(fused_features)
        gnn_results = await self.gnn_analyzer.analyze_graph(graph)
        
        # Stage 5: Advanced attention processing
        attention_results = await self.transformer_attention.process_with_legal_attention(
            fused_features, gnn_results.attention_guidance
        )
        
        # Stage 6: Causal inference
        causal_results = await self.causal_engine.analyze_causal_relationships(
            attention_results.entities, attention_results.relationships
        )
        
        # Stage 7: Result compilation
        processed_doc = ProcessedDocument(
            original_document=document,
            text_features=text_features,
            visual_features=visual_features,
            gnn_analysis=gnn_results,
            attention_analysis=attention_results,
            causal_analysis=causal_results,
            processing_metadata=self._create_processing_metadata()
        )
        
        return processed_doc
    
    def _create_processing_metadata(self) -> ProcessingMetadata:
        """Create metadata about processing pipeline."""
        return ProcessingMetadata(
            pipeline_version="4.0.0",
            algorithms_used=[
                "graph_neural_networks",
                "advanced_transformer_attention", 
                "causal_inference",
                "multimodal_fusion"
            ],
            processing_time=time.time(),
            quality_score=self._compute_quality_score()
        )
```

#### Plugin Architecture

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class ProcessingPlugin(ABC):
    """Base class for processing plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @abstractmethod
    async def process(self, input_data: Any, context: Dict[str, Any]) -> Any:
        """Process input data."""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data format."""
        pass

class PluginManager:
    """Manage and execute processing plugins."""
    
    def __init__(self):
        self.plugins: Dict[str, ProcessingPlugin] = {}
        self.plugin_registry = PluginRegistry()
    
    def register_plugin(self, plugin: ProcessingPlugin):
        """Register a new plugin."""
        self.plugins[plugin.name] = plugin
        self.plugin_registry.register(plugin)
    
    def discover_plugins(self, plugin_dir: str = "plugins/"):
        """Discover and load plugins from directory."""
        import importlib
        import os
        
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                spec = importlib.util.spec_from_file_location(
                    module_name, 
                    os.path.join(plugin_dir, filename)
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for plugin classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, ProcessingPlugin) and 
                        attr != ProcessingPlugin):
                        plugin_instance = attr()
                        self.register_plugin(plugin_instance)
    
    async def execute_plugin(self, plugin_name: str, 
                           input_data: Any, 
                           context: Dict[str, Any] = None) -> Any:
        """Execute a specific plugin."""
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' not found")
        
        plugin = self.plugins[plugin_name]
        
        # Validate input
        if not plugin.validate_input(input_data):
            raise ValueError(f"Invalid input for plugin '{plugin_name}'")
        
        # Execute plugin
        context = context or {}
        result = await plugin.process(input_data, context)
        
        return result

# Example plugin implementation
class CustomLegalAnalysisPlugin(ProcessingPlugin):
    """Custom legal analysis plugin example."""
    
    @property
    def name(self) -> str:
        return "custom_legal_analysis"
    
    @property  
    def version(self) -> str:
        return "1.0.0"
    
    async def process(self, input_data: ProcessedDocument, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform custom legal analysis."""
        
        # Custom analysis logic
        analysis_results = {
            'risk_score': self._calculate_risk_score(input_data),
            'compliance_check': self._check_compliance(input_data),
            'recommendations': self._generate_recommendations(input_data)
        }
        
        return analysis_results
    
    def validate_input(self, input_data: Any) -> bool:
        """Validate input data."""
        return isinstance(input_data, ProcessedDocument)
    
    def _calculate_risk_score(self, document: ProcessedDocument) -> float:
        """Calculate document risk score."""
        # Implementation specific logic
        return 0.75
    
    def _check_compliance(self, document: ProcessedDocument) -> Dict[str, bool]:
        """Check regulatory compliance."""
        return {
            'gdpr_compliant': True,
            'hipaa_compliant': False,
            'sox_compliant': True
        }
    
    def _generate_recommendations(self, document: ProcessedDocument) -> List[str]:
        """Generate improvement recommendations."""
        return [
            "Add explicit data retention clauses",
            "Clarify termination procedures",
            "Include penalty specifications"
        ]
```

### Data Models

#### Core Data Structures

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

# Enums
class DocumentType(Enum):
    CONTRACT = "contract"
    NDA = "nda" 
    EMPLOYMENT = "employment"
    LEASE = "lease"
    PURCHASE = "purchase"
    SERVICE = "service"

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConfidenceLevel(Enum):
    LOW = "low"      # < 0.7
    MEDIUM = "medium"  # 0.7 - 0.85
    HIGH = "high"    # 0.85 - 0.95
    VERY_HIGH = "very_high"  # > 0.95

# Core Models
@dataclass
class BoundingBox:
    """Bounding box for text/visual elements."""
    x: float
    y: float
    width: float
    height: float
    page_number: int = 0
    
    def area(self) -> float:
        return self.width * self.height
    
    def center(self) -> tuple:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box intersects with another."""
        return not (self.x + self.width < other.x or
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or
                   other.y + other.height < self.y)

class LegalEntity(BaseModel):
    """Legal entity extracted from documents."""
    id: str = Field(..., description="Unique entity identifier")
    type: str = Field(..., description="Entity type (party, obligation, etc.)")
    name: str = Field(..., description="Entity name or text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    position: Optional[BoundingBox] = Field(None, description="Position in document")
    attributes: Dict[str, Any] = Field(default_factory=dict)
    normalized_form: Optional[str] = Field(None, description="Normalized entity name")
    
    class Config:
        json_encoders = {
            BoundingBox: lambda v: {
                'x': v.x, 'y': v.y, 'width': v.width, 'height': v.height, 'page': v.page_number
            }
        }

class LegalClause(BaseModel):
    """Legal clause extracted from documents."""
    id: str = Field(..., description="Unique clause identifier")
    type: str = Field(..., description="Clause type")
    text: str = Field(..., description="Full clause text")
    confidence: float = Field(..., ge=0.0, le=1.0)
    position: Optional[BoundingBox] = None
    page_number: int = Field(1, ge=1)
    
    # Legal analysis results
    entities: List[LegalEntity] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    
    # Research algorithm results
    gnn_analysis: Optional[Dict[str, Any]] = None
    causal_relationships: List[Dict[str, Any]] = Field(default_factory=list)
    
    def get_confidence_level(self) -> ConfidenceLevel:
        """Get categorical confidence level."""
        if self.confidence < 0.7:
            return ConfidenceLevel.LOW
        elif self.confidence < 0.85:
            return ConfidenceLevel.MEDIUM
        elif self.confidence < 0.95:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH

class ProcessedDocument(BaseModel):
    """Fully processed legal document with all analysis results."""
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    document_type: DocumentType
    processing_status: ProcessingStatus
    
    # Content
    text_content: str = Field("", description="Extracted text content")
    page_count: int = Field(1, ge=1)
    
    # Extraction results
    clauses: List[LegalClause] = Field(default_factory=list)
    entities: List[LegalEntity] = Field(default_factory=list)
    
    # Research algorithm results
    gnn_analysis: Optional[Dict[str, Any]] = None
    transformer_analysis: Optional[Dict[str, Any]] = None
    causal_analysis: Optional[Dict[str, Any]] = None
    multimodal_analysis: Optional[Dict[str, Any]] = None
    
    # Processing metadata
    processing_time_ms: int = Field(0, ge=0)
    algorithms_used: List[str] = Field(default_factory=list)
    quality_metrics: Dict[str, float] = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_overall_confidence(self) -> float:
        """Calculate overall document processing confidence."""
        if not self.clauses:
            return 0.0
        
        clause_confidences = [clause.confidence for clause in self.clauses]
        return sum(clause_confidences) / len(clause_confidences)
    
    def get_clauses_by_type(self, clause_type: str) -> List[LegalClause]:
        """Get all clauses of a specific type."""
        return [clause for clause in self.clauses if clause.type == clause_type]
    
    def get_high_risk_clauses(self, risk_threshold: float = 0.7) -> List[LegalClause]:
        """Get clauses with high risk factors."""
        return [
            clause for clause in self.clauses 
            if len(clause.risk_factors) > 0 and 
               clause.confidence > risk_threshold
        ]
```

### Configuration Management

```python
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml
from pydantic import BaseSettings, Field

class DatabaseConfig(BaseSettings):
    """Database configuration."""
    url: str = Field(..., env='DATABASE_URL')
    pool_size: int = Field(10, env='DB_POOL_SIZE')
    max_overflow: int = Field(20, env='DB_MAX_OVERFLOW')
    pool_timeout: int = Field(30, env='DB_POOL_TIMEOUT')
    pool_recycle: int = Field(3600, env='DB_POOL_RECYCLE')
    echo: bool = Field(False, env='DB_ECHO')

class RedisConfig(BaseSettings):
    """Redis configuration."""
    url: str = Field(..., env='REDIS_URL')
    max_connections: int = Field(20, env='REDIS_MAX_CONNECTIONS')
    retry_on_timeout: bool = Field(True, env='REDIS_RETRY_ON_TIMEOUT')
    socket_timeout: int = Field(30, env='REDIS_SOCKET_TIMEOUT')

class ProcessingConfig(BaseSettings):
    """Document processing configuration."""
    batch_size: int = Field(32, env='PROCESSING_BATCH_SIZE')
    max_concurrent_requests: int = Field(100, env='MAX_CONCURRENT_REQUESTS')
    timeout_seconds: int = Field(300, env='PROCESSING_TIMEOUT')
    
    # OCR settings
    ocr_engine: str = Field('tesseract', env='OCR_ENGINE')
    ocr_languages: List[str] = Field(['eng'], env='OCR_LANGUAGES')
    ocr_confidence_threshold: float = Field(0.6, env='OCR_CONFIDENCE_THRESHOLD')
    
    # Research algorithm settings
    enable_gnn: bool = Field(True, env='ENABLE_GNN')
    enable_advanced_attention: bool = Field(True, env='ENABLE_ADVANCED_ATTENTION')
    enable_causal_inference: bool = Field(True, env='ENABLE_CAUSAL_INFERENCE')
    enable_multimodal_fusion: bool = Field(True, env='ENABLE_MULTIMODAL_FUSION')
    enable_federated_learning: bool = Field(False, env='ENABLE_FEDERATED_LEARNING')

class ApplicationConfig(BaseSettings):
    """Main application configuration."""
    
    # Application settings
    app_name: str = Field('Multimodal Contract Extractor', env='APP_NAME')
    version: str = Field('4.0.0', env='APP_VERSION')
    environment: str = Field('development', env='ENVIRONMENT')
    debug: bool = Field(False, env='DEBUG')
    
    # Server settings
    host: str = Field('0.0.0.0', env='HOST')
    port: int = Field(8000, env='PORT')
    workers: int = Field(1, env='WORKERS')
    
    # Security settings
    secret_key: str = Field(..., env='SECRET_KEY')
    access_token_expire_minutes: int = Field(30, env='ACCESS_TOKEN_EXPIRE_MINUTES')
    
    # External services
    openai_api_key: Optional[str] = Field(None, env='OPENAI_API_KEY')
    huggingface_token: Optional[str] = Field(None, env='HUGGINGFACE_TOKEN')
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    
    class Config:
        env_file = '.env'
        case_sensitive = False

class ConfigManager:
    """Centralized configuration management."""
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        self.config_file = Path(config_file) if config_file else None
        self._config_cache: Dict[str, Any] = {}
        self._config = self._load_config()
    
    def _load_config(self) -> ApplicationConfig:
        """Load configuration from file and environment."""
        
        config_data = {}
        
        # Load from YAML file if provided
        if self.config_file and self.config_file.exists():
            with open(self.config_file, 'r') as f:
                yaml_data = yaml.safe_load(f)
                config_data.update(yaml_data or {})
        
        # Create configuration object (env vars take precedence)
        return ApplicationConfig(**config_data)
    
    def get_config(self) -> ApplicationConfig:
        """Get current configuration."""
        return self._config
    
    def reload_config(self):
        """Reload configuration from file and environment."""
        self._config = self._load_config()
        self._config_cache.clear()
    
    def get_research_config(self) -> Dict[str, Any]:
        """Get research algorithm-specific configuration."""
        
        if 'research_config' not in self._config_cache:
            research_config = {
                'gnn': {
                    'enabled': self._config.processing.enable_gnn,
                    'model_type': 'legal_gat',
                    'hidden_dimensions': 256,
                    'num_layers': 6,
                    'attention_heads': 8,
                    'dropout': 0.1
                },
                'transformer_attention': {
                    'enabled': self._config.processing.enable_advanced_attention,
                    'model_size': 'large',
                    'num_attention_heads': 12,
                    'max_sequence_length': 2048,
                    'attention_dropout': 0.1
                },
                'causal_inference': {
                    'enabled': self._config.processing.enable_causal_inference,
                    'method': 'pc_algorithm',
                    'significance_level': 0.05,
                    'max_conditioning_set_size': 3
                },
                'multimodal_fusion': {
                    'enabled': self._config.processing.enable_multimodal_fusion,
                    'fusion_method': 'attention',
                    'text_weight': 0.7,
                    'visual_weight': 0.3
                },
                'federated_learning': {
                    'enabled': self._config.processing.enable_federated_learning,
                    'privacy_budget': 2.0,
                    'aggregation_strategy': 'federated_averaging'
                }
            }
            self._config_cache['research_config'] = research_config
        
        return self._config_cache['research_config']

# Global configuration instance
config_manager = ConfigManager()

def get_config() -> ApplicationConfig:
    """Get application configuration."""
    return config_manager.get_config()

def get_research_config() -> Dict[str, Any]:
    """Get research configuration."""
    return config_manager.get_research_config()
```

---

## 🧪 Testing Guide

### Test Structure

The project follows a comprehensive testing strategy with multiple test levels:

#### Test Pyramid

```
                    E2E Tests (Few)
                   /             \
              Integration Tests (Some)  
             /                       \
        Unit Tests (Many)         Performance Tests
```

### Unit Testing

#### Test Organization

```python
# tests/unit/test_document_processing.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from multimodal_contract_extractor.document import DocumentProcessor, ProcessingConfig

class TestDocumentProcessor:
    """Unit tests for DocumentProcessor."""
    
    @pytest.fixture
    def processing_config(self):
        """Provide test processing configuration."""
        return ProcessingConfig(
            batch_size=16,
            ocr_engine='tesseract',
            enable_gnn=True,
            enable_advanced_attention=True
        )
    
    @pytest.fixture
    def document_processor(self, processing_config):
        """Provide DocumentProcessor instance."""
        return DocumentProcessor(processing_config)
    
    @pytest.fixture
    def sample_document(self):
        """Provide sample document for testing."""
        return RawDocument(
            content=b"sample pdf content",
            filename="test_contract.pdf",
            content_type="application/pdf"
        )
    
    async def test_process_document_success(self, document_processor, sample_document):
        """Test successful document processing."""
        
        # Mock external dependencies
        with patch.object(document_processor.ocr_engine, 'extract_text') as mock_ocr, \
             patch.object(document_processor.gnn_analyzer, 'analyze_graph') as mock_gnn:
            
            # Configure mocks
            mock_ocr.return_value = "Sample contract text"
            mock_gnn.return_value = Mock(
                entities=['Party A', 'Party B'],
                clauses=['Payment Terms', 'Termination'],
                confidence=0.92
            )
            
            # Execute
            result = await document_processor.process_document(sample_document)
            
            # Assertions
            assert isinstance(result, ProcessedDocument)
            assert result.processing_status == ProcessingStatus.COMPLETED
            assert len(result.clauses) > 0
            assert result.get_overall_confidence() > 0.8
            
            # Verify mock calls
            mock_ocr.assert_called_once()
            mock_gnn.assert_called_once()
    
    async def test_process_document_ocr_failure(self, document_processor, sample_document):
        """Test handling of OCR failure."""
        
        with patch.object(document_processor.ocr_engine, 'extract_text') as mock_ocr:
            # Configure mock to raise exception
            mock_ocr.side_effect = OCRException("OCR processing failed")
            
            # Execute and assert exception
            with pytest.raises(ProcessingException):
                await document_processor.process_document(sample_document)
    
    @pytest.mark.parametrize("document_type,expected_clauses", [
        (DocumentType.NDA, ['confidentiality', 'non_disclosure']),
        (DocumentType.EMPLOYMENT, ['compensation', 'termination', 'benefits']),
        (DocumentType.LEASE, ['rent', 'duration', 'deposit'])
    ])
    async def test_document_type_specific_processing(
        self, document_processor, document_type, expected_clauses
    ):
        """Test document type-specific processing logic."""
        
        document = RawDocument(
            content=b"sample content",
            filename=f"test_{document_type.value}.pdf",
            document_type=document_type
        )
        
        with patch.object(document_processor, '_extract_type_specific_clauses') as mock_extract:
            mock_extract.return_value = expected_clauses
            
            result = await document_processor.process_document(document)
            
            # Verify type-specific processing was called
            mock_extract.assert_called_once_with(document_type, mock.ANY)

# tests/unit/test_research_algorithms.py
class TestGraphNeuralNetworks:
    """Unit tests for GNN algorithms."""
    
    @pytest.fixture
    def legal_graph_builder(self):
        """Provide LegalGraphBuilder instance."""
        return LegalGraphBuilder()
    
    @pytest.fixture
    def sample_contract_text(self):
        """Provide sample contract text."""
        return """
        This Agreement is entered into between Company A and Company B.
        Payment terms: Company B shall pay $10,000 within 30 days.
        Termination: Either party may terminate with 30 days notice.
        """
    
    async def test_graph_construction(self, legal_graph_builder, sample_contract_text):
        """Test legal graph construction."""
        
        clauses = [
            {'text': 'Payment terms: Company B shall pay $10,000 within 30 days.',
             'type': 'payment', 'confidence': 0.9},
            {'text': 'Either party may terminate with 30 days notice.',
             'type': 'termination', 'confidence': 0.85}
        ]
        
        graph = await legal_graph_builder.build_contract_graph(
            sample_contract_text, clauses
        )
        
        # Assertions
        assert isinstance(graph, ContractGraph)
        assert len(graph.entities) > 0
        assert len(graph.relations) > 0
        
        # Check entity types
        entity_types = {entity.entity_type for entity in graph.entities.values()}
        assert LegalEntityType.PARTY in entity_types
        assert LegalEntityType.CLAUSE in entity_types
    
    def test_attention_mechanism(self):
        """Test legal graph attention mechanism."""
        
        attention_layer = LegalGraphAttentionLayer(
            input_dim=768,
            output_dim=256,
            num_heads=8
        )
        
        # Create sample input
        node_features = np.random.randn(1, 10, 768)  # batch=1, nodes=10, features=768
        adjacency = np.random.randint(0, 2, (10, 10)).astype(float)
        
        # Execute attention
        output, attention_weights = attention_layer.compute_attention(
            node_features, adjacency
        )
        
        # Assertions
        assert output.shape == (1, 10, 256)
        assert attention_weights.shape[0] == 8  # num_heads
        assert attention_weights.shape[-2:] == (10, 10)  # attention matrix size

class TestAdvancedTransformerAttention:
    """Unit tests for advanced transformer attention."""
    
    def test_jurisdictional_attention(self):
        """Test jurisdictional attention mechanism."""
        
        jurisdictional_attention = JurisdictionalAttention()
        
        # Create tokens with jurisdictional context
        tokens = [
            LegalToken(
                token_id=i,
                text=f"token_{i}",
                semantic_level=LegalSemanticLevel.TOKEN,
                jurisdiction_context=JurisdictionType.US_FEDERAL if i % 2 == 0 else JurisdictionType.EU_GDPR
            )
            for i in range(5)
        ]
        
        # Compute jurisdictional bias
        bias_matrix = jurisdictional_attention.compute_jurisdictional_bias(tokens)
        
        # Assertions
        assert bias_matrix.shape == (5, 5)
        
        # Same jurisdiction tokens should have positive bias
        assert bias_matrix[0, 2] > 0  # Both US_FEDERAL
        assert bias_matrix[1, 3] > 0  # Both EU_GDPR
```

### Integration Testing

```python
# tests/integration/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from multimodal_contract_extractor.api.app import app

class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Provide test client."""
        return TestClient(app)
    
    @pytest.fixture
    def test_pdf_file(self):
        """Provide test PDF file."""
        return open('tests/fixtures/sample_contract.pdf', 'rb')
    
    def test_extract_endpoint(self, client, test_pdf_file):
        """Test document extraction endpoint."""
        
        response = client.post(
            "/api/v1/extract",
            files={"file": ("test_contract.pdf", test_pdf_file, "application/pdf")},
            data={"enable_gnn": "true", "enable_advanced_attention": "true"}
        )
        
        assert response.status_code == 200
        
        result = response.json()
        assert result["status"] == "completed"
        assert "clauses" in result["results"]
        assert "entities" in result["results"]
        assert len(result["results"]["clauses"]) > 0
    
    def test_batch_processing(self, client):
        """Test batch document processing."""
        
        files = [
            ("files", ("contract1.pdf", open("tests/fixtures/contract1.pdf", "rb"), "application/pdf")),
            ("files", ("contract2.pdf", open("tests/fixtures/contract2.pdf", "rb"), "application/pdf"))
        ]
        
        response = client.post("/api/v1/extract/batch", files=files)
        
        assert response.status_code == 200
        
        result = response.json()
        assert len(result["results"]) == 2
        
        for doc_result in result["results"]:
            assert doc_result["status"] == "completed"
            assert len(doc_result["clauses"]) > 0
    
    def test_research_endpoints(self, client):
        """Test research algorithm endpoints."""
        
        # Test GNN analysis endpoint
        gnn_response = client.post(
            "/api/v1/research/gnn/analyze",
            json={
                "document_text": "Sample contract text...",
                "clauses": [{"text": "payment clause", "type": "payment"}]
            }
        )
        
        assert gnn_response.status_code == 200
        gnn_result = gnn_response.json()
        assert "graph_statistics" in gnn_result
        assert "novel_insights" in gnn_result
        
        # Test federated learning endpoint  
        fed_response = client.post(
            "/api/v1/research/federated/status",
            json={"federation_id": "test_federation"}
        )
        
        assert fed_response.status_code == 200

# tests/integration/test_database_integration.py
class TestDatabaseIntegration:
    """Integration tests for database operations."""
    
    @pytest.fixture
    async def db_session(self):
        """Provide database session for testing."""
        # Use test database
        engine = create_async_engine(TEST_DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession)
        
        async with async_session() as session:
            yield session
    
    async def test_document_storage_retrieval(self, db_session):
        """Test document storage and retrieval."""
        
        # Create test document
        document = ProcessedDocument(
            id="test_doc_1",
            filename="test_contract.pdf",
            document_type=DocumentType.CONTRACT,
            processing_status=ProcessingStatus.COMPLETED,
            clauses=[
                LegalClause(
                    id="clause_1",
                    type="payment",
                    text="Payment terms clause",
                    confidence=0.9
                )
            ]
        )
        
        # Store document
        repository = DocumentRepository(db_session)
        stored_doc = await repository.create(document)
        
        # Retrieve document
        retrieved_doc = await repository.get_by_id(stored_doc.id)
        
        # Assertions
        assert retrieved_doc is not None
        assert retrieved_doc.filename == document.filename
        assert len(retrieved_doc.clauses) == 1
        assert retrieved_doc.clauses[0].type == "payment"
    
    async def test_search_functionality(self, db_session):
        """Test document search functionality."""
        
        repository = DocumentRepository(db_session)
        
        # Search by document type
        contracts = await repository.search_by_type(DocumentType.CONTRACT)
        assert len(contracts) > 0
        
        # Search by clause type
        payment_docs = await repository.search_by_clause_type("payment")
        assert len(payment_docs) > 0
        
        # Full-text search
        search_results = await repository.full_text_search("payment terms")
        assert len(search_results) > 0
```

### End-to-End Testing

```python
# tests/e2e/test_complete_workflow.py
import pytest
import asyncio
from pathlib import Path

class TestCompleteWorkflow:
    """End-to-end workflow testing."""
    
    @pytest.fixture
    def test_documents(self):
        """Provide various test documents."""
        return [
            Path("tests/fixtures/nda_contract.pdf"),
            Path("tests/fixtures/employment_agreement.pdf"),
            Path("tests/fixtures/lease_agreement.pdf"),
            Path("tests/fixtures/scanned_contract.png")
        ]
    
    async def test_complete_processing_pipeline(self, test_documents):
        """Test complete document processing pipeline."""
        
        from multimodal_contract_extractor import ContractExtractor, ExtractionConfig
        
        # Configure extraction
        config = ExtractionConfig(
            enable_gnn=True,
            use_advanced_attention=True,
            enable_causal_inference=True,
            confidence_threshold=0.7
        )
        
        extractor = ContractExtractor(config)
        
        results = []
        for doc_path in test_documents:
            result = await extractor.extract_from_file(str(doc_path))
            results.append(result)
        
        # Verify all documents processed successfully
        assert len(results) == len(test_documents)
        
        for result in results:
            assert result.processing_status == ProcessingStatus.COMPLETED
            assert len(result.clauses) > 0
            assert result.get_overall_confidence() > 0.7
            
            # Verify research algorithm results
            assert result.gnn_analysis is not None
            assert result.transformer_analysis is not None
            assert result.causal_analysis is not None
    
    async def test_batch_processing_workflow(self, test_documents):
        """Test batch processing workflow."""
        
        from multimodal_contract_extractor.batch_processor import BatchProcessor
        
        batch_processor = BatchProcessor(
            max_concurrent=3,
            enable_all_algorithms=True
        )
        
        # Process all documents in batch
        batch_results = await batch_processor.process_batch(test_documents)
        
        # Verify batch results
        assert len(batch_results.successful) == len(test_documents)
        assert len(batch_results.failed) == 0
        
        # Verify processing times are reasonable
        for result in batch_results.successful:
            assert result.processing_time_ms < 30000  # Less than 30 seconds
    
    async def test_web_interface_workflow(self):
        """Test web interface workflow."""
        
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Start web server
        # (Assuming web server is running on localhost:8501)
        
        driver = webdriver.Chrome()
        try:
            driver.get("http://localhost:8501")
            
            # Upload file
            file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            file_input.send_keys(str(Path("tests/fixtures/nda_contract.pdf").absolute()))
            
            # Click process button
            process_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Process')]")
            process_button.click()
            
            # Wait for results
            results_section = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "results-container"))
            )
            
            # Verify results displayed
            assert "Processing completed" in driver.page_source
            assert "Clauses extracted" in driver.page_source
            
        finally:
            driver.quit()

# tests/e2e/test_research_pipeline.py
class TestResearchPipeline:
    """End-to-end testing of research algorithms."""
    
    async def test_gnn_complete_pipeline(self):
        """Test complete GNN research pipeline."""
        
        from multimodal_contract_extractor.research import (
            GraphNeuralNetworkFramework,
            LegalDataset,
            BenchmarkSuite
        )
        
        # Load test dataset
        dataset = LegalDataset.load("tests/fixtures/research_dataset")
        
        # Initialize GNN framework
        gnn_framework = GraphNeuralNetworkFramework(
            config_path="tests/fixtures/gnn_test_config.yml"
        )
        
        # Run complete analysis
        results = await gnn_framework.run_complete_analysis(dataset)
        
        # Verify research results
        assert results['accuracy'] > 0.8
        assert results['f1_score'] > 0.75
        assert 'novel_insights' in results
        assert len(results['critical_entities']) > 0
    
    async def test_federated_learning_simulation(self):
        """Test federated learning simulation."""
        
        from multimodal_contract_extractor.research.federated_learning import (
            FederatedLearningSimulator,
            LegalClient
        )
        
        # Create simulated clients
        clients = [
            LegalClient(f"client_{i}", f"jurisdiction_{i%3}")
            for i in range(5)
        ]
        
        # Run federated learning simulation
        simulator = FederatedLearningSimulator(clients)
        results = await simulator.run_federated_training(
            num_rounds=10,
            privacy_budget=2.0
        )
        
        # Verify federated results
        assert results['final_accuracy'] > 0.8
        assert results['privacy_cost'] < 2.0
        assert all(client_result['participated'] for client_result in results['client_results'])
```

### Performance Testing

```python
# tests/performance/test_performance_benchmarks.py
import pytest
import time
import asyncio
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

class TestPerformanceBenchmarks:
    """Performance benchmarking tests."""
    
    @pytest.mark.performance
    async def test_single_document_performance(self):
        """Test single document processing performance."""
        
        from multimodal_contract_extractor import ContractExtractor, ExtractionConfig
        
        config = ExtractionConfig(enable_gnn=True, use_advanced_attention=True)
        extractor = ContractExtractor(config)
        
        # Load test document
        test_doc = "tests/fixtures/medium_contract.pdf"  # ~10 pages
        
        # Measure processing time
        processing_times = []
        for _ in range(5):  # 5 runs for statistical significance
            start_time = time.time()
            result = await extractor.extract_from_file(test_doc)
            end_time = time.time()
            
            processing_time = end_time - start_time
            processing_times.append(processing_time)
            
            # Verify successful processing
            assert result.processing_status == ProcessingStatus.COMPLETED
        
        # Performance assertions
        avg_time = statistics.mean(processing_times)
        assert avg_time < 10.0  # Less than 10 seconds average
        assert max(processing_times) < 15.0  # No run over 15 seconds
        
        print(f"Average processing time: {avg_time:.2f}s")
        print(f"Min/Max: {min(processing_times):.2f}s / {max(processing_times):.2f}s")
    
    @pytest.mark.performance
    async def test_concurrent_processing_performance(self):
        """Test concurrent document processing performance."""
        
        from multimodal_contract_extractor import ContractExtractor, ExtractionConfig
        
        config = ExtractionConfig(enable_gnn=True, use_advanced_attention=True)
        extractor = ContractExtractor(config)
        
        # Prepare multiple test documents
        test_docs = [
            f"tests/fixtures/contract_{i}.pdf" 
            for i in range(10)
        ]
        
        # Measure concurrent processing
        start_time = time.time()
        
        # Process documents concurrently
        tasks = [extractor.extract_from_file(doc) for doc in test_docs]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance assertions
        assert len(results) == len(test_docs)
        assert all(r.processing_status == ProcessingStatus.COMPLETED for r in results)
        assert total_time < 60.0  # Total processing under 1 minute
        
        # Calculate throughput
        throughput = len(test_docs) / total_time
        assert throughput > 0.5  # At least 0.5 docs/second
        
        print(f"Concurrent processing: {len(test_docs)} docs in {total_time:.2f}s")
        print(f"Throughput: {throughput:.2f} docs/second")
    
    @pytest.mark.performance
    def test_memory_usage(self):
        """Test memory usage during processing."""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large document
        from multimodal_contract_extractor import ContractExtractor
        extractor = ContractExtractor()
        
        result = extractor.extract_from_file("tests/fixtures/large_contract.pdf")
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory usage assertions
        assert memory_increase < 2000  # Less than 2GB increase
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {peak_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB")
```

### Test Configuration

```python
# pytest.ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra 
    -q 
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
testpaths = tests
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    research: Research algorithm tests
    slow: Slow running tests
    gpu: Tests requiring GPU
python_files = test_*.py
python_classes = Test*
python_functions = test_*
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning

# conftest.py
import pytest
import asyncio
import os
from pathlib import Path
import tempfile
import shutil

# Configure pytest-asyncio
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide test data directory."""
    return Path("tests/fixtures")

@pytest.fixture
def temp_dir():
    """Provide temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        'database_url': 'sqlite:///:memory:',
        'redis_url': 'redis://localhost:6379/15',  # Test database
        'enable_research_algorithms': True,
        'log_level': 'DEBUG'
    }

# Fixtures for research algorithm testing
@pytest.fixture
def sample_legal_documents():
    """Provide sample legal documents for testing."""
    return [
        {
            'text': 'This is a sample NDA contract...',
            'type': 'nda',
            'entities': ['Party A', 'Party B'],
            'clauses': ['confidentiality', 'non_disclosure']
        },
        {
            'text': 'This is a sample employment agreement...',
            'type': 'employment',
            'entities': ['Employer', 'Employee'],
            'clauses': ['compensation', 'benefits', 'termination']
        }
    ]

@pytest.fixture
async def research_test_environment():
    """Setup research testing environment."""
    # Mock external services
    with patch('multimodal_contract_extractor.external_services') as mock_services:
        mock_services.return_value = Mock()
        yield mock_services
```

---

## 📝 Contributing Guidelines

### Code Contribution Process

#### 1. Getting Started

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/multimodal-contract-extractor.git
cd multimodal-contract-extractor

# Add upstream remote
git remote add upstream https://github.com/original-org/multimodal-contract-extractor.git

# Create development branch
git checkout -b feature/your-feature-name

# Install development environment
pip install -e ".[dev,test,research]"
pre-commit install
```

#### 2. Development Workflow

```bash
# Keep your fork synced
git fetch upstream
git checkout main
git merge upstream/main
git push origin main

# Create feature branch
git checkout -b feature/amazing-new-feature

# Make your changes...
# Write tests...
# Update documentation...

# Run quality checks
make lint          # Code linting
make type-check    # Type checking
make test          # Run tests
make security-check # Security scanning

# Commit changes
git add .
git commit -m "feat: implement amazing new feature"

# Push to your fork
git push origin feature/amazing-new-feature

# Create pull request via GitHub interface
```

#### 3. Pull Request Guidelines

**PR Title Format:**
- `feat: add new research algorithm`
- `fix: resolve memory leak in document processing`
- `docs: update API documentation`
- `test: add integration tests for GNN`
- `refactor: improve code organization`
- `perf: optimize document processing speed`

**PR Description Template:**
```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] End-to-end tests pass
- [ ] Performance tests pass (if applicable)
- [ ] Manual testing completed

## Research Algorithms (if applicable)
- [ ] Algorithm implementation follows research documentation
- [ ] Performance benchmarks meet targets
- [ ] Statistical validation completed
- [ ] Reproducibility verified

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No breaking changes (or clearly documented)
- [ ] Security considerations addressed
```

### Research Contributions

#### Contributing New Algorithms

```python
# Template for new research algorithm contribution
class NewResearchAlgorithm:
    """
    New Research Algorithm for Legal Document Processing
    
    This class implements [algorithm name] for [specific legal AI task].
    
    Research Paper: [Citation if applicable]
    Performance Target: [Specific metrics and targets]
    
    Args:
        config: Algorithm configuration parameters
        
    Example:
        >>> algorithm = NewResearchAlgorithm(config)
        >>> results = await algorithm.process(legal_document)
        >>> assert results.accuracy > 0.85
    """
    
    def __init__(self, config: AlgorithmConfig):
        self.config = config
        self._validate_config()
        
    def _validate_config(self):
        """Validate algorithm configuration."""
        required_fields = ['parameter1', 'parameter2']
        for field in required_fields:
            if not hasattr(self.config, field):
                raise ValueError(f"Missing required configuration: {field}")
    
    async def process(self, input_data: LegalDocument) -> AlgorithmResults:
        """
        Process legal document with new algorithm.
        
        Args:
            input_data: Legal document to process
            
        Returns:
            AlgorithmResults: Processing results with performance metrics
            
        Raises:
            ProcessingException: If processing fails
        """
        # Implementation here
        pass
    
    def evaluate_performance(self, test_dataset: Dataset) -> PerformanceMetrics:
        """
        Evaluate algorithm performance on test dataset.
        
        Returns metrics required for research validation:
        - accuracy, precision, recall, f1_score
        - processing_time, memory_usage
        - statistical_significance
        """
        pass

# tests/test_new_research_algorithm.py
class TestNewResearchAlgorithm:
    """Comprehensive tests for new research algorithm."""
    
    @pytest.fixture
    def algorithm_config(self):
        return AlgorithmConfig(
            parameter1=0.8,
            parameter2=256,
            # ... other parameters
        )
    
    def test_algorithm_initialization(self, algorithm_config):
        """Test algorithm initializes correctly."""
        algorithm = NewResearchAlgorithm(algorithm_config)
        assert algorithm.config == algorithm_config
    
    async def test_processing_accuracy(self, algorithm_config):
        """Test processing accuracy meets research targets."""
        algorithm = NewResearchAlgorithm(algorithm_config)
        
        # Load test dataset
        test_data = load_research_test_dataset()
        
        # Process documents
        results = []
        for document in test_data:
            result = await algorithm.process(document)
            results.append(result)
        
        # Evaluate performance
        accuracy = compute_accuracy(results, test_data.ground_truth)
        assert accuracy > 0.85  # Research target
    
    def test_statistical_significance(self, algorithm_config):
        """Test statistical significance of results."""
        algorithm = NewResearchAlgorithm(algorithm_config)
        
        # Run multiple trials
        trial_results = []
        for trial in range(10):
            trial_result = algorithm.evaluate_performance(test_dataset)
            trial_results.append(trial_result.accuracy)
        
        # Statistical testing
        mean_accuracy = np.mean(trial_results)
        p_value = stats.ttest_1samp(trial_results, 0.80).pvalue
        
        assert mean_accuracy > 0.85
        assert p_value < 0.05  # Statistically significant improvement
```

#### Research Documentation Requirements

When contributing research algorithms:

1. **Algorithm Documentation**: Complete mathematical formulation and implementation details
2. **Performance Benchmarks**: Comparison against established baselines
3. **Statistical Validation**: Significance testing and confidence intervals
4. **Reproducibility Package**: Code, data, and environment specifications
5. **Integration Tests**: Ensure compatibility with existing system
6. **Performance Tests**: Verify computational efficiency requirements

### Code Review Process

#### Review Checklist

**Functionality:**
- [ ] Code implements requirements correctly
- [ ] Edge cases handled appropriately
- [ ] Error handling is comprehensive
- [ ] Performance is acceptable

**Code Quality:**
- [ ] Code follows style guidelines
- [ ] Functions/classes have clear single responsibilities
- [ ] Variable/function names are descriptive
- [ ] Complex logic is well-commented

**Testing:**
- [ ] Unit tests cover all code paths
- [ ] Integration tests verify end-to-end functionality
- [ ] Test cases cover edge cases and error conditions
- [ ] Performance tests validate efficiency requirements

**Research Quality (if applicable):**
- [ ] Algorithm implementation matches research paper
- [ ] Performance targets are met
- [ ] Statistical validation is thorough
- [ ] Reproducibility is ensured

**Documentation:**
- [ ] Public APIs are documented with docstrings
- [ ] README and other docs updated if needed
- [ ] Configuration changes documented
- [ ] Migration guides provided for breaking changes

**Security:**
- [ ] Input validation implemented
- [ ] No sensitive data in logs
- [ ] Authentication/authorization respected
- [ ] Dependencies are secure

### Community Guidelines

#### Communication Standards

- **Be Respectful**: Treat all contributors with respect
- **Be Constructive**: Provide actionable feedback
- **Be Patient**: Allow time for responses and iterations
- **Be Inclusive**: Welcome contributors of all backgrounds

#### Issue Reporting

```markdown
## Bug Report Template

**Description**
Clear description of the bug.

**Steps to Reproduce**
1. Step 1
2. Step 2
3. Step 3

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.10.6]
- Package Version: [e.g., 4.0.0]
- GPU: [if applicable]

**Additional Context**
Any other context about the problem.

**Logs**
```
Relevant log output
```

## Feature Request Template

**Feature Description**
Clear description of the proposed feature.

**Use Case**
Description of the use case this feature addresses.

**Proposed Solution**
Detailed description of proposed implementation.

**Alternatives Considered**
Alternative solutions you've considered.

**Research Context** (if applicable)
- Related academic papers
- Performance targets
- Validation requirements
```

This comprehensive developer documentation provides everything needed to contribute to and extend the advanced multimodal contract extractor system, from basic setup to advanced research algorithm development.