"""Agreement between the refund judge and human labels (Cohen's kappa).

pip install scikit-learn
python judge_kappa.py labels.csv
labels.csv columns: chat_id,human,judge  (pass/fail per chat; label ~100 chats)
"""
import csv
import sys
from sklearn.metrics import cohen_kappa_score

path = sys.argv[1] if len(sys.argv) > 1 else "labels.csv"
with open(path, newline="") as f:
    rows = list(csv.DictReader(f))  # chat_id, human, judge
kappa = cohen_kappa_score([r["human"] for r in rows],
                          [r["judge"] for r in rows])
print(f"{len(rows)} chats, kappa = {kappa:.2f}")
