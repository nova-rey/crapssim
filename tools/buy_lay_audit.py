"""Audit Buy/Lay behavior for bankroll debits, payouts, and commissions."""
from __future__ import annotations

import datetime as dt
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crapssim.bet import Buy, Lay, compute_commission
from crapssim.strategy.tools import NullStrategy
from crapssim.table import Player, Table, TableUpdate

BANKROLL = 100.0
WAGER = 20.0
TOL = 0.01

BET_FAMILIES: dict[str, Sequence[int]] = {
    "4/10": (4, 10),
    "5/9": (5, 9),
}

DICE_MAP: dict[int, tuple[int, int]] = {
    2: (1, 1),
    3: (1, 2),
    4: (2, 2),
    5: (2, 3),
    6: (2, 4),
    7: (3, 4),
    8: (4, 4),
    9: (3, 6),
    10: (5, 5),
    11: (5, 6),
    12: (6, 6),
}

REPORT_PATH = Path("REPORT_buy_lay_audit.md")

ModeKey = Literal["A", "B"]
BetKind = Literal["Buy", "Lay"]


@dataclass(slots=True)
class ModeConfig:
    key: ModeKey
    description: str
    buy_vig_on_win: bool


MODES: tuple[ModeConfig, ...] = (
    ModeConfig("A", "Commission on win (no upfront vig)", True),
    ModeConfig("B", "Commission upfront (vig paid on placement)", False),
)


@dataclass(slots=True)
class CheckRecord:
    category: str
    mode: ModeKey
    bet: BetKind
    family: str
    scenario: str
    observed: str
    expected: str
    passed: bool | None


@dataclass(slots=True)
class AffordabilityRecord:
    category: str
    mode: ModeKey
    bet: BetKind
    family: str
    first_cost_obs: float
    first_cost_exp: float
    max_count_obs: int
    max_count_exp: int
    end_bankroll_obs: float
    end_bankroll_exp: float
    passed: bool


def within_tolerance(observed: float, expected: float, tol: float = TOL) -> bool:
    return abs(observed - expected) <= tol


def deterministic_roll(table: Table, total: int) -> None:
    dice_values = DICE_MAP[total]
    try:
        TableUpdate.roll(table, fixed_outcome=dice_values)
    except TypeError:  # Some versions require lists instead of tuples
        TableUpdate.roll(table, fixed_outcome=list(dice_values))
    TableUpdate.update_bets(table)


def create_table(mode: ModeConfig) -> Table:
    table = Table()
    table.settings["buy_vig_on_win"] = mode.buy_vig_on_win
    return table


def add_auditor(table: Table) -> Player:
    return table.add_player(bankroll=BANKROLL, strategy=NullStrategy(), name="Auditor")


def compute_incremental_cost(player: Player, bet: Buy | Lay) -> float:
    table = player.table
    existing = player.already_placed_bets(bet)
    existing_cost = sum(b.placement_cost(table) for b in existing)
    combined = bet
    for ex in existing:
        combined = combined + ex
    if hasattr(combined, "wager"):
        combined.wager = combined.amount
    new_cost = combined.placement_cost(table)
    return float(new_cost - existing_cost)


def place_and_charge(player: Player, bet: Buy | Lay) -> tuple[bool, float, float]:
    expected_cost = compute_incremental_cost(player, bet)
    before = player.bankroll
    player.add_bet(bet)
    delta = before - player.bankroll
    placed = within_tolerance(delta, expected_cost)
    return placed, delta, expected_cost


def format_money(value: float) -> str:
    return f"${value:0.2f}"


def run_affordability_checks(records: list[AffordabilityRecord], raw: list[CheckRecord]) -> None:
    for mode in MODES:
        for bet_cls, bet_name in ((Buy, "Buy"), (Lay, "Lay")):
            for family, numbers in BET_FAMILIES.items():
                number = numbers[0]
                table = create_table(mode)
                player = add_auditor(table)

                expected_remaining = BANKROLL
                first_obs_cost = None
                first_exp_cost = None
                observed_count = 0
                expected_count = 0

                while True:
                    bet = bet_cls(number, WAGER)
                    expected_cost = compute_incremental_cost(player, bet)
                    can_afford = expected_cost <= player.bankroll + TOL
                    if not can_afford:
                        # Confirm rejection without altering reference values.
                        before = player.bankroll
                        player.add_bet(bet)
                        assert within_tolerance(before - player.bankroll, 0.0)
                        break

                    placed, delta, exp_cost = place_and_charge(player, bet)
                    if not placed:
                        break
                    if first_obs_cost is None:
                        first_obs_cost = delta
                        first_exp_cost = exp_cost
                    observed_count += 1

                    if exp_cost <= expected_remaining + TOL:
                        expected_remaining -= exp_cost
                        expected_count += 1

                end_bankroll_obs = player.bankroll
                end_bankroll_exp = expected_remaining
                passed = (
                    within_tolerance(first_obs_cost, first_exp_cost)
                    and observed_count == expected_count
                    and within_tolerance(end_bankroll_obs, end_bankroll_exp)
                )
                records.append(
                    AffordabilityRecord(
                        category="Affordability",
                        mode=mode.key,
                        bet=bet_name,
                        family=family,
                        first_cost_obs=first_obs_cost,
                        first_cost_exp=first_exp_cost,
                        max_count_obs=observed_count,
                        max_count_exp=expected_count,
                        end_bankroll_obs=end_bankroll_obs,
                        end_bankroll_exp=end_bankroll_exp,
                        passed=passed,
                    )
                )
                raw.append(
                    CheckRecord(
                        category="Affordability",
                        mode=mode.key,
                        bet=bet_name,
                        family=family,
                        scenario="Placement capacity",
                        observed=(
                            f"first={format_money(first_obs_cost)}; "
                            f"max={observed_count}; end={format_money(end_bankroll_obs)}"
                        ),
                        expected=(
                            f"first={format_money(first_exp_cost)}; "
                            f"max={expected_count}; end={format_money(end_bankroll_exp)}"
                        ),
                        passed=passed,
                    )
                )


def expected_loss_delta(mode: ModeConfig) -> float:
    if mode.buy_vig_on_win:
        return -WAGER
    commission = compute_commission(WAGER)
    return -(WAGER + commission)


def run_loss_checks(records: list[CheckRecord]) -> None:
    for mode in MODES:
        for bet_cls, bet_name in ((Buy, "Buy"), (Lay, "Lay")):
            for family, numbers in BET_FAMILIES.items():
                number = numbers[0]
                table = create_table(mode)
                player = add_auditor(table)
                initial = player.bankroll
                placed, delta, exp_cost = place_and_charge(player, bet_cls(number, WAGER))
                assert placed, "Initial placement failed"
                loss_total = 7 if bet_name == "Buy" else number
                deterministic_roll(table, loss_total)
                observed_delta = player.bankroll - initial
                expected_delta = expected_loss_delta(mode)
                passed = within_tolerance(observed_delta, expected_delta)
                records.append(
                    CheckRecord(
                        category="Loss",
                        mode=mode.key,
                        bet=bet_name,
                        family=family,
                        scenario="Loss resolution",
                        observed=format_money(observed_delta),
                        expected=format_money(expected_delta),
                        passed=passed,
                    )
                )


def commission_upfront(mode: ModeConfig) -> float:
    return 0.0 if mode.buy_vig_on_win else compute_commission(WAGER)


def run_win_checks(records: list[CheckRecord]) -> None:
    for mode in MODES:
        for bet_cls, bet_name in ((Buy, "Buy"), (Lay, "Lay")):
            for family, numbers in BET_FAMILIES.items():
                number = numbers[0]
                table = create_table(mode)
                player = add_auditor(table)
                initial = player.bankroll
                placed, _, _ = place_and_charge(player, bet_cls(number, WAGER))
                assert placed, "Initial placement failed"
                win_total = number if bet_name == "Buy" else 7
                deterministic_roll(table, win_total)
                final_bankroll = player.bankroll
                net_delta = final_bankroll - initial

                payout_ratio = bet_cls.true_odds[number]
                gross_payout = WAGER * payout_ratio
                commission_on_win = 0.0 if not mode.buy_vig_on_win else compute_commission(gross_payout)
                raw_win = gross_payout - commission_on_win
                expected_net = raw_win - commission_upfront(mode)
                actual_raw_win = net_delta + commission_upfront(mode)

                raw_pass = within_tolerance(actual_raw_win, raw_win)
                passed = within_tolerance(net_delta, expected_net)
                records.append(
                    CheckRecord(
                        category="Win",
                        mode=mode.key,
                        bet=bet_name,
                        family=family,
                        scenario="Raw win credited",
                        observed=format_money(actual_raw_win),
                        expected=format_money(raw_win),
                        passed=raw_pass,
                    )
                )
                records.append(
                    CheckRecord(
                        category="Win",
                        mode=mode.key,
                        bet=bet_name,
                        family=family,
                        scenario="Net bankroll delta",
                        observed=format_money(net_delta),
                        expected=format_money(expected_net),
                        passed=passed,
                    )
                )


def run_press_checks(records: list[CheckRecord]) -> None:
    for mode in MODES:
        for bet_cls, bet_name in ((Buy, "Buy"), (Lay, "Lay")):
            for family, numbers in BET_FAMILIES.items():
                number = numbers[0]
                table = create_table(mode)
                player = add_auditor(table)
                placed, _, _ = place_and_charge(player, bet_cls(number, WAGER))
                assert placed, "Initial placement failed"
                second = bet_cls(number, WAGER)
                placed, delta, exp_cost = place_and_charge(player, second)
                expected_increment = WAGER if mode.buy_vig_on_win else WAGER + compute_commission(WAGER)
                passed = within_tolerance(delta, expected_increment)
                records.append(
                    CheckRecord(
                        category="Press",
                        mode=mode.key,
                        bet=bet_name,
                        family=family,
                        scenario="Second increment",
                        observed=format_money(delta),
                        expected=format_money(expected_increment),
                        passed=passed,
                    )
                )


def run_removal_checks(records: list[CheckRecord]) -> None:
    for mode in MODES:
        for bet_cls, bet_name in ((Buy, "Buy"), (Lay, "Lay")):
            for family, numbers in BET_FAMILIES.items():
                number = numbers[0]
                table = create_table(mode)
                player = add_auditor(table)
                initial = player.bankroll
                placed, _, _ = place_and_charge(player, bet_cls(number, WAGER))
                assert placed, "Initial placement failed"
                outstanding_bet = player.get_bets_by_type(bet_cls)[0]
                player.remove_bet(outstanding_bet)
                final = player.bankroll
                expected = -commission_upfront(mode)
                delta = final - initial
                passed = within_tolerance(delta, expected)
                records.append(
                    CheckRecord(
                        category="Removal",
                        mode=mode.key,
                        bet=bet_name,
                        family=family,
                        scenario="Pull bet",
                        observed=format_money(delta),
                        expected=format_money(expected),
                        passed=passed,
                    )
                )


def run_timing_checks(records: list[CheckRecord]) -> None:
    # Table API does not expose mid-resolution placement hooks; mark as not tested.
    for mode in MODES:
        for bet_name in ("Buy", "Lay"):
            for family in BET_FAMILIES:
                records.append(
                    CheckRecord(
                        category="Timing",
                        mode=mode.key,
                        bet=bet_name,
                        family=family,
                        scenario="Illegal timing",
                        observed="Not tested",
                        expected="API not available",
                        passed=None,
                    )
                )


def render_markdown(
    affordability: Iterable[AffordabilityRecord],
    others: Iterable[CheckRecord],
    summary: dict[str, int],
) -> str:
    now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines: list[str] = [f"# Buy/Lay Audit Report\n", f"_Generated {now}_\n"]

    lines.append("\n## Summary\n")
    lines.append(
        (
            "Total checks: {total} | Passed: {passed} | Failed: {failed}\n"
            "Mode A passes: {mode_a} | Mode B passes: {mode_b}\n"
        ).format(**summary)
    )

    def render_affordability_table() -> None:
        lines.append("\n## Affordability\n")
        lines.append(
            "| Mode | Bet | Family | First placement cost (obs/exp) | Max count (obs/exp) | "
            "End bankroll (obs/exp) | Result |\n"
        )
        lines.append(
            "| --- | --- | --- | --- | --- | --- | --- |\n"
        )
        for record in affordability:
            lines.append(
                "| {mode} | {bet} | {family} | {first_obs}/{first_exp} | {count_obs}/{count_exp} | "
                "{bank_obs}/{bank_exp} | {result} |\n".format(
                    mode=record.mode,
                    bet=record.bet,
                    family=record.family,
                    first_obs=format_money(record.first_cost_obs),
                    first_exp=format_money(record.first_cost_exp),
                    count_obs=record.max_count_obs,
                    count_exp=record.max_count_exp,
                    bank_obs=format_money(record.end_bankroll_obs),
                    bank_exp=format_money(record.end_bankroll_exp),
                    result="PASS" if record.passed else "FAIL",
                )
            )

    def render_category(title: str, category_key: str) -> None:
        lines.append(f"\n## {title}\n")
        lines.append("| Mode | Bet | Family | Scenario | Observed | Expected | Result |\n")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |\n")
        for record in others:
            if record.category != category_key:
                continue
            result = (
                "PASS" if record.passed else "FAIL" if record.passed is False else "N/A"
            )
            lines.append(
                "| {mode} | {bet} | {family} | {scenario} | {observed} | {expected} | {result} |\n".format(
                    mode=record.mode,
                    bet=record.bet,
                    family=record.family,
                    scenario=record.scenario,
                    observed=record.observed,
                    expected=record.expected,
                    result=result,
                )
            )

    render_affordability_table()
    render_category("Loss Bookkeeping", "Loss")
    render_category("Win Bookkeeping", "Win")
    render_category("Pressing", "Press")
    render_category("Removal / Refund", "Removal")
    timing_section = [r for r in others if r.category == "Timing"]
    if timing_section:
        render_category("Timing / Legality", "Timing")

    lines.append("\n## Method\n")
    lines.append(
        (
            "- Modes: A (vig on win), B (vig upfront).\n"
            "- Bankroll {bankroll}, wager increment {wager}.\n"
            "- Dice outcomes forced via deterministic map.\n"
            "- Tolerance: ±{tol:.2f}.\n"
            "- No engine code modified; audit relies on public Table/Bet APIs.\n"
        ).format(bankroll=format_money(BANKROLL), wager=format_money(WAGER), tol=TOL)
    )

    lines.append("\n## Appendix\n")
    lines.append("category,mode,bet,family,scenario,observed,expected,result\n")
    for record in others:
        result = (
            "PASS" if record.passed else "FAIL" if record.passed is False else "N/A"
        )
        lines.append(
            f"{record.category},{record.mode},{record.bet},{record.family},{record.scenario},"
            f"{record.observed},{record.expected},{result}\n"
        )

    return "".join(lines)


def main() -> int:
    affordability_records: list[AffordabilityRecord] = []
    check_records: list[CheckRecord] = []

    run_affordability_checks(affordability_records, check_records)
    run_loss_checks(check_records)
    run_win_checks(check_records)
    run_press_checks(check_records)
    run_removal_checks(check_records)
    run_timing_checks(check_records)

    total = sum(1 for r in check_records if r.category != "Timing") + len(affordability_records)
    passed = sum(1 for r in affordability_records if r.passed)
    passed += sum(1 for r in check_records if r.passed is True)
    failed = (
        sum(1 for r in affordability_records if not r.passed)
        + sum(1 for r in check_records if r.passed is False)
    )
    mode_passes = {"A": 0, "B": 0}
    for record in affordability_records:
        if record.passed:
            mode_passes[record.mode] += 1
    for record in check_records:
        if record.passed and record.mode in mode_passes:
            mode_passes[record.mode] += 1

    summary = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "mode_a": mode_passes["A"],
        "mode_b": mode_passes["B"],
    }

    REPORT_PATH.write_text(
        render_markdown(affordability_records, check_records, summary), encoding="utf-8"
    )

    report_absolute = REPORT_PATH.resolve()
    print(report_absolute)
    print(f"{passed}/{total} checks passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
