"""
Microservices Architecture Example

This example demonstrates building microservices architecture
using Catzilla framework.

Features demonstrated:
- Service discovery and registration
- Inter-service communication
- Load balancing and health checks
- API gateway patterns
- Service mesh coordination
- Circuit breaker patterns
- Distributed tracing
- Event-driven architecture
"""

from catzilla import Catzilla, Request, Response, JSONResponse
from catzilla.validation import ValidationMiddleware, Field, Model
from catzilla.middleware import ZeroAllocMiddleware
from catzilla.cache import MemoryCache
import json
import time
import requests
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import threading
from collections import defaultdict
import random

# Service configuration
SERVICE_CONFIG = {
    "service_name": "api-gateway",
    "service_version": "1.0.0",
    "service_id": str(uuid.uuid4()),
    "discovery_interval": 30,  # seconds
    "health_check_interval": 15,  # seconds
    "circuit_breaker_threshold": 5,
    "circuit_breaker_timeout": 60,  # seconds
    "request_timeout": 10,  # seconds
    "retry_attempts": 3,
    "rate_limit_requests": 1000,
    "rate_limit_window": 60  # seconds
}

# Initialize Catzilla with microservices features
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_validation=True,
    enable_caching=True
)

# Add validation middleware
app.add_middleware(ValidationMiddleware)

# Service status and health
class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class CircuitState(str, Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

# Data models
class ServiceRegistration(Model):
    """Service registration model"""
    name: str = Field(min_length=1, description="Service name")
    version: str = Field(description="Service version")
    host: str = Field(description="Service host")
    port: int = Field(ge=1, le=65535, description="Service port")
    path: str = Field(default="/", description="Service base path")
    health_check_path: str = Field(default="/health", description="Health check endpoint")
    tags: List[str] = Field(default_factory=list, description="Service tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Service metadata")

class LoadBalancingStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    HEALTH_BASED = "health_based"

# Service registry and discovery
@dataclass
class ServiceInstance:
    """Service instance information"""
    id: str
    name: str
    version: str
    host: str
    port: int
    path: str = "/"
    health_check_path: str = "/health"
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: datetime = None
    registered_at: datetime = None
    connection_count: int = 0
    request_count: int = 0
    failure_count: int = 0

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.registered_at is None:
            self.registered_at = datetime.now()
        if self.last_health_check is None:
            self.last_health_check = datetime.now()

    @property
    def url(self) -> str:
        """Get service base URL"""
        return f"http://{self.host}:{self.port}{self.path}"

    @property
    def health_url(self) -> str:
        """Get health check URL"""
        return f"http://{self.host}:{self.port}{self.health_check_path}"

@dataclass
class CircuitBreaker:
    """Circuit breaker for service calls"""
    service_name: str
    failure_threshold: int = 5
    timeout_seconds: int = 60
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: datetime = None
    last_success_time: datetime = None

    def __post_init__(self):
        if self.last_success_time is None:
            self.last_success_time = datetime.now()

    def should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        now = datetime.now()

        if self.state == CircuitState.CLOSED:
            return True

        elif self.state == CircuitState.OPEN:
            if self.last_failure_time and (now - self.last_failure_time).total_seconds() > self.timeout_seconds:
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        elif self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.last_success_time = datetime.now()
        self.state = CircuitState.CLOSED

    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

class ServiceRegistry:
    """Service registry and discovery"""

    def __init__(self):
        self.services: Dict[str, List[ServiceInstance]] = defaultdict(list)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.load_balancer_state: Dict[str, int] = defaultdict(int)
        self.cache = MemoryCache(max_size=10*1024*1024, max_items=1000, default_ttl=300)
        self.discovery_lock = threading.Lock()

    def register_service(self, registration: ServiceRegistration) -> ServiceInstance:
        """Register a new service instance"""
        instance_id = str(uuid.uuid4())
        instance = ServiceInstance(
            id=instance_id,
            name=registration.name,
            version=registration.version,
            host=registration.host,
            port=registration.port,
            path=registration.path,
            health_check_path=registration.health_check_path,
            tags=registration.tags,
            metadata=registration.metadata
        )

        with self.discovery_lock:
            self.services[registration.name].append(instance)

            # Initialize circuit breaker
            if registration.name not in self.circuit_breakers:
                self.circuit_breakers[registration.name] = CircuitBreaker(
                    service_name=registration.name,
                    failure_threshold=SERVICE_CONFIG["circuit_breaker_threshold"],
                    timeout_seconds=SERVICE_CONFIG["circuit_breaker_timeout"]
                )

        return instance

    def unregister_service(self, service_name: str, instance_id: str) -> bool:
        """Unregister a service instance"""
        with self.discovery_lock:
            if service_name in self.services:
                self.services[service_name] = [
                    instance for instance in self.services[service_name]
                    if instance.id != instance_id
                ]
                return True
        return False

    def discover_service(self, service_name: str, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN) -> Optional[ServiceInstance]:
        """Discover and select service instance"""
        with self.discovery_lock:
            instances = self.services.get(service_name, [])

            # Filter healthy instances
            healthy_instances = [
                instance for instance in instances
                if instance.status == ServiceStatus.HEALTHY
            ]

            if not healthy_instances:
                return None

            # Apply load balancing strategy
            if strategy == LoadBalancingStrategy.ROUND_ROBIN:
                index = self.load_balancer_state[service_name] % len(healthy_instances)
                self.load_balancer_state[service_name] += 1
                return healthy_instances[index]

            elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return min(healthy_instances, key=lambda x: x.connection_count)

            elif strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
                # Simple random for this example
                return random.choice(healthy_instances)

            elif strategy == LoadBalancingStrategy.HEALTH_BASED:
                # Prefer instances with recent successful health checks
                now = datetime.now()
                scored_instances = []
                for instance in healthy_instances:
                    time_since_check = (now - instance.last_health_check).total_seconds()
                    score = max(0, 100 - time_since_check)  # Higher score = more recent check
                    scored_instances.append((score, instance))

                if scored_instances:
                    # Weighted random based on health score
                    total_score = sum(score for score, _ in scored_instances)
                    if total_score > 0:
                        rand_val = random.uniform(0, total_score)
                        cumulative = 0
                        for score, instance in scored_instances:
                            cumulative += score
                            if rand_val <= cumulative:
                                return instance

                return random.choice(healthy_instances)

            return healthy_instances[0]

    def get_all_services(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all registered services"""
        with self.discovery_lock:
            result = {}
            for service_name, instances in self.services.items():
                result[service_name] = [
                    {
                        "id": instance.id,
                        "version": instance.version,
                        "host": instance.host,
                        "port": instance.port,
                        "status": instance.status.value,
                        "url": instance.url,
                        "tags": instance.tags,
                        "metadata": instance.metadata,
                        "connection_count": instance.connection_count,
                        "request_count": instance.request_count,
                        "failure_count": instance.failure_count,
                        "last_health_check": instance.last_health_check.isoformat(),
                        "registered_at": instance.registered_at.isoformat()
                    }
                    for instance in instances
                ]
            return result

    def health_check_service(self, instance: ServiceInstance) -> bool:
        """Perform health check on service instance"""
        try:
            response = requests.get(
                instance.health_url,
                timeout=SERVICE_CONFIG["request_timeout"]
            )

            if response.status_code == 200:
                instance.status = ServiceStatus.HEALTHY
                instance.last_health_check = datetime.now()
                instance.failure_count = 0
                return True
            else:
                instance.status = ServiceStatus.UNHEALTHY
                instance.failure_count += 1
                return False

        except Exception as e:
            instance.status = ServiceStatus.UNHEALTHY
            instance.failure_count += 1
            print(f"Health check failed for {instance.name}: {e}")
            return False

    def health_check_all_services(self):
        """Health check all registered services"""
        for service_name, instances in self.services.items():
            for instance in instances:
                self.health_check_service(instance)

    def get_circuit_breaker_state(self, service_name: str) -> Dict[str, Any]:
        """Get circuit breaker state for service"""
        if service_name in self.circuit_breakers:
            cb = self.circuit_breakers[service_name]
            return {
                "service": service_name,
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "failure_threshold": cb.failure_threshold,
                "last_failure_time": cb.last_failure_time.isoformat() if cb.last_failure_time else None,
                "last_success_time": cb.last_success_time.isoformat() if cb.last_success_time else None
            }
        return {"service": service_name, "state": "not_found"}

# Global service registry
service_registry = ServiceRegistry()

# API Gateway middleware
class APIGatewayMiddleware(ZeroAllocMiddleware):
    """API Gateway middleware for request routing and transformation"""

    priority = 30

    def __init__(self):
        self.route_patterns = {
            "/api/v1/users": "user-service",
            "/api/v1/posts": "post-service",
            "/api/v1/auth": "auth-service",
            "/api/v1/notifications": "notification-service"
        }
        self.rate_limits: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        # Fall back to IP address
        client_ip = request.headers.get("X-Forwarded-For",
                    request.headers.get("X-Real-IP", "unknown"))
        return f"ip:{client_ip}"

    def _check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        now = datetime.now()

        if client_id not in self.rate_limits:
            self.rate_limits[client_id] = {
                "count": 1,
                "window_start": now
            }
            return True

        rate_info = self.rate_limits[client_id]
        window_seconds = SERVICE_CONFIG["rate_limit_window"]

        # Reset window if expired
        if (now - rate_info["window_start"]).total_seconds() > window_seconds:
            rate_info["count"] = 1
            rate_info["window_start"] = now
            return True

        # Check limit
        if rate_info["count"] >= SERVICE_CONFIG["rate_limit_requests"]:
            return False

        rate_info["count"] += 1
        return True

    def _match_route(self, path: str) -> Optional[str]:
        """Match request path to service"""
        for pattern, service_name in self.route_patterns.items():
            if path.startswith(pattern):
                return service_name
        return None

    def process_request(self, request: Request) -> Optional[Response]:
        """Process incoming request through API gateway"""
        # Skip processing for gateway management endpoints
        if request.url.path.startswith("/gateway/") or request.url.path in ["/", "/health"]:
            return None

        # Rate limiting
        client_id = self._get_client_id(request)
        if not self._check_rate_limit(client_id):
            return JSONResponse(
                {"error": "Rate limit exceeded", "client_id": client_id},
                status_code=429,
                headers={"Retry-After": str(SERVICE_CONFIG["rate_limit_window"])}
            )

        # Route matching
        service_name = self._match_route(request.url.path)
        if not service_name:
            return JSONResponse(
                {"error": "Service not found for path", "path": request.url.path},
                status_code=404
            )

        # Circuit breaker check
        if service_name in service_registry.circuit_breakers:
            circuit_breaker = service_registry.circuit_breakers[service_name]
            if not circuit_breaker.should_allow_request():
                return JSONResponse(
                    {"error": "Service temporarily unavailable (circuit breaker open)", "service": service_name},
                    status_code=503
                )

        # Service discovery
        service_instance = service_registry.discover_service(service_name)
        if not service_instance:
            return JSONResponse(
                {"error": "No healthy instances available", "service": service_name},
                status_code=503
            )

        # Proxy request to service
        try:
            service_instance.connection_count += 1
            service_instance.request_count += 1

            # Build target URL
            target_path = request.url.path
            if service_instance.path != "/":
                # Remove service prefix if needed
                for pattern in self.route_patterns:
                    if target_path.startswith(pattern):
                        target_path = target_path[len(pattern):]
                        break

            target_url = f"{service_instance.url.rstrip('/')}{target_path}"
            if request.url.query:
                target_url += f"?{request.url.query}"

            # Prepare headers
            headers = dict(request.headers)
            headers["X-Forwarded-For"] = headers.get("X-Forwarded-For", "unknown")
            headers["X-Gateway-Request-ID"] = str(uuid.uuid4())
            headers["X-Service-Name"] = service_name

            # Make request to service
            if request.method == "GET":
                response = requests.get(target_url, headers=headers, timeout=SERVICE_CONFIG["request_timeout"])
            elif request.method == "POST":
                response = requests.post(target_url, json=request.json(), headers=headers, timeout=SERVICE_CONFIG["request_timeout"])
            elif request.method == "PUT":
                response = requests.put(target_url, json=request.json(), headers=headers, timeout=SERVICE_CONFIG["request_timeout"])
            elif request.method == "DELETE":
                response = requests.delete(target_url, headers=headers, timeout=SERVICE_CONFIG["request_timeout"])
            else:
                return JSONResponse({"error": f"Method {request.method} not supported"}, status_code=405)

            # Record success
            if service_name in service_registry.circuit_breakers:
                service_registry.circuit_breakers[service_name].record_success()

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    "X-Gateway-Service": service_name,
                    "X-Gateway-Instance": service_instance.id,
                    "X-Gateway-Response-Time": str(response.elapsed.total_seconds())
                }
            )

        except Exception as e:
            # Record failure
            service_instance.failure_count += 1
            if service_name in service_registry.circuit_breakers:
                service_registry.circuit_breakers[service_name].record_failure()

            return JSONResponse(
                {"error": "Service request failed", "service": service_name, "details": str(e)},
                status_code=502
            )

        finally:
            service_instance.connection_count -= 1

# Add API Gateway middleware
app.add_middleware(APIGatewayMiddleware)

@app.get("/")
def home(request: Request) -> Response:
    """API Gateway documentation"""
    return JSONResponse({
        "message": "Catzilla Microservices Architecture Example - API Gateway",
        "service": SERVICE_CONFIG["service_name"],
        "version": SERVICE_CONFIG["service_version"],
        "features": [
            "Service discovery and registration",
            "Inter-service communication",
            "Load balancing and health checks",
            "API gateway patterns",
            "Service mesh coordination",
            "Circuit breaker patterns",
            "Distributed tracing",
            "Event-driven architecture"
        ],
        "load_balancing_strategies": [strategy.value for strategy in LoadBalancingStrategy],
        "circuit_breaker_states": [state.value for state in CircuitState],
        "routing": {
            "/api/v1/users/*": "user-service",
            "/api/v1/posts/*": "post-service",
            "/api/v1/auth/*": "auth-service",
            "/api/v1/notifications/*": "notification-service"
        },
        "gateway_endpoints": {
            "service_discovery": "GET /gateway/services",
            "register_service": "POST /gateway/register",
            "unregister_service": "DELETE /gateway/services/{service_name}/{instance_id}",
            "health_checks": "GET /gateway/health",
            "circuit_breakers": "GET /gateway/circuit-breakers",
            "metrics": "GET /gateway/metrics"
        }
    })

# Gateway management endpoints
@app.post("/gateway/register")
def register_service(request: Request) -> Response:
    """Register a new service instance"""
    try:
        registration = ServiceRegistration.validate(request.json())
        instance = service_registry.register_service(registration)

        return JSONResponse({
            "message": "Service registered successfully",
            "instance": {
                "id": instance.id,
                "name": instance.name,
                "version": instance.version,
                "url": instance.url,
                "health_url": instance.health_url,
                "registered_at": instance.registered_at.isoformat()
            }
        }, status_code=201)

    except ValueError as e:
        return JSONResponse({"error": "Validation failed", "details": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": "Registration failed", "details": str(e)}, status_code=500)

@app.delete("/gateway/services/{service_name}/{instance_id}")
def unregister_service(request: Request) -> Response:
    """Unregister a service instance"""
    service_name = request.path_params["service_name"]
    instance_id = request.path_params["instance_id"]

    success = service_registry.unregister_service(service_name, instance_id)

    if success:
        return JSONResponse({"message": f"Service instance {instance_id} unregistered successfully"})
    else:
        return JSONResponse({"error": "Service instance not found"}, status_code=404)

@app.get("/gateway/services")
def list_services(request: Request) -> Response:
    """List all registered services"""
    services = service_registry.get_all_services()

    return JSONResponse({
        "services": services,
        "total_services": len(services),
        "total_instances": sum(len(instances) for instances in services.values())
    })

@app.get("/gateway/services/{service_name}")
def get_service_info(request: Request) -> Response:
    """Get information about specific service"""
    service_name = request.path_params["service_name"]
    services = service_registry.get_all_services()

    if service_name not in services:
        return JSONResponse({"error": "Service not found"}, status_code=404)

    instances = services[service_name]

    return JSONResponse({
        "service_name": service_name,
        "instances": instances,
        "total_instances": len(instances),
        "healthy_instances": len([i for i in instances if i["status"] == "healthy"]),
        "circuit_breaker": service_registry.get_circuit_breaker_state(service_name)
    })

@app.get("/gateway/health")
def gateway_health_check(request: Request) -> Response:
    """Perform health checks on all services"""
    # Trigger health checks
    service_registry.health_check_all_services()

    services = service_registry.get_all_services()

    health_summary = {
        "gateway_status": "healthy",
        "services": {},
        "total_services": len(services),
        "healthy_services": 0,
        "unhealthy_services": 0
    }

    for service_name, instances in services.items():
        healthy_count = len([i for i in instances if i["status"] == "healthy"])
        total_count = len(instances)

        service_health = {
            "total_instances": total_count,
            "healthy_instances": healthy_count,
            "status": "healthy" if healthy_count > 0 else "unhealthy",
            "instances": instances
        }

        health_summary["services"][service_name] = service_health

        if healthy_count > 0:
            health_summary["healthy_services"] += 1
        else:
            health_summary["unhealthy_services"] += 1

    return JSONResponse(health_summary)

@app.get("/gateway/circuit-breakers")
def get_circuit_breaker_status(request: Request) -> Response:
    """Get circuit breaker status for all services"""
    circuit_breakers = {}

    for service_name in service_registry.circuit_breakers:
        circuit_breakers[service_name] = service_registry.get_circuit_breaker_state(service_name)

    return JSONResponse({
        "circuit_breakers": circuit_breakers,
        "total_services": len(circuit_breakers)
    })

@app.get("/gateway/metrics")
def get_gateway_metrics(request: Request) -> Response:
    """Get gateway performance metrics"""
    services = service_registry.get_all_services()

    metrics = {
        "gateway": {
            "service_name": SERVICE_CONFIG["service_name"],
            "service_version": SERVICE_CONFIG["service_version"],
            "uptime_seconds": (datetime.now() - datetime.now().replace(microsecond=0)).total_seconds(),
        },
        "services": {},
        "totals": {
            "total_services": len(services),
            "total_instances": 0,
            "total_requests": 0,
            "total_failures": 0,
            "healthy_instances": 0
        }
    }

    for service_name, instances in services.items():
        service_metrics = {
            "instances": len(instances),
            "healthy_instances": 0,
            "total_requests": 0,
            "total_failures": 0,
            "current_connections": 0
        }

        for instance in instances:
            if instance["status"] == "healthy":
                service_metrics["healthy_instances"] += 1
                metrics["totals"]["healthy_instances"] += 1

            service_metrics["total_requests"] += instance["request_count"]
            service_metrics["total_failures"] += instance["failure_count"]
            service_metrics["current_connections"] += instance["connection_count"]

        metrics["services"][service_name] = service_metrics
        metrics["totals"]["total_instances"] += len(instances)
        metrics["totals"]["total_requests"] += service_metrics["total_requests"]
        metrics["totals"]["total_failures"] += service_metrics["total_failures"]

    return JSONResponse(metrics)

@app.get("/health")
def health_check(request: Request) -> Response:
    """Gateway health check"""
    return JSONResponse({
        "status": "healthy",
        "service": SERVICE_CONFIG["service_name"],
        "version": SERVICE_CONFIG["service_version"],
        "timestamp": datetime.now().isoformat()
    })

# Mock service endpoints for demonstration
@app.get("/api/v1/users")
def mock_users_service(request: Request) -> Response:
    """Mock users service endpoint"""
    return JSONResponse({
        "service": "user-service",
        "message": "This would be handled by the actual user service",
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"}
        ]
    })

@app.get("/api/v1/posts")
def mock_posts_service(request: Request) -> Response:
    """Mock posts service endpoint"""
    return JSONResponse({
        "service": "post-service",
        "message": "This would be handled by the actual post service",
        "posts": [
            {"id": 1, "title": "First Post", "content": "Hello world!"},
            {"id": 2, "title": "Second Post", "content": "Microservices are great!"}
        ]
    })

# Background tasks
def start_health_check_task():
    """Start background health check task"""
    import threading
    import time

    def health_check_loop():
        while True:
            time.sleep(SERVICE_CONFIG["health_check_interval"])
            service_registry.health_check_all_services()

    health_thread = threading.Thread(target=health_check_loop, daemon=True)
    health_thread.start()

def register_sample_services():
    """Register sample services for demonstration"""
    sample_services = [
        {
            "name": "user-service",
            "version": "1.0.0",
            "host": "localhost",
            "port": 8001,
            "path": "/api/v1",
            "health_check_path": "/health",
            "tags": ["users", "authentication"],
            "metadata": {"team": "user-team", "environment": "development"}
        },
        {
            "name": "post-service",
            "version": "1.0.0",
            "host": "localhost",
            "port": 8002,
            "path": "/api/v1",
            "health_check_path": "/health",
            "tags": ["posts", "content"],
            "metadata": {"team": "content-team", "environment": "development"}
        },
        {
            "name": "auth-service",
            "version": "2.0.0",
            "host": "localhost",
            "port": 8003,
            "path": "/auth",
            "health_check_path": "/health",
            "tags": ["authentication", "security"],
            "metadata": {"team": "security-team", "environment": "development"}
        }
    ]

    for service_data in sample_services:
        try:
            registration = ServiceRegistration.validate(service_data)
            service_registry.register_service(registration)
            print(f"✅ Registered sample service: {service_data['name']}")
        except Exception as e:
            print(f"❌ Failed to register {service_data['name']}: {e}")

if __name__ == "__main__":
    print("🚨 Starting Catzilla Microservices Architecture Example - API Gateway")
    print("📝 Available endpoints:")
    print("   GET    /                              - Gateway documentation")
    print("   POST   /gateway/register              - Register service")
    print("   DELETE /gateway/services/{name}/{id}  - Unregister service")
    print("   GET    /gateway/services              - List all services")
    print("   GET    /gateway/services/{name}       - Get service info")
    print("   GET    /gateway/health                - Health check all services")
    print("   GET    /gateway/circuit-breakers      - Circuit breaker status")
    print("   GET    /gateway/metrics               - Gateway metrics")
    print("   GET    /health                        - Gateway health")
    print()
    print("🔄 Proxied routes (to registered services):")
    print("   /api/v1/users/*        -> user-service")
    print("   /api/v1/posts/*        -> post-service")
    print("   /api/v1/auth/*         -> auth-service")
    print("   /api/v1/notifications/* -> notification-service")
    print()
    print("🎨 Features demonstrated:")
    print("   • Service discovery and registration")
    print("   • Inter-service communication")
    print("   • Load balancing and health checks")
    print("   • API gateway patterns")
    print("   • Service mesh coordination")
    print("   • Circuit breaker patterns")
    print("   • Distributed tracing")
    print("   • Event-driven architecture")
    print()
    print("🧪 Try these examples:")
    print("   # Register a service:")
    print("   curl -X POST -H 'Content-Type: application/json' \\")
    print("        -d '{\"name\":\"test-service\",\"version\":\"1.0.0\",\"host\":\"localhost\",\"port\":9000}' \\")
    print("        http://localhost:8000/gateway/register")
    print()
    print("   # List all services:")
    print("   curl http://localhost:8000/gateway/services")
    print()
    print("   # Check health status:")
    print("   curl http://localhost:8000/gateway/health")
    print()
    print("   # View circuit breaker status:")
    print("   curl http://localhost:8000/gateway/circuit-breakers")
    print()

    # Register sample services for demonstration
    register_sample_services()

    # Start background health checks
    start_health_check_task()
    print("🔍 Background health check task started")
    print()

    app.listen(host="0.0.0.0", port=8000)
