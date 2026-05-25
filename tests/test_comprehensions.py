import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sards.shell import run
from sards.data_types import List, Dict, String, Number

def run_last(code):
    """Run multi-line code and return the last statement's value."""
    result, error = run('<test>', code)
    if error:
        return None, str(error.details)
    # Multi-line programs return a ListNode result — take last element
    if isinstance(result, List):
        val = result.elements[-1] if result.elements else result
    else:
        val = result
    return val, None

passed = failed = 0

def check(desc, code, expected_repr):
    global passed, failed
    result, error = run_last(code)
    if error:
        print(f"FAIL [{desc}]: error -> {error}")
        failed += 1
        return
    got = repr(result)
    if got == expected_repr:
        print(f"PASS [{desc}]  => {got}")
        passed += 1
    else:
        print(f"FAIL [{desc}]: expected {expected_repr!r}, got {got!r}")
        failed += 1

# ────────────────────────────────────────────
# LIST COMPREHENSIONS  — Cycle (range-based)
# ────────────────────────────────────────────

check(
    "List comp Cycle: squares of 1 to 5",
    "[i * i Cycle i = 1 : 5]",
    "[1, 4, 9, 16, 25]"
)

check(
    "List comp Cycle: evens 0 to 10 (step 2)",
    "[i Cycle i = 0 : 10 : 2]",
    "[0, 2, 4, 6, 8, 10]"
)

check(
    "List comp Cycle + when: odd numbers 1 to 10",
    "[i Cycle i = 1 : 10 when i % 2 == 1]",
    "[1, 3, 5, 7, 9]"
)

check(
    "List comp Cycle: countdown 5 to 1 (step -1)",
    "[i Cycle i = 5 : 1 : -1]",
    "[5, 4, 3, 2, 1]"
)

check(
    "List comp Cycle + when + expr: double if > 3",
    "[i * 2 Cycle i = 1 : 6 when i > 3]",
    "[8, 10, 12]"
)

# ────────────────────────────────────────────
# LIST COMPREHENSIONS  — trace (collection-based)
# ────────────────────────────────────────────

check(
    "List comp trace: double each element",
    "nums = [1, 2, 3, 4, 5]\n[x * 2 trace x <- nums]",
    "[2, 4, 6, 8, 10]"
)

check(
    "List comp trace + when: filter > 2",
    "nums = [1, 2, 3, 4, 5]\n[x trace x <- nums when x > 2]",
    "[3, 4, 5]"
)

check(
    "List comp trace: characters of a string",
    'word = "hello"\n[c trace c <- word]',
    '[h, e, l, l, o]'
)

check(
    "List comp trace: unpack pairs and sum",
    "pairs = [[1, 10], [2, 20], [3, 30]]\n[k + v trace k, v <- pairs]",
    "[11, 22, 33]"
)

check(
    "List comp trace + when: filter pairs where k > 1",
    "pairs = [[1, 10], [2, 20], [3, 30]]\n[v trace k, v <- pairs when k > 1]",
    "[20, 30]"
)

# ────────────────────────────────────────────
# DICT COMPREHENSIONS  — Cycle (range-based)
# ────────────────────────────────────────────

check(
    "Dict comp Cycle: i -> i*i for 1..4",
    "{i : i * i Cycle i = 1 : 4}",
    '{1: 1, 2: 4, 3: 9, 4: 16}'
)

check(
    "Dict comp Cycle + when: odd keys 1..6",
    "{i : i * 10 Cycle i = 1 : 6 when i % 2 == 1}",
    '{1: 10, 3: 30, 5: 50}'
)

check(
    "Dict comp Cycle: key as string via fstring",
    "{i : i * i Cycle i = 1 : 3}",
    '{1: 1, 2: 4, 3: 9}'
)

# ────────────────────────────────────────────
# DICT COMPREHENSIONS  — trace (collection-based)
# ────────────────────────────────────────────

check(
    "Dict comp trace: num -> squared",
    "nums = [1, 2, 3]\n{x : x * x trace x <- nums}",
    '{1: 1, 2: 4, 3: 9}'
)

check(
    "Dict comp trace: unpack pairs to dict",
    'pairs = [["a", 1], ["b", 2], ["c", 3]]\n{k : v trace k, v <- pairs}',
    "{'a': 1, 'b': 2, 'c': 3}"
)

check(
    "Dict comp trace + when: filter values > 2",
    "nums = [1, 2, 3, 4]\n{x : x * 2 trace x <- nums when x > 2}",
    '{3: 6, 4: 8}'
)

# ────────────────────────────────────────────
# SCOPE ISOLATION
# ────────────────────────────────────────────

check(
    "Scope isolation: outer var unchanged after Cycle comp",
    "i = 99\ndummy = [i * 2 Cycle j = 1 : 3]\ni",
    "99"
)

check(
    "Scope isolation: outer var unchanged after trace comp",
    "x = 42\ndata = [1, 2, 3]\ndummy = [x trace y <- data]\nx",
    "42"
)

print(f"\n{'='*52}")
print(f"  {passed}/{passed + failed} tests passed")
print(f"{'='*52}")
