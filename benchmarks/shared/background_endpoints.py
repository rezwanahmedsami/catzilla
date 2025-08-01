#!/usr/bin/env python3
"""
Shared background task endpoint definitions for consistent benchmarking across frameworks.

This module defines background task test scenarios that each framework will implement
to ensure fair performance comparisons for background task processing capabilities.
"""

import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta

def get_background_endpoints():
    """
    Returns background task endpoint definitions for benchmarking.
    Each endpoint tests different aspects of background task processing performance.
    """
    return {
        # Single task creation
        "create_computation_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create CPU-intensive computation task",
            "test_data": {
                "task_type": "computation",
                "parameters": {"iterations": 10000},
                "priority": 5,
                "delay_seconds": 0
            }
        },

        "create_io_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create I/O intensive task",
            "test_data": {
                "task_type": "io",
                "parameters": {"file_count": 20, "file_size": 2048},
                "priority": 5,
                "delay_seconds": 0
            }
        },

        "create_network_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create network operation simulation task",
            "test_data": {
                "task_type": "network",
                "parameters": {"request_count": 10, "delay_ms": 50},
                "priority": 5,
                "delay_seconds": 0
            }
        },

        "create_data_processing_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create data processing task",
            "test_data": {
                "task_type": "data_processing",
                "parameters": {"record_count": 5000, "operation": "aggregate"},
                "priority": 5,
                "delay_seconds": 0
            }
        },

        "create_email_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create email sending simulation task",
            "test_data": {
                "task_type": "email",
                "parameters": {"recipient_count": 50, "template": "newsletter"},
                "priority": 5,
                "delay_seconds": 0
            }
        },

        "create_report_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create report generation task",
            "test_data": {
                "task_type": "report",
                "parameters": {"report_type": "summary", "data_points": 2000},
                "priority": 5,
                "delay_seconds": 0
            }
        },

        # Delayed task creation
        "create_delayed_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create delayed computation task",
            "test_data": {
                "task_type": "computation",
                "parameters": {"iterations": 5000},
                "priority": 5,
                "delay_seconds": 2
            }
        },

        # Priority task creation
        "create_high_priority_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create high priority task",
            "test_data": {
                "task_type": "computation",
                "parameters": {"iterations": 1000},
                "priority": 10,
                "delay_seconds": 0
            }
        },

        "create_low_priority_task": {
            "method": "POST",
            "path": "/tasks/create",
            "description": "Create low priority task",
            "test_data": {
                "task_type": "computation",
                "parameters": {"iterations": 1000},
                "priority": 1,
                "delay_seconds": 0
            }
        },

        # Batch task creation
        "create_batch_small": {
            "method": "POST",
            "path": "/tasks/batch",
            "description": "Create small batch of tasks (10 tasks)",
            "test_data": {
                "tasks": [
                    {
                        "task_type": "computation",
                        "parameters": {"iterations": 1000},
                        "priority": 5,
                        "delay_seconds": 0
                    }
                    for _ in range(10)
                ],
                "execute_parallel": True
            }
        },

        "create_batch_medium": {
            "method": "POST",
            "path": "/tasks/batch",
            "description": "Create medium batch of tasks (50 tasks)",
            "test_data": {
                "tasks": [
                    {
                        "task_type": "computation",
                        "parameters": {"iterations": 500},
                        "priority": 5,
                        "delay_seconds": 0
                    }
                    for _ in range(50)
                ],
                "execute_parallel": True
            }
        },

        "create_batch_large": {
            "method": "POST",
            "path": "/tasks/batch",
            "description": "Create large batch of tasks (100 tasks)",
            "test_data": {
                "tasks": [
                    {
                        "task_type": "computation",
                        "parameters": {"iterations": 200},
                        "priority": 5,
                        "delay_seconds": 0
                    }
                    for _ in range(100)
                ],
                "execute_parallel": True
            }
        },

        "create_batch_mixed": {
            "method": "POST",
            "path": "/tasks/batch",
            "description": "Create mixed type batch of tasks",
            "test_data": {
                "tasks": [
                    {
                        "task_type": "computation",
                        "parameters": {"iterations": 1000},
                        "priority": 5,
                        "delay_seconds": 0
                    },
                    {
                        "task_type": "io",
                        "parameters": {"file_count": 5, "file_size": 1024},
                        "priority": 7,
                        "delay_seconds": 0
                    },
                    {
                        "task_type": "data_processing",
                        "parameters": {"record_count": 1000, "operation": "filter", "threshold": 500},
                        "priority": 6,
                        "delay_seconds": 0
                    },
                    {
                        "task_type": "email",
                        "parameters": {"recipient_count": 10, "template": "alert"},
                        "priority": 8,
                        "delay_seconds": 0
                    }
                ] * 5,  # 20 tasks total (5 of each type)
                "execute_parallel": True
            }
        },

        # Task status and monitoring
        "get_task_status": {
            "method": "GET",
            "path": "/tasks/{task_id}",
            "description": "Get single task status",
            "path_params": {"task_id": "generated_task_id"}
        },

        "get_batch_status": {
            "method": "GET",
            "path": "/tasks/batch/status",
            "description": "Get batch task status",
            "query_params": {"task_ids": "comma_separated_task_ids"}
        },

        "get_queue_stats": {
            "method": "GET",
            "path": "/tasks/queue/stats",
            "description": "Get task queue statistics"
        },

        # Task management
        "cancel_task": {
            "method": "DELETE",
            "path": "/tasks/{task_id}",
            "description": "Cancel a background task",
            "path_params": {"task_id": "generated_task_id"}
        },

        "clear_completed_tasks": {
            "method": "DELETE",
            "path": "/tasks/queue/clear",
            "description": "Clear completed and failed tasks"
        },

        # Scheduled tasks
        "schedule_future_task": {
            "method": "POST",
            "path": "/tasks/schedule",
            "description": "Schedule task for future execution",
            "test_data": {
                "task_type": "computation",
                "parameters": {"iterations": 2000},
                "priority": 5,
                "delay_seconds": 0
            },
            "query_params": {
                "schedule_time": (datetime.now() + timedelta(seconds=5)).isoformat()
            }
        }
    }


# Task generation functions for different scenarios
def generate_computation_tasks(count: int = 10, iterations_per_task: int = 1000) -> List[Dict[str, Any]]:
    """Generate computation tasks for batch testing"""
    return [
        {
            "task_type": "computation",
            "parameters": {"iterations": iterations_per_task},
            "priority": 5,
            "delay_seconds": 0
        }
        for _ in range(count)
    ]

def generate_mixed_workload_tasks(count: int = 20) -> List[Dict[str, Any]]:
    """Generate mixed workload tasks for realistic testing"""
    task_types = [
        ("computation", {"iterations": 2000}),
        ("io", {"file_count": 10, "file_size": 1024}),
        ("data_processing", {"record_count": 2000, "operation": "aggregate"}),
        ("network", {"request_count": 5, "delay_ms": 100}),
        ("email", {"recipient_count": 20, "template": "notification"}),
        ("report", {"report_type": "detailed", "data_points": 1000})
    ]

    tasks = []
    for i in range(count):
        task_type, parameters = task_types[i % len(task_types)]
        tasks.append({
            "task_type": task_type,
            "parameters": parameters,
            "priority": 5 + (i % 6),  # Varying priority 5-10
            "delay_seconds": 0
        })

    return tasks

def generate_priority_test_tasks() -> List[Dict[str, Any]]:
    """Generate tasks with different priorities for priority testing"""
    return [
        # High priority tasks
        {
            "task_type": "computation",
            "parameters": {"iterations": 500},
            "priority": 10,
            "delay_seconds": 0
        },
        {
            "task_type": "email",
            "parameters": {"recipient_count": 5, "template": "urgent"},
            "priority": 9,
            "delay_seconds": 0
        },
        # Medium priority tasks
        {
            "task_type": "data_processing",
            "parameters": {"record_count": 1000, "operation": "filter"},
            "priority": 5,
            "delay_seconds": 0
        },
        {
            "task_type": "report",
            "parameters": {"report_type": "summary", "data_points": 500},
            "priority": 5,
            "delay_seconds": 0
        },
        # Low priority tasks
        {
            "task_type": "io",
            "parameters": {"file_count": 20, "file_size": 2048},
            "priority": 2,
            "delay_seconds": 0
        },
        {
            "task_type": "computation",
            "parameters": {"iterations": 5000},
            "priority": 1,
            "delay_seconds": 0
        }
    ]

def generate_stress_test_tasks(count: int = 100) -> List[Dict[str, Any]]:
    """Generate tasks for stress testing the background task system"""
    tasks = []

    for i in range(count):
        # Vary task types and complexity
        if i % 4 == 0:
            task = {
                "task_type": "computation",
                "parameters": {"iterations": 1000 + (i * 10)},
                "priority": 5,
                "delay_seconds": 0
            }
        elif i % 4 == 1:
            task = {
                "task_type": "io",
                "parameters": {"file_count": 5 + (i % 10), "file_size": 512 + (i * 32)},
                "priority": 5,
                "delay_seconds": 0
            }
        elif i % 4 == 2:
            task = {
                "task_type": "data_processing",
                "parameters": {"record_count": 500 + (i * 20), "operation": "aggregate"},
                "priority": 5,
                "delay_seconds": 0
            }
        else:
            task = {
                "task_type": "email",
                "parameters": {"recipient_count": 10 + (i % 20), "template": "batch"},
                "priority": 5,
                "delay_seconds": 0
            }

        tasks.append(task)

    return tasks

# Performance test configurations
PERFORMANCE_CONFIGS = {
    "light_load": {
        "task_count": 10,
        "iterations": 1000,
        "description": "Light load testing (10 tasks)"
    },
    "medium_load": {
        "task_count": 50,
        "iterations": 500,
        "description": "Medium load testing (50 tasks)"
    },
    "heavy_load": {
        "task_count": 100,
        "iterations": 200,
        "description": "Heavy load testing (100 tasks)"
    },
    "stress_load": {
        "task_count": 200,
        "iterations": 100,
        "description": "Stress load testing (200 tasks)"
    }
}

def get_performance_config(config_name: str) -> Dict[str, Any]:
    """Get performance test configuration by name"""
    return PERFORMANCE_CONFIGS.get(config_name, PERFORMANCE_CONFIGS["light_load"])
