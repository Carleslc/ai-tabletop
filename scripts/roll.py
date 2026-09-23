#!/usr/bin/env python3
"""Dice roller for tabletop RPG sessions, with standard dice notation.

Usage:
  python scripts/roll.py <expression>
  python scripts/roll.py check <value> [--bonus N | --penalty N]

Expressions add or subtract terms: dice (NdX) and numbers.
  d100, 1d6, 1d4+2, 1d8+2d6+3   plain dice (d% = d100)
  2d20kh1, 2d20kl1              keep the highest / lowest N (advantage / disadvantage)
  4d6kh3, 4d6dl1                keep the highest 3 = drop the lowest 1 (dh = drop highest)
  d6!, 3d6!                     exploding dice: a die showing its maximum rolls again and adds
  5d10>=8, 6d6>=5, 5d10!>=8     dice pools: count the dice that meet the target (successes)
  4dF                           Fate/Fudge dice: each die is -1, 0 or +1

check <value> rolls d100 against a Call of Cthulhu (7e) skill or characteristic and gives
the success level. --bonus/--penalty N adds N bonus or penalty dice (N tens dice: keep the
lowest tens for a bonus, the highest for a penalty).
"""
import random
import re
import sys

TERM_RE = re.compile(
    r"^(?P<n>\d*)d(?P<sides>\d+|%|f)"
    r"(?P<explode>!)?"
    r"(?:(?P<kd>kh|kl|dh|dl|k|d)(?P<count>\d+))?"
    r"(?:(?P<cmp>>=|<=|>|<|=)(?P<target>\d+))?$",
    re.IGNORECASE,
)
MAX_DICE = 100
MAX_EXPLOSIONS = 100


def roll_die(sides):
    return random.randint(-1, 1) if sides == "F" else random.randint(1, sides)


def roll_term(term):
    """Roll one dice term. Returns (description, value, is_pool)."""
    m = TERM_RE.match(term)
    if not m:
        raise ValueError("can't read %r; use terms like 2d6, 2d20kh1, 4d6kh3, d6!, 5d10>=8, 4dF" % term)
    n = int(m["n"] or 1)
    sides = m["sides"].upper()
    sides = 100 if sides == "%" else "F" if sides == "F" else int(sides)
    if not 1 <= n <= MAX_DICE:
        raise ValueError("roll 1 to %d dice per term" % MAX_DICE)
    if sides != "F" and not 2 <= sides <= 1000:
        raise ValueError("dice need 2 to 1000 sides")
    if m["explode"] and sides == "F":
        raise ValueError("Fate dice can't explode")

    # Each die is a list of rolls: several when it explodes.
    dice = []
    for _ in range(n):
        rolls = [roll_die(sides)]
        while m["explode"] and rolls[-1] == sides and len(rolls) <= MAX_EXPLOSIONS:
            rolls.append(roll_die(sides))
        dice.append(rolls)

    kept = list(range(n))
    if m["kd"]:
        kd, count = m["kd"].lower(), int(m["count"])
        kd = {"k": "kh", "d": "dl"}.get(kd, kd)
        if count > n:
            raise ValueError("can't keep or drop %d of %d dice" % (count, n))
        by_value = sorted(range(n), key=lambda i: sum(dice[i]))
        if kd == "kh":
            kept = by_value[n - count:]
        elif kd == "kl":
            kept = by_value[:count]
        elif kd == "dh":
            kept = by_value[:n - count]
        else:
            kept = by_value[count:]

    def show(i):
        face = lambda r: {-1: "-", 0: "0", 1: "+"}[r] if sides == "F" else str(r)
        s = "+".join(face(r) + ("!" if m["explode"] and r == sides else "") for r in dice[i])
        return s if i in kept else "(%s)" % s

    shown = "[%s]" % ", ".join(show(i) for i in range(n))
    if m["cmp"]:
        target = int(m["target"])
        test = {">=": lambda r: r >= target, "<=": lambda r: r <= target, ">": lambda r: r > target,
                "<": lambda r: r < target, "=": lambda r: r == target}[m["cmp"]]
        # In a pool every roll counts on its own, exploded ones too.
        hits = sum(1 for i in kept for r in dice[i] if test(r))
        return "%s: %s -> %d success%s" % (term, shown, hits, "" if hits == 1 else "es"), hits, True
    value = sum(sum(dice[i]) for i in kept)
    return "%s: %s -> %d" % (term, shown, value), value, False


def roll_expr(expr):
    """Roll a whole expression. Returns (detail lines, total, all terms were pools)."""
    expr = re.sub(r"\s+", "", expr)
    if not expr:
        raise ValueError("empty expression")
    parts = re.findall(r"([+-]?)([^+-]+)", expr)
    if "".join(sign + term for sign, term in parts) != expr:
        raise ValueError("can't read %r" % expr)
    lines, total, pools = [], 0, []
    for sign, term in parts:
        if term.isdigit():
            value = int(term)
        else:
            line, value, is_pool = roll_term(term)
            lines.append(line)
            pools.append(is_pool)
        total += -value if sign == "-" else value
    return lines, total, bool(pools) and all(pools)


def success_level(roll, value):
    if roll == 1:
        return "Critical success"
    if roll > value:
        if roll >= 96 and value < 50 or roll == 100:
            return "Fumble"
        return "Failure"
    if roll <= value // 5:
        return "Extreme success"
    if roll <= value // 2:
        return "Hard success"
    return "Regular success"


def check(value, bonus=0, penalty=0):
    """Call of Cthulhu d100 check, with bonus or penalty dice."""
    if not 1 <= value <= 100:
        raise ValueError("check value must be 1..100")
    if bonus and penalty:
        raise ValueError("bonus and penalty dice cancel out: give only the difference")
    extra = bonus or penalty
    if not 0 <= extra <= 2:
        raise ValueError("use 0 to 2 bonus or penalty dice")
    units = random.randint(0, 9)
    tens = [random.randint(0, 9) * 10 for _ in range(1 + extra)]
    totals = [t + units or 100 for t in tens]
    roll = (min if bonus else max)(totals)
    if extra:
        kind = "bonus" if bonus else "penalty"
        detail = "1D100 with %d %s di%s: tens %s, units %d -> %d" % (
            extra, kind, "e" if extra == 1 else "ce", [str(t).zfill(2) for t in tens], units, roll)
    else:
        detail = "1D100 = %d" % roll
    return "%s; %s" % (detail, success_level(roll, value))


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if argv[1].lower() == "check":
        args = argv[2:]
        if not args:
            print("usage: roll.py check <value> [--bonus N | --penalty N]", file=sys.stderr)
            return 2
        value = int(args[0])
        opts = {"--bonus": 0, "--penalty": 0}
        rest = args[1:]
        while rest:
            flag = rest.pop(0)
            if flag not in opts:
                raise ValueError("unknown option %s" % flag)
            opts[flag] = int(rest.pop(0)) if rest and rest[0].isdigit() else 1
        print(check(value, opts["--bonus"], opts["--penalty"]))
        return 0
    lines, total, pool = roll_expr(" ".join(argv[1:]))
    print("\n".join(lines))
    print("successes = %d" % total if pool else "total = %d" % total)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception as exc:
        print("error: %s" % exc, file=sys.stderr)
        raise SystemExit(1)
