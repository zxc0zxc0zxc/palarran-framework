"""Independent CPU-only behavior checks; candidate must create solution.py."""
import runpy

unique = runpy.run_path('solution.py')['unique']
assert unique([]) == []
assert unique([2, 1, 2, 3, 1]) == [2, 1, 3]
assert unique([0, False, 0]) == [0]
