import time
import random
from tasks.job_tasks import send_email, process_data, generate_report

TOTAL_JOBS = 10_000

# Distribution: 20% high, 60% default, 20% low
HIGH_COUNT    = int(TOTAL_JOBS * 0.20)   # 2000 email tasks
DEFAULT_COUNT = int(TOTAL_JOBS * 0.60)   # 6000 data processing tasks
LOW_COUNT     = int(TOTAL_JOBS * 0.20)   # 2000 report tasks

def submit_batch(task_fn, queue, args_list, label):
    print(f"  Submitting {len(args_list)} {label} tasks to [{queue}] queue...")
    start = time.time()
    for args in args_list:
        task_fn.apply_async(args=args, queue=queue)
    elapsed = time.time() - start
    rate = len(args_list) / elapsed
    print(f"  Done in {elapsed:.2f}s  ({rate:.0f} tasks/sec submitted)")

print("=" * 55)
print(f"  LOAD TEST — {TOTAL_JOBS:,} jobs")
print("=" * 55)

overall_start = time.time()

# HIGH: email tasks
email_args = [
    [f"user{i}@example.com", f"Subject {i}", f"Body {i}"]
    for i in range(HIGH_COUNT)
]
submit_batch(send_email, 'high', email_args, 'email')

# DEFAULT: data processing tasks
data_args = [
    [f"dataset_{i}", random.choice(['aggregate', 'transform', 'export'])]
    for i in range(DEFAULT_COUNT)
]
submit_batch(process_data, 'default', data_args, 'data processing')

# LOW: report tasks
report_args = [
    [random.choice(['monthly', 'weekly', 'annual']), f"2024-{(i % 12)+1:02d}"]
    for i in range(LOW_COUNT)
]
submit_batch(generate_report, 'low', report_args, 'report')

overall_elapsed = time.time() - overall_start

print()
print("=" * 55)
print(f"  {TOTAL_JOBS:,} jobs submitted in {overall_elapsed:.2f}s")
print(f"  Avg submission rate: {TOTAL_JOBS / overall_elapsed:.0f} tasks/sec")
print(f"  Watch the worker terminal for processing.")
print(f"  Watch http://localhost:5001 for live queue depths.")
print("=" * 55)