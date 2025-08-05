"""
Enterprise integration features for Generation 3 scaling.

This module provides enterprise SSO integration, API gateway patterns,
microservices architecture preparation, and cloud-native deployment support.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

import jwt

logger = logging.getLogger(__name__)


class AuthProvider(Enum):
    """Supported authentication providers."""
    OAUTH2 = "oauth2"
    SAML = "saml"
    LDAP = "ldap"
    OPENID_CONNECT = "openid_connect"
    AZURE_AD = "azure_ad"
    GOOGLE_WORKSPACE = "google_workspace"
    OKTA = "okta"
    JWT_CUSTOM = "jwt_custom"


class APIGatewayFeature(Enum):
    """API Gateway features."""
    RATE_LIMITING = "rate_limiting"
    LOAD_BALANCING = "load_balancing"
    REQUEST_ROUTING = "request_routing"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    REQUEST_TRANSFORMATION = "request_transformation"
    RESPONSE_TRANSFORMATION = "response_transformation"
    LOGGING = "logging"
    METRICS = "metrics"
    CIRCUIT_BREAKER = "circuit_breaker"


class ServiceType(Enum):
    """Microservice types."""
    API_GATEWAY = "api_gateway"
    DOCUMENT_PROCESSOR = "document_processor"
    OCR_SERVICE = "ocr_service"
    CLASSIFICATION_SERVICE = "classification_service"
    CACHING_SERVICE = "caching_service"
    NOTIFICATION_SERVICE = "notification_service"
    AUTHENTICATION_SERVICE = "authentication_service"
    ANALYTICS_SERVICE = "analytics_service"


@dataclass
class SSOConfiguration:
    """SSO configuration."""

    provider: AuthProvider
    provider_url: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: List[str] = field(default_factory=list)
    additional_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding sensitive data)."""
        data = asdict(self)
        data['provider'] = self.provider.value
        data.pop('client_secret', None)  # Don't expose secrets
        return data


@dataclass
class JWTToken:
    """JWT token representation."""

    token: str
    payload: Dict[str, Any]
    header: Dict[str, Any]
    expires_at: float
    issued_at: float

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return time.time() > self.expires_at

    @property
    def time_to_expiry(self) -> float:
        """Get time until expiry in seconds."""
        return max(0, self.expires_at - time.time())


class SSOProvider(ABC):
    """Abstract SSO provider interface."""

    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate user with provider."""
        pass

    @abstractmethod
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate authentication token."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh authentication token."""
        pass

    @abstractmethod
    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from token."""
        pass


class OAuth2Provider(SSOProvider):
    """OAuth2 authentication provider."""

    def __init__(self, config: SSOConfiguration):
        self.config = config

    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate using OAuth2 flow."""
        # This would implement actual OAuth2 authentication
        # For now, return mock authentication

        username = credentials.get('username')
        password = credentials.get('password')

        if not username or not password:
            return None

        # Mock authentication - replace with actual OAuth2 flow
        user_info = {
            'user_id': str(uuid4()),
            'username': username,
            'email': f"{username}@example.com",
            'roles': ['user'],
            'provider': self.config.provider.value
        }

        # Generate JWT token
        token = self._generate_jwt_token(user_info)

        return {
            'access_token': token.token,
            'token_type': 'Bearer',
            'expires_in': int(token.time_to_expiry),
            'user_info': user_info
        }

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate OAuth2 token."""
        try:
            jwt_token = self._decode_jwt_token(token)

            if jwt_token.is_expired:
                return None

            return jwt_token.payload

        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh OAuth2 token."""
        # Mock implementation - replace with actual refresh logic
        return await self.authenticate({'username': 'refreshed_user', 'password': 'dummy'})

    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user info from OAuth2 token."""
        payload = await self.validate_token(token)

        if not payload:
            return None

        return {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'email': payload.get('email'),
            'roles': payload.get('roles', [])
        }

    def _generate_jwt_token(self, user_info: Dict[str, Any]) -> JWTToken:
        """Generate JWT token for user."""
        now = time.time()
        expires_in = 3600  # 1 hour

        payload = {
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'email': user_info['email'],
            'roles': user_info['roles'],
            'iat': now,
            'exp': now + expires_in,
            'iss': 'multimodal-contract-extractor',
            'aud': 'mce-api'
        }

        # Use a secret key (in production, this should be configurable)
        secret_key = self.config.client_secret or 'default-secret-key'

        token = jwt.encode(payload, secret_key, algorithm='HS256')

        return JWTToken(
            token=token,
            payload=payload,
            header={'alg': 'HS256', 'typ': 'JWT'},
            expires_at=now + expires_in,
            issued_at=now
        )

    def _decode_jwt_token(self, token: str) -> JWTToken:
        """Decode JWT token."""
        secret_key = self.config.client_secret or 'default-secret-key'

        # Decode header without verification to get algorithm info
        header = jwt.get_unverified_header(token)

        # Decode and verify payload
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])

        return JWTToken(
            token=token,
            payload=payload,
            header=header,
            expires_at=payload.get('exp', time.time()),
            issued_at=payload.get('iat', time.time())
        )


class SAMLProvider(SSOProvider):
    """SAML authentication provider."""

    def __init__(self, config: SSOConfiguration):
        self.config = config

    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate using SAML."""
        # Mock SAML implementation
        return {
            'access_token': 'saml-token',
            'token_type': 'SAML',
            'expires_in': 3600,
            'user_info': {
                'user_id': str(uuid4()),
                'username': credentials.get('username', 'saml_user'),
                'provider': 'saml'
            }
        }

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate SAML token."""
        # Mock validation
        if token.startswith('saml-'):
            return {'valid': True, 'provider': 'saml'}
        return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh SAML token."""
        return None  # SAML doesn't typically support refresh

    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user info from SAML token."""
        if await self.validate_token(token):
            return {'username': 'saml_user', 'provider': 'saml'}
        return None


class SSOManager:
    """Single Sign-On management system."""

    def __init__(self):
        self._providers: Dict[AuthProvider, SSOProvider] = {}
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        self._session_timeout = 3600  # 1 hour

    def register_provider(self, provider: SSOProvider, auth_type: AuthProvider) -> None:
        """Register an SSO provider."""
        self._providers[auth_type] = provider
        logger.info(f"Registered SSO provider: {auth_type.value}")

    async def authenticate(
        self,
        provider_type: AuthProvider,
        credentials: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with specified provider."""
        if provider_type not in self._providers:
            logger.error(f"SSO provider not configured: {provider_type.value}")
            return None

        provider = self._providers[provider_type]

        try:
            auth_result = await provider.authenticate(credentials)

            if auth_result:
                # Create session
                session_id = str(uuid4())
                self._active_sessions[session_id] = {
                    'user_info': auth_result.get('user_info', {}),
                    'provider': provider_type.value,
                    'created_at': time.time(),
                    'last_accessed': time.time(),
                    'access_token': auth_result.get('access_token')
                }

                auth_result['session_id'] = session_id

                logger.info(f"User authenticated via {provider_type.value}: {auth_result.get('user_info', {}).get('username')}")

            return auth_result

        except Exception as e:
            logger.error(f"Authentication failed with {provider_type.value}: {e}")
            return None

    async def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate user session."""
        if session_id not in self._active_sessions:
            return None

        session = self._active_sessions[session_id]

        # Check session timeout
        if time.time() - session['last_accessed'] > self._session_timeout:
            del self._active_sessions[session_id]
            return None

        # Update last accessed time
        session['last_accessed'] = time.time()

        return session

    async def logout(self, session_id: str) -> bool:
        """Logout user session."""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            logger.info(f"User session logged out: {session_id}")
            return True
        return False

    def get_active_sessions_count(self) -> int:
        """Get count of active sessions."""
        return len(self._active_sessions)


@dataclass
class APIRoute:
    """API route definition."""

    path: str
    method: str
    handler: Callable
    auth_required: bool = True
    rate_limit: Optional[int] = None  # Requests per minute
    roles_required: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitRule:
    """Rate limiting rule."""

    requests_per_minute: int
    burst_limit: int
    key_generator: Callable[[Dict[str, Any]], str]  # Function to generate rate limit key

    def __post_init__(self):
        if self.burst_limit < self.requests_per_minute:
            self.burst_limit = self.requests_per_minute


class APIGateway:
    """API Gateway implementation."""

    def __init__(self, sso_manager: SSOManager):
        self.sso_manager = sso_manager
        self._routes: Dict[str, APIRoute] = {}
        self._rate_limits: Dict[str, RateLimitRule] = {}
        self._request_counts: Dict[str, List[float]] = {}  # Track request timestamps
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # Gateway features configuration
        self._features_enabled: Set[APIGatewayFeature] = {
            APIGatewayFeature.AUTHENTICATION,
            APIGatewayFeature.RATE_LIMITING,
            APIGatewayFeature.LOGGING
        }

    def enable_feature(self, feature: APIGatewayFeature) -> None:
        """Enable API Gateway feature."""
        self._features_enabled.add(feature)
        logger.info(f"API Gateway feature enabled: {feature.value}")

    def disable_feature(self, feature: APIGatewayFeature) -> None:
        """Disable API Gateway feature."""
        self._features_enabled.discard(feature)
        logger.info(f"API Gateway feature disabled: {feature.value}")

    def register_route(self, route: APIRoute) -> None:
        """Register API route."""
        route_key = f"{route.method}:{route.path}"
        self._routes[route_key] = route
        logger.info(f"API route registered: {route_key}")

    def set_rate_limit(self, path_pattern: str, rule: RateLimitRule) -> None:
        """Set rate limiting rule for path pattern."""
        self._rate_limits[path_pattern] = rule
        logger.info(f"Rate limit set for {path_pattern}: {rule.requests_per_minute} req/min")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming API request through gateway."""
        request_id = str(uuid4())
        start_time = time.time()

        try:
            # Log request if logging enabled
            if APIGatewayFeature.LOGGING in self._features_enabled:
                logger.info(f"API Request [{request_id}]: {request.get('method')} {request.get('path')}")

            # Find matching route
            route = self._find_route(request)
            if not route:
                return self._error_response(404, "Route not found", request_id)

            # Check authentication
            if (APIGatewayFeature.AUTHENTICATION in self._features_enabled and
                route.auth_required):

                auth_result = await self._authenticate_request(request)
                if not auth_result['success']:
                    return self._error_response(401, auth_result['message'], request_id)

                request['user'] = auth_result['user']

            # Check authorization (roles)
            if route.roles_required and 'user' in request:
                user_roles = request['user'].get('roles', [])
                if not any(role in user_roles for role in route.roles_required):
                    return self._error_response(403, "Insufficient permissions", request_id)

            # Check rate limits
            if APIGatewayFeature.RATE_LIMITING in self._features_enabled:
                rate_limit_result = await self._check_rate_limit(request, route)
                if not rate_limit_result['allowed']:
                    return self._error_response(429, "Rate limit exceeded", request_id)

            # Check circuit breaker
            if APIGatewayFeature.CIRCUIT_BREAKER in self._features_enabled:
                circuit_check = self._check_circuit_breaker(route.path)
                if not circuit_check['allowed']:
                    return self._error_response(503, "Service temporarily unavailable", request_id)

            # Transform request if enabled
            if APIGatewayFeature.REQUEST_TRANSFORMATION in self._features_enabled:
                request = await self._transform_request(request, route)

            # Call route handler
            try:
                response = await route.handler(request)

                # Update circuit breaker on success
                if APIGatewayFeature.CIRCUIT_BREAKER in self._features_enabled:
                    self._update_circuit_breaker(route.path, success=True)

            except Exception as e:
                logger.error(f"Route handler failed [{request_id}]: {e}")

                # Update circuit breaker on failure
                if APIGatewayFeature.CIRCUIT_BREAKER in self._features_enabled:
                    self._update_circuit_breaker(route.path, success=False)

                return self._error_response(500, "Internal server error", request_id)

            # Transform response if enabled
            if APIGatewayFeature.RESPONSE_TRANSFORMATION in self._features_enabled:
                response = await self._transform_response(response, route)

            # Add gateway metadata
            response['_gateway'] = {
                'request_id': request_id,
                'processing_time': time.time() - start_time,
                'route': f"{route.method}:{route.path}"
            }

            return response

        except Exception as e:
            logger.error(f"API Gateway error [{request_id}]: {e}")
            return self._error_response(500, "Gateway error", request_id)

    def _find_route(self, request: Dict[str, Any]) -> Optional[APIRoute]:
        """Find matching route for request."""
        method = request.get('method', 'GET')
        path = request.get('path', '/')

        route_key = f"{method}:{path}"

        return self._routes.get(route_key)

    async def _authenticate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate request."""
        auth_header = request.get('headers', {}).get('Authorization', '')

        if not auth_header:
            return {'success': False, 'message': 'Authorization header missing'}

        if not auth_header.startswith('Bearer '):
            return {'success': False, 'message': 'Invalid authorization format'}

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        # Try to validate token with each provider
        for provider in self.sso_manager._providers.values():
            try:
                user_info = await provider.get_user_info(token)
                if user_info:
                    return {'success': True, 'user': user_info}
            except Exception:
                continue

        return {'success': False, 'message': 'Invalid or expired token'}

    async def _check_rate_limit(self, request: Dict[str, Any], route: APIRoute) -> Dict[str, Any]:
        """Check rate limiting."""
        # Find applicable rate limit rule
        rate_limit_rule = None

        for pattern, rule in self._rate_limits.items():
            if pattern in route.path or pattern == '*':
                rate_limit_rule = rule
                break

        # Check route-specific rate limit
        if route.rate_limit:
            rate_limit_rule = RateLimitRule(
                requests_per_minute=route.rate_limit,
                burst_limit=route.rate_limit * 2,
                key_generator=lambda r: r.get('client_ip', 'unknown')
            )

        if not rate_limit_rule:
            return {'allowed': True}

        # Generate rate limit key
        rate_key = rate_limit_rule.key_generator(request)

        # Check current request count
        now = time.time()
        minute_ago = now - 60

        if rate_key not in self._request_counts:
            self._request_counts[rate_key] = []

        # Remove old requests
        self._request_counts[rate_key] = [
            timestamp for timestamp in self._request_counts[rate_key]
            if timestamp > minute_ago
        ]

        # Check limits
        current_count = len(self._request_counts[rate_key])

        if current_count >= rate_limit_rule.requests_per_minute:
            return {'allowed': False, 'message': 'Rate limit exceeded'}

        # Record this request
        self._request_counts[rate_key].append(now)

        return {'allowed': True}

    def _check_circuit_breaker(self, path: str) -> Dict[str, Any]:
        """Check circuit breaker status."""
        if path not in self._circuit_breakers:
            self._circuit_breakers[path] = {
                'state': 'closed',  # closed, open, half-open
                'failure_count': 0,
                'last_failure_time': 0,
                'next_attempt_time': 0
            }

        breaker = self._circuit_breakers[path]
        now = time.time()

        if breaker['state'] == 'open':
            if now < breaker['next_attempt_time']:
                return {'allowed': False, 'message': 'Circuit breaker open'}
            else:
                # Transition to half-open
                breaker['state'] = 'half-open'
                return {'allowed': True}

        return {'allowed': True}

    def _update_circuit_breaker(self, path: str, success: bool) -> None:
        """Update circuit breaker state."""
        if path not in self._circuit_breakers:
            return

        breaker = self._circuit_breakers[path]
        now = time.time()

        if success:
            if breaker['state'] == 'half-open':
                breaker['state'] = 'closed'
            breaker['failure_count'] = 0
        else:
            breaker['failure_count'] += 1
            breaker['last_failure_time'] = now

            # Trip circuit breaker after 5 failures
            if breaker['failure_count'] >= 5:
                breaker['state'] = 'open'
                breaker['next_attempt_time'] = now + 60  # Try again in 1 minute

    async def _transform_request(self, request: Dict[str, Any], route: APIRoute) -> Dict[str, Any]:
        """Transform request (placeholder for custom transformations)."""
        return request

    async def _transform_response(self, response: Dict[str, Any], route: APIRoute) -> Dict[str, Any]:
        """Transform response (placeholder for custom transformations)."""
        return response

    def _error_response(self, status_code: int, message: str, request_id: str) -> Dict[str, Any]:
        """Generate error response."""
        return {
            'success': False,
            'error': {
                'code': status_code,
                'message': message,
                'request_id': request_id,
                'timestamp': time.time()
            }
        }

    def get_gateway_stats(self) -> Dict[str, Any]:
        """Get API Gateway statistics."""
        return {
            'routes_registered': len(self._routes),
            'rate_limits_active': len(self._rate_limits),
            'circuit_breakers': {
                path: {
                    'state': breaker['state'],
                    'failure_count': breaker['failure_count']
                }
                for path, breaker in self._circuit_breakers.items()
            },
            'features_enabled': [f.value for f in self._features_enabled],
            'active_rate_limit_keys': len(self._request_counts)
        }


@dataclass
class ServiceRegistry:
    """Service registry for microservices."""

    service_name: str
    service_type: ServiceType
    version: str
    host: str
    port: int
    health_check_url: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)

    @property
    def is_healthy(self) -> bool:
        """Check if service is healthy based on heartbeat."""
        return time.time() - self.last_heartbeat < 30  # 30 seconds timeout

    @property
    def service_url(self) -> str:
        """Get service URL."""
        return f"http://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['service_type'] = self.service_type.value
        data['is_healthy'] = self.is_healthy
        return data


class MicroservicesManager:
    """Microservices architecture management."""

    def __init__(self):
        self._services: Dict[str, ServiceRegistry] = {}
        self._service_dependencies: Dict[str, List[str]] = {}
        self._load_balancer_state: Dict[str, int] = {}  # Round-robin state

    def register_service(self, service: ServiceRegistry) -> None:
        """Register a microservice."""
        service_key = f"{service.service_name}:{service.version}"
        self._services[service_key] = service

        logger.info(f"Microservice registered: {service_key} at {service.service_url}")

    def unregister_service(self, service_name: str, version: str) -> bool:
        """Unregister a microservice."""
        service_key = f"{service_name}:{version}"

        if service_key in self._services:
            del self._services[service_key]
            logger.info(f"Microservice unregistered: {service_key}")
            return True

        return False

    def heartbeat(self, service_name: str, version: str) -> bool:
        """Update service heartbeat."""
        service_key = f"{service_name}:{version}"

        if service_key in self._services:
            self._services[service_key].last_heartbeat = time.time()
            return True

        return False

    def discover_service(self, service_name: str, version: Optional[str] = None) -> Optional[ServiceRegistry]:
        """Discover a service instance."""
        if version:
            service_key = f"{service_name}:{version}"
            return self._services.get(service_key)

        # Find any version of the service
        matching_services = [
            service for key, service in self._services.items()
            if key.startswith(f"{service_name}:")
        ]

        if matching_services:
            # Return healthy service if available
            healthy_services = [s for s in matching_services if s.is_healthy]
            if healthy_services:
                return healthy_services[0]
            else:
                return matching_services[0]  # Return any service if none are healthy

        return None

    def discover_services_by_type(self, service_type: ServiceType) -> List[ServiceRegistry]:
        """Discover services by type."""
        return [
            service for service in self._services.values()
            if service.service_type == service_type and service.is_healthy
        ]

    def load_balance_service(self, service_name: str) -> Optional[ServiceRegistry]:
        """Get service instance using round-robin load balancing."""
        matching_services = [
            service for key, service in self._services.items()
            if key.startswith(f"{service_name}:") and service.is_healthy
        ]

        if not matching_services:
            return None

        # Round-robin load balancing
        if service_name not in self._load_balancer_state:
            self._load_balancer_state[service_name] = 0

        index = self._load_balancer_state[service_name] % len(matching_services)
        self._load_balancer_state[service_name] += 1

        return matching_services[index]

    def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services."""
        healthy_count = sum(1 for service in self._services.values() if service.is_healthy)

        return {
            'total_services': len(self._services),
            'healthy_services': healthy_count,
            'unhealthy_services': len(self._services) - healthy_count,
            'services': [service.to_dict() for service in self._services.values()]
        }


class EnterpriseIntegrationManager:
    """Main enterprise integration manager."""

    def __init__(self):
        self.sso_manager = SSOManager()
        self.api_gateway = APIGateway(self.sso_manager)
        self.microservices_manager = MicroservicesManager()
        self._initialized = False

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize enterprise integration."""
        if self._initialized:
            return

        # Configure SSO providers
        sso_config = config.get('sso', {})
        for provider_config in sso_config.get('providers', []):
            self._setup_sso_provider(provider_config)

        # Configure API Gateway
        gateway_config = config.get('api_gateway', {})
        self._setup_api_gateway(gateway_config)

        # Register microservices
        services_config = config.get('microservices', {})
        for service_config in services_config.get('services', []):
            self._register_microservice(service_config)

        self._initialized = True
        logger.info("Enterprise integration initialized")

    def _setup_sso_provider(self, config: Dict[str, Any]) -> None:
        """Setup SSO provider from configuration."""
        provider_type = AuthProvider(config['type'])

        sso_config = SSOConfiguration(
            provider=provider_type,
            provider_url=config['provider_url'],
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            redirect_uri=config['redirect_uri'],
            scopes=config.get('scopes', []),
            additional_config=config.get('additional_config', {})
        )

        if provider_type == AuthProvider.OAUTH2:
            provider = OAuth2Provider(sso_config)
        elif provider_type == AuthProvider.SAML:
            provider = SAMLProvider(sso_config)
        else:
            logger.warning(f"Unsupported SSO provider type: {provider_type.value}")
            return

        self.sso_manager.register_provider(provider, provider_type)

    def _setup_api_gateway(self, config: Dict[str, Any]) -> None:
        """Setup API Gateway from configuration."""
        # Enable features
        for feature_name in config.get('features', []):
            try:
                feature = APIGatewayFeature(feature_name)
                self.api_gateway.enable_feature(feature)
            except ValueError:
                logger.warning(f"Unknown API Gateway feature: {feature_name}")

        # Setup rate limits
        for rate_limit_config in config.get('rate_limits', []):
            rule = RateLimitRule(
                requests_per_minute=rate_limit_config['requests_per_minute'],
                burst_limit=rate_limit_config.get('burst_limit', rate_limit_config['requests_per_minute']),
                key_generator=lambda r: r.get('client_ip', 'unknown')  # Default key generator
            )

            self.api_gateway.set_rate_limit(rate_limit_config['path_pattern'], rule)

    def _register_microservice(self, config: Dict[str, Any]) -> None:
        """Register microservice from configuration."""
        service = ServiceRegistry(
            service_name=config['service_name'],
            service_type=ServiceType(config['service_type']),
            version=config['version'],
            host=config['host'],
            port=config['port'],
            health_check_url=config['health_check_url'],
            metadata=config.get('metadata', {})
        )

        self.microservices_manager.register_service(service)

    def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status."""
        return {
            'initialized': self._initialized,
            'sso': {
                'providers_registered': len(self.sso_manager._providers),
                'active_sessions': self.sso_manager.get_active_sessions_count()
            },
            'api_gateway': self.api_gateway.get_gateway_stats(),
            'microservices': self.microservices_manager.get_service_health()
        }


# Global enterprise integration manager
_integration_manager: Optional[EnterpriseIntegrationManager] = None


def get_enterprise_integration(config: Optional[Dict[str, Any]] = None) -> EnterpriseIntegrationManager:
    """Get global enterprise integration manager."""
    global _integration_manager

    if _integration_manager is None:
        _integration_manager = EnterpriseIntegrationManager()

        if config:
            _integration_manager.initialize(config)

    return _integration_manager
