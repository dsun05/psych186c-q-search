# psych186c-q-search

PSYCH 186C final project, Group 8 (David Sun, Jackson Kim): a yes/no signal detection
task where participants report whether a brief 4 × 4 grid of O's contains a Q. The
design crosses Q frequency (25% vs. 50%) with the miss penalty (−1 vs. −5 points) and
compares observers' criterion shifts with the ideal observer.

## Layout

- `q_search/`: the PsychoPy project to zip and upload.
  - `q_search.psyexp`: the Builder experiment.
  - `q_search_helpers.py`: trial building, scoring, and roster lookup.
  - `participant_assignment.csv`: each classmate's ID and block order, from `make_assignment.py`.
  - `data/`: created at run time; one CSV per session, `sub-<id>_q_search.csv`.
    `elapsed_s` is seconds since the session started, so the last row gives session length.
- `q_search_tools/`: not part of the submission.
  - `build_psyexp.py`: generates the `.psyexp`. Rerunning it overwrites Builder edits.
  - `make_assignment.py`: builds the roster CSV from `roster.txt` (one classmate first name per line).
  - `test_helpers.py`: `python3 test_helpers.py`.

## Piloting

Enter `pilot50`, `pilot100`, or `pilot150` as the participant name to run with that grid
duration in ms. Then set `GRID_DUR` in the `setup` code component of the `welcome` routine.

## Before submitting

Edit the `.psyexp` one person at a time (Builder rewrites the whole file). Empty `data/`,
make sure `participant_assignment.csv` is present, zip `q_search/`, and test on a lab computer.
