"""
Service Factories Example

This example demonstrates Catzilla's advanced service factory system
for creating configurable and conditional services with DI.

Features demonstrated:
- Service factories (Class, Function, Conditional)
- Factory configuration and parameters
- Conditional service creation based on environment
- Factory registry and management
- Service lifecycle management
"""

from catzilla import (
    Catzilla, Request, Response, JSONResponse,
    FactoryRegistry, ClassFactory, FunctionFactory, ConditionalFactory,
    SingletonFactory, ConfigurableFactory, FactoryConfig,
    create_class_factory, create_function_factory, create_conditional_factory,
    factory, register_service, Depends
)
import os
from typing import Dict, Any, Protocol, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Initialize Catzilla with factory system
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True,
    enable_di=True
)

# Configuration classes
@dataclass
class EmailConfig:
    """Email service configuration"""
    provider: str
    api_key: str
    from_address: str
    rate_limit: int = 100

@dataclass
class StorageConfig:
    """Storage service configuration"""
    provider: str
    bucket: str
    region: str
    max_file_size: int = 10485760  # 10MB

# Service interfaces
class EmailService(ABC):
    """Email service interface"""

    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        pass

class StorageService(ABC):
    """Storage service interface"""

    @abstractmethod
    def upload_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_service_info(self) -> Dict[str, Any]:
        pass

# Concrete implementations
class SMTPEmailService(EmailService):
    """SMTP email service implementation"""

    def __init__(self, config: EmailConfig):
        self.config = config
        self.sent_count = 0
        print(f"📧 SMTP Email Service initialized: {config.provider}")

    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        self.sent_count += 1
        return {
            "provider": "smtp",
            "to": to,
            "subject": subject,
            "message_id": f"smtp_{self.sent_count}",
            "status": "sent",
            "from": self.config.from_address
        }

    def get_service_info(self) -> Dict[str, Any]:
        return {
            "type": "SMTPEmailService",
            "provider": self.config.provider,
            "from_address": self.config.from_address,
            "rate_limit": self.config.rate_limit,
            "sent_count": self.sent_count
        }

class SendGridEmailService(EmailService):
    """SendGrid email service implementation"""

    def __init__(self, config: EmailConfig):
        self.config = config
        self.sent_count = 0
        print(f"📧 SendGrid Email Service initialized: {config.provider}")

    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        self.sent_count += 1
        return {
            "provider": "sendgrid",
            "to": to,
            "subject": subject,
            "message_id": f"sg_{self.sent_count}",
            "status": "sent",
            "api_version": "v3"
        }

    def get_service_info(self) -> Dict[str, Any]:
        return {
            "type": "SendGridEmailService",
            "provider": self.config.provider,
            "api_key": self.config.api_key[:8] + "***",
            "rate_limit": self.config.rate_limit,
            "sent_count": self.sent_count
        }

class LocalStorageService(StorageService):
    """Local file storage service"""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.uploaded_files = []
        print(f"💾 Local Storage Service initialized: {config.provider}")

    def upload_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        file_info = {
            "filename": filename,
            "size": len(content),
            "provider": "local",
            "path": f"/local/storage/{filename}",
            "uploaded_at": "2024-01-15T10:30:00Z"
        }
        self.uploaded_files.append(file_info)
        return file_info

    def get_service_info(self) -> Dict[str, Any]:
        return {
            "type": "LocalStorageService",
            "provider": self.config.provider,
            "max_file_size": self.config.max_file_size,
            "uploaded_count": len(self.uploaded_files)
        }

class S3StorageService(StorageService):
    """AWS S3 storage service"""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.uploaded_files = []
        print(f"☁️  S3 Storage Service initialized: {config.provider}")

    def upload_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        file_info = {
            "filename": filename,
            "size": len(content),
            "provider": "s3",
            "bucket": self.config.bucket,
            "region": self.config.region,
            "url": f"https://{self.config.bucket}.s3.{self.config.region}.amazonaws.com/{filename}",
            "uploaded_at": "2024-01-15T10:30:00Z"
        }
        self.uploaded_files.append(file_info)
        return file_info

    def get_service_info(self) -> Dict[str, Any]:
        return {
            "type": "S3StorageService",
            "provider": self.config.provider,
            "bucket": self.config.bucket,
            "region": self.config.region,
            "max_file_size": self.config.max_file_size,
            "uploaded_count": len(self.uploaded_files)
        }

# Factory functions
def create_email_service(config: EmailConfig) -> EmailService:
    """Factory function to create email service based on configuration"""
    if config.provider == "sendgrid":
        return SendGridEmailService(config)
    else:
        return SMTPEmailService(config)

def create_storage_service(config: StorageConfig) -> StorageService:
    """Factory function to create storage service based on configuration"""
    if config.provider == "s3":
        return S3StorageService(config)
    else:
        return LocalStorageService(config)

# Environment-based service selection
def get_email_config() -> EmailConfig:
    """Get email configuration based on environment"""
    env = os.getenv("ENV", "development")

    if env == "production":
        return EmailConfig(
            provider="sendgrid",
            api_key=os.getenv("SENDGRID_API_KEY", "sg_test_key"),
            from_address="noreply@catzilla.com",
            rate_limit=1000
        )
    else:
        return EmailConfig(
            provider="smtp",
            api_key="smtp_dev_key",
            from_address="dev@catzilla.com",
            rate_limit=10
        )

def get_storage_config() -> StorageConfig:
    """Get storage configuration based on environment"""
    env = os.getenv("ENV", "development")

    if env == "production":
        return StorageConfig(
            provider="s3",
            bucket="catzilla-prod",
            region="us-east-1",
            max_file_size=52428800  # 50MB
        )
    else:
        return StorageConfig(
            provider="local",
            bucket="local-dev",
            region="local",
            max_file_size=10485760  # 10MB
        )

# Setup factories
@app.on_startup
def setup_factories():
    """Setup service factories"""
    factory_registry = app.di_container.factory_registry

    # Register configuration factories
    factory_registry.register("email_config", create_function_factory(get_email_config))
    factory_registry.register("storage_config", create_function_factory(get_storage_config))

    # Register conditional service factories
    email_factory = create_conditional_factory(
        condition=lambda: get_email_config().provider == "sendgrid",
        true_factory=create_class_factory(SendGridEmailService),
        false_factory=create_class_factory(SMTPEmailService)
    )
    factory_registry.register("email_service", email_factory)

    storage_factory = create_conditional_factory(
        condition=lambda: get_storage_config().provider == "s3",
        true_factory=create_class_factory(S3StorageService),
        false_factory=create_class_factory(LocalStorageService)
    )
    factory_registry.register("storage_service", storage_factory)

    # Register as singleton services
    register_service(EmailConfig, factory="email_config", scope="singleton")
    register_service(StorageConfig, factory="storage_config", scope="singleton")
    register_service(EmailService, factory="email_service", scope="singleton")
    register_service(StorageService, factory="storage_service", scope="singleton")

    print("✅ Service factories registered")

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with factory system info"""
    return JSONResponse({
        "message": "Catzilla Service Factories Example",
        "features": [
            "Service factories (Class, Function, Conditional)",
            "Environment-based service selection",
            "Factory configuration and parameters",
            "Factory registry management",
            "Conditional service creation"
        ],
        "environment": os.getenv("ENV", "development"),
        "factory_types": [
            "ClassFactory", "FunctionFactory", "ConditionalFactory",
            "SingletonFactory", "ConfigurableFactory"
        ]
    })

@app.post("/api/email/send")
def send_email(
    request: Request,
    email_service: EmailService = Depends()
) -> Response:
    """Send email using factory-created service"""
    try:
        data = request.json()
        to = data["to"]
        subject = data["subject"]
        body = data["body"]

        result = email_service.send_email(to, subject, body)
        service_info = email_service.get_service_info()

        return JSONResponse({
            "message": "Email sent successfully",
            "result": result,
            "service_info": service_info
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to send email",
            "details": str(e)
        }, status_code=400)

@app.post("/api/storage/upload")
def upload_file(
    request: Request,
    storage_service: StorageService = Depends()
) -> Response:
    """Upload file using factory-created service"""
    try:
        data = request.json()
        filename = data["filename"]
        content = data["content"].encode()  # Simulate file content

        result = storage_service.upload_file(filename, content)
        service_info = storage_service.get_service_info()

        return JSONResponse({
            "message": "File uploaded successfully",
            "result": result,
            "service_info": service_info
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to upload file",
            "details": str(e)
        }, status_code=400)

@app.get("/api/services/info")
def get_services_info(
    request: Request,
    email_service: EmailService = Depends(),
    storage_service: StorageService = Depends(),
    email_config: EmailConfig = Depends(),
    storage_config: StorageConfig = Depends()
) -> Response:
    """Get information about factory-created services"""
    return JSONResponse({
        "services": {
            "email": email_service.get_service_info(),
            "storage": storage_service.get_service_info()
        },
        "configurations": {
            "email": {
                "provider": email_config.provider,
                "from_address": email_config.from_address,
                "rate_limit": email_config.rate_limit
            },
            "storage": {
                "provider": storage_config.provider,
                "bucket": storage_config.bucket,
                "region": storage_config.region,
                "max_file_size": storage_config.max_file_size
            }
        },
        "environment": os.getenv("ENV", "development"),
        "factory_selection": {
            "email": "conditional based on provider",
            "storage": "conditional based on provider"
        }
    })

@app.get("/api/factories/registry")
def get_factory_registry(request: Request) -> Response:
    """Get factory registry information"""
    factory_registry = app.di_container.factory_registry

    return JSONResponse({
        "registered_factories": {
            "email_config": "FunctionFactory(get_email_config)",
            "storage_config": "FunctionFactory(get_storage_config)",
            "email_service": "ConditionalFactory(SendGrid|SMTP)",
            "storage_service": "ConditionalFactory(S3|Local)"
        },
        "factory_types": {
            "ClassFactory": "Creates instances from class constructors",
            "FunctionFactory": "Creates instances from factory functions",
            "ConditionalFactory": "Selects factory based on condition",
            "SingletonFactory": "Ensures single instance creation",
            "ConfigurableFactory": "Creates instances with configuration"
        },
        "environment_conditions": {
            "email": f"Provider: {get_email_config().provider}",
            "storage": f"Provider: {get_storage_config().provider}"
        }
    })

@app.post("/api/environment/switch")
def switch_environment(request: Request) -> Response:
    """Switch environment for testing factory conditions"""
    try:
        data = request.json()
        new_env = data.get("environment", "development")

        # Set environment variable
        os.environ["ENV"] = new_env

        # Get new configurations
        email_config = get_email_config()
        storage_config = get_storage_config()

        return JSONResponse({
            "message": f"Environment switched to {new_env}",
            "new_configurations": {
                "email": {
                    "provider": email_config.provider,
                    "from_address": email_config.from_address
                },
                "storage": {
                    "provider": storage_config.provider,
                    "bucket": storage_config.bucket
                }
            },
            "note": "Restart required for changes to take effect in DI services"
        })

    except Exception as e:
        return JSONResponse({
            "error": "Failed to switch environment",
            "details": str(e)
        }, status_code=400)

@app.get("/factories/examples")
def get_factory_examples(request: Request) -> Response:
    """Get examples for testing service factories"""
    return JSONResponse({
        "examples": {
            "send_email": {
                "url": "/api/email/send",
                "method": "POST",
                "payload": {
                    "to": "user@example.com",
                    "subject": "Factory Test Email",
                    "body": "This email was sent using a factory-created service!"
                }
            },
            "upload_file": {
                "url": "/api/storage/upload",
                "method": "POST",
                "payload": {
                    "filename": "test.txt",
                    "content": "Hello from factory-created storage service!"
                }
            },
            "switch_environment": {
                "url": "/api/environment/switch",
                "method": "POST",
                "payload": {
                    "environment": "production"
                }
            }
        },
        "testing_scenarios": {
            "development": {
                "email": "SMTP service",
                "storage": "Local storage"
            },
            "production": {
                "email": "SendGrid service",
                "storage": "S3 storage"
            }
        },
        "factory_features": [
            "Environment-based service selection",
            "Conditional factory creation",
            "Configuration-driven services",
            "Factory registry management"
        ]
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with factory system status"""
    return JSONResponse({
        "status": "healthy",
        "factory_system": "enabled",
        "framework": "Catzilla v0.2.0",
        "environment": os.getenv("ENV", "development")
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Service Factories Example")
    print("📝 Available endpoints:")
    print("   GET  /                         - Home with factory system info")
    print("   POST /api/email/send           - Send email using factory service")
    print("   POST /api/storage/upload       - Upload file using factory service")
    print("   GET  /api/services/info        - Get factory-created services info")
    print("   GET  /api/factories/registry   - Get factory registry info")
    print("   POST /api/environment/switch   - Switch environment for testing")
    print("   GET  /factories/examples       - Get example requests")
    print("   GET  /health                   - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Service factories (Class, Function, Conditional)")
    print("   • Environment-based service selection")
    print("   • Factory configuration and parameters")
    print("   • Conditional service creation")
    print("   • Factory registry management")
    print()
    print("🧪 Try these examples:")
    print("   curl http://localhost:8000/api/services/info")
    print("   curl -X POST http://localhost:8000/api/email/send \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"to\":\"test@example.com\",\"subject\":\"Test\",\"body\":\"Hello!\"}'")
    print("   curl -X POST http://localhost:8000/api/environment/switch \\")
    print("     -H 'Content-Type: application/json' -d '{\"environment\":\"production\"}'")
    print()

    app.listen(host="0.0.0.0", port=8000)
