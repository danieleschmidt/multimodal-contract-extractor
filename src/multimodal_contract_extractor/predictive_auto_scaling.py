"""
Predictive Auto-Scaling System with Cost Optimization and Intelligent Resource Management.

This module provides advanced auto-scaling capabilities with machine learning-based demand
forecasting, cost optimization, spot instance management, and intelligent resource allocation
for the distributed contract extraction system.
"""

from __future__ import annotations

import asyncio
import logging
import math
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Try to import ML and cloud libraries
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    LinearRegression = None
    StandardScaler = None

try:
    import boto3
    HAS_AWS = True
except ImportError:
    HAS_AWS = False
    boto3 = None


class ScalingDirection(Enum):
    """Scaling direction."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"


class ScalingReason(Enum):
    """Reasons for scaling decisions."""
    CPU_THRESHOLD = "cpu_threshold"
    MEMORY_THRESHOLD = "memory_threshold"
    QUEUE_LENGTH = "queue_length"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    PREDICTIVE_DEMAND = "predictive_demand"
    COST_OPTIMIZATION = "cost_optimization"
    SCHEDULE_BASED = "schedule_based"
    PROACTIVE_SCALING = "proactive_scaling"


class InstanceType(Enum):
    """Cloud instance types."""
    ON_DEMAND = "on_demand"
    SPOT = "spot"
    RESERVED = "reserved"
    PREEMPTIBLE = "preemptible"
    BURSTABLE = "burstable"


class ResourceType(Enum):
    """Resource types for scaling."""
    CPU_CORES = "cpu_cores"
    MEMORY_GB = "memory_gb"
    GPU_UNITS = "gpu_units"
    NETWORK_BANDWIDTH = "network_bandwidth"
    STORAGE_CAPACITY = "storage_capacity"
    WORKER_INSTANCES = "worker_instances"


@dataclass
class ScalingMetric:
    """Scaling metric definition."""
    name: str
    current_value: float
    threshold_up: float
    threshold_down: float
    weight: float = 1.0
    aggregation_window: int = 5  # minutes
    breach_duration: int = 2  # consecutive periods
    unit: str = ""
    description: str = ""


@dataclass
class ScalingEvent:
    """Scaling event record."""
    event_id: str
    timestamp: float
    direction: ScalingDirection
    reason: ScalingReason
    resource_type: ResourceType
    previous_capacity: int
    new_capacity: int
    cost_impact: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceCapacity:
    """Resource capacity information."""
    resource_type: ResourceType
    current: float
    minimum: float
    maximum: float
    desired: float
    available: float
    cost_per_unit: float
    instance_type: InstanceType = InstanceType.ON_DEMAND


@dataclass
class DemandForecast:
    """Demand forecast data."""
    resource_type: ResourceType
    timestamp: float
    forecast_horizon: int  # minutes
    forecasted_demand: List[float]
    confidence_interval: Tuple[float, float]
    model_accuracy: float
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    seasonality_factor: float = 1.0


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation."""
    recommendation_id: str
    resource_type: ResourceType
    current_cost: float
    optimized_cost: float
    potential_savings: float
    risk_level: str  # 'low', 'medium', 'high'
    recommendation_type: str
    implementation_steps: List[str]
    confidence: float


class DemandPredictor:
    """Machine learning-based demand prediction."""

    def __init__(self, history_window: int = 1440):  # 24 hours in minutes
        self.history_window = history_window
        self.demand_history: Dict[ResourceType, deque] = {
            resource: deque(maxlen=history_window)
            for resource in ResourceType
        }

        # ML models for each resource type
        self.models: Dict[ResourceType, Any] = {}
        self.scalers: Dict[ResourceType, Any] = {}
        self.model_accuracy: Dict[ResourceType, float] = {}

        # Pattern analysis
        self.hourly_patterns: Dict[ResourceType, List[float]] = {}
        self.daily_patterns: Dict[ResourceType, List[float]] = {}
        self.weekly_patterns: Dict[ResourceType, List[float]] = {}

        self.lock = threading.RLock()

    def add_demand_sample(self, resource_type: ResourceType, demand: float, timestamp: Optional[float] = None) -> None:
        """Add a demand sample to historical data."""
        with self.lock:
            if timestamp is None:
                timestamp = time.time()

            sample = {
                'demand': demand,
                'timestamp': timestamp,
                'hour': datetime.fromtimestamp(timestamp).hour,
                'day_of_week': datetime.fromtimestamp(timestamp).weekday(),
                'day_of_month': datetime.fromtimestamp(timestamp).day
            }

            self.demand_history[resource_type].append(sample)

            # Update patterns periodically
            if len(self.demand_history[resource_type]) % 60 == 0:  # Every hour
                self._update_patterns(resource_type)

    def predict_demand(self, resource_type: ResourceType, forecast_horizon: int = 60) -> DemandForecast:
        """Predict future demand for a resource type."""
        with self.lock:
            try:
                history = list(self.demand_history[resource_type])
                if len(history) < 10:
                    # Not enough data for prediction
                    current_demand = history[-1]['demand'] if history else 1.0
                    return self._create_simple_forecast(resource_type, current_demand, forecast_horizon)

                # Prepare features and targets
                features, targets = self._prepare_ml_data(history)

                if len(features) < 5:
                    return self._create_pattern_based_forecast(resource_type, history, forecast_horizon)

                # Train or update ML model
                model = self._get_or_create_model(resource_type)
                scaler = self._get_or_create_scaler(resource_type)

                if HAS_SKLEARN:
                    # Normalize features
                    features_scaled = scaler.fit_transform(features)

                    # Train model
                    model.fit(features_scaled, targets)

                    # Calculate model accuracy
                    predictions = model.predict(features_scaled)
                    accuracy = 1.0 - np.mean(np.abs(predictions - targets) / np.maximum(targets, 0.1))
                    self.model_accuracy[resource_type] = max(0.0, min(1.0, accuracy))

                    # Generate forecast
                    forecast_features = self._generate_forecast_features(history, forecast_horizon)
                    forecast_scaled = scaler.transform(forecast_features)
                    forecasted_demand = model.predict(forecast_scaled).tolist()
                else:
                    # Fallback to pattern-based prediction
                    return self._create_pattern_based_forecast(resource_type, history, forecast_horizon)

                # Apply seasonality and trend adjustments
                adjusted_forecast = self._apply_seasonality_adjustments(
                    resource_type, forecasted_demand, history[-1]['timestamp']
                )

                # Calculate confidence interval
                confidence_interval = self._calculate_confidence_interval(
                    adjusted_forecast, self.model_accuracy.get(resource_type, 0.5)
                )

                # Determine trend direction
                trend_direction = self._analyze_trend(adjusted_forecast)

                return DemandForecast(
                    resource_type=resource_type,
                    timestamp=time.time(),
                    forecast_horizon=forecast_horizon,
                    forecasted_demand=adjusted_forecast,
                    confidence_interval=confidence_interval,
                    model_accuracy=self.model_accuracy.get(resource_type, 0.5),
                    trend_direction=trend_direction,
                    seasonality_factor=self._get_current_seasonality_factor(resource_type)
                )

            except Exception as e:
                logger.error(f"Demand prediction failed for {resource_type}: {e}")
                # Return simple forecast as fallback
                current_demand = history[-1]['demand'] if history else 1.0
                return self._create_simple_forecast(resource_type, current_demand, forecast_horizon)

    def _prepare_ml_data(self, history: List[Dict[str, Any]]) -> Tuple[List[List[float]], List[float]]:
        """Prepare ML training data from history."""
        features = []
        targets = []

        # Use sliding window approach
        window_size = min(10, len(history) // 2)

        for i in range(window_size, len(history)):
            # Features: historical values and time-based features
            window = history[i-window_size:i]
            feature_vector = []

            # Historical demand values
            feature_vector.extend([sample['demand'] for sample in window])

            # Time-based features
            current_sample = history[i]
            feature_vector.extend([
                current_sample['hour'] / 23.0,  # Normalized hour
                current_sample['day_of_week'] / 6.0,  # Normalized day of week
                current_sample['day_of_month'] / 31.0,  # Normalized day of month
                np.sin(2 * np.pi * current_sample['hour'] / 24),  # Cyclical hour
                np.cos(2 * np.pi * current_sample['hour'] / 24),
                np.sin(2 * np.pi * current_sample['day_of_week'] / 7),  # Cyclical day
                np.cos(2 * np.pi * current_sample['day_of_week'] / 7)
            ])

            # Statistical features
            demands = [sample['demand'] for sample in window]
            feature_vector.extend([
                np.mean(demands),
                np.std(demands) if len(demands) > 1 else 0,
                np.max(demands),
                np.min(demands)
            ])

            features.append(feature_vector)
            targets.append(current_sample['demand'])

        return features, targets

    def _get_or_create_model(self, resource_type: ResourceType) -> Any:
        """Get or create ML model for resource type."""
        if resource_type not in self.models:
            if HAS_SKLEARN:
                self.models[resource_type] = LinearRegression()
            else:
                self.models[resource_type] = None
        return self.models[resource_type]

    def _get_or_create_scaler(self, resource_type: ResourceType) -> Any:
        """Get or create feature scaler for resource type."""
        if resource_type not in self.scalers:
            if HAS_SKLEARN:
                self.scalers[resource_type] = StandardScaler()
            else:
                self.scalers[resource_type] = None
        return self.scalers[resource_type]

    def _generate_forecast_features(self, history: List[Dict[str, Any]], forecast_horizon: int) -> List[List[float]]:
        """Generate features for forecasting."""
        if not history:
            return []

        forecast_features = []
        last_timestamp = history[-1]['timestamp']
        window_size = min(10, len(history))

        for i in range(forecast_horizon):
            future_timestamp = last_timestamp + (i + 1) * 60  # Assume 1-minute intervals
            future_dt = datetime.fromtimestamp(future_timestamp)

            # Use last window_size samples for historical context
            window = history[-window_size:]
            feature_vector = []

            # Historical demand values (use last available values)
            feature_vector.extend([sample['demand'] for sample in window])

            # Time-based features for future timestamp
            feature_vector.extend([
                future_dt.hour / 23.0,
                future_dt.weekday() / 6.0,
                future_dt.day / 31.0,
                np.sin(2 * np.pi * future_dt.hour / 24),
                np.cos(2 * np.pi * future_dt.hour / 24),
                np.sin(2 * np.pi * future_dt.weekday() / 7),
                np.cos(2 * np.pi * future_dt.weekday() / 7)
            ])

            # Statistical features
            demands = [sample['demand'] for sample in window]
            feature_vector.extend([
                np.mean(demands),
                np.std(demands) if len(demands) > 1 else 0,
                np.max(demands),
                np.min(demands)
            ])

            forecast_features.append(feature_vector)

        return forecast_features

    def _update_patterns(self, resource_type: ResourceType) -> None:
        """Update seasonal patterns for resource type."""
        try:
            history = list(self.demand_history[resource_type])
            if len(history) < 24:  # Need at least 24 samples
                return

            # Hourly pattern
            hourly_demands = defaultdict(list)
            for sample in history:
                hourly_demands[sample['hour']].append(sample['demand'])

            self.hourly_patterns[resource_type] = [
                np.mean(hourly_demands[hour]) if hourly_demands[hour] else 1.0
                for hour in range(24)
            ]

            # Daily pattern (day of week)
            daily_demands = defaultdict(list)
            for sample in history:
                daily_demands[sample['day_of_week']].append(sample['demand'])

            self.daily_patterns[resource_type] = [
                np.mean(daily_demands[day]) if daily_demands[day] else 1.0
                for day in range(7)
            ]

        except Exception as e:
            logger.error(f"Failed to update patterns for {resource_type}: {e}")

    def _create_simple_forecast(self, resource_type: ResourceType, current_demand: float, forecast_horizon: int) -> DemandForecast:
        """Create simple forecast based on current demand."""
        # Simple linear trend with small random variation
        base_trend = 0.01 * np.random.normal(0, 1)  # Small random trend
        forecasted_demand = [
            max(0.1, current_demand * (1 + base_trend * i / forecast_horizon))
            for i in range(forecast_horizon)
        ]

        return DemandForecast(
            resource_type=resource_type,
            timestamp=time.time(),
            forecast_horizon=forecast_horizon,
            forecasted_demand=forecasted_demand,
            confidence_interval=(min(forecasted_demand) * 0.8, max(forecasted_demand) * 1.2),
            model_accuracy=0.3,  # Low accuracy for simple model
            trend_direction='stable',
            seasonality_factor=1.0
        )

    def _create_pattern_based_forecast(self, resource_type: ResourceType, history: List[Dict[str, Any]], forecast_horizon: int) -> DemandForecast:
        """Create forecast based on historical patterns."""
        if not history:
            return self._create_simple_forecast(resource_type, 1.0, forecast_horizon)

        current_timestamp = history[-1]['timestamp']
        forecasted_demand = []

        for i in range(forecast_horizon):
            future_timestamp = current_timestamp + (i + 1) * 60
            future_dt = datetime.fromtimestamp(future_timestamp)

            # Base demand (recent average)
            recent_demands = [sample['demand'] for sample in history[-min(60, len(history)):]]
            base_demand = np.mean(recent_demands)

            # Apply hourly pattern if available
            hourly_factor = 1.0
            if resource_type in self.hourly_patterns:
                hourly_pattern = self.hourly_patterns[resource_type]
                pattern_avg = np.mean(hourly_pattern)
                if pattern_avg > 0:
                    hourly_factor = hourly_pattern[future_dt.hour] / pattern_avg

            # Apply daily pattern if available
            daily_factor = 1.0
            if resource_type in self.daily_patterns:
                daily_pattern = self.daily_patterns[resource_type]
                pattern_avg = np.mean(daily_pattern)
                if pattern_avg > 0:
                    daily_factor = daily_pattern[future_dt.weekday()] / pattern_avg

            # Combine factors
            predicted_demand = base_demand * hourly_factor * daily_factor
            forecasted_demand.append(max(0.1, predicted_demand))

        return DemandForecast(
            resource_type=resource_type,
            timestamp=time.time(),
            forecast_horizon=forecast_horizon,
            forecasted_demand=forecasted_demand,
            confidence_interval=(min(forecasted_demand) * 0.7, max(forecasted_demand) * 1.3),
            model_accuracy=0.6,  # Medium accuracy for pattern-based
            trend_direction=self._analyze_trend(forecasted_demand),
            seasonality_factor=self._get_current_seasonality_factor(resource_type)
        )

    def _apply_seasonality_adjustments(self, resource_type: ResourceType, forecast: List[float], base_timestamp: float) -> List[float]:
        """Apply seasonality adjustments to forecast."""
        if resource_type not in self.hourly_patterns:
            return forecast

        adjusted = []
        for i, value in enumerate(forecast):
            future_timestamp = base_timestamp + (i + 1) * 60
            future_dt = datetime.fromtimestamp(future_timestamp)

            # Hourly adjustment
            hourly_pattern = self.hourly_patterns[resource_type]
            hourly_avg = np.mean(hourly_pattern)
            if hourly_avg > 0:
                hourly_factor = hourly_pattern[future_dt.hour] / hourly_avg
                value *= hourly_factor

            adjusted.append(max(0.1, value))

        return adjusted

    def _calculate_confidence_interval(self, forecast: List[float], accuracy: float) -> Tuple[float, float]:
        """Calculate confidence interval for forecast."""
        if not forecast:
            return (0.0, 1.0)

        # Error margin based on accuracy
        error_margin = (1.0 - accuracy) * 0.5  # 50% of error translates to confidence interval

        forecast_mean = np.mean(forecast)
        lower_bound = forecast_mean * (1 - error_margin)
        upper_bound = forecast_mean * (1 + error_margin)

        return (max(0.0, lower_bound), upper_bound)

    def _analyze_trend(self, forecast: List[float]) -> str:
        """Analyze trend direction in forecast."""
        if len(forecast) < 2:
            return 'stable'

        # Linear regression on forecast values
        x = np.array(range(len(forecast)))
        y = np.array(forecast)

        if np.std(y) < 0.01:  # Very small variation
            return 'stable'

        slope = np.polyfit(x, y, 1)[0]

        if slope > 0.05:
            return 'increasing'
        elif slope < -0.05:
            return 'decreasing'
        else:
            return 'stable'

    def _get_current_seasonality_factor(self, resource_type: ResourceType) -> float:
        """Get current seasonality factor."""
        if resource_type not in self.hourly_patterns:
            return 1.0

        current_hour = datetime.now().hour
        hourly_pattern = self.hourly_patterns[resource_type]
        pattern_avg = np.mean(hourly_pattern)

        if pattern_avg > 0:
            return hourly_pattern[current_hour] / pattern_avg

        return 1.0


class CostOptimizer:
    """Cost optimization engine for cloud resources."""

    def __init__(self):
        self.instance_pricing: Dict[InstanceType, Dict[str, float]] = {
            InstanceType.ON_DEMAND: {'cpu': 0.05, 'memory': 0.01, 'gpu': 0.50},
            InstanceType.SPOT: {'cpu': 0.015, 'memory': 0.003, 'gpu': 0.15},
            InstanceType.RESERVED: {'cpu': 0.03, 'memory': 0.006, 'gpu': 0.30},
            InstanceType.PREEMPTIBLE: {'cpu': 0.012, 'memory': 0.002, 'gpu': 0.12}
        }

        self.spot_price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1440))  # 24 hours
        self.utilization_history: Dict[ResourceType, deque] = {
            resource: deque(maxlen=1440) for resource in ResourceType
        }

        self.lock = threading.RLock()

    def analyze_cost_optimization_opportunities(self, current_capacity: Dict[ResourceType, ResourceCapacity]) -> List[CostOptimizationRecommendation]:
        """Analyze current setup and recommend cost optimizations."""
        recommendations = []

        try:
            for resource_type, capacity in current_capacity.items():
                # Analyze utilization patterns
                utilization_recommendation = self._analyze_utilization_patterns(resource_type, capacity)
                if utilization_recommendation:
                    recommendations.append(utilization_recommendation)

                # Analyze instance type optimization
                instance_recommendation = self._analyze_instance_type_optimization(resource_type, capacity)
                if instance_recommendation:
                    recommendations.append(instance_recommendation)

                # Analyze spot instance opportunities
                spot_recommendation = self._analyze_spot_opportunities(resource_type, capacity)
                if spot_recommendation:
                    recommendations.append(spot_recommendation)

                # Analyze reserved instance opportunities
                reserved_recommendation = self._analyze_reserved_opportunities(resource_type, capacity)
                if reserved_recommendation:
                    recommendations.append(reserved_recommendation)

            # Sort by potential savings
            recommendations.sort(key=lambda x: x.potential_savings, reverse=True)

        except Exception as e:
            logger.error(f"Cost optimization analysis failed: {e}")

        return recommendations

    def _analyze_utilization_patterns(self, resource_type: ResourceType, capacity: ResourceCapacity) -> Optional[CostOptimizationRecommendation]:
        """Analyze resource utilization patterns."""
        try:
            utilization_data = list(self.utilization_history[resource_type])
            if len(utilization_data) < 60:  # Need at least 1 hour of data
                return None

            recent_utilization = [sample['utilization'] for sample in utilization_data[-60:]]
            avg_utilization = np.mean(recent_utilization)
            max_utilization = np.max(recent_utilization)

            current_cost = capacity.current * capacity.cost_per_unit * 24  # Daily cost

            # Under-utilization opportunity
            if avg_utilization < 0.3 and max_utilization < 0.6:
                # Recommend downsizing
                optimal_capacity = math.ceil(capacity.current * max_utilization * 1.2)  # 20% buffer
                optimal_capacity = max(capacity.minimum, optimal_capacity)

                optimized_cost = optimal_capacity * capacity.cost_per_unit * 24
                savings = current_cost - optimized_cost

                if savings > 0:
                    return CostOptimizationRecommendation(
                        recommendation_id=f"util_{resource_type.value}_{int(time.time())}",
                        resource_type=resource_type,
                        current_cost=current_cost,
                        optimized_cost=optimized_cost,
                        potential_savings=savings,
                        risk_level='low',
                        recommendation_type='rightsizing',
                        implementation_steps=[
                            f"Reduce {resource_type.value} capacity from {capacity.current} to {optimal_capacity}",
                            "Monitor performance metrics after reduction",
                            "Adjust if performance degradation occurs"
                        ],
                        confidence=0.8
                    )

            # Over-utilization warning
            elif avg_utilization > 0.8:
                # Recommend upsizing before issues occur
                optimal_capacity = math.ceil(capacity.current * 1.3)  # 30% increase
                optimal_capacity = min(capacity.maximum, optimal_capacity)

                optimized_cost = optimal_capacity * capacity.cost_per_unit * 24
                additional_cost = optimized_cost - current_cost

                return CostOptimizationRecommendation(
                    recommendation_id=f"util_scale_{resource_type.value}_{int(time.time())}",
                    resource_type=resource_type,
                    current_cost=current_cost,
                    optimized_cost=optimized_cost,
                    potential_savings=-additional_cost,  # Negative savings (cost increase)
                    risk_level='medium',
                    recommendation_type='proactive_scaling',
                    implementation_steps=[
                        f"Increase {resource_type.value} capacity from {capacity.current} to {optimal_capacity}",
                        "Prevent performance bottlenecks",
                        "Monitor and adjust as needed"
                    ],
                    confidence=0.7
                )

        except Exception as e:
            logger.error(f"Utilization pattern analysis failed: {e}")

        return None

    def _analyze_instance_type_optimization(self, resource_type: ResourceType, capacity: ResourceCapacity) -> Optional[CostOptimizationRecommendation]:
        """Analyze instance type optimization opportunities."""
        try:
            current_cost = capacity.current * capacity.cost_per_unit * 24

            # Compare costs across different instance types
            best_alternative = None
            max_savings = 0

            for instance_type, pricing in self.instance_pricing.items():
                if instance_type == capacity.instance_type:
                    continue

                # Get cost for this resource type
                resource_cost_key = self._get_pricing_key(resource_type)
                if resource_cost_key not in pricing:
                    continue

                alternative_cost = capacity.current * pricing[resource_cost_key] * 24
                savings = current_cost - alternative_cost

                if savings > max_savings:
                    max_savings = savings
                    best_alternative = instance_type

            if best_alternative and max_savings > current_cost * 0.1:  # At least 10% savings
                risk_level = self._assess_instance_type_risk(capacity.instance_type, best_alternative)

                return CostOptimizationRecommendation(
                    recommendation_id=f"instance_{resource_type.value}_{int(time.time())}",
                    resource_type=resource_type,
                    current_cost=current_cost,
                    optimized_cost=current_cost - max_savings,
                    potential_savings=max_savings,
                    risk_level=risk_level,
                    recommendation_type='instance_type_optimization',
                    implementation_steps=[
                        f"Migrate from {capacity.instance_type.value} to {best_alternative.value}",
                        "Test performance with new instance type",
                        "Implement gradual migration if suitable"
                    ],
                    confidence=0.6
                )

        except Exception as e:
            logger.error(f"Instance type optimization analysis failed: {e}")

        return None

    def _analyze_spot_opportunities(self, resource_type: ResourceType, capacity: ResourceCapacity) -> Optional[CostOptimizationRecommendation]:
        """Analyze spot instance opportunities."""
        try:
            if capacity.instance_type == InstanceType.SPOT:
                return None  # Already using spot instances

            current_cost = capacity.current * capacity.cost_per_unit * 24

            # Get spot pricing
            resource_cost_key = self._get_pricing_key(resource_type)
            spot_pricing = self.instance_pricing[InstanceType.SPOT]

            if resource_cost_key not in spot_pricing:
                return None

            spot_cost = capacity.current * spot_pricing[resource_cost_key] * 24
            savings = current_cost - spot_cost

            if savings > current_cost * 0.3:  # At least 30% savings for spot recommendation
                # Assess workload suitability for spot instances
                fault_tolerance = self._assess_fault_tolerance(resource_type)

                if fault_tolerance >= 0.7:  # High fault tolerance
                    return CostOptimizationRecommendation(
                        recommendation_id=f"spot_{resource_type.value}_{int(time.time())}",
                        resource_type=resource_type,
                        current_cost=current_cost,
                        optimized_cost=spot_cost,
                        potential_savings=savings,
                        risk_level='medium',
                        recommendation_type='spot_instances',
                        implementation_steps=[
                            "Implement spot instance request strategy",
                            "Set up automatic fallback to on-demand",
                            "Monitor spot price trends and availability",
                            "Implement checkpointing for long-running tasks"
                        ],
                        confidence=0.7
                    )

        except Exception as e:
            logger.error(f"Spot opportunity analysis failed: {e}")

        return None

    def _analyze_reserved_opportunities(self, resource_type: ResourceType, capacity: ResourceCapacity) -> Optional[CostOptimizationRecommendation]:
        """Analyze reserved instance opportunities."""
        try:
            if capacity.instance_type == InstanceType.RESERVED:
                return None

            # Analyze usage stability
            utilization_data = list(self.utilization_history[resource_type])
            if len(utilization_data) < 1440:  # Need at least 24 hours
                return None

            # Calculate baseline usage
            usage_values = [sample.get('capacity', 0) for sample in utilization_data]
            min_usage = np.percentile(usage_values, 10)  # 10th percentile as baseline

            if min_usage >= capacity.current * 0.7:  # Stable high usage
                current_cost = capacity.current * capacity.cost_per_unit * 24 * 365  # Annual

                resource_cost_key = self._get_pricing_key(resource_type)
                reserved_pricing = self.instance_pricing[InstanceType.RESERVED]

                if resource_cost_key in reserved_pricing:
                    reserved_cost = capacity.current * reserved_pricing[resource_cost_key] * 24 * 365
                    savings = current_cost - reserved_cost

                    if savings > current_cost * 0.2:  # At least 20% annual savings
                        return CostOptimizationRecommendation(
                            recommendation_id=f"reserved_{resource_type.value}_{int(time.time())}",
                            resource_type=resource_type,
                            current_cost=current_cost,
                            optimized_cost=reserved_cost,
                            potential_savings=savings,
                            risk_level='low',
                            recommendation_type='reserved_instances',
                            implementation_steps=[
                                f"Purchase reserved instances for baseline capacity of {min_usage}",
                                "Use on-demand for additional capacity above baseline",
                                "Monitor usage patterns to optimize reserved capacity"
                            ],
                            confidence=0.9
                        )

        except Exception as e:
            logger.error(f"Reserved opportunity analysis failed: {e}")

        return None

    def _get_pricing_key(self, resource_type: ResourceType) -> str:
        """Map resource type to pricing key."""
        mapping = {
            ResourceType.CPU_CORES: 'cpu',
            ResourceType.MEMORY_GB: 'memory',
            ResourceType.GPU_UNITS: 'gpu',
            ResourceType.WORKER_INSTANCES: 'cpu'  # Default to CPU pricing
        }
        return mapping.get(resource_type, 'cpu')

    def _assess_instance_type_risk(self, current_type: InstanceType, new_type: InstanceType) -> str:
        """Assess risk of changing instance type."""
        risk_matrix = {
            (InstanceType.ON_DEMAND, InstanceType.SPOT): 'high',
            (InstanceType.ON_DEMAND, InstanceType.RESERVED): 'low',
            (InstanceType.SPOT, InstanceType.ON_DEMAND): 'low',
            (InstanceType.RESERVED, InstanceType.ON_DEMAND): 'medium',
        }
        return risk_matrix.get((current_type, new_type), 'medium')

    def _assess_fault_tolerance(self, resource_type: ResourceType) -> float:
        """Assess fault tolerance of resource type (0.0 to 1.0)."""
        # In practice, this would analyze the specific workload characteristics
        tolerance_map = {
            ResourceType.CPU_CORES: 0.8,
            ResourceType.MEMORY_GB: 0.7,
            ResourceType.GPU_UNITS: 0.6,
            ResourceType.WORKER_INSTANCES: 0.9,
            ResourceType.STORAGE_CAPACITY: 0.3
        }
        return tolerance_map.get(resource_type, 0.5)


class PredictiveAutoScaler:
    """Main predictive auto-scaling system."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}

        self.scaler_id = f"scaler_{uuid.uuid4().hex[:8]}"
        self.enabled = config.get('enabled', True)

        # Scaling configuration
        self.min_scaling_interval = config.get('min_scaling_interval', 300)  # 5 minutes
        self.scaling_cooldown = config.get('scaling_cooldown', 600)  # 10 minutes
        self.prediction_horizon = config.get('prediction_horizon', 60)  # 1 hour
        self.confidence_threshold = config.get('confidence_threshold', 0.6)

        # Resource management
        self.resource_capacity: Dict[ResourceType, ResourceCapacity] = {}
        self.scaling_metrics: Dict[str, ScalingMetric] = {}

        # Components
        self.demand_predictor = DemandPredictor()
        self.cost_optimizer = CostOptimizer()

        # Scaling history
        self.scaling_events: deque = deque(maxlen=1000)
        self.last_scaling_time: Dict[ResourceType, float] = {}

        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self.is_running = False

        self.lock = threading.RLock()

    def add_scaling_metric(self, metric: ScalingMetric) -> None:
        """Add a scaling metric to monitor."""
        with self.lock:
            self.scaling_metrics[metric.name] = metric

    def set_resource_capacity(self, resource_type: ResourceType, capacity: ResourceCapacity) -> None:
        """Set current resource capacity."""
        with self.lock:
            self.resource_capacity[resource_type] = capacity

    def update_metric_value(self, metric_name: str, value: float) -> None:
        """Update a metric value."""
        with self.lock:
            if metric_name in self.scaling_metrics:
                self.scaling_metrics[metric_name].current_value = value

                # Add to demand predictor for relevant metrics
                if metric_name in ['cpu_utilization', 'memory_utilization', 'queue_length']:
                    resource_type = self._map_metric_to_resource(metric_name)
                    if resource_type:
                        self.demand_predictor.add_demand_sample(resource_type, value)

    async def start(self) -> None:
        """Start the auto-scaler."""
        if self.is_running:
            return

        self.is_running = True

        # Start background tasks
        self.background_tasks = [
            asyncio.create_task(self._scaling_loop()),
            asyncio.create_task(self._cost_optimization_loop()),
            asyncio.create_task(self._metrics_collection_loop())
        ]

        logger.info(f"Started predictive auto-scaler {self.scaler_id}")

    async def stop(self) -> None:
        """Stop the auto-scaler."""
        if not self.is_running:
            return

        self.is_running = False

        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.background_tasks.clear()
        logger.info(f"Stopped predictive auto-scaler {self.scaler_id}")

    async def _scaling_loop(self) -> None:
        """Main scaling decision loop."""
        while self.is_running:
            try:
                await asyncio.sleep(60)  # Check every minute

                if not self.enabled:
                    continue

                # Evaluate scaling decisions for each resource type
                for resource_type, capacity in self.resource_capacity.items():
                    scaling_decision = await self._evaluate_scaling_decision(resource_type, capacity)

                    if scaling_decision and scaling_decision[0] != ScalingDirection.MAINTAIN:
                        direction, reason, new_capacity, confidence = scaling_decision
                        await self._execute_scaling_action(resource_type, capacity, direction, reason, new_capacity, confidence)

            except Exception as e:
                logger.error(f"Scaling loop error: {e}")

    async def _cost_optimization_loop(self) -> None:
        """Cost optimization analysis loop."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Run every hour

                recommendations = self.cost_optimizer.analyze_cost_optimization_opportunities(self.resource_capacity)

                # Log high-value recommendations
                high_value_recs = [rec for rec in recommendations if rec.potential_savings > 100]  # $100+ savings
                for rec in high_value_recs:
                    logger.info(f"Cost optimization opportunity: {rec.recommendation_type} could save ${rec.potential_savings:.2f}")

                # Auto-apply low-risk, high-confidence recommendations
                auto_apply_recs = [
                    rec for rec in recommendations
                    if rec.risk_level == 'low' and rec.confidence > 0.8 and rec.potential_savings > 50
                ]

                for rec in auto_apply_recs:
                    logger.info(f"Auto-applying cost optimization: {rec.recommendation_type}")
                    # In practice, would implement the optimization here

            except Exception as e:
                logger.error(f"Cost optimization loop error: {e}")

    async def _metrics_collection_loop(self) -> None:
        """Metrics collection and processing loop."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Collect every 30 seconds

                # Simulate metric collection (in practice, would get from monitoring system)
                await self._collect_system_metrics()

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

    async def _evaluate_scaling_decision(self, resource_type: ResourceType, capacity: ResourceCapacity) -> Optional[Tuple[ScalingDirection, ScalingReason, int, float]]:
        """Evaluate whether scaling is needed for a resource type."""
        try:
            current_time = time.time()

            # Check cooldown period
            last_scaling = self.last_scaling_time.get(resource_type, 0)
            if current_time - last_scaling < self.scaling_cooldown:
                return None

            # Get demand forecast
            forecast = self.demand_predictor.predict_demand(resource_type, self.prediction_horizon)

            if forecast.model_accuracy < self.confidence_threshold:
                # Fallback to reactive scaling
                return await self._reactive_scaling_decision(resource_type, capacity)

            # Analyze forecast for scaling needs
            max_forecasted_demand = max(forecast.forecasted_demand)
            avg_forecasted_demand = np.mean(forecast.forecasted_demand)

            # Calculate required capacity
            peak_capacity_needed = math.ceil(max_forecasted_demand * 1.1)  # 10% buffer
            avg_capacity_needed = math.ceil(avg_forecasted_demand)

            # Scaling decisions
            if peak_capacity_needed > capacity.current and peak_capacity_needed <= capacity.maximum:
                # Scale up for predicted peak
                new_capacity = min(peak_capacity_needed, capacity.maximum)
                return (ScalingDirection.SCALE_UP, ScalingReason.PREDICTIVE_DEMAND, new_capacity, forecast.model_accuracy)

            elif avg_capacity_needed < capacity.current * 0.7 and forecast.trend_direction == 'decreasing':
                # Scale down for predicted low demand
                new_capacity = max(avg_capacity_needed, capacity.minimum)
                if new_capacity < capacity.current:
                    return (ScalingDirection.SCALE_DOWN, ScalingReason.PREDICTIVE_DEMAND, new_capacity, forecast.model_accuracy)

            return (ScalingDirection.MAINTAIN, ScalingReason.PREDICTIVE_DEMAND, int(capacity.current), forecast.model_accuracy)

        except Exception as e:
            logger.error(f"Scaling evaluation failed for {resource_type}: {e}")
            return None

    async def _reactive_scaling_decision(self, resource_type: ResourceType, capacity: ResourceCapacity) -> Optional[Tuple[ScalingDirection, ScalingReason, int, float]]:
        """Fallback reactive scaling based on current metrics."""
        try:
            # Find relevant metrics for this resource type
            relevant_metrics = []
            for metric_name, metric in self.scaling_metrics.items():
                if self._map_metric_to_resource(metric_name) == resource_type:
                    relevant_metrics.append(metric)

            if not relevant_metrics:
                return None

            # Calculate weighted score
            scale_up_votes = 0
            scale_down_votes = 0
            total_weight = 0

            for metric in relevant_metrics:
                if metric.current_value > metric.threshold_up:
                    scale_up_votes += metric.weight
                elif metric.current_value < metric.threshold_down:
                    scale_down_votes += metric.weight
                total_weight += metric.weight

            if total_weight == 0:
                return None

            scale_up_score = scale_up_votes / total_weight
            scale_down_score = scale_down_votes / total_weight

            # Make scaling decision
            if scale_up_score > 0.6:  # 60% threshold
                new_capacity = min(int(capacity.current * 1.5), capacity.maximum)
                return (ScalingDirection.SCALE_UP, ScalingReason.CPU_THRESHOLD, new_capacity, 0.7)

            elif scale_down_score > 0.6:
                new_capacity = max(int(capacity.current * 0.7), capacity.minimum)
                if new_capacity < capacity.current:
                    return (ScalingDirection.SCALE_DOWN, ScalingReason.CPU_THRESHOLD, new_capacity, 0.7)

            return (ScalingDirection.MAINTAIN, ScalingReason.CPU_THRESHOLD, int(capacity.current), 0.5)

        except Exception as e:
            logger.error(f"Reactive scaling decision failed for {resource_type}: {e}")
            return None

    async def _execute_scaling_action(self, resource_type: ResourceType, capacity: ResourceCapacity,
                                     direction: ScalingDirection, reason: ScalingReason,
                                     new_capacity: int, confidence: float) -> None:
        """Execute a scaling action."""
        try:
            # Calculate cost impact
            cost_per_unit = capacity.cost_per_unit
            cost_impact = (new_capacity - capacity.current) * cost_per_unit * 24  # Daily cost change

            # Create scaling event
            event = ScalingEvent(
                event_id=f"scale_{int(time.time() * 1000)}",
                timestamp=time.time(),
                direction=direction,
                reason=reason,
                resource_type=resource_type,
                previous_capacity=int(capacity.current),
                new_capacity=new_capacity,
                cost_impact=cost_impact,
                confidence=confidence
            )

            # Record event
            with self.lock:
                self.scaling_events.append(event)
                self.last_scaling_time[resource_type] = time.time()

            # Update capacity
            capacity.current = float(new_capacity)
            capacity.desired = float(new_capacity)

            logger.info(f"Scaling action executed: {direction.value} {resource_type.value} "
                       f"from {event.previous_capacity} to {new_capacity} "
                       f"(reason: {reason.value}, confidence: {confidence:.2f})")

            # In practice, would trigger actual infrastructure scaling here
            await self._trigger_infrastructure_scaling(resource_type, new_capacity, event)

        except Exception as e:
            logger.error(f"Scaling action execution failed: {e}")

    async def _trigger_infrastructure_scaling(self, resource_type: ResourceType, new_capacity: int, event: ScalingEvent) -> None:
        """Trigger actual infrastructure scaling (placeholder)."""
        # This is where you would integrate with cloud APIs (AWS, GCP, Azure)
        # For now, just simulate the action

        logger.info(f"Triggered infrastructure scaling for {resource_type.value} to {new_capacity} units")

        # Simulate scaling delay
        await asyncio.sleep(0.1)

        # In a real implementation:
        # - Call cloud provider APIs
        # - Update load balancer configurations
        # - Trigger container orchestration scaling
        # - Update monitoring and alerting thresholds

    async def _collect_system_metrics(self) -> None:
        """Collect system metrics (placeholder)."""
        # Simulate metric collection
        import random

        # Update some metrics with simulated values
        for metric_name in ['cpu_utilization', 'memory_utilization', 'queue_length', 'response_time']:
            if metric_name in self.scaling_metrics:
                # Simulate realistic metric values with some variation
                base_value = self.scaling_metrics[metric_name].current_value
                variation = random.uniform(-0.1, 0.1) * base_value
                new_value = max(0, base_value + variation)
                self.update_metric_value(metric_name, new_value)

    def _map_metric_to_resource(self, metric_name: str) -> Optional[ResourceType]:
        """Map metric name to resource type."""
        mapping = {
            'cpu_utilization': ResourceType.CPU_CORES,
            'memory_utilization': ResourceType.MEMORY_GB,
            'gpu_utilization': ResourceType.GPU_UNITS,
            'queue_length': ResourceType.WORKER_INSTANCES,
            'response_time': ResourceType.WORKER_INSTANCES,
            'network_utilization': ResourceType.NETWORK_BANDWIDTH,
            'storage_utilization': ResourceType.STORAGE_CAPACITY
        }
        return mapping.get(metric_name)

    def get_scaling_status(self) -> Dict[str, Any]:
        """Get comprehensive scaling status."""
        with self.lock:
            recent_events = list(self.scaling_events)[-10:]  # Last 10 events

            status = {
                'scaler_id': self.scaler_id,
                'enabled': self.enabled,
                'is_running': self.is_running,
                'resource_capacity': {
                    rt.value: {
                        'current': cap.current,
                        'desired': cap.desired,
                        'minimum': cap.minimum,
                        'maximum': cap.maximum,
                        'cost_per_unit': cap.cost_per_unit,
                        'instance_type': cap.instance_type.value
                    }
                    for rt, cap in self.resource_capacity.items()
                },
                'scaling_metrics': {
                    name: {
                        'current_value': metric.current_value,
                        'threshold_up': metric.threshold_up,
                        'threshold_down': metric.threshold_down,
                        'weight': metric.weight
                    }
                    for name, metric in self.scaling_metrics.items()
                },
                'recent_events': [
                    {
                        'timestamp': event.timestamp,
                        'direction': event.direction.value,
                        'reason': event.reason.value,
                        'resource_type': event.resource_type.value,
                        'previous_capacity': event.previous_capacity,
                        'new_capacity': event.new_capacity,
                        'cost_impact': event.cost_impact,
                        'confidence': event.confidence
                    }
                    for event in recent_events
                ],
                'total_events': len(self.scaling_events),
                'cost_optimization_enabled': True
            }

        return status


# Global auto-scaler instance
_auto_scaler: Optional[PredictiveAutoScaler] = None


def get_predictive_auto_scaler(config: Optional[Dict[str, Any]] = None) -> PredictiveAutoScaler:
    """Get the global predictive auto-scaler instance."""
    global _auto_scaler
    if _auto_scaler is None:
        _auto_scaler = PredictiveAutoScaler(config)
    return _auto_scaler


@asynccontextmanager
async def auto_scaling_context(resource_requirements: Dict[ResourceType, float]):
    """Context manager for auto-scaling operations."""
    scaler = get_predictive_auto_scaler()

    # Register resource requirements
    for resource_type, requirement in resource_requirements.items():
        scaler.update_metric_value(f"{resource_type.value}_demand", requirement)

    try:
        yield scaler
    except Exception as e:
        logger.error(f"Auto-scaling context error: {e}")
        raise
    finally:
        # Cleanup if needed
        pass
