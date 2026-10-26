import argparse

p = argparse.ArgumentParser()
p.add_argument("--amount", type=float, required=True)
p.add_argument("--days", type=int, required=True)
a = p.parse_args()
share = max(0.0, (60 - a.days) / 30)    # day 30: 1.0, day 60: 0.0
print(f"{round(a.amount * min(share, 1.0), 2)}")
