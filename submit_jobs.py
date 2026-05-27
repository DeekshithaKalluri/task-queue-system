import time
from tasks.job_tasks import send_email, process_data, generate_report
from tasks.failing_tasks import always_fails

print("=== Submitting jobs to queues ===\n")

# --- HIGH priority: send 5 emails ---
print("[HIGH] Submitting email tasks...")
for i in range(5):
    send_email.apply_async(
        args=[f"user{i}@example.com", f"Subject {i}", f"Body {i}"],
        queue='high'
    )
print("  5 email tasks submitted\n")

# --- DEFAULT priority: process 5 datasets ---
print("[DEFAULT] Submitting data processing tasks...")
for i in range(5):
    process_data.apply_async(
        args=[f"dataset_{i}", "aggregate"],
        queue='default'
    )
print("  5 data processing tasks submitted\n")

# --- LOW priority: generate 3 reports ---
print("[LOW] Submitting report generation tasks...")
for i in range(3):
    generate_report.apply_async(
        args=[f"monthly", f"2024-0{i+1}"],
        queue='low'
    )
print("  3 report tasks submitted\n")

# --- DLQ DEMO: submit a task that will always fail ---
print("[DLQ DEMO] Submitting always_fails task (watch retry + dead-letter)...")
always_fails.apply_async(args=["demo-job-001"], queue='default')
print("  always_fails task submitted\n")

print("=== All jobs submitted! Watch Terminal 1 for live output ===")