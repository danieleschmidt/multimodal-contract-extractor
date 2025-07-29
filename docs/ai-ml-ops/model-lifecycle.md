# AI/ML Operations - Model Lifecycle Management

This document outlines the machine learning operations (MLOps) framework for managing Vision-Language Models and OCR pipelines in the Contract Extractor system.

## Overview

The MLOps framework provides:
- Automated model training and evaluation
- Model versioning and deployment pipelines
- Performance monitoring and drift detection
- A/B testing capabilities for model comparison
- Automated retraining triggers

## Model Architecture

### Current Models

1. **OCR Engine**
   - Tesseract OCR with custom preprocessing
   - Confidence scoring and quality assessment
   - Text extraction and coordinate mapping

2. **Vision-Language Model (VLM)**
   - Multimodal transformer architecture
   - Clause classification and extraction
   - Semantic understanding of contract structure

3. **Document Classification**
   - Contract type identification
   - Layout analysis and structure detection
   - Page segmentation and region identification

## Model Lifecycle Stages

### 1. Data Management

```python
# mlops/data_management.py
"""
Data pipeline for model training and evaluation
"""

import os
import json
import hashlib
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DocumentSample:
    """Represents a training/validation sample"""
    document_id: str
    file_path: str
    document_type: str
    annotations: Dict[str, Any]
    quality_score: float
    metadata: Dict[str, Any]

class DataManager:
    """Manages training data and model artifacts"""
    
    def __init__(self, data_root: str = "data/"):
        self.data_root = Path(data_root)
        self.data_root.mkdir(exist_ok=True)
        
    def register_training_data(self, samples: List[DocumentSample]) -> str:
        """Register new training data with versioning"""
        # Create data version hash
        content_hash = hashlib.sha256()
        for sample in sorted(samples, key=lambda x: x.document_id):
            content_hash.update(f"{sample.document_id}:{sample.quality_score}".encode())
        
        data_version = content_hash.hexdigest()[:12]
        version_dir = self.data_root / f"v{data_version}"
        version_dir.mkdir(exist_ok=True)
        
        # Save metadata
        metadata = {
            "version": data_version,
            "sample_count": len(samples),
            "document_types": list(set(s.document_type for s in samples)),
            "avg_quality_score": sum(s.quality_score for s in samples) / len(samples),
            "created_at": "2024-01-15T10:30:00Z"
        }
        
        with open(version_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Save sample registry
        sample_data = [
            {
                "document_id": s.document_id,
                "file_path": s.file_path,
                "document_type": s.document_type,
                "quality_score": s.quality_score,
                "annotations": s.annotations,
                "metadata": s.metadata
            }
            for s in samples
        ]
        
        with open(version_dir / "samples.json", "w") as f:
            json.dump(sample_data, f, indent=2)
        
        return data_version
    
    def get_training_split(self, data_version: str, 
                          train_ratio: float = 0.8) -> Tuple[List[DocumentSample], List[DocumentSample]]:
        """Get train/validation split for a data version"""
        version_dir = self.data_root / f"v{data_version}"
        
        with open(version_dir / "samples.json", "r") as f:
            sample_data = json.load(f)
        
        # Convert to DocumentSample objects
        samples = [
            DocumentSample(
                document_id=s["document_id"],
                file_path=s["file_path"],
                document_type=s["document_type"],
                annotations=s["annotations"],
                quality_score=s["quality_score"],
                metadata=s["metadata"]
            )
            for s in sample_data
        ]
        
        # Stratified split by document type
        train_samples = []
        val_samples = []
        
        for doc_type in set(s.document_type for s in samples):
            type_samples = [s for s in samples if s.document_type == doc_type]
            split_idx = int(len(type_samples) * train_ratio)
            train_samples.extend(type_samples[:split_idx])
            val_samples.extend(type_samples[split_idx:])
        
        return train_samples, val_samples
```

### 2. Model Training Pipeline

```yaml
# mlops/training-pipeline.yml
name: Model Training Pipeline

on:
  workflow_dispatch:
    inputs:
      data_version:
        description: 'Data version to use for training'
        required: true
        type: string
      model_type:
        description: 'Model type to train'
        required: true
        type: choice
        options:
          - ocr
          - vlm
          - classifier
      experiment_name:
        description: 'Experiment name'
        required: true
        type: string

jobs:
  training:
    runs-on: ubuntu-latest
    timeout-minutes: 480  # 8 hours
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: 'pip'
      
      - name: Install ML dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-gpu.txt
          pip install mlflow wandb
      
      - name: Download training data
        run: |
          python mlops/download_data.py --version ${{ inputs.data_version }}
      
      - name: Start MLflow tracking
        run: |
          export MLFLOW_TRACKING_URI=https://mlflow.your-domain.com
          export MLFLOW_EXPERIMENT_NAME=${{ inputs.experiment_name }}
      
      - name: Train model
        run: |
          python mlops/train_model.py \
            --model-type ${{ inputs.model_type }} \
            --data-version ${{ inputs.data_version }} \
            --experiment-name ${{ inputs.experiment_name }} \
            --gpu-enabled true
      
      - name: Evaluate model
        run: |
          python mlops/evaluate_model.py \
            --model-path models/latest \
            --test-data-path data/test \
            --output-path evaluation-results.json
      
      - name: Upload model artifacts
        uses: actions/upload-artifact@v3
        with:
          name: model-artifacts-${{ inputs.model_type }}
          path: |
            models/
            evaluation-results.json
            training-logs/
      
      - name: Register model
        if: success()
        run: |
          python mlops/register_model.py \
            --model-path models/latest \
            --model-type ${{ inputs.model_type }} \
            --performance-metrics evaluation-results.json
```

### 3. Model Evaluation and Testing

```python
# mlops/model_evaluation.py
"""
Comprehensive model evaluation and testing framework
"""

import json
import numpy as np
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from sklearn.metrics import precision_recall_fscore_support, confusion_matrix

@dataclass
class EvaluationMetrics:
    """Model evaluation metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confidence_scores: List[float]
    confusion_matrix: List[List[int]]
    per_class_metrics: Dict[str, Dict[str, float]]

class ModelEvaluator:
    """Evaluates model performance across multiple dimensions"""
    
    def __init__(self, model_type: str):
        self.model_type = model_type
        
    def evaluate_ocr_model(self, predictions: List[str], 
                          ground_truth: List[str]) -> EvaluationMetrics:
        """Evaluate OCR model performance"""
        # Character-level accuracy
        total_chars = sum(len(gt) for gt in ground_truth)
        correct_chars = sum(
            sum(p == g for p, g in zip(pred, gt))
            for pred, gt in zip(predictions, ground_truth)
        )
        char_accuracy = correct_chars / total_chars if total_chars > 0 else 0
        
        # Word-level accuracy
        total_words = sum(len(gt.split()) for gt in ground_truth)
        correct_words = sum(
            sum(p == g for p, g in zip(pred.split(), gt.split()))
            for pred, gt in zip(predictions, ground_truth)
        )
        word_accuracy = correct_words / total_words if total_words > 0 else 0
        
        # Edit distance (Levenshtein)
        edit_distances = [
            self._edit_distance(pred, gt)
            for pred, gt in zip(predictions, ground_truth)
        ]
        avg_edit_distance = np.mean(edit_distances)
        
        return EvaluationMetrics(
            accuracy=char_accuracy,
            precision=word_accuracy,
            recall=word_accuracy,
            f1_score=2 * (char_accuracy * word_accuracy) / (char_accuracy + word_accuracy) if (char_accuracy + word_accuracy) > 0 else 0,
            confidence_scores=[1.0] * len(predictions),  # Placeholder
            confusion_matrix=[],
            per_class_metrics={
                "character_accuracy": {"value": char_accuracy},
                "word_accuracy": {"value": word_accuracy},
                "avg_edit_distance": {"value": avg_edit_distance}
            }
        )
    
    def evaluate_clause_extraction(self, predictions: List[Dict[str, Any]], 
                                 ground_truth: List[Dict[str, Any]]) -> EvaluationMetrics:
        """Evaluate clause extraction model"""
        # Extract clause types for classification metrics
        pred_types = []
        true_types = []
        
        for pred, gt in zip(predictions, ground_truth):
            pred_clauses = pred.get("clauses", [])
            true_clauses = gt.get("clauses", [])
            
            # Match clauses by position/overlap for evaluation
            matched_pairs = self._match_clauses(pred_clauses, true_clauses)
            
            for pred_clause, true_clause in matched_pairs:
                if pred_clause and true_clause:
                    pred_types.append(pred_clause.get("type", "unknown"))
                    true_types.append(true_clause.get("type", "unknown"))
        
        # Calculate classification metrics
        precision, recall, f1, _ = precision_recall_fscore_support(
            true_types, pred_types, average='weighted', zero_division=0
        )
        
        accuracy = sum(p == t for p, t in zip(pred_types, true_types)) / len(true_types) if true_types else 0
        
        # Confusion matrix
        unique_labels = sorted(set(true_types + pred_types))
        cm = confusion_matrix(true_types, pred_types, labels=unique_labels)
        
        # Per-class metrics
        per_class_precision, per_class_recall, per_class_f1, _ = precision_recall_fscore_support(
            true_types, pred_types, average=None, zero_division=0, labels=unique_labels
        )
        
        per_class_metrics = {}
        for i, label in enumerate(unique_labels):
            per_class_metrics[label] = {
                "precision": per_class_precision[i],
                "recall": per_class_recall[i],
                "f1_score": per_class_f1[i]
            }
        
        return EvaluationMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            confidence_scores=[1.0] * len(predictions),  # Placeholder
            confusion_matrix=cm.tolist(),
            per_class_metrics=per_class_metrics
        )
    
    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings"""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _match_clauses(self, pred_clauses: List[Dict], 
                      true_clauses: List[Dict]) -> List[Tuple[Dict, Dict]]:
        """Match predicted and ground truth clauses for evaluation"""
        # Simplified matching by position overlap
        matched_pairs = []
        
        for pred_clause in pred_clauses:
            pred_coords = pred_clause.get("coordinates", [0, 0, 0, 0])
            best_match = None
            best_overlap = 0
            
            for true_clause in true_clauses:
                true_coords = true_clause.get("coordinates", [0, 0, 0, 0])
                overlap = self._calculate_overlap(pred_coords, true_coords)
                
                if overlap > best_overlap and overlap > 0.5:  # 50% overlap threshold
                    best_match = true_clause
                    best_overlap = overlap
            
            matched_pairs.append((pred_clause, best_match))
        
        return matched_pairs
    
    def _calculate_overlap(self, coords1: List[int], coords2: List[int]) -> float:
        """Calculate overlap ratio between two bounding boxes"""
        x1, y1, x2, y2 = coords1
        x3, y3, x4, y4 = coords2
        
        # Calculate intersection
        intersect_x1 = max(x1, x3)
        intersect_y1 = max(y1, y3)
        intersect_x2 = min(x2, x4)
        intersect_y2 = min(y2, y4)
        
        if intersect_x2 <= intersect_x1 or intersect_y2 <= intersect_y1:
            return 0.0
        
        intersect_area = (intersect_x2 - intersect_x1) * (intersect_y2 - intersect_y1)
        
        # Calculate union
        area1 = (x2 - x1) * (y2 - y1)
        area2 = (x4 - x3) * (y4 - y3)
        union_area = area1 + area2 - intersect_area
        
        return intersect_area / union_area if union_area > 0 else 0.0
    
    def generate_evaluation_report(self, metrics: EvaluationMetrics) -> Dict[str, Any]:
        """Generate comprehensive evaluation report"""
        return {
            "model_type": self.model_type,
            "timestamp": "2024-01-15T10:30:00Z",
            "overall_metrics": {
                "accuracy": metrics.accuracy,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1_score": metrics.f1_score
            },
            "detailed_metrics": {
                "confusion_matrix": metrics.confusion_matrix,
                "per_class_metrics": metrics.per_class_metrics,
                "confidence_distribution": {
                    "mean": np.mean(metrics.confidence_scores),
                    "std": np.std(metrics.confidence_scores),
                    "percentiles": {
                        "25th": np.percentile(metrics.confidence_scores, 25),
                        "50th": np.percentile(metrics.confidence_scores, 50),
                        "75th": np.percentile(metrics.confidence_scores, 75),
                        "95th": np.percentile(metrics.confidence_scores, 95)
                    }
                }
            },
            "performance_benchmarks": {
                "meets_accuracy_threshold": metrics.accuracy >= 0.85,
                "meets_precision_threshold": metrics.precision >= 0.80,
                "meets_recall_threshold": metrics.recall >= 0.80,
                "production_ready": all([
                    metrics.accuracy >= 0.85,
                    metrics.precision >= 0.80,
                    metrics.recall >= 0.80,
                    metrics.f1_score >= 0.80
                ])
            },
            "recommendations": self._generate_recommendations(metrics)
        }
    
    def _generate_recommendations(self, metrics: EvaluationMetrics) -> List[str]:
        """Generate improvement recommendations based on metrics"""
        recommendations = []
        
        if metrics.accuracy < 0.85:
            recommendations.append("Accuracy below threshold - consider data augmentation or model architecture changes")
        
        if metrics.precision < 0.80:
            recommendations.append("Low precision - review false positive cases and adjust classification thresholds")
        
        if metrics.recall < 0.80:
            recommendations.append("Low recall - increase training data diversity or adjust model sensitivity")
        
        if len(recommendations) == 0:
            recommendations.append("Model performance meets all thresholds - ready for production deployment")
        
        return recommendations
```

### 4. Model Deployment and Monitoring

```python
# mlops/model_monitor.py
"""
Production model monitoring and drift detection
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import psutil
import time

@dataclass
class ModelMetrics:
    """Real-time model performance metrics"""
    timestamp: str
    model_version: str
    request_count: int
    avg_response_time: float
    avg_confidence: float
    error_rate: float
    throughput: float
    memory_usage: float
    cpu_usage: float

class ModelMonitor:
    """Monitor model performance in production"""
    
    def __init__(self, model_version: str):
        self.model_version = model_version
        self.metrics_history: List[ModelMetrics] = []
        
    def log_prediction(self, prediction_time: float, confidence: float, 
                      success: bool) -> None:
        """Log individual prediction metrics"""
        # Implementation would store metrics in time-series database
        pass
    
    def detect_drift(self, recent_predictions: List[Dict[str, Any]], 
                    baseline_predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect model drift using statistical tests"""
        
        # Extract confidence scores
        recent_confidences = [p.get("confidence", 0.0) for p in recent_predictions]
        baseline_confidences = [p.get("confidence", 0.0) for p in baseline_predictions]
        
        # Statistical drift detection
        recent_mean = np.mean(recent_confidences)
        baseline_mean = np.mean(baseline_confidences)
        
        # Simple drift detection (would use more sophisticated methods in practice)
        confidence_drift = abs(recent_mean - baseline_mean) / baseline_mean if baseline_mean > 0 else 0
        
        # Class distribution drift
        recent_classes = [p.get("predicted_class", "unknown") for p in recent_predictions]
        baseline_classes = [p.get("predicted_class", "unknown") for p in baseline_predictions]
        
        recent_dist = self._calculate_class_distribution(recent_classes)
        baseline_dist = self._calculate_class_distribution(baseline_classes)
        
        distribution_drift = self._calculate_distribution_distance(recent_dist, baseline_dist)
        
        # Overall drift assessment
        drift_detected = confidence_drift > 0.1 or distribution_drift > 0.2
        
        return {
            "drift_detected": drift_detected,
            "confidence_drift": confidence_drift,
            "distribution_drift": distribution_drift,
            "recent_metrics": {
                "mean_confidence": recent_mean,
                "prediction_count": len(recent_predictions),
                "class_distribution": recent_dist
            },
            "baseline_metrics": {
                "mean_confidence": baseline_mean,
                "prediction_count": len(baseline_predictions),
                "class_distribution": baseline_dist
            },
            "recommendations": self._generate_drift_recommendations(
                confidence_drift, distribution_drift
            )
        }
    
    def _calculate_class_distribution(self, classes: List[str]) -> Dict[str, float]:
        """Calculate class distribution"""
        if not classes:
            return {}
        
        class_counts = {}
        for cls in classes:
            class_counts[cls] = class_counts.get(cls, 0) + 1
        
        total = len(classes)
        return {cls: count / total for cls, count in class_counts.items()}
    
    def _calculate_distribution_distance(self, dist1: Dict[str, float], 
                                       dist2: Dict[str, float]) -> float:
        """Calculate distance between two distributions"""
        all_classes = set(dist1.keys()) | set(dist2.keys())
        
        distance = 0.0
        for cls in all_classes:
            p1 = dist1.get(cls, 0.0)
            p2 = dist2.get(cls, 0.0)
            distance += abs(p1 - p2)
        
        return distance / 2  # Normalize to [0, 1]
    
    def _generate_drift_recommendations(self, confidence_drift: float, 
                                      distribution_drift: float) -> List[str]:
        """Generate drift mitigation recommendations"""
        recommendations = []
        
        if confidence_drift > 0.15:
            recommendations.append("Significant confidence drift detected - consider model retraining")
        
        if distribution_drift > 0.3:
            recommendations.append("Class distribution drift detected - review input data quality")
        
        if confidence_drift > 0.1 or distribution_drift > 0.2:
            recommendations.extend([
                "Increase monitoring frequency",
                "Collect additional training data from recent inputs",
                "Consider gradual model rollback if performance degrades"
            ])
        
        return recommendations
    
    def get_model_health(self) -> Dict[str, Any]:
        """Get overall model health status"""
        if not self.metrics_history:
            return {"status": "unknown", "message": "No metrics available"}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        avg_error_rate = np.mean([m.error_rate for m in recent_metrics])
        avg_response_time = np.mean([m.avg_response_time for m in recent_metrics])
        avg_throughput = np.mean([m.throughput for m in recent_metrics])
        
        # Health thresholds
        if avg_error_rate > 0.05:  # 5% error rate
            status = "unhealthy"
            message = f"High error rate: {avg_error_rate:.2%}"
        elif avg_response_time > 10.0:  # 10 seconds
            status = "degraded"
            message = f"Slow response time: {avg_response_time:.2f}s"
        elif avg_throughput < 1.0:  # 1 request per second
            status = "degraded"
            message = f"Low throughput: {avg_throughput:.2f} req/s"
        else:
            status = "healthy"
            message = "All metrics within normal ranges"
        
        return {
            "status": status,
            "message": message,
            "metrics": {
                "error_rate": avg_error_rate,
                "response_time": avg_response_time,
                "throughput": avg_throughput
            },
            "model_version": self.model_version,
            "last_updated": datetime.utcnow().isoformat()
        }
```

## Deployment Strategy

### Blue-Green Deployment

```yaml
# mlops/blue-green-deploy.yml
name: Blue-Green Model Deployment

on:
  workflow_dispatch:
    inputs:
      model_version:
        description: 'Model version to deploy'
        required: true
        type: string
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Download model artifacts
        run: |
          python mlops/download_model.py --version ${{ inputs.model_version }}
      
      - name: Deploy to blue environment
        run: |
          kubectl apply -f mlops/k8s/blue-deployment.yaml
          kubectl set image deployment/contract-extractor-blue \
            app=contract-extractor:${{ inputs.model_version }}
      
      - name: Run health checks
        run: |
          python mlops/health_check.py --environment blue --timeout 300
      
      - name: Run smoke tests
        run: |
          python mlops/smoke_tests.py --environment blue
      
      - name: Switch traffic to blue
        if: success()
        run: |
          kubectl patch service contract-extractor-service \
            -p '{"spec":{"selector":{"version":"blue"}}}'
      
      - name: Monitor metrics
        run: |
          python mlops/monitor_deployment.py --duration 600  # 10 minutes
      
      - name: Rollback on failure
        if: failure()
        run: |
          kubectl patch service contract-extractor-service \
            -p '{"spec":{"selector":{"version":"green"}}}'
```

This comprehensive MLOps framework enables automated model lifecycle management, ensuring reliable and performant AI/ML operations for the Contract Extractor system.