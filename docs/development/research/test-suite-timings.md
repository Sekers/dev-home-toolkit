# Test suite timings

What the tests spend their time on, measured to see whether the whole suite's run time buys
anything, and what would shorten it.

## How

On 2026-11-11, on a Windows PC with 8 cores and Python 3.14.8, with the tests of `e9bdb92`, each
test file was timed on a single worker with pytest's `--durations=0`, so each test was timed
without others competing. At pytest's default of one worker per core, the whole suite took 205 to
252 seconds in three runs that day.

## Results

| File | Time on one worker | Tests | Average per test |
| --- | --- | --- | --- |
| `test_setup.py` | 198 s | 336 | 0.45 s |
| `test_sync.py` | 184 s | 98 | 1.7 s |
| `test_setup_questions.py` | 147 s | 173 | 0.7 s |
| `test_facts.py` | 74 s | 132 | 0.5 s |
| The other nine files | 104 s together | 315 | |

- The tests took 708 s in all. 421 take under 0.05 s each, 4.5 s together; the 170 that take
  over 1 s take 384 s, 54% of the time.
- The slow tests run setup or a sync as a separate process against real git repos: fetch, push,
  merge, and locks. [Testing](../testing.md) asks for that, since git and the file system stay
  real, and it's what finds a sync's bugs.
- Building a module's sandbox takes 5 to 15 s: 14.6 s for `test_sync.py`'s, 5.4 s for
  `test_setup.py`'s.
- Each file marked `xdist_group`, seven of the thirteen, runs on one worker against one shared
  sandbox. So a run with one worker per core takes about as long as its slowest group, 198 s for
  `test_setup.py` alone, where 708 s spread evenly over 8 workers would take about 88 s. Most
  workers sit idle once their groups finish.
- Only `test_docs.py` reads `README.md` and the pages under `docs/`, and ruff and mypy read no
  Markdown, so a commit that changes only those runs `test_docs.py` alone.
- `written_files` in `test_docs.py` walks all of `.venv`, 3,596 files in 0.35 s, to find 175.

## Limits

- One PC, and one timed run of each file.
- The estimate below isn't measured, and no test was judged on whether it earns its time.

## What would shorten it

Splitting the three largest groups, in `test_setup.py`, `test_sync.py`, and
`test_setup_questions.py`, into several groups, each with a sandbox of its own, would spread the
work across the cores: perhaps about 1.5 minutes in place of 3.5, at 5 to 15 s of building for
each extra sandbox. It would also shrink the order dependence between tests that share a sandbox.

## When to redo it

After the groups change, or once the suite takes a minute or more longer than here.
