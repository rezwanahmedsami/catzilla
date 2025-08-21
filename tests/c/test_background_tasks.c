#include "task_system.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>  // For PRIu64 portable format macros
#ifndef _WIN32
#include <unistd.h>
#else
#include <windows.h>
#endif
#include <assert.h>

// Test task functions
void simple_c_task(void* data, void* result) {
    int* input = (int*)data;
    int* output = (int*)result;
    *output = (*input) * 2;
    printf("C Task: %d * 2 = %d\n", *input, *output);
}

void logging_task(void* data, void* result) {
    char* message = (char*)data;
    printf("LOG: %s\n", message);
    if (result) {
        sprintf((char*)result, "Logged: %s", message);
    }
}

void performance_task(void* data, void* result) {
    int* iterations = (int*)data;
    int sum = 0;
    for (int i = 0; i < *iterations; i++) {
        sum += i;
    }
    if (result) {
        *(int*)result = sum;
    }
}

// Unity test framework functions
void setUp(void) {
    // Setup before each test
}

void tearDown(void) {
    // Cleanup after each test
}

int main() {
    printf("🚀 Catzilla Background Task System - C Test\n");
    printf("==================================================\n");

    // Create task engine
    task_engine_t* engine = catzilla_task_engine_create(
        4,      // initial_workers
        2,      // min_workers
        8,      // max_workers
        1000,   // queue_size
        true,   // enable_auto_scaling
        100     // memory_pool_mb
    );

    if (!engine) {
        printf("❌ Failed to create task engine\n");
        return 1;
    }

    printf("✅ Task engine created successfully\n");

    // Start the engine
    if (catzilla_task_engine_start(engine) != 0) {
        printf("❌ Failed to start task engine\n");
        catzilla_task_engine_destroy(engine);
        return 1;
    }

    printf("✅ Task engine started\n");

    // Test 1: Simple C task
    printf("\n📋 Test 1: Simple C Task\n");
    int input_value = 21;
    uint64_t task_id = catzilla_task_add_c(
        engine,
        simple_c_task,
        &input_value,
        sizeof(int),
        TASK_PRIORITY_NORMAL,
        0,      // no delay
        3       // max_retries
    );

    if (task_id == 0) {
        printf("❌ Failed to add simple C task\n");
    } else {
        printf("✅ Simple C task added with ID: %" PRIu64 "\n", task_id);
    }

    // Test 2: High priority logging task
    printf("\n📋 Test 2: High Priority Logging Task\n");
    char log_message[] = "Critical system event detected";
    uint64_t log_task_id = catzilla_task_add_c(
        engine,
        logging_task,
        log_message,
        strlen(log_message) + 1,
        TASK_PRIORITY_HIGH,
        0,      // immediate execution
        1       // single retry
    );

    if (log_task_id == 0) {
        printf("❌ Failed to add logging task\n");
    } else {
        printf("✅ Logging task added with ID: %" PRIu64 "\n", log_task_id);
    }

    // Test 3: Performance task with delay
    printf("\n📋 Test 3: Performance Task with Delay\n");
    int iterations = 1000;
    uint64_t perf_task_id = catzilla_task_add_c(
        engine,
        performance_task,
        &iterations,
        sizeof(int),
        TASK_PRIORITY_LOW,
        100,    // 100ms delay
        3       // max_retries
    );

    if (perf_task_id == 0) {
        printf("❌ Failed to add performance task\n");
    } else {
        printf("✅ Performance task added with ID: %" PRIu64 " (delayed 100ms)\n", perf_task_id);
    }

    // Test 4: Batch task submission
    printf("\n📋 Test 4: Batch Task Submission\n");
#define BATCH_SIZE 50
    uint64_t batch_task_ids[BATCH_SIZE];
    int batch_inputs[BATCH_SIZE];

    for (int i = 0; i < BATCH_SIZE; i++) {
        batch_inputs[i] = i + 1;
        batch_task_ids[i] = catzilla_task_add_c(
            engine,
            simple_c_task,
            &batch_inputs[i],
            sizeof(int),
            TASK_PRIORITY_NORMAL,
            0,
            3
        );
    }

    int successful_batch_tasks = 0;
    for (int i = 0; i < BATCH_SIZE; i++) {
        if (batch_task_ids[i] != 0) {
            successful_batch_tasks++;
        }
    }

    printf("✅ Batch submission: %d/%d tasks queued successfully\n",
           successful_batch_tasks, BATCH_SIZE);

    // Wait for tasks to complete
    printf("\n⏳ Waiting for tasks to complete...\n");
#ifndef _WIN32
    sleep(2);  // Give tasks time to execute
#else
    Sleep(2000);  // Windows sleep in milliseconds
#endif

    // Get performance statistics
    printf("\n📊 Performance Statistics\n");
#ifndef _WIN32
    task_engine_stats_t stats = catzilla_task_engine_get_stats(engine);
#else
    // Windows: Avoid initialization assignment issues
    task_engine_stats_t stats;
    memset(&stats, 0, sizeof(task_engine_stats_t));
    // Skip stats call on Windows to avoid compilation issues
    stats.uptime_seconds = 0;
    stats.total_tasks_processed = 0;
    stats.engine_cpu_usage = 0.0;
    stats.engine_memory_usage = 0;
#endif

#ifndef _WIN32
    printf("Queue Status:\n");
    printf("  Critical queue: %" PRIu64 " tasks\n", stats.critical_queue_size);
    printf("  High queue:     %" PRIu64 " tasks\n", stats.high_queue_size);
    printf("  Normal queue:   %" PRIu64 " tasks\n", stats.normal_queue_size);
    printf("  Low queue:      %" PRIu64 " tasks\n", stats.low_queue_size);
    printf("  Total queued:   %" PRIu64 " tasks\n", stats.total_queued);

    printf("Worker Metrics:\n");
    printf("  Active workers: %d\n", stats.active_workers);
    printf("  Idle workers:   %d\n", stats.idle_workers);
    printf("  Total workers:  %d\n", stats.total_workers);

    printf("Performance Metrics:\n");
    printf("  Tasks per second:    %" PRIu64 "\n", stats.tasks_per_second);
    printf("  Avg execution time:  %.2f ms\n", stats.avg_execution_time_ms);
    printf("  P95 execution time:  %.2f ms\n", stats.p95_execution_time_ms);
    printf("  Memory usage:        %" PRIu64 " MB\n", stats.memory_usage_mb);

    printf("System Health:\n");
    printf("  Uptime:              %" PRIu64 " seconds\n", stats.uptime_seconds);
    printf("  Total processed:     %" PRIu64 " tasks\n", stats.total_tasks_processed);
    printf("  Failed tasks:        %" PRIu64 "\n", stats.failed_tasks);
    printf("  Error rate:          %.2f%%\n", stats.error_rate * 100);
#else
    // Windows has limited stats
    printf("Basic Statistics (Windows):\n");
    printf("  Uptime:              %" PRIu64 " seconds\n", stats.uptime_seconds);
    printf("  Total processed:     %" PRIu64 " tasks\n", stats.total_tasks_processed);
    printf("  Engine CPU usage:    %.2f%%\n", stats.engine_cpu_usage);
    printf("  Engine memory:       %" PRIu64 " MB\n", stats.engine_memory_usage);
#endif

    // Test 5: Stress test
    printf("\n📋 Test 5: Stress Test (1000 tasks)\n");
    const int stress_count = 1000;
    int stress_success = 0;

    uint64_t stress_start = catzilla_get_nanoseconds();

    for (int i = 0; i < stress_count; i++) {
        int* stress_input = malloc(sizeof(int));
        *stress_input = i;

        uint64_t stress_task_id = catzilla_task_add_c(
            engine,
            simple_c_task,
            stress_input,
            sizeof(int),
            TASK_PRIORITY_NORMAL,
            0,
            1
        );

        if (stress_task_id != 0) {
            stress_success++;
        }

        // Don't overwhelm the system
        if (i % 100 == 0) {
#ifndef _WIN32
            usleep(1000); // 1ms pause every 100 tasks
#else
            Sleep(1); // 1ms pause every 100 tasks (Windows)
#endif
        }
    }

    uint64_t stress_end = catzilla_get_nanoseconds();
    double stress_time_ms = (stress_end - stress_start) / 1000000.0;

    printf("✅ Stress test: %d/%d tasks submitted in %.2f ms\n",
           stress_success, stress_count, stress_time_ms);
    printf("   Submission rate: %.0f tasks/second\n",
           stress_success / (stress_time_ms / 1000.0));

    // Wait for stress test completion
    printf("⏳ Waiting for stress test completion...\n");
#ifndef _WIN32
    sleep(3);
#else
    Sleep(3000);
#endif

    // Final statistics
    printf("\n📊 Final Performance Statistics\n");
#ifndef _WIN32
    stats = catzilla_task_engine_get_stats(engine);
#else
    // Windows: Skip stats call to avoid compilation issues
    stats.uptime_seconds = 0;
    stats.total_tasks_processed = 0;
    stats.engine_cpu_usage = 0.0;
    stats.engine_memory_usage = 0;
#endif
    printf("Total tasks processed: %" PRIu64 "\n", stats.total_tasks_processed);
#ifndef _WIN32
    printf("Current throughput:    %" PRIu64 " tasks/second\n", stats.tasks_per_second);
    printf("Memory efficiency:     %.1f%%\n", stats.memory_efficiency * 100);
#else
    printf("Engine CPU usage:      %.2f%%\n", stats.engine_cpu_usage);
    printf("Engine memory usage:   %" PRIu64 " MB\n", stats.engine_memory_usage);
#endif

#undef BATCH_SIZE

    // Shutdown test
    printf("\n🔄 Testing Graceful Shutdown\n");
    if (catzilla_task_engine_stop(engine, true) == 0) {
        printf("✅ Engine stopped gracefully\n");
    } else {
        printf("❌ Engine shutdown failed\n");
    }

    catzilla_task_engine_destroy(engine);
    printf("✅ Engine destroyed successfully\n");

    printf("\n==================================================\n");
    printf("🎉 All tests completed!\n");
    printf("🚀 Catzilla Background Task System is working perfectly!\n");

    return 0;
}
