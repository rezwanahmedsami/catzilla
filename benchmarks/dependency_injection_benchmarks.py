#!/usr/bin/env python3
"""
🚀 Catzilla v0.2.0 - Dependency Injection Performance Benchmarks

This script benchmarks Catzilla's revolutionary dependency injection system
against other popular Python DI frameworks and pure Python implementations.
"""

import time
import statistics
import gc
import tracemalloc
from typing import List, Dict, Any
from dataclasses import dataclass

# Catzilla DI
from catzilla.dependency_injection import DIContainer, AdvancedDIContainer
from catzilla import service, Depends

# Comparison frameworks (install as needed)
try:
    from dependency_injector import containers, providers
    from dependency_injector.wiring import Provide, inject as di_inject
    HAS_DEPENDENCY_INJECTOR = True
except ImportError:
    HAS_DEPENDENCY_INJECTOR = False

try:
    from injector import Injector, inject as injector_inject, singleton
    HAS_INJECTOR = True
except ImportError:
    HAS_INJECTOR = False


@dataclass
class BenchmarkResult:
    """Benchmark result data"""
    framework: str
    operation: str
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    memory_usage_mb: float
    throughput_ops_per_sec: float


class BenchmarkSuite:
    """Comprehensive dependency injection benchmarks"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.warmup_iterations = 100
        self.benchmark_iterations = 1000

    def run_all_benchmarks(self):
        """Run all benchmark suites"""
        print("🚀 Catzilla v0.2.0 - Dependency Injection Benchmarks")
        print("=" * 60)

        self.benchmark_simple_resolution()
        self.benchmark_complex_dependency_chains()
        self.benchmark_hierarchical_containers()
        self.benchmark_factory_patterns()
        self.benchmark_memory_usage()
        self.benchmark_concurrent_access()

        self.print_summary()

    def benchmark_simple_resolution(self):
        """Benchmark simple service resolution"""
        print("\n📊 Simple Service Resolution")
        print("-" * 40)

        # Define test services
        class SimpleService:
            def __init__(self, value: str = "test"):
                self.value = value

        class DependentService:
            def __init__(self, simple: SimpleService):
                self.simple = simple

        # Catzilla DI
        self._benchmark_catzilla_simple(SimpleService, DependentService)

        # Pure Python (baseline)
        self._benchmark_pure_python_simple(SimpleService, DependentService)

        # Other frameworks
        if HAS_DEPENDENCY_INJECTOR:
            self._benchmark_dependency_injector_simple(SimpleService, DependentService)

        if HAS_INJECTOR:
            self._benchmark_injector_simple(SimpleService, DependentService)

    def _benchmark_catzilla_simple(self, SimpleService, DependentService):
        """Benchmark Catzilla DI simple resolution"""
        container = DIContainer()
        container.register("simple", SimpleService, "singleton")
        container.register("dependent",
                          lambda simple: DependentService(simple),
                          "transient", ["simple"])

        # Warmup
        for _ in range(self.warmup_iterations):
            container.resolve("dependent")

        # Benchmark
        times = []
        tracemalloc.start()

        for _ in range(self.benchmark_iterations):
            start = time.perf_counter()
            service = container.resolve("dependent")
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self._record_result("Catzilla DI", "Simple Resolution", times, current)

    def _benchmark_pure_python_simple(self, SimpleService, DependentService):
        """Benchmark pure Python implementation"""
        services = {}

        def register(name, factory, dependencies=None):
            services[name] = {
                'factory': factory,
                'dependencies': dependencies or [],
                'instance': None
            }

        def resolve(name):
            service = services[name]
            if service['instance'] is None:
                deps = {dep: resolve(dep) for dep in service['dependencies']}
                if deps:
                    service['instance'] = service['factory'](**deps)
                else:
                    service['instance'] = service['factory']()
            return service['instance']

        register("simple", SimpleService)
        register("dependent", lambda simple: DependentService(simple), ["simple"])

        # Warmup
        for _ in range(self.warmup_iterations):
            resolve("dependent")

        # Benchmark
        times = []
        tracemalloc.start()

        for _ in range(self.benchmark_iterations):
            start = time.perf_counter()
            service = resolve("dependent")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self._record_result("Pure Python", "Simple Resolution", times, current)

    def benchmark_complex_dependency_chains(self):
        """Benchmark complex dependency resolution"""
        print("\n📊 Complex Dependency Chains (10 levels deep)")
        print("-" * 50)

        # Create 10-level dependency chain
        class ConfigService:
            def __init__(self):
                self.value = "config"

        class DatabaseService:
            def __init__(self, config: ConfigService):
                self.config = config

        class CacheService:
            def __init__(self, config: ConfigService):
                self.config = config

        class UserRepository:
            def __init__(self, db: DatabaseService, cache: CacheService):
                self.db = db
                self.cache = cache

        class AuthService:
            def __init__(self, user_repo: UserRepository):
                self.user_repo = user_repo

        class SessionService:
            def __init__(self, auth: AuthService, cache: CacheService):
                self.auth = auth
                self.cache = cache

        class NotificationService:
            def __init__(self, config: ConfigService):
                self.config = config

        class EmailService:
            def __init__(self, notification: NotificationService):
                self.notification = notification

        class UserService:
            def __init__(self, user_repo: UserRepository, session: SessionService, email: EmailService):
                self.user_repo = user_repo
                self.session = session
                self.email = email

        class APIService:
            def __init__(self, user_service: UserService, auth: AuthService):
                self.user_service = user_service
                self.auth = auth

        # Catzilla DI
        container = DIContainer()
        container.register("config", ConfigService, "singleton")
        container.register("database", lambda config: DatabaseService(config), "singleton", ["config"])
        container.register("cache", lambda config: CacheService(config), "singleton", ["config"])
        container.register("user_repo", lambda db, cache: UserRepository(db, cache), "singleton", ["database", "cache"])
        container.register("auth", lambda user_repo: AuthService(user_repo), "singleton", ["user_repo"])
        container.register("session", lambda auth, cache: SessionService(auth, cache), "singleton", ["auth", "cache"])
        container.register("notification", lambda config: NotificationService(config), "singleton", ["config"])
        container.register("email", lambda notification: EmailService(notification), "singleton", ["notification"])
        container.register("user_service", lambda user_repo, session, email: UserService(user_repo, session, email), "singleton", ["user_repo", "session", "email"])
        container.register("api", lambda user_service, auth: APIService(user_service, auth), "transient", ["user_service", "auth"])

        # Benchmark
        times = []
        tracemalloc.start()

        for _ in range(self.benchmark_iterations):
            start = time.perf_counter()
            service = container.resolve("api")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self._record_result("Catzilla DI", "Complex Chain Resolution", times, current)

    def benchmark_hierarchical_containers(self):
        """Benchmark hierarchical container performance"""
        print("\n📊 Hierarchical Container Resolution")
        print("-" * 40)

        from catzilla.dependency_injection import ContainerConfig

        # Parent container
        parent = AdvancedDIContainer(config=ContainerConfig(
            name="Parent",
            inherit_services=True
        ))
        parent.register("core_service", lambda: "core", "singleton")
        parent.register("shared_service", lambda: "shared", "singleton")

        # Child container
        child = parent.create_child_container(ContainerConfig(
            name="Child",
            inherit_services=True
        ))
        child.register("child_service", lambda core, shared: f"child-{core}-{shared}",
                      "transient", ["core_service", "shared_service"])

        # Benchmark
        times = []
        tracemalloc.start()

        for _ in range(self.benchmark_iterations):
            start = time.perf_counter()
            service = child.resolve("child_service")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self._record_result("Catzilla DI", "Hierarchical Resolution", times, current)

    def benchmark_factory_patterns(self):
        """Benchmark advanced factory patterns"""
        print("\n📊 Advanced Factory Patterns")
        print("-" * 35)

        container = AdvancedDIContainer()

        class ConfigService:
            def __init__(self, env="production"):
                self.env = env

        class DatabaseService:
            def __init__(self, config):
                self.config = config

        # Builder factory
        def config_builder():
            return ConfigService("production")

        def database_factory(config):
            return DatabaseService(config)

        container.register_builder_factory(
            "database_built",
            config_builder,
            database_factory
        )

        # Conditional factory
        def use_redis():
            return True

        def redis_factory():
            return "redis_cache"

        def memory_factory():
            return "memory_cache"

        container.register_conditional_factory(
            "cache",
            use_redis,
            redis_factory,
            memory_factory
        )

        # Benchmark builder factory
        times = []
        for _ in range(self.benchmark_iterations):
            start = time.perf_counter()
            service = container.resolve("database_built")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        self._record_result("Catzilla DI", "Builder Factory", times, 0)

        # Benchmark conditional factory
        times = []
        for _ in range(self.benchmark_iterations):
            start = time.perf_counter()
            service = container.resolve("cache")
            end = time.perf_counter()
            times.append((end - start) * 1000)

        self._record_result("Catzilla DI", "Conditional Factory", times, 0)

    def benchmark_memory_usage(self):
        """Benchmark memory usage patterns"""
        print("\n📊 Memory Usage Comparison")
        print("-" * 30)

        # Large number of services
        container = DIContainer()

        # Register 1000 services
        for i in range(1000):
            container.register(f"service_{i}", lambda: f"instance_{i}", "singleton")

        # Resolve all services
        tracemalloc.start()

        start_time = time.perf_counter()
        for i in range(1000):
            container.resolve(f"service_{i}")
        end_time = time.perf_counter()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / 1000

        result = BenchmarkResult(
            framework="Catzilla DI",
            operation="1000 Service Resolution",
            avg_time_ms=avg_time_ms,
            min_time_ms=avg_time_ms,
            max_time_ms=avg_time_ms,
            memory_usage_mb=current / 1024 / 1024,
            throughput_ops_per_sec=1000 / (total_time_ms / 1000)
        )
        self.results.append(result)

    def benchmark_concurrent_access(self):
        """Benchmark thread safety and concurrent access"""
        print("\n📊 Concurrent Access Performance")
        print("-" * 35)

        import threading
        import concurrent.futures

        container = DIContainer()
        container.register("thread_safe_service", lambda: "thread_safe", "singleton")

        def resolve_service():
            times = []
            for _ in range(100):
                start = time.perf_counter()
                service = container.resolve("thread_safe_service")
                end = time.perf_counter()
                times.append((end - start) * 1000)
            return times

        # Run concurrent resolution
        start_total = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(resolve_service) for _ in range(10)]
            all_times = []
            for future in concurrent.futures.as_completed(futures):
                all_times.extend(future.result())
        end_total = time.perf_counter()

        self._record_result("Catzilla DI", "Concurrent Access", all_times, 0)

    def _record_result(self, framework: str, operation: str, times: List[float], memory_bytes: int):
        """Record benchmark result"""
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        memory_mb = memory_bytes / 1024 / 1024 if memory_bytes > 0 else 0
        throughput = 1000 / avg_time if avg_time > 0 else 0

        result = BenchmarkResult(
            framework=framework,
            operation=operation,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            memory_usage_mb=memory_mb,
            throughput_ops_per_sec=throughput
        )

        self.results.append(result)
        print(f"✅ {framework:15} | {operation:25} | {avg_time:.3f}ms avg | {throughput:.0f} ops/sec")

    def print_summary(self):
        """Print comprehensive benchmark summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE BENCHMARK RESULTS")
        print("=" * 80)

        # Group results by operation
        operations = {}
        for result in self.results:
            if result.operation not in operations:
                operations[result.operation] = []
            operations[result.operation].append(result)

        for operation, results in operations.items():
            print(f"\n🎯 {operation}")
            print("-" * 60)
            print(f"{'Framework':<20} {'Avg Time':<12} {'Throughput':<15} {'Memory':<10}")
            print("-" * 60)

            # Sort by average time (fastest first)
            results.sort(key=lambda x: x.avg_time_ms)

            baseline = results[0].avg_time_ms if results else 1
            for result in results:
                speedup = baseline / result.avg_time_ms if result.avg_time_ms > 0 else 1
                speedup_str = f"({speedup:.1f}x)" if speedup > 1 else ""

                print(f"{result.framework:<20} "
                      f"{result.avg_time_ms:>8.3f}ms {speedup_str:<8} "
                      f"{result.throughput_ops_per_sec:>10.0f}/sec "
                      f"{result.memory_usage_mb:>6.1f}MB")

        # Overall performance summary
        catzilla_results = [r for r in self.results if r.framework == "Catzilla DI"]
        python_results = [r for r in self.results if r.framework == "Pure Python"]

        if catzilla_results and python_results:
            avg_catzilla = statistics.mean([r.avg_time_ms for r in catzilla_results])
            avg_python = statistics.mean([r.avg_time_ms for r in python_results])
            overall_speedup = avg_python / avg_catzilla

            print(f"\n🏆 OVERALL PERFORMANCE SUMMARY")
            print("-" * 40)
            print(f"Catzilla DI Average:    {avg_catzilla:.3f}ms")
            print(f"Pure Python Average:    {avg_python:.3f}ms")
            print(f"Overall Speedup:        {overall_speedup:.1f}x faster")
            print(f"Performance Target:     5-8x faster ✅" if 5 <= overall_speedup <= 8 else
                  f"Performance Target:     5-8x faster ❌")


def main():
    """Run all benchmarks"""
    benchmark = BenchmarkSuite()
    benchmark.run_all_benchmarks()


if __name__ == "__main__":
    main()
