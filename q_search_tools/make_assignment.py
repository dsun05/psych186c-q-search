"""Write ../q_search/participant_assignment.csv from roster.txt.

roster.txt: one classmate first name per line (not the team). Following the
Lab 7 procedure, the names are shuffled with a fixed seed, then the four
counterbalanced block orders are dealt out in turn so each order gets an
equal share (differing by at most one).

  python3 make_assignment.py
"""
import csv
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'q_search'))
from q_search_helpers import BLOCK_ORDERS  # noqa: E402

SEED = 'group8-qsearch'
TEAM = ['jackson', 'david']

here = Path(__file__).resolve().parent
out = here.parent / 'q_search' / 'participant_assignment.csv'

classmates = [line.strip().lower() for line in (here / 'roster.txt').read_text().splitlines()
              if line.strip()]
names = classmates + TEAM
dupes = sorted({n for n in names if names.count(n) > 1})
if dupes:
    sys.exit(f'Duplicate first names, resolve with the instructor first: {dupes}')

random.seed(SEED)
random.shuffle(classmates)

rows = []
for i, name in enumerate(classmates):
    rows.append({'participant': name, 'sub_id': 101 + i,
                 'block_order': BLOCK_ORDERS[i % len(BLOCK_ORDERS)], 'is_team': 0})
for i, name in enumerate(TEAM):
    rows.append({'participant': name, 'sub_id': 1 + i,
                 'block_order': BLOCK_ORDERS[i % len(BLOCK_ORDERS)], 'is_team': 1})

with out.open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['participant', 'sub_id', 'block_order', 'is_team'])
    writer.writeheader()
    writer.writerows(rows)

counts = {o: sum(r['block_order'] == o for r in rows if not r['is_team']) for o in BLOCK_ORDERS}
print(f'wrote {out}: {len(classmates)} classmates, orders {counts}')
