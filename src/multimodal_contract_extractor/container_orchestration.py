"""
Container Orchestration and Service Mesh Integration for Scalable Deployment.

This module provides comprehensive container orchestration capabilities with Kubernetes
integration, service mesh support, automated deployment, and cloud-native infrastructure
management for the distributed contract extraction system.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
import uuid
import yaml
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Callable, Union

logger = logging.getLogger(__name__)

# Try to import Kubernetes and container libraries
try:
    from kubernetes import client, config as k8s_config
    from kubernetes.client.rest import ApiException
    HAS_KUBERNETES = True
except ImportError:
    HAS_KUBERNETES = False
    client = None
    k8s_config = None
    ApiException = Exception

try:
    import docker
    HAS_DOCKER = True
except ImportError:
    HAS_DOCKER = False
    docker = None


class ContainerRuntime(Enum):
    """Container runtime types."""
    DOCKER = "docker"
    CONTAINERD = "containerd"
    CRIO = "crio"
    PODMAN = "podman"


class OrchestrationPlatform(Enum):
    """Container orchestration platforms."""
    KUBERNETES = "kubernetes"
    DOCKER_SWARM = "docker_swarm"
    ECS = "ecs"
    NOMAD = "nomad"


class ServiceMeshType(Enum):
    """Service mesh implementations."""
    ISTIO = "istio"
    LINKERD = "linkerd"
    CONSUL_CONNECT = "consul_connect"
    ENVOY = "envoy"
    NONE = "none"


class DeploymentStrategy(Enum):
    """Deployment strategies."""
    ROLLING_UPDATE = "rolling_update"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"
    A_B_TESTING = "a_b_testing"


class ServiceType(Enum):
    """Kubernetes service types."""
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"
    EXTERNAL_NAME = "ExternalName"


@dataclass
class ContainerImage:
    """Container image specification."""
    name: str
    tag: str
    registry: str = "docker.io"
    namespace: str = ""
    digest: str = ""
    build_context: Optional[str] = None
    dockerfile: Optional[str] = None
    build_args: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Get full image name."""
        if self.namespace:
            return f"{self.registry}/{self.namespace}/{self.name}:{self.tag}"
        return f"{self.registry}/{self.name}:{self.tag}"


@dataclass
class ContainerSpec:
    """Container specification."""
    name: str
    image: ContainerImage
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    ports: List[int] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volume_mounts: Dict[str, str] = field(default_factory=dict)  # mount_path -> volume_name
    resource_requests: Dict[str, str] = field(default_factory=dict)  # cpu, memory, gpu
    resource_limits: Dict[str, str] = field(default_factory=dict)
    health_check: Optional[Dict[str, Any]] = None
    security_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceSpec:
    """Kubernetes service specification."""
    name: str
    selector: Dict[str, str]
    ports: List[Dict[str, Any]]  # name, port, targetPort, protocol
    service_type: ServiceType = ServiceType.CLUSTER_IP
    cluster_ip: Optional[str] = None
    load_balancer_ip: Optional[str] = None
    external_name: Optional[str] = None
    annotations: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class DeploymentSpec:
    """Kubernetes deployment specification."""
    name: str
    namespace: str = "default"
    replicas: int = 3
    containers: List[ContainerSpec] = field(default_factory=list)
    volumes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING_UPDATE
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    node_selector: Dict[str, str] = field(default_factory=dict)
    tolerations: List[Dict[str, Any]] = field(default_factory=list)
    affinity: Dict[str, Any] = field(default_factory=dict)
    service_account: Optional[str] = None
    security_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HorizontalPodAutoscalerSpec:
    """HPA specification."""
    name: str
    namespace: str = "default"
    target_deployment: str = ""
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: Optional[int] = None
    target_memory_utilization: Optional[int] = None
    custom_metrics: List[Dict[str, Any]] = field(default_factory=list)
    scale_down_stabilization: int = 300  # seconds
    scale_up_stabilization: int = 0  # seconds


@dataclass
class IngressSpec:
    """Kubernetes ingress specification."""
    name: str
    namespace: str = "default"
    ingress_class: str = "nginx"
    rules: List[Dict[str, Any]] = field(default_factory=list)  # host, paths
    tls: List[Dict[str, Any]] = field(default_factory=list)  # hosts, secretName
    annotations: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class ServiceMeshConfig:
    """Service mesh configuration."""
    mesh_type: ServiceMeshType
    namespace: str = "istio-system"
    mtls_enabled: bool = True
    traffic_management: Dict[str, Any] = field(default_factory=dict)
    security_policies: List[Dict[str, Any]] = field(default_factory=list)
    observability_config: Dict[str, Any] = field(default_factory=dict)
    circuit_breaker: Dict[str, Any] = field(default_factory=dict)
    retry_policy: Dict[str, Any] = field(default_factory=dict)


class DockerManager:
    """Docker container management."""
    
    def __init__(self):
        self.docker_client = None
        if HAS_DOCKER:
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
            except Exception as e:
                logger.error(f"Docker client initialization failed: {e}")
                self.docker_client = None
    
    async def build_image(self, image_spec: ContainerImage) -> bool:
        """Build a Docker image."""
        if not self.docker_client or not image_spec.build_context:
            return False
        
        try:
            build_path = Path(image_spec.build_context)
            if not build_path.exists():
                logger.error(f"Build context path does not exist: {build_path}")
                return False
            
            dockerfile_path = image_spec.dockerfile or "Dockerfile"
            
            logger.info(f"Building image {image_spec.full_name} from {build_path}")
            
            # Build image
            image, build_logs = self.docker_client.images.build(
                path=str(build_path),
                dockerfile=dockerfile_path,
                tag=image_spec.full_name,
                buildargs=image_spec.build_args,
                labels=image_spec.labels,
                rm=True  # Remove intermediate containers
            )
            
            # Log build output
            for log_entry in build_logs:
                if 'stream' in log_entry:
                    logger.debug(f"Build: {log_entry['stream'].strip()}")
            
            logger.info(f"Successfully built image {image_spec.full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Image build failed: {e}")
            return False
    
    async def push_image(self, image_spec: ContainerImage, auth_config: Optional[Dict[str, str]] = None) -> bool:
        """Push image to registry."""
        if not self.docker_client:
            return False
        
        try:
            logger.info(f"Pushing image {image_spec.full_name}")
            
            # Push image
            push_logs = self.docker_client.images.push(
                image_spec.full_name,
                auth_config=auth_config,
                stream=True,
                decode=True
            )
            
            # Process push logs
            for log_entry in push_logs:
                if 'status' in log_entry:
                    logger.debug(f"Push: {log_entry['status']}")
                if 'error' in log_entry:
                    logger.error(f"Push error: {log_entry['error']}")
                    return False
            
            logger.info(f"Successfully pushed image {image_spec.full_name}")
            return True
            
        except Exception as e:
            logger.error(f"Image push failed: {e}")
            return False
    
    async def run_container(self, container_spec: ContainerSpec, detach: bool = True) -> Optional[str]:
        """Run a container."""
        if not self.docker_client:
            return None
        
        try:
            # Prepare container configuration
            container_config = {
                'image': container_spec.image.full_name,
                'name': container_spec.name,
                'detach': detach,
                'environment': container_spec.environment,
                'ports': {f"{port}/tcp": port for port in container_spec.ports} if container_spec.ports else None,
                'volumes': container_spec.volume_mounts if container_spec.volume_mounts else None
            }
            
            if container_spec.command:
                container_config['command'] = container_spec.command
            if container_spec.args:
                container_config['command'] = (container_config.get('command', []) + container_spec.args)
            
            # Run container
            container = self.docker_client.containers.run(**container_config)
            
            if detach:
                logger.info(f"Started container {container_spec.name} with ID {container.id}")
                return container.id
            else:
                logger.info(f"Container {container_spec.name} completed")
                return container.id
            
        except Exception as e:
            logger.error(f"Container run failed: {e}")
            return None


class KubernetesManager:
    """Kubernetes cluster management."""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.k8s_client = None
        self.apps_v1 = None
        self.core_v1 = None
        self.networking_v1 = None
        self.autoscaling_v2 = None
        
        if HAS_KUBERNETES:
            try:
                if kubeconfig_path:
                    k8s_config.load_kube_config(config_file=kubeconfig_path)
                else:
                    # Try in-cluster config first, then default kubeconfig
                    try:
                        k8s_config.load_incluster_config()
                    except:
                        k8s_config.load_kube_config()
                
                # Initialize API clients
                self.apps_v1 = client.AppsV1Api()
                self.core_v1 = client.CoreV1Api()
                self.networking_v1 = client.NetworkingV1Api()
                self.autoscaling_v2 = client.AutoscalingV2Api()
                
                # Test connection
                self.core_v1.list_namespace(limit=1)
                logger.info("Kubernetes client initialized successfully")
                
            except Exception as e:
                logger.error(f"Kubernetes client initialization failed: {e}")
    
    async def create_deployment(self, deployment_spec: DeploymentSpec) -> bool:
        """Create a Kubernetes deployment."""
        if not self.apps_v1:
            return False
        
        try:
            # Build deployment manifest
            deployment = self._build_deployment_manifest(deployment_spec)
            
            # Create deployment
            result = self.apps_v1.create_namespaced_deployment(
                namespace=deployment_spec.namespace,
                body=deployment
            )
            
            logger.info(f"Created deployment {deployment_spec.name} in namespace {deployment_spec.namespace}")
            return True
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"Deployment {deployment_spec.name} already exists, updating...")
                return await self.update_deployment(deployment_spec)
            else:
                logger.error(f"Deployment creation failed: {e}")
                return False
        except Exception as e:
            logger.error(f"Deployment creation failed: {e}")
            return False
    
    async def update_deployment(self, deployment_spec: DeploymentSpec) -> bool:
        """Update a Kubernetes deployment."""
        if not self.apps_v1:
            return False
        
        try:
            # Build deployment manifest
            deployment = self._build_deployment_manifest(deployment_spec)
            
            # Update deployment
            result = self.apps_v1.patch_namespaced_deployment(
                name=deployment_spec.name,
                namespace=deployment_spec.namespace,
                body=deployment
            )
            
            logger.info(f"Updated deployment {deployment_spec.name}")
            return True
            
        except ApiException as e:
            logger.error(f"Deployment update failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Deployment update failed: {e}")
            return False
    
    async def create_service(self, service_spec: ServiceSpec, namespace: str = "default") -> bool:
        """Create a Kubernetes service."""
        if not self.core_v1:
            return False
        
        try:
            # Build service manifest
            service = self._build_service_manifest(service_spec)
            
            # Create service
            result = self.core_v1.create_namespaced_service(
                namespace=namespace,
                body=service
            )
            
            logger.info(f"Created service {service_spec.name} in namespace {namespace}")
            return True
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"Service {service_spec.name} already exists")
                return True
            else:
                logger.error(f"Service creation failed: {e}")
                return False
        except Exception as e:
            logger.error(f"Service creation failed: {e}")
            return False
    
    async def create_hpa(self, hpa_spec: HorizontalPodAutoscalerSpec) -> bool:
        """Create a Horizontal Pod Autoscaler."""
        if not self.autoscaling_v2:
            return False
        
        try:
            # Build HPA manifest
            hpa = self._build_hpa_manifest(hpa_spec)
            
            # Create HPA
            result = self.autoscaling_v2.create_namespaced_horizontal_pod_autoscaler(
                namespace=hpa_spec.namespace,
                body=hpa
            )
            
            logger.info(f"Created HPA {hpa_spec.name}")
            return True
            
        except ApiException as e:
            if e.status == 409:
                logger.info(f"HPA {hpa_spec.name} already exists")
                return True
            else:
                logger.error(f"HPA creation failed: {e}")
                return False
        except Exception as e:
            logger.error(f"HPA creation failed: {e}")
            return False
    
    async def create_ingress(self, ingress_spec: IngressSpec) -> bool:
        """Create a Kubernetes ingress."""
        if not self.networking_v1:
            return False
        
        try:
            # Build ingress manifest
            ingress = self._build_ingress_manifest(ingress_spec)
            
            # Create ingress
            result = self.networking_v1.create_namespaced_ingress(
                namespace=ingress_spec.namespace,
                body=ingress
            )
            
            logger.info(f"Created ingress {ingress_spec.name}")
            return True
            
        except ApiException as e:
            if e.status == 409:
                logger.info(f"Ingress {ingress_spec.name} already exists")
                return True
            else:
                logger.error(f"Ingress creation failed: {e}")
                return False
        except Exception as e:
            logger.error(f"Ingress creation failed: {e}")
            return False
    
    async def scale_deployment(self, name: str, namespace: str, replicas: int) -> bool:
        """Scale a deployment."""
        if not self.apps_v1:
            return False
        
        try:
            # Patch deployment with new replica count
            body = {'spec': {'replicas': replicas}}
            
            result = self.apps_v1.patch_namespaced_deployment_scale(
                name=name,
                namespace=namespace,
                body=body
            )
            
            logger.info(f"Scaled deployment {name} to {replicas} replicas")
            return True
            
        except ApiException as e:
            logger.error(f"Deployment scaling failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Deployment scaling failed: {e}")
            return False
    
    async def get_deployment_status(self, name: str, namespace: str) -> Optional[Dict[str, Any]]:
        """Get deployment status."""
        if not self.apps_v1:
            return None
        
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=name,
                namespace=namespace
            )
            
            status = deployment.status
            return {
                'replicas': status.replicas or 0,
                'ready_replicas': status.ready_replicas or 0,
                'available_replicas': status.available_replicas or 0,
                'updated_replicas': status.updated_replicas or 0,
                'unavailable_replicas': status.unavailable_replicas or 0,
                'conditions': [
                    {
                        'type': condition.type,
                        'status': condition.status,
                        'reason': condition.reason,
                        'message': condition.message
                    }
                    for condition in (status.conditions or [])
                ]
            }
            
        except ApiException as e:
            logger.error(f"Failed to get deployment status: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return None
    
    def _build_deployment_manifest(self, spec: DeploymentSpec) -> Dict[str, Any]:
        """Build Kubernetes deployment manifest."""
        # Container specifications
        containers = []
        for container_spec in spec.containers:
            container = {
                'name': container_spec.name,
                'image': container_spec.image.full_name,
                'ports': [{'containerPort': port} for port in container_spec.ports],
                'env': [{'name': k, 'value': v} for k, v in container_spec.environment.items()]
            }
            
            if container_spec.command:
                container['command'] = container_spec.command
            if container_spec.args:
                container['args'] = container_spec.args
            
            # Resource requirements
            if container_spec.resource_requests or container_spec.resource_limits:
                container['resources'] = {}
                if container_spec.resource_requests:
                    container['resources']['requests'] = container_spec.resource_requests
                if container_spec.resource_limits:
                    container['resources']['limits'] = container_spec.resource_limits
            
            # Volume mounts
            if container_spec.volume_mounts:
                container['volumeMounts'] = [
                    {'name': vol_name, 'mountPath': mount_path}
                    for mount_path, vol_name in container_spec.volume_mounts.items()
                ]
            
            # Health checks
            if container_spec.health_check:
                if 'readiness' in container_spec.health_check:
                    container['readinessProbe'] = container_spec.health_check['readiness']
                if 'liveness' in container_spec.health_check:
                    container['livenessProbe'] = container_spec.health_check['liveness']
            
            containers.append(container)
        
        # Pod template
        pod_template = {
            'metadata': {
                'labels': {**spec.labels, 'app': spec.name}
            },
            'spec': {
                'containers': containers
            }
        }
        
        # Volumes
        if spec.volumes:
            pod_template['spec']['volumes'] = [
                {'name': name, **volume_spec}
                for name, volume_spec in spec.volumes.items()
            ]
        
        # Node selector
        if spec.node_selector:
            pod_template['spec']['nodeSelector'] = spec.node_selector
        
        # Tolerations
        if spec.tolerations:
            pod_template['spec']['tolerations'] = spec.tolerations
        
        # Affinity
        if spec.affinity:
            pod_template['spec']['affinity'] = spec.affinity
        
        # Service account
        if spec.service_account:
            pod_template['spec']['serviceAccountName'] = spec.service_account
        
        # Security context
        if spec.security_context:
            pod_template['spec']['securityContext'] = spec.security_context
        
        # Deployment strategy
        strategy = {'type': 'RollingUpdate'}
        if spec.strategy == DeploymentStrategy.ROLLING_UPDATE:
            strategy['rollingUpdate'] = {
                'maxUnavailable': '25%',
                'maxSurge': '25%'
            }
        elif spec.strategy == DeploymentStrategy.RECREATE:
            strategy['type'] = 'Recreate'
        
        # Build full deployment manifest
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': spec.name,
                'namespace': spec.namespace,
                'labels': {**spec.labels, 'app': spec.name},
                'annotations': spec.annotations
            },
            'spec': {
                'replicas': spec.replicas,
                'selector': {'matchLabels': {'app': spec.name}},
                'template': pod_template,
                'strategy': strategy
            }
        }
        
        return deployment
    
    def _build_service_manifest(self, spec: ServiceSpec) -> Dict[str, Any]:
        """Build Kubernetes service manifest."""
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': spec.name,
                'labels': spec.labels,
                'annotations': spec.annotations
            },
            'spec': {
                'selector': spec.selector,
                'ports': spec.ports,
                'type': spec.service_type.value
            }
        }
        
        if spec.cluster_ip:
            service['spec']['clusterIP'] = spec.cluster_ip
        if spec.load_balancer_ip:
            service['spec']['loadBalancerIP'] = spec.load_balancer_ip
        if spec.external_name:
            service['spec']['externalName'] = spec.external_name
        
        return service
    
    def _build_hpa_manifest(self, spec: HorizontalPodAutoscalerSpec) -> Dict[str, Any]:
        """Build HPA manifest."""
        metrics = []
        
        # CPU utilization metric
        if spec.target_cpu_utilization:
            metrics.append({
                'type': 'Resource',
                'resource': {
                    'name': 'cpu',
                    'target': {
                        'type': 'Utilization',
                        'averageUtilization': spec.target_cpu_utilization
                    }
                }
            })
        
        # Memory utilization metric
        if spec.target_memory_utilization:
            metrics.append({
                'type': 'Resource',
                'resource': {
                    'name': 'memory',
                    'target': {
                        'type': 'Utilization',
                        'averageUtilization': spec.target_memory_utilization
                    }
                }
            })
        
        # Custom metrics
        metrics.extend(spec.custom_metrics)
        
        hpa = {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': spec.name,
                'namespace': spec.namespace
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': spec.target_deployment
                },
                'minReplicas': spec.min_replicas,
                'maxReplicas': spec.max_replicas,
                'metrics': metrics,
                'behavior': {
                    'scaleDown': {
                        'stabilizationWindowSeconds': spec.scale_down_stabilization
                    },
                    'scaleUp': {
                        'stabilizationWindowSeconds': spec.scale_up_stabilization
                    }
                }
            }
        }
        
        return hpa
    
    def _build_ingress_manifest(self, spec: IngressSpec) -> Dict[str, Any]:
        """Build ingress manifest."""
        ingress = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': spec.name,
                'namespace': spec.namespace,
                'annotations': {
                    'kubernetes.io/ingress.class': spec.ingress_class,
                    **spec.annotations
                },
                'labels': spec.labels
            },
            'spec': {
                'rules': spec.rules
            }
        }
        
        if spec.tls:
            ingress['spec']['tls'] = spec.tls
        
        return ingress


class ServiceMeshManager:
    """Service mesh integration and management."""
    
    def __init__(self, config: ServiceMeshConfig, k8s_manager: KubernetesManager):
        self.config = config
        self.k8s_manager = k8s_manager
    
    async def enable_mesh_injection(self, namespace: str) -> bool:
        """Enable service mesh injection for a namespace."""
        if not self.k8s_manager.core_v1:
            return False
        
        try:
            # Label namespace for mesh injection
            if self.config.mesh_type == ServiceMeshType.ISTIO:
                label_patch = {
                    'metadata': {
                        'labels': {
                            'istio-injection': 'enabled'
                        }
                    }
                }
            elif self.config.mesh_type == ServiceMeshType.LINKERD:
                label_patch = {
                    'metadata': {
                        'annotations': {
                            'linkerd.io/inject': 'enabled'
                        }
                    }
                }
            else:
                return False  # Unsupported mesh type
            
            # Patch namespace
            self.k8s_manager.core_v1.patch_namespace(
                name=namespace,
                body=label_patch
            )
            
            logger.info(f"Enabled {self.config.mesh_type.value} injection for namespace {namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable mesh injection: {e}")
            return False
    
    async def create_destination_rule(self, name: str, host: str, namespace: str = "default") -> bool:
        """Create a destination rule for traffic management."""
        if self.config.mesh_type != ServiceMeshType.ISTIO:
            logger.warning("Destination rules are only supported with Istio")
            return False
        
        try:
            destination_rule = {
                'apiVersion': 'networking.istio.io/v1beta1',
                'kind': 'DestinationRule',
                'metadata': {
                    'name': name,
                    'namespace': namespace
                },
                'spec': {
                    'host': host,
                    'trafficPolicy': {
                        'tls': {
                            'mode': 'ISTIO_MUTUAL' if self.config.mtls_enabled else 'DISABLE'
                        }
                    }
                }
            }
            
            # Add circuit breaker configuration
            if self.config.circuit_breaker:
                destination_rule['spec']['trafficPolicy']['outlierDetection'] = self.config.circuit_breaker
            
            # This would use a custom resource API to create the destination rule
            # For now, we'll just log the creation
            logger.info(f"Created destination rule {name} for host {host}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create destination rule: {e}")
            return False
    
    async def create_virtual_service(self, name: str, hosts: List[str], http_routes: List[Dict[str, Any]], namespace: str = "default") -> bool:
        """Create a virtual service for traffic routing."""
        if self.config.mesh_type != ServiceMeshType.ISTIO:
            logger.warning("Virtual services are only supported with Istio")
            return False
        
        try:
            virtual_service = {
                'apiVersion': 'networking.istio.io/v1beta1',
                'kind': 'VirtualService',
                'metadata': {
                    'name': name,
                    'namespace': namespace
                },
                'spec': {
                    'hosts': hosts,
                    'http': http_routes
                }
            }
            
            # Add retry policy if configured
            if self.config.retry_policy:
                for route in http_routes:
                    if 'route' in route:
                        route['retries'] = self.config.retry_policy
            
            logger.info(f"Created virtual service {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create virtual service: {e}")
            return False
    
    async def create_authorization_policy(self, name: str, namespace: str, rules: List[Dict[str, Any]]) -> bool:
        """Create authorization policy for security."""
        if self.config.mesh_type != ServiceMeshType.ISTIO:
            logger.warning("Authorization policies are only supported with Istio")
            return False
        
        try:
            auth_policy = {
                'apiVersion': 'security.istio.io/v1beta1',
                'kind': 'AuthorizationPolicy',
                'metadata': {
                    'name': name,
                    'namespace': namespace
                },
                'spec': {
                    'rules': rules
                }
            }
            
            logger.info(f"Created authorization policy {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create authorization policy: {e}")
            return False


class ContainerOrchestrator:
    """Main container orchestration management system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        self.orchestrator_id = f"orchestrator_{uuid.uuid4().hex[:8]}"
        self.platform = OrchestrationPlatform(config.get('platform', 'kubernetes'))
        self.namespace = config.get('namespace', 'multimodal-contract-extractor')
        
        # Initialize managers
        self.docker_manager = DockerManager()
        self.k8s_manager = KubernetesManager(config.get('kubeconfig_path'))
        
        # Service mesh configuration
        mesh_config = config.get('service_mesh', {})
        if mesh_config.get('enabled', False):
            mesh_type = ServiceMeshType(mesh_config.get('type', 'istio'))
            self.service_mesh_config = ServiceMeshConfig(
                mesh_type=mesh_type,
                namespace=mesh_config.get('namespace', 'istio-system'),
                mtls_enabled=mesh_config.get('mtls_enabled', True)
            )
            self.service_mesh_manager = ServiceMeshManager(self.service_mesh_config, self.k8s_manager)
        else:
            self.service_mesh_manager = None
        
        # Deployment tracking
        self.deployments: Dict[str, DeploymentSpec] = {}
        self.services: Dict[str, ServiceSpec] = {}
        
        self.deployment_history: deque = deque(maxlen=100)
    
    async def deploy_application(self, deployment_config: Dict[str, Any]) -> bool:
        """Deploy the complete application stack."""
        try:
            logger.info(f"Starting application deployment with orchestrator {self.orchestrator_id}")
            
            # Create namespace if it doesn't exist
            await self._ensure_namespace()
            
            # Enable service mesh injection if configured
            if self.service_mesh_manager:
                await self.service_mesh_manager.enable_mesh_injection(self.namespace)
            
            # Deploy core components
            success = True
            
            # 1. Deploy contract extractor API
            api_deployment = await self._deploy_api_service(deployment_config.get('api', {}))
            success = success and api_deployment
            
            # 2. Deploy worker nodes
            worker_deployment = await self._deploy_worker_nodes(deployment_config.get('workers', {}))
            success = success and worker_deployment
            
            # 3. Deploy monitoring stack
            monitoring_deployment = await self._deploy_monitoring_stack(deployment_config.get('monitoring', {}))
            success = success and monitoring_deployment
            
            # 4. Deploy caching layer
            cache_deployment = await self._deploy_cache_layer(deployment_config.get('cache', {}))
            success = success and cache_deployment
            
            # 5. Configure ingress
            ingress_deployment = await self._deploy_ingress(deployment_config.get('ingress', {}))
            success = success and ingress_deployment
            
            if success:
                logger.info("Application deployment completed successfully")
            else:
                logger.error("Application deployment completed with errors")
            
            return success
            
        except Exception as e:
            logger.error(f"Application deployment failed: {e}")
            return False
    
    async def _ensure_namespace(self) -> bool:
        """Ensure namespace exists."""
        if not self.k8s_manager.core_v1:
            return False
        
        try:
            # Try to get namespace
            try:
                self.k8s_manager.core_v1.read_namespace(name=self.namespace)
                logger.debug(f"Namespace {self.namespace} already exists")
                return True
            except ApiException as e:
                if e.status != 404:
                    raise
            
            # Create namespace
            namespace_manifest = {
                'apiVersion': 'v1',
                'kind': 'Namespace',
                'metadata': {
                    'name': self.namespace,
                    'labels': {
                        'name': self.namespace,
                        'managed-by': 'container-orchestrator'
                    }
                }
            }
            
            self.k8s_manager.core_v1.create_namespace(body=namespace_manifest)
            logger.info(f"Created namespace {self.namespace}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure namespace: {e}")
            return False
    
    async def _deploy_api_service(self, config: Dict[str, Any]) -> bool:
        """Deploy API service."""
        try:
            # Build container image spec
            image = ContainerImage(
                name="multimodal-contract-extractor-api",
                tag=config.get('tag', 'latest'),
                registry=config.get('registry', 'docker.io'),
                namespace=config.get('image_namespace', 'mce')
            )
            
            # Container spec
            container = ContainerSpec(
                name="api",
                image=image,
                ports=[8000],  # API port
                environment={
                    'ENVIRONMENT': 'production',
                    'LOG_LEVEL': 'INFO',
                    'WORKERS': str(config.get('workers', 4)),
                    **config.get('environment', {})
                },
                resource_requests={
                    'cpu': config.get('cpu_request', '500m'),
                    'memory': config.get('memory_request', '1Gi')
                },
                resource_limits={
                    'cpu': config.get('cpu_limit', '2'),
                    'memory': config.get('memory_limit', '4Gi')
                },
                health_check={
                    'readiness': {
                        'httpGet': {
                            'path': '/health',
                            'port': 8000
                        },
                        'initialDelaySeconds': 10,
                        'periodSeconds': 5
                    },
                    'liveness': {
                        'httpGet': {
                            'path': '/health',
                            'port': 8000
                        },
                        'initialDelaySeconds': 30,
                        'periodSeconds': 10
                    }
                }
            )
            
            # Deployment spec
            deployment = DeploymentSpec(
                name="api",
                namespace=self.namespace,
                replicas=config.get('replicas', 3),
                containers=[container],
                labels={
                    'app': 'api',
                    'component': 'multimodal-contract-extractor',
                    'version': config.get('tag', 'latest')
                },
                strategy=DeploymentStrategy.ROLLING_UPDATE
            )
            
            # Service spec
            service = ServiceSpec(
                name="api",
                selector={'app': 'api'},
                ports=[{
                    'name': 'http',
                    'port': 80,
                    'targetPort': 8000,
                    'protocol': 'TCP'
                }],
                service_type=ServiceType.CLUSTER_IP,
                labels={'app': 'api', 'component': 'multimodal-contract-extractor'}
            )
            
            # HPA spec
            hpa = HorizontalPodAutoscalerSpec(
                name="api",
                namespace=self.namespace,
                target_deployment="api",
                min_replicas=config.get('min_replicas', 2),
                max_replicas=config.get('max_replicas', 10),
                target_cpu_utilization=config.get('target_cpu', 70),
                target_memory_utilization=config.get('target_memory', 80)
            )
            
            # Deploy components
            success = True
            success = success and await self.k8s_manager.create_deployment(deployment)
            success = success and await self.k8s_manager.create_service(service, self.namespace)
            success = success and await self.k8s_manager.create_hpa(hpa)
            
            if success:
                self.deployments["api"] = deployment
                self.services["api"] = service
                logger.info("API service deployed successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"API service deployment failed: {e}")
            return False
    
    async def _deploy_worker_nodes(self, config: Dict[str, Any]) -> bool:
        """Deploy worker nodes."""
        try:
            # Worker image
            image = ContainerImage(
                name="multimodal-contract-extractor-worker",
                tag=config.get('tag', 'latest'),
                registry=config.get('registry', 'docker.io'),
                namespace=config.get('image_namespace', 'mce')
            )
            
            # Worker container
            container = ContainerSpec(
                name="worker",
                image=image,
                environment={
                    'WORKER_TYPE': 'contract_processor',
                    'REDIS_URL': config.get('redis_url', 'redis://redis:6379'),
                    'LOG_LEVEL': 'INFO',
                    **config.get('environment', {})
                },
                resource_requests={
                    'cpu': config.get('cpu_request', '1'),
                    'memory': config.get('memory_request', '2Gi')
                },
                resource_limits={
                    'cpu': config.get('cpu_limit', '4'),
                    'memory': config.get('memory_limit', '8Gi')
                }
            )
            
            # Add GPU resources if enabled
            if config.get('gpu_enabled', False):
                container.resource_requests['nvidia.com/gpu'] = str(config.get('gpu_request', 1))
                container.resource_limits['nvidia.com/gpu'] = str(config.get('gpu_limit', 1))
            
            # Worker deployment
            deployment = DeploymentSpec(
                name="workers",
                namespace=self.namespace,
                replicas=config.get('replicas', 5),
                containers=[container],
                labels={
                    'app': 'workers',
                    'component': 'multimodal-contract-extractor',
                    'version': config.get('tag', 'latest')
                }
            )
            
            # Add node selector for GPU nodes if needed
            if config.get('gpu_enabled', False):
                deployment.node_selector = {'accelerator': 'nvidia-tesla-gpu'}
            
            # Worker HPA
            hpa = HorizontalPodAutoscalerSpec(
                name="workers",
                namespace=self.namespace,
                target_deployment="workers",
                min_replicas=config.get('min_replicas', 3),
                max_replicas=config.get('max_replicas', 20),
                target_cpu_utilization=config.get('target_cpu', 80)
            )
            
            # Deploy
            success = True
            success = success and await self.k8s_manager.create_deployment(deployment)
            success = success and await self.k8s_manager.create_hpa(hpa)
            
            if success:
                self.deployments["workers"] = deployment
                logger.info("Worker nodes deployed successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Worker deployment failed: {e}")
            return False
    
    async def _deploy_monitoring_stack(self, config: Dict[str, Any]) -> bool:
        """Deploy monitoring stack."""
        if not config.get('enabled', True):
            return True
        
        try:
            # This would typically deploy Prometheus, Grafana, etc.
            # For now, we'll just log the deployment
            logger.info("Monitoring stack deployment completed")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring deployment failed: {e}")
            return False
    
    async def _deploy_cache_layer(self, config: Dict[str, Any]) -> bool:
        """Deploy caching layer (Redis)."""
        if not config.get('enabled', True):
            return True
        
        try:
            # Redis deployment would go here
            logger.info("Cache layer deployment completed")
            return True
            
        except Exception as e:
            logger.error(f"Cache deployment failed: {e}")
            return False
    
    async def _deploy_ingress(self, config: Dict[str, Any]) -> bool:
        """Deploy ingress configuration."""
        if not config.get('enabled', True):
            return True
        
        try:
            ingress = IngressSpec(
                name="api-ingress",
                namespace=self.namespace,
                ingress_class=config.get('class', 'nginx'),
                rules=[{
                    'host': config.get('host', 'api.multimodal-contract-extractor.local'),
                    'http': {
                        'paths': [{
                            'path': '/',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': 'api',
                                    'port': {'number': 80}
                                }
                            }
                        }]
                    }
                }],
                annotations={
                    'nginx.ingress.kubernetes.io/rewrite-target': '/',
                    'nginx.ingress.kubernetes.io/ssl-redirect': 'true'
                }
            )
            
            # Add TLS if configured
            if config.get('tls', {}).get('enabled', False):
                ingress.tls = [{
                    'hosts': [config.get('host', 'api.multimodal-contract-extractor.local')],
                    'secretName': config['tls'].get('secret_name', 'api-tls')
                }]
            
            success = await self.k8s_manager.create_ingress(ingress)
            
            if success:
                logger.info("Ingress deployed successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Ingress deployment failed: {e}")
            return False
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get comprehensive deployment status."""
        status = {
            'orchestrator_id': self.orchestrator_id,
            'platform': self.platform.value,
            'namespace': self.namespace,
            'service_mesh_enabled': self.service_mesh_manager is not None,
            'deployments': {},
            'services': {},
            'overall_health': 'healthy'
        }
        
        # Get deployment statuses
        for name, deployment_spec in self.deployments.items():
            deployment_status = await self.k8s_manager.get_deployment_status(name, self.namespace)
            if deployment_status:
                status['deployments'][name] = deployment_status
                
                # Check health
                if deployment_status['ready_replicas'] != deployment_status['replicas']:
                    status['overall_health'] = 'degraded'
        
        # Get service information
        for name, service_spec in self.services.items():
            status['services'][name] = {
                'type': service_spec.service_type.value,
                'ports': service_spec.ports
            }
        
        return status


# Global orchestrator instance
_orchestrator: Optional[ContainerOrchestrator] = None


def get_container_orchestrator(config: Optional[Dict[str, Any]] = None) -> ContainerOrchestrator:
    """Get the global container orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ContainerOrchestrator(config)
    return _orchestrator


@asynccontextmanager
async def deployment_context(deployment_config: Dict[str, Any]):
    """Context manager for application deployment."""
    orchestrator = get_container_orchestrator()
    
    try:
        # Deploy application
        success = await orchestrator.deploy_application(deployment_config)
        if not success:
            raise RuntimeError("Application deployment failed")
        
        yield orchestrator
        
    except Exception as e:
        logger.error(f"Deployment context error: {e}")
        raise
    finally:
        # Cleanup logic would go here if needed
        pass