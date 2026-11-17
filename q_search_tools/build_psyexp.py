"""Generate ../q_search/q_search.psyexp with PsychoPy's experiment API.

Run with PsychoPy's bundled Python:
  PYTHONHOME=/Applications/PsychoPy.app/Contents/Resources \
    /Applications/PsychoPy.app/Contents/MacOS/python build_psyexp.py

After this, edit the experiment in Builder as usual; rerunning this script
overwrites Builder edits.
"""
from pathlib import Path

from psychopy import experiment
from psychopy.experiment.components.code import CodeComponent
from psychopy.experiment.components.keyboard import KeyboardComponent
from psychopy.experiment.components.text import TextComponent
from psychopy.experiment.loops import TrialHandler

OUT = Path(__file__).resolve().parent.parent / 'q_search' / 'q_search.psyexp'

# Imports go in Before Experiment (module level). Importing inside Begin
# Experiment makes the names local to PsychoPy's run() function, which breaks
# PsychoPy's own earlier use of os.
BEFORE_EXPERIMENT = '''\
import os
import random
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q_search_helpers as qs
'''

BEGIN_EXPERIMENT = '''\
# ---- Set after piloting: how long the grid is shown (seconds) ----
GRID_DUR = 0.100
TASK_VERSION = 'v1'

FIX_DUR = 0.5        # fixation cross
MASK_DUR = 0.2       # pattern mask right after the grid
RESP_DEADLINE = 3.0  # seconds from trial start (2.5 s after grid onset)
FEEDBACK_DUR = 0.8

# Seed with the participant's name so each person gets their own order
participant_name = expInfo['participant'].strip().lower()
random.seed(participant_name)

# Block order comes from the roster, assigned before data collection
roster = data.importConditions('participant_assignment.csv')
info = qs.lookup_participant(participant_name, roster)
sub_id = info['sub_id']
block_order = info['block_order']

# Pilot names like 'pilot50' override the grid duration (in ms)
if qs.pilot_ms(participant_name) is not None:
    grid_dur = qs.pilot_ms(participant_name) / 1000
else:
    grid_dur = GRID_DUR
grid_on = FIX_DUR
mask_on = FIX_DUR + grid_dur
prompt_on = mask_on + MASK_DUR

# Build every trial up front so the sequence depends only on the seed
practice_trials = qs.build_practice(random)
block_trials = {code: qs.build_block(code, random) for code in block_order}

os.makedirs('data', exist_ok=True)
output_filepath = qs.output_path(sub_id, os.path.exists)
session_list = []

# Practice runs first with the same trial routines as the main blocks
phase = 'practice'
block_num = 0
block_code = 'practice'
q_freq = 0.5
miss_penalty = 1
current_trials = practice_trials
trial_i = 0
block_score = 0
total_score = 0
trial_overall = 0
'''

NAME_CHECK_SKIP_IF = "info['roster_match'] or qs.pilot_ms(participant_name) is not None"

NAME_CHECK_BEGIN = '''\
name_check_str = (f"The name '{expInfo['participant']}' is not on the class list.\\n\\n"
                  "Press ESCAPE to quit, then re-enter your first name\\n"
                  "as one word.\\n\\n"
                  "Press SPACE only if the experimenter tells you to.")
'''

WELCOME_TEXT = (
    'Welcome!\n\n'
    'Each trial shows a +, then a quick flash of a 4 × 4 grid of letters, '
    'then a scrambled pattern.\n\n'
    'Usually every letter is an O. Sometimes one of them is a Q.\n\n'
    'Press J if you saw a Q.\n'
    'Press F if there was no Q.\n\n'
    'You have about 2 seconds to answer. You earn and lose points '
    'depending on your answers.\n\n'
    'First, 8 practice trials.\n'
    'Put your fingers on F and J, then press SPACE to start.'
)

TRIAL_BEGIN = '''\
cur_trial = current_trials[trial_i]
grid_str = cur_trial['grid_text']
mask_str = cur_trial['mask_text']
'''

TRIAL_END = '''\
key = qs.first_key(resp.keys)
rt = resp.rt if key is not None else None
if isinstance(rt, (list, tuple)):
    rt = rt[0] if rt else None
outcome, said_present, points = qs.score(cur_trial['q_present'], key, miss_penalty)
block_score += points
if phase == 'main':
    total_score += points
    trial_overall += 1
fb_str, fb_color = qs.feedback(outcome, points)

# Actual on-screen grid time (None if a key ended the trial mid-grid)
grid_shown = None
if search_grid.tStartRefresh is not None and search_grid.tStopRefresh is not None:
    grid_shown = round(search_grid.tStopRefresh - search_grid.tStartRefresh, 4)

session_list.append({
    'sub_id': sub_id,
    'roster_match': info['roster_match'],
    'is_team': info['is_team'],
    'task_version': TASK_VERSION,
    'block_order': block_order,
    'phase': phase,
    'block_num': block_num,
    'block_code': block_code,
    'q_freq': q_freq,
    'miss_penalty': miss_penalty,
    'trial_in_block': trial_i + 1,
    'trial_overall': trial_overall if phase == 'main' else None,
    'q_present': cur_trial['q_present'],
    'q_loc': cur_trial['q_loc'],
    'grid_dur_set': grid_dur,
    'grid_dur_shown': grid_shown,
    'key': key,
    'said_present': said_present,
    'outcome': outcome,
    'correct': None if outcome == 'timeout' else int(outcome in ('hit', 'correct_rejection')),
    'rt': rt,
    'points': points,
    'block_score': block_score,
    'total_score': total_score,
})
'''

FEEDBACK_END = '''\
trial_i += 1
# Save after every trial so a crash or Escape keeps everything so far
pd.DataFrame(session_list).to_csv(output_filepath, index=False)
'''

BLOCK_INTRO_BEGIN = '''\
prev_block_score = block_score if blocks.thisRepN > 0 else None
phase = 'main'
block_num = blocks.thisRepN + 1
block_code = block_order[blocks.thisRepN]
q_freq = qs.BLOCKS[block_code]['q_freq']
miss_penalty = qs.BLOCKS[block_code]['miss_penalty']
current_trials = block_trials[block_code]
trial_i = 0
block_score = 0
block_intro_str = qs.block_intro_text(block_num, len(block_order), block_code, prev_block_score)
if block_num == 1:
    block_intro_str = 'Practice complete!\\n\\n' + block_intro_str
'''

THANKS_BEGIN = '''\
pd.DataFrame(session_list).to_csv(output_filepath, index=False)
thanks_str = (f"All done. Thank you!\\n\\nTotal points: {total_score}\\n\\n"
              f"Your data file is:\\n{output_filepath}\\n\\n"
              "Upload it to our group's folder in SUBMIT DATA HERE.\\n\\n"
              "Press SPACE to exit.")
'''

END_EXPERIMENT = '''\
if session_list:
    pd.DataFrame(session_list).to_csv(output_filepath, index=False)
'''


def code(exp, routine, name, **tabs):
    c = CodeComponent(exp=exp, parentName=routine.name, name=name)
    for tab, src in tabs.items():
        c.params[tab.replace('_', ' ')].val = src
    routine.addComponent(c)
    return c


def text(exp, routine, name, value, start='0', stop='', stop_type='duration (s)',
         height=0.035, pos='(0, 0)', font='Arial', color='white', wrap=1.3,
         every_repeat=False):
    c = TextComponent(exp=exp, parentName=routine.name, name=name)
    p = c.params
    p['text'].val = value
    if every_repeat:
        p['text'].updates = 'set every repeat'
    p['startVal'].val = start
    p['stopType'].val = stop_type
    p['stopVal'].val = stop
    p['letterHeight'].val = height
    p['pos'].val = pos
    p['font'].val = font
    p['color'].val = color
    p['wrapWidth'].val = wrap
    routine.addComponent(c)
    return c


def space_key(exp, routine, name):
    k = KeyboardComponent(exp=exp, parentName=routine.name, name=name)
    k.params['allowedKeys'].val = "'space'"
    k.params['stopVal'].val = ''
    k.params['store'].val = 'nothing'
    routine.addComponent(k)
    return k


def build():
    exp = experiment.Experiment()
    s = exp.settings.params
    s['expName'].val = 'q_search'
    s['Experiment info'].val = "{'participant':''}"
    s['Full-screen window'].val = True
    s['Units'].val = 'height'
    s['Show mouse'].val = False
    s['runMode'].val = 1
    s['Use version'].val = ''
    # The experiment writes its own CSV; turn off PsychoPy's files
    for name in ('Save csv file', 'Save excel file', 'Save log file',
                 'Save psydat file', 'Save wide csv file', 'Save hdf5 file'):
        s[name].val = False

    name_check = exp.addRoutine('name_check')
    name_check.settings.params['skipIf'].val = NAME_CHECK_SKIP_IF
    code(exp, name_check, 'name_check_code', Begin_Routine=NAME_CHECK_BEGIN)
    text(exp, name_check, 'name_check_text', '$name_check_str', every_repeat=True)
    space_key(exp, name_check, 'name_check_key')

    welcome = exp.addRoutine('welcome')
    code(exp, welcome, 'setup', Before_Experiment=BEFORE_EXPERIMENT,
         Begin_Experiment=BEGIN_EXPERIMENT,
         End_Experiment=END_EXPERIMENT)
    text(exp, welcome, 'welcome_text', WELCOME_TEXT, height=0.03)
    space_key(exp, welcome, 'welcome_key')

    trial = exp.addRoutine('trial')
    code(exp, trial, 'trial_code', Begin_Routine=TRIAL_BEGIN, End_Routine=TRIAL_END)
    text(exp, trial, 'fixation', '+', stop='FIX_DUR', height=0.05)
    text(exp, trial, 'search_grid', '$grid_str', start='grid_on', stop='grid_dur',
         height=0.05, font='Courier New', every_repeat=True)
    text(exp, trial, 'mask_grid', '$mask_str', start='mask_on', stop='MASK_DUR',
         height=0.05, font='Courier New', every_repeat=True)
    text(exp, trial, 'prompt', 'F = no Q          J = Q', start='prompt_on',
         stop='RESP_DEADLINE', stop_type='time (s)', height=0.03, pos='(0, -0.3)')
    resp = KeyboardComponent(exp=exp, parentName='trial', name='resp')
    resp.params['allowedKeys'].val = "'f','j'"
    resp.params['store'].val = 'first key'
    resp.params['startVal'].val = 'grid_on'
    resp.params['stopType'].val = 'time (s)'
    resp.params['stopVal'].val = 'RESP_DEADLINE'
    trial.addComponent(resp)

    feedback = exp.addRoutine('feedback')
    code(exp, feedback, 'feedback_code', End_Routine=FEEDBACK_END)
    fb = text(exp, feedback, 'feedback_text', '$fb_str', stop='FEEDBACK_DUR',
              height=0.05, every_repeat=True)
    fb.params['color'].val = '$fb_color'
    fb.params['color'].updates = 'set every repeat'

    block_intro = exp.addRoutine('block_intro')
    code(exp, block_intro, 'block_intro_code', Begin_Routine=BLOCK_INTRO_BEGIN)
    text(exp, block_intro, 'block_intro_text', '$block_intro_str', every_repeat=True)
    space_key(exp, block_intro, 'block_intro_key')

    thanks = exp.addRoutine('thanks')
    code(exp, thanks, 'thanks_code', Begin_Routine=THANKS_BEGIN)
    text(exp, thanks, 'thanks_text', '$thanks_str', every_repeat=True)
    space_key(exp, thanks, 'thanks_key')

    # Flow: welcome, name_check, [practice: trial, feedback],
    #       [blocks: block_intro, [trials: trial, feedback]], thanks
    flow = exp.flow
    for i, r in enumerate([welcome, name_check, trial, feedback, block_intro,
                           trial, feedback, thanks]):
        flow.addRoutine(r, i)
    trials = TrialHandler(exp, name='trials', loopType='sequential',
                          nReps='len(current_trials)')
    flow.addLoop(trials, startPos=5, endPos=7)
    blocks = TrialHandler(exp, name='blocks', loopType='sequential',
                          nReps='len(block_order)')
    flow.addLoop(blocks, startPos=4, endPos=9)
    practice = TrialHandler(exp, name='practice', loopType='sequential',
                            nReps='len(practice_trials)')
    flow.addLoop(practice, startPos=2, endPos=4)

    exp.saveToXML(str(OUT))
    print('wrote', OUT)


if __name__ == '__main__':
    build()
