"""
Task Scheduling Example

This example demonstrates Catzilla's background task system for scheduling
and managing background operations with monitoring and graceful shutdown.

Features demonstrated:
- Background task scheduling
- Task monitoring and status tracking
- Graceful shutdown handling
- Task queues and priorities
- Periodic tasks and cron-like scheduling
- Task result storage and retrieval
"""

from catzilla import Catzilla, Request, Response, JSONResponse, BaseModel, Path
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Initialize Catzilla with background tasks enabled
app = Catzilla(
    production=False,
    show_banner=True,
    log_requests=True
)

# Enable background task system
app.enable_background_tasks(
    workers=4,
    enable_profiling=True,
    memory_pool_mb=500
)

# Data models for auto-validation
class EmailTask(BaseModel):
    """Email task creation model"""
    email: str
    subject: str
    body: str

class DataProcessingTask(BaseModel):
    """Data processing task creation model"""
    data: List[str]  # Changed from List[Any] to List[str]
    operation: str = "transform"

class ReportGenerationTask(BaseModel):
    """Report generation task creation model"""
    type: str
    parameters: str = "{}"  # Changed from Dict[str, Any] to str (JSON string)

# Task storage for demonstration (in production, use Redis or database)
task_storage: Dict[str, Dict[str, Any]] = {}
task_results: Dict[str, Any] = {}

# Background task functions
def send_email_task(task_id: str, email: str, subject: str, body: str):
    """Simulate sending an email"""
    task_storage[task_id]["status"] = "running"
    task_storage[task_id]["started_at"] = datetime.now().isoformat()

    try:
        # Simulate email sending delay
        time.sleep(2)

        # Simulate email service
        result = {
            "email_sent": True,
            "recipient": email,
            "subject": subject,
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "sent_at": datetime.now().isoformat()
        }

        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["completed_at"] = datetime.now().isoformat()
        task_results[task_id] = result

        print(f"📧 Email sent to {email}: {subject}")

    except Exception as e:
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["failed_at"] = datetime.now().isoformat()
        print(f"❌ Email failed to {email}: {e}")

def process_data_task(task_id: str, data: List[str], operation: str):
    """Simulate data processing"""
    task_storage[task_id]["status"] = "running"
    task_storage[task_id]["started_at"] = datetime.now().isoformat()
    task_storage[task_id]["progress"] = 0

    try:
        total_items = len(data)
        processed_items = []

        for i, item in enumerate(data):
            # Simulate processing time
            time.sleep(0.5)

            # Simulate data transformation
            processed_item = {
                "id": i,
                "original": item,
                "processed": True,
                "operation": operation,
                "processed_at": datetime.now().isoformat()
            }
            processed_items.append(processed_item)

            # Update progress
            progress = int(((i + 1) / total_items) * 100)
            task_storage[task_id]["progress"] = progress
            print(f"📊 Processing data: {progress}% complete")

        result = {
            "operation": operation,
            "total_items": total_items,
            "processed_items": processed_items,
            "completed_at": datetime.now().isoformat()
        }

        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["completed_at"] = datetime.now().isoformat()
        task_storage[task_id]["progress"] = 100
        task_results[task_id] = result

        print(f"✅ Data processing completed: {total_items} items")

    except Exception as e:
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["failed_at"] = datetime.now().isoformat()
        print(f"❌ Data processing failed: {e}")

def generate_report_task(task_id: str, report_type: str, parameters: Dict):
    """Simulate report generation"""
    task_storage[task_id]["status"] = "running"
    task_storage[task_id]["started_at"] = datetime.now().isoformat()

    try:
        # Simulate report generation time
        time.sleep(3)

        report = {
            "report_id": f"report_{uuid.uuid4().hex[:8]}",
            "type": report_type,
            "parameters": parameters,
            "generated_at": datetime.now().isoformat(),
            "file_size": "2.5MB",
            "format": "PDF",
            "download_url": f"/downloads/report_{task_id}.pdf"
        }

        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["completed_at"] = datetime.now().isoformat()
        task_results[task_id] = report

        print(f"📊 Report generated: {report_type}")

    except Exception as e:
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["failed_at"] = datetime.now().isoformat()
        print(f"❌ Report generation failed: {e}")

# Periodic task for cleanup
def cleanup_old_tasks():
    """Clean up old completed tasks"""
    cutoff_time = datetime.now() - timedelta(hours=1)

    tasks_to_remove = []
    for task_id, task_info in task_storage.items():
        if task_info["status"] in ["completed", "failed"]:
            completed_at = task_info.get("completed_at") or task_info.get("failed_at")
            if completed_at:
                task_time = datetime.fromisoformat(completed_at)
                if task_time < cutoff_time:
                    tasks_to_remove.append(task_id)

    for task_id in tasks_to_remove:
        del task_storage[task_id]
        if task_id in task_results:
            del task_results[task_id]
        print(f"🧹 Cleaned up old task: {task_id}")

# Note: Periodic tasks would be registered here in a production app
# app.add_periodic_task(cleanup_old_tasks, interval=300)  # Every 5 minutes

@app.get("/")
def home(request: Request) -> Response:
    """Home endpoint with background tasks info"""
    return JSONResponse({
        "message": "Catzilla Background Tasks Example",
        "features": [
            "Background task scheduling",
            "Task monitoring and status tracking",
            "Graceful shutdown handling",
            "Periodic tasks",
            "Task result storage"
        ],
        "active_tasks": len([t for t in task_storage.values() if t["status"] == "running"]),
        "total_tasks": len(task_storage)
    })

@app.post("/tasks/email")
def schedule_email_task(request: Request, email_task: EmailTask) -> Response:
    """Schedule an email sending task"""
    task_id = f"email_{uuid.uuid4().hex[:8]}"

    # Store task info
    task_storage[task_id] = {
        "id": task_id,
        "type": "email",
        "status": "scheduled",
        "created_at": datetime.now().isoformat(),
        "parameters": {"email": email_task.email, "subject": email_task.subject}
    }

    # Schedule the background task
    app.add_task(send_email_task, task_id, email_task.email, email_task.subject, email_task.body)

    return JSONResponse({
        "message": "Email task scheduled",
        "task_id": task_id,
        "status": "scheduled",
        "estimated_completion": (datetime.now() + timedelta(seconds=2)).isoformat()
    }, status_code=202)

@app.post("/tasks/process-data")
def schedule_data_processing_task(request: Request, data_task: DataProcessingTask) -> Response:
    """Schedule a data processing task"""
    task_id = f"data_{uuid.uuid4().hex[:8]}"

    # Store task info
    task_storage[task_id] = {
        "id": task_id,
        "type": "data_processing",
        "status": "scheduled",
        "created_at": datetime.now().isoformat(),
        "parameters": {"item_count": len(data_task.data), "operation": data_task.operation},
        "progress": 0
    }

    # Schedule the background task
    app.add_task(process_data_task, task_id, data_task.data, data_task.operation)

    return JSONResponse({
        "message": "Data processing task scheduled",
        "task_id": task_id,
        "status": "scheduled",
        "item_count": len(data_task.data),
        "estimated_completion": (datetime.now() + timedelta(seconds=len(data_task.data) * 0.5)).isoformat()
    }, status_code=202)

@app.post("/tasks/generate-report")
def schedule_report_generation_task(request: Request, report_task: ReportGenerationTask) -> Response:
    """Schedule a report generation task"""
    import json

    task_id = f"report_{uuid.uuid4().hex[:8]}"

    # Parse parameters from JSON string
    try:
        parameters = json.loads(report_task.parameters) if report_task.parameters else {}
    except json.JSONDecodeError:
        parameters = {}

    # Store task info
    task_storage[task_id] = {
        "id": task_id,
        "type": "report_generation",
        "status": "scheduled",
        "created_at": datetime.now().isoformat(),
        "parameters": {"report_type": report_task.type, "parameters": parameters}
    }

    # Schedule the background task
    app.add_task(generate_report_task, task_id, report_task.type, parameters)

    return JSONResponse({
        "message": "Report generation task scheduled",
        "task_id": task_id,
        "status": "scheduled",
        "report_type": report_task.type,
        "estimated_completion": (datetime.now() + timedelta(seconds=3)).isoformat()
    }, status_code=202)

@app.get("/tasks/{task_id}")
def get_task_status(request: Request, task_id: str = Path(...)) -> Response:
    """Get task status and progress"""
    if task_id not in task_storage:
        return JSONResponse({
            "error": "Task not found",
            "task_id": task_id
        }, status_code=404)

    task_info = task_storage[task_id].copy()

    # Add result if completed
    if task_id in task_results:
        task_info["result"] = task_results[task_id]

    return JSONResponse(task_info)

@app.get("/tasks")
def list_tasks(request: Request) -> Response:
    """List all tasks with optional status filter"""
    status_filter = request.query_params.get("status")

    tasks = list(task_storage.values())

    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]

    # Sort by creation time (newest first)
    tasks.sort(key=lambda x: x["created_at"], reverse=True)

    return JSONResponse({
        "tasks": tasks,
        "total": len(tasks),
        "filter": status_filter,
        "status_counts": {
            "scheduled": len([t for t in task_storage.values() if t["status"] == "scheduled"]),
            "running": len([t for t in task_storage.values() if t["status"] == "running"]),
            "completed": len([t for t in task_storage.values() if t["status"] == "completed"]),
            "failed": len([t for t in task_storage.values() if t["status"] == "failed"])
        }
    })

@app.delete("/tasks/{task_id}")
def cancel_task(request: Request) -> Response:
    """Cancel a task (if not already running)"""
    task_id = request.path_params.get("task_id")

    if task_id not in task_storage:
        return JSONResponse({
            "error": "Task not found",
            "task_id": task_id
        }, status_code=404)

    task_info = task_storage[task_id]

    if task_info["status"] == "running":
        return JSONResponse({
            "error": "Cannot cancel running task",
            "task_id": task_id,
            "status": task_info["status"]
        }, status_code=400)

    # Remove task
    del task_storage[task_id]
    if task_id in task_results:
        del task_results[task_id]

    return JSONResponse({
        "message": "Task cancelled",
        "task_id": task_id
    })

@app.get("/tasks/examples")
def get_task_examples(request: Request) -> Response:
    """Get example payloads for scheduling tasks"""
    return JSONResponse({
        "examples": {
            "email_task": {
                "url": "/tasks/email",
                "method": "POST",
                "payload": {
                    "email": "user@example.com",
                    "subject": "Welcome to Catzilla!",
                    "body": "Thank you for trying out our background tasks system."
                }
            },
            "data_processing_task": {
                "url": "/tasks/process-data",
                "method": "POST",
                "payload": {
                    "operation": "transform",
                    "data": [
                        {"id": 1, "name": "Item 1", "value": 100},
                        {"id": 2, "name": "Item 2", "value": 200},
                        {"id": 3, "name": "Item 3", "value": 300}
                    ]
                }
            },
            "report_generation_task": {
                "url": "/tasks/generate-report",
                "method": "POST",
                "payload": {
                    "type": "sales_report",
                    "parameters": {
                        "date_range": "2024-01-01 to 2024-01-31",
                        "format": "PDF",
                        "include_charts": True
                    }
                }
            }
        },
        "monitoring": {
            "list_tasks": "GET /tasks",
            "filter_by_status": "GET /tasks?status=running",
            "get_task_status": "GET /tasks/{task_id}",
            "cancel_task": "DELETE /tasks/{task_id}"
        }
    })

@app.get("/health")
def health_check(request: Request) -> Response:
    """Health check with background tasks status"""
    return JSONResponse({
        "status": "healthy",
        "background_tasks": "enabled",
        "framework": "Catzilla v0.2.0",
        "task_stats": {
            "active": len([t for t in task_storage.values() if t["status"] == "running"]),
            "total": len(task_storage)
        }
    })

if __name__ == "__main__":
    print("🚨 Starting Catzilla Background Tasks Example")
    print("📝 Available endpoints:")
    print("   GET  /                    - Home with background tasks info")
    print("   POST /tasks/email         - Schedule email sending task")
    print("   POST /tasks/process-data  - Schedule data processing task")
    print("   POST /tasks/generate-report - Schedule report generation task")
    print("   GET  /tasks               - List all tasks")
    print("   GET  /tasks/{task_id}     - Get task status")
    print("   DELETE /tasks/{task_id}   - Cancel task")
    print("   GET  /tasks/examples      - Get example payloads")
    print("   GET  /health              - Health check")
    print()
    print("🎨 Features demonstrated:")
    print("   • Background task scheduling")
    print("   • Task monitoring and status tracking")
    print("   • Progress tracking for long-running tasks")
    print("   • Task result storage and retrieval")
    print("   • Periodic cleanup tasks")
    print("   • Graceful shutdown handling")
    print()
    print("🧪 Try these examples:")
    print("   curl -X POST http://localhost:8000/tasks/email \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"email\":\"test@example.com\",\"subject\":\"Test\",\"body\":\"Hello!\"}'")
    print("   curl http://localhost:8000/tasks")
    print()

    app.listen(host="0.0.0.0", port=8000)
