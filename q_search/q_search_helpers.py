"""Trial building, scoring, and roster lookup for the Q-among-O's experiment.

Imported by the Code components in q_search.psyexp. Every function that
shuffles takes the `random` module (or a random.Random) so the whole session
follows the participant-name seed set in Begin Experiment.
"""
import hashlib
import re

# Block codes: (Q frequency, points lost for a miss)
BLOCKS = {
    'A': {'q_freq': 0.25, 'miss_penalty': 1},
    'B': {'q_freq': 0.25, 'miss_penalty': 5},
    'C': {'q_freq': 0.50, 'miss_penalty': 1},
    'D': {'q_freq': 0.50, 'miss_penalty': 5},
}

# Balanced 4x4 Latin square: every block appears once in each position and
# directly follows every other block exactly once.
BLOCK_ORDERS = ['ABDC', 'BCAD', 'CDBA', 'DACB']

TRIALS_PER_BLOCK = 48
N_PRACTICE = 8
N_CELLS = 16          # 4 x 4 grid
MASK_CHARS = '@&%#8'

# Fallback IDs for names missing from the roster start here
UNLISTED_ID_START = 900


def build_block(block_code, rng):
    """Return a shuffled list of trial dicts for one block."""
    n_q = round(BLOCKS[block_code]['q_freq'] * TRIALS_PER_BLOCK)
    return _build_trials(n_q, TRIALS_PER_BLOCK, rng)


def build_practice(rng):
    """Practice uses 50% Q trials so both answers get rehearsed."""
    return _build_trials(N_PRACTICE // 2, N_PRACTICE, rng)


def _build_trials(n_q, n_total, rng):
    # Spread Q locations: every cell once before any cell repeats
    locs = []
    while len(locs) < n_q:
        locs += rng.sample(range(N_CELLS), min(N_CELLS, n_q - len(locs)))
    trials = [{'q_present': 1, 'q_loc': loc} for loc in locs]
    trials += [{'q_present': 0, 'q_loc': -1} for _ in range(n_total - n_q)]
    rng.shuffle(trials)
    for t in trials:
        t['grid_text'] = grid_text(t['q_loc'])
        t['mask_text'] = mask_text(rng)
    return trials


def grid_text(q_loc):
    """4 x 4 grid of O's with a Q at q_loc (-1 for no Q).

    Columns are separated by one space, which in a monospaced font makes the
    horizontal and vertical spacing roughly equal.
    """
    cells = ['Q' if i == q_loc else 'O' for i in range(N_CELLS)]
    return '\n'.join(' '.join(cells[r * 4:r * 4 + 4]) for r in range(4))


def mask_text(rng):
    cells = [rng.choice(MASK_CHARS) for _ in range(N_CELLS)]
    return '\n'.join(' '.join(cells[r * 4:r * 4 + 4]) for r in range(4))


def score(q_present, key, miss_penalty):
    """Return (outcome, said_present, points) for one response.

    key is 'j' (Q present), 'f' (Q absent), or None for a timeout.
    """
    if key is None:
        return 'timeout', None, -1
    said_present = 1 if key == 'j' else 0
    if q_present and said_present:
        return 'hit', 1, 1
    if q_present:
        return 'miss', 0, -miss_penalty
    if said_present:
        return 'false_alarm', 1, -1
    return 'correct_rejection', 0, 1


FEEDBACK = {
    'hit': ('Correct!', 'green'),
    'correct_rejection': ('Correct!', 'green'),
    'miss': ('Missed the Q!', 'red'),
    'false_alarm': ('False alarm!', 'red'),
    'timeout': ('Too slow!', 'red'),
}


def feedback(outcome, points):
    msg, color = FEEDBACK[outcome]
    return f'{msg}   {points:+d}'.replace('-', '−'), color


def first_key(keys):
    """Keyboard .keys can be None, '', a string, or a list depending on version."""
    if not keys:
        return None
    return keys[0] if isinstance(keys, (list, tuple)) else keys


def pilot_ms(name):
    """'pilot100' -> 100 (grid duration override in ms); None otherwise."""
    m = re.fullmatch(r'pilot(\d+)', name)
    return int(m.group(1)) if m else None


def lookup_participant(name, roster):
    """Find name in the roster rows from participant_assignment.csv.

    Returns dict with sub_id, block_order, is_team, roster_match. Pilot names
    and names missing from the roster get a deterministic fallback (no random
    assignment at run time), flagged with roster_match = 0.
    """
    matches = [row for row in roster
               if str(row['participant']).strip().lower() == name]
    if len(matches) == 1:
        row = matches[0]
        return {'sub_id': str(int(row['sub_id'])),
                'block_order': str(row['block_order']).strip().upper(),
                'is_team': int(row['is_team']),
                'roster_match': 1}
    digest = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16)
    if pilot_ms(name) is not None:
        sub_id = name
    else:
        sub_id = str(UNLISTED_ID_START + digest % 100)
    return {'sub_id': sub_id,
            'block_order': BLOCK_ORDERS[digest % len(BLOCK_ORDERS)],
            'is_team': int(pilot_ms(name) is not None),
            'roster_match': 0}


def block_intro_text(block_num, n_blocks, block_code, prev_block_score):
    b = BLOCKS[block_code]
    pct = round(b['q_freq'] * 100)
    lines = []
    if prev_block_score is not None:
        lines += [f'Points in the last block: {prev_block_score:+d}'.replace('-', '−'), '']
    lines += [
        f'Block {block_num} of {n_blocks}',
        '',
        f'In this block, a Q appears on about {pct}% of trials.',
        '',
        'Scoring:',
        'Correct answer:  +1',
        'False alarm (J when there is no Q):  −1',
        f'Missed Q (F when there is a Q):  −{b["miss_penalty"]}',
        '',
        'Press SPACE to begin.',
    ]
    return '\n'.join(lines)


def output_path(sub_id, exists):
    """data/sub-<id>_q_search.csv, adding _2, _3 ... instead of overwriting."""
    base = f'data/sub-{sub_id}_q_search'
    path, n = base + '.csv', 2
    while exists(path):
        path, n = f'{base}_{n}.csv', n + 1
    return path
