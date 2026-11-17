"""Checks for q_search_helpers. Run: python3 test_helpers.py"""
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'q_search'))
import q_search_helpers as qs  # noqa: E402


def session(name, order='ABDC'):
    random.seed(name)
    practice = qs.build_practice(random)
    return practice, {code: qs.build_block(code, random) for code in order}


def test_block_contents():
    _, blocks = session('alice')
    for code, trials in blocks.items():
        n_q = round(qs.BLOCKS[code]['q_freq'] * qs.TRIALS_PER_BLOCK)
        assert len(trials) == qs.TRIALS_PER_BLOCK
        assert sum(t['q_present'] for t in trials) == n_q
        locs = Counter(t['q_loc'] for t in trials if t['q_present'])
        # every cell used once before any repeats
        assert max(locs.values()) - min(locs.values() or [0]) <= 1
        assert len(locs) == min(n_q, qs.N_CELLS)
        for t in trials:
            rows = t['grid_text'].split('\n')
            assert len(rows) == 4 and all(len(r) == 7 for r in rows)
            assert t['grid_text'].count('Q') == t['q_present']
            assert t['grid_text'].count('O') == 16 - t['q_present']
            assert len(t['mask_text'].split('\n')) == 4


def test_practice():
    practice, _ = session('alice')
    assert len(practice) == qs.N_PRACTICE
    assert sum(t['q_present'] for t in practice) == qs.N_PRACTICE // 2


def test_seeded_by_name():
    a1, b1 = session('alice')
    a2, b2 = session('alice')
    _, b3 = session('bob')
    assert (a1, b1) == (a2, b2)
    assert [t['q_loc'] for t in b1['A']] != [t['q_loc'] for t in b3['A']]


def test_scoring():
    assert qs.score(1, 'j', 5) == ('hit', 1, 1)
    assert qs.score(1, 'f', 5) == ('miss', 0, -5)
    assert qs.score(1, 'f', 1) == ('miss', 0, -1)
    assert qs.score(0, 'j', 5) == ('false_alarm', 1, -1)
    assert qs.score(0, 'f', 5) == ('correct_rejection', 0, 1)
    assert qs.score(0, None, 5) == ('timeout', None, -1)
    assert qs.feedback('miss', -5) == ('Missed the Q!   −5', 'red')
    assert qs.feedback('hit', 1) == ('Correct!   +1', 'green')


def test_first_key():
    assert qs.first_key(None) is None
    assert qs.first_key([]) is None
    assert qs.first_key('') is None
    assert qs.first_key('j') == 'j'
    assert qs.first_key(['f', 'j']) == 'f'


def test_latin_square_balanced():
    orders = qs.BLOCK_ORDERS
    for pos in range(4):
        assert sorted(o[pos] for o in orders) == list('ABCD')
    pairs = Counter((o[i], o[i + 1]) for o in orders for i in range(3))
    assert len(pairs) == 12 and set(pairs.values()) == {1}


def test_lookup():
    roster = [{'participant': 'Alice', 'sub_id': 101, 'block_order': 'BCAD', 'is_team': 0}]
    assert qs.lookup_participant('alice', roster) == {
        'sub_id': '101', 'block_order': 'BCAD', 'is_team': 0, 'roster_match': 1}
    unknown = qs.lookup_participant('zed', roster)
    assert unknown['roster_match'] == 0 and unknown['block_order'] in qs.BLOCK_ORDERS
    assert unknown == qs.lookup_participant('zed', roster)  # deterministic
    pilot = qs.lookup_participant('pilot50', roster)
    assert pilot['sub_id'] == 'pilot50' and pilot['is_team'] == 1
    assert qs.pilot_ms('pilot50') == 50 and qs.pilot_ms('pilotx') is None


def test_output_path():
    taken = {'data/sub-101_q_search.csv', 'data/sub-101_q_search_2.csv'}
    assert qs.output_path('101', taken.__contains__) == 'data/sub-101_q_search_3.csv'
    assert qs.output_path('102', taken.__contains__) == 'data/sub-102_q_search.csv'


def test_block_intro_text():
    txt = qs.block_intro_text(2, 4, 'B', -3)
    assert '25%' in txt and '−5' in txt and '−3' in txt and 'Block 2 of 4' in txt


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
        print('ok', t.__name__)
    print(f'{len(tests)} tests passed')
