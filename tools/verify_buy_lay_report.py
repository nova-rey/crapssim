#!/usr/bin/env python3
"""Generate a Buy/Lay consistency report for vig handling modes.

This script exercises Buy and Lay bets under two table configurations:
commission collected on win ("Mode A") and commission paid upfront ("Mode B").
It records affordability limits, loss handling, and win payouts for both the
4/10 and 5/9 number families, then renders a Markdown report summarizing the
results.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crapssim.bet import Bet, Buy, Lay
from crapssim.table import Table
from crapssim.strategy.tools import NullStrategy

BANKROLL = 100.0
WAGER = 20.0
TOLERANCE = 0.01

NUMBER_FAMILIES: dict[str, Sequence[int]] = {
    "4/10": (4, 10),
    "5/9": (5, 9),
}

MODE_SETTINGS: dict[str, bool] = {
    "Mode A (vig_on_win)": True,
    "Mode B (upfront_vig)": False,
}

BET_TYPES: dict[str, type[Bet]] = {
    "Buy": Buy,
    "Lay": Lay,
}

DICE_PRESETS: dict[int, tuple[int, int]] = {
    2: (1, 1),
    3: (1, 2),
    4: (2, 2),
    5: (2, 3),
    6: (3, 3),
    7: (3, 4),
    8: (3, 5),
    9: (4, 5),
    10: (5, 5),
    11: (5, 6),
    12: (6, 6),
}


@dataclass
class AffordabilityResult:
    mode: str
    bet_type: str
    family: str
    numbers_tested: tuple[int, ...]
    placement_cost: float
    max_count_observed: int
    max_count_expected: int
    ending_bankroll_observed: float
    ending_bankroll_expected: float
    expected_notes: str
    passed: bool


@dataclass
class OutcomeResult:
    mode: str
    bet_type: str
    family: str
    numbers_tested: tuple[int, ...]
    scenario: str
    bankroll_delta_observed: float
    bankroll_delta_expected: float
    win_amount_observed: float
    win_amount_expected: float
    expected_notes: str
    passed: bool


@dataclass
class RawLogEntry:
    mode: str
    bet_type: str
    number: int
    family: str
    scenario: str
    bankroll_before: float
    bankroll_after: float
    additional_info: str


def dice_pair(total: int) -> tuple[int, int]:
    try:
        return DICE_PRESETS[total]
    except KeyError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"No dice preset defined for total {total}") from exc


def create_table(buy_vig_on_win: bool) -> Table:
    table = Table()
    table.settings["buy_vig_on_win"] = buy_vig_on_win
    return table


def placement_cost_for_initial(table: Table, bet: Bet) -> float:
    return bet.placement_cost(table)


def compute_expected_affordability(
    bet_cls: type[Bet],
    table: Table,
    number: int,
    bankroll: float,
    wager: float,
) -> tuple[int, float]:
    amount = 0.0
    remaining = bankroll
    count = 0
    while True:
        new_amount = amount + wager
        existing_cost = bet_cls(number, amount).placement_cost(table) if amount > 0 else 0.0
        new_cost = bet_cls(number, new_amount).placement_cost(table)
        required_cash = new_cost - existing_cost
        if required_cash <= remaining + 1e-9:
            remaining -= required_cash
            amount = new_amount
            count += 1
        else:
            break
    return count, remaining


def run_affordability_trial(
    bet_cls: type[Bet],
    table: Table,
    number: int,
    bankroll: float,
    wager: float,
) -> tuple[int, float, float, list[RawLogEntry]]:
    player = table.add_player(bankroll=bankroll, strategy=NullStrategy(), name="Verifier")
    log_entries: list[RawLogEntry] = []
    count = 0
    placement_cost = 0.0
    while True:
        before_bankroll = player.bankroll
        existing = [
            b for b in player.bets if isinstance(b, bet_cls) and getattr(b, "number", None) == number
        ]
        previous_amount = existing[0].amount if existing else 0.0
        player.add_bet(bet_cls(number, wager))
        updated = [
            b for b in player.bets if isinstance(b, bet_cls) and getattr(b, "number", None) == number
        ]
        after_amount = updated[0].amount if updated else 0.0
        after_bankroll = player.bankroll
        log_entries.append(
            RawLogEntry(
                mode="",  # populated by caller
                bet_type=bet_cls.__name__,
                number=number,
                family="",
                scenario="affordability",
                bankroll_before=before_bankroll,
                bankroll_after=after_bankroll,
                additional_info=f"amount {previous_amount:.2f} -> {after_amount:.2f}",
            )
        )
        if after_amount >= previous_amount + wager - 1e-9:
            count += 1
            if placement_cost == 0.0:
                placement_cost = before_bankroll - after_bankroll
        else:
            break
    return count, player.bankroll, placement_cost, log_entries


def compute_expected_outcome(
    bet_cls: type[Bet],
    table: Table,
    number: int,
    roll_total: int,
    wager: float,
) -> tuple[float, float, float]:
    bet = bet_cls(number, wager)
    placement_cost = bet.placement_cost(table)
    if not table.settings.get("buy_vig_on_win", True):
        bet.vig_paid = placement_cost - getattr(bet, "wager", bet.amount)
    table.dice.result = dice_pair(roll_total)
    result = bet.get_result(table)
    bankroll_delta = -placement_cost
    if result.amount > 0:
        bankroll_delta += result.amount
        win_amount = result.amount
    else:
        win_amount = 0.0
    return placement_cost, bankroll_delta, win_amount


def run_outcome_trial(
    bet_cls: type[Bet],
    table: Table,
    number: int,
    roll_total: int,
    bankroll: float,
    wager: float,
    scenario: str,
) -> tuple[float, float, float, list[RawLogEntry]]:
    player = table.add_player(bankroll=bankroll, strategy=NullStrategy(), name="Verifier")
    initial_bankroll = player.bankroll
    player.add_bet(bet_cls(number, wager))
    after_placement = player.bankroll
    table.dice.fixed_roll(dice_pair(roll_total))
    player.update_bet()
    final_bankroll = player.bankroll
    win_amount = final_bankroll - after_placement
    log_entry = RawLogEntry(
        mode="",
        bet_type=bet_cls.__name__,
        number=number,
        family="",
        scenario=scenario,
        bankroll_before=initial_bankroll,
        bankroll_after=final_bankroll,
        additional_info=f"after placement {after_placement:.2f}, win amount {win_amount:.2f}",
    )
    return initial_bankroll, final_bankroll, win_amount, [log_entry]


def close_enough(left: float, right: float, tol: float = TOLERANCE) -> bool:
    return abs(left - right) <= tol


def format_currency(value: float) -> str:
    return f"${value:.2f}"


def render_report(
    affordability_results: Iterable[AffordabilityResult],
    outcome_results: Iterable[OutcomeResult],
    raw_logs: Iterable[RawLogEntry],
    output_path: Path,
) -> None:
    affordability_results = list(affordability_results)
    outcome_results = list(outcome_results)
    raw_logs = list(raw_logs)
    total_checks = len(affordability_results) + len(outcome_results)
    passed_checks = sum(1 for result in affordability_results if result.passed)
    passed_checks += sum(1 for result in outcome_results if result.passed)

    lines: list[str] = []
    lines.append("# Buy/Lay Consistency Report")
    lines.append("")
    lines.append("## Summary")
    status_icon = "✅" if passed_checks == total_checks else "❌"
    lines.append(
        f"- {status_icon} {passed_checks} of {total_checks} automated checks passed"
    )
    lines.append("")

    lines.append("## Affordability")
    lines.append(
        "| Mode | Bet | Family | Placement Cost | Max Placeable (obs/exp) | Ending Bankroll (obs/exp) | Notes | Result |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for result in affordability_results:
        result_icon = "✅" if result.passed else "❌"
        notes = result.expected_notes.replace("\n", "<br>")
        lines.append(
            "| {mode} | {bet} | {family} | {placement} | {obs}/{exp} | {end_obs}/{end_exp} | {notes} | {icon} |".format(
                mode=result.mode,
                bet=result.bet_type,
                family=result.family,
                placement=format_currency(result.placement_cost),
                obs=result.max_count_observed,
                exp=result.max_count_expected,
                end_obs=format_currency(result.ending_bankroll_observed),
                end_exp=format_currency(result.ending_bankroll_expected),
                notes=notes,
                icon=result_icon,
            )
        )
    lines.append("")

    lines.append("## Outcome Checks")
    lines.append(
        "| Mode | Bet | Family | Scenario | Bankroll Δ (obs/exp) | Win Amount (obs/exp) | Notes | Result |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for result in outcome_results:
        result_icon = "✅" if result.passed else "❌"
        notes = result.expected_notes.replace("\n", "<br>")
        lines.append(
            "| {mode} | {bet} | {family} | {scenario} | {delta_obs}/{delta_exp} | {win_obs}/{win_exp} | {notes} | {icon} |".format(
                mode=result.mode,
                bet=result.bet_type,
                family=result.family,
                scenario=result.scenario,
                delta_obs=format_currency(result.bankroll_delta_observed),
                delta_exp=format_currency(result.bankroll_delta_expected),
                win_obs=format_currency(result.win_amount_observed),
                win_exp=format_currency(result.win_amount_expected),
                notes=notes,
                icon=result_icon,
            )
        )
    lines.append("")

    lines.append("## Method")
    lines.append(
        "Tests were run with an initial bankroll of $100 and $20 wagers. Mode A keeps the vig on the win, "
        "so only the principal is removed on placement. Mode B charges the 5% commission upfront, "
        "deducting it immediately and skipping the commission on wins. Dice outcomes were forced "
        "via `Dice.fixed_roll` to create deterministic win and loss scenarios."
    )
    lines.append("")

    lines.append("## Appendix: Raw Trial Log")
    lines.append("| Mode | Bet | Family | Number | Scenario | Bankroll Before | Bankroll After | Details |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for entry in raw_logs:
        lines.append(
            "| {mode} | {bet} | {family} | {number} | {scenario} | {before} | {after} | {info} |".format(
                mode=entry.mode,
                bet=entry.bet_type,
                family=entry.family,
                number=entry.number,
                scenario=entry.scenario,
                before=format_currency(entry.bankroll_before),
                after=format_currency(entry.bankroll_after),
                info=entry.additional_info.replace("\n", "<br>"),
            )
        )
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    affordability_results: list[AffordabilityResult] = []
    outcome_results: list[OutcomeResult] = []
    raw_logs: list[RawLogEntry] = []

    for mode_label, buy_vig_on_win in MODE_SETTINGS.items():
        for bet_label, bet_cls in BET_TYPES.items():
            for family_label, numbers in NUMBER_FAMILIES.items():
                # Affordability checks for each number in the family
                observed_counts: list[int] = []
                observed_endings: list[float] = []
                placement_cost = 0.0
                table_for_expect = create_table(buy_vig_on_win)
                expected_count, expected_remaining = compute_expected_affordability(
                    bet_cls, table_for_expect, numbers[0], BANKROLL, WAGER
                )
                expected_notes = [
                    f"Expected {expected_count} placements with remaining bankroll ${expected_remaining:.2f}."
                ]
                for number in numbers:
                    table = create_table(buy_vig_on_win)
                    count, ending_bankroll, placement_cost_observed, log_entries = run_affordability_trial(
                        bet_cls, table, number, BANKROLL, WAGER
                    )
                    for entry in log_entries:
                        entry.mode = mode_label
                        entry.family = family_label
                        raw_logs.append(entry)
                    observed_counts.append(count)
                    observed_endings.append(ending_bankroll)
                    placement_cost = max(placement_cost, placement_cost_observed)
                consistent_counts = all(close_enough(count, observed_counts[0]) for count in observed_counts)
                consistent_endings = all(
                    close_enough(ending, observed_endings[0]) for ending in observed_endings
                )
                if len(numbers) > 1:
                    expected_notes.append(
                        "Mirror number check: "
                        + ", ".join(str(num) for num in numbers)
                        + " all matched within tolerance."
                    )
                passed = (
                    consistent_counts
                    and consistent_endings
                    and observed_counts[0] == expected_count
                    and close_enough(observed_endings[0], expected_remaining)
                )
                affordability_results.append(
                    AffordabilityResult(
                        mode=mode_label,
                        bet_type=bet_label,
                        family=family_label,
                        numbers_tested=tuple(numbers),
                        placement_cost=placement_cost,
                        max_count_observed=observed_counts[0],
                        max_count_expected=expected_count,
                        ending_bankroll_observed=observed_endings[0],
                        ending_bankroll_expected=expected_remaining,
                        expected_notes=" ".join(expected_notes),
                        passed=passed,
                    )
                )

                # Outcome checks (loss and win)
                for scenario in ("loss", "win"):
                    expected_rolls: list[int] = []
                    observed_deltas: list[float] = []
                    observed_win_amounts: list[float] = []
                    expected_deltas: list[float] = []
                    expected_win_amounts: list[float] = []
                    notes: list[str] = []
                    for number in numbers:
                        roll_total = number if (scenario == "win" and bet_label == "Buy") else 7
                        if scenario == "loss":
                            if bet_label == "Buy":
                                roll_total = 7
                            else:
                                roll_total = number
                        expected_rolls.append(roll_total)
                        table = create_table(buy_vig_on_win)
                        initial, final, win_amount, log_entries = run_outcome_trial(
                            bet_cls, table, number, roll_total, BANKROLL, WAGER, scenario
                        )
                        for entry in log_entries:
                            entry.mode = mode_label
                            entry.family = family_label
                            raw_logs.append(entry)
                        observed_deltas.append(final - initial)
                        observed_win_amounts.append(win_amount)

                        expected_table = create_table(buy_vig_on_win)
                        _, expected_delta, expected_win_amount = compute_expected_outcome(
                            bet_cls, expected_table, number, roll_total, WAGER
                        )
                        expected_deltas.append(expected_delta)
                        expected_win_amounts.append(expected_win_amount)

                    consistent_delta = all(
                        close_enough(delta, observed_deltas[0]) for delta in observed_deltas
                    )
                    consistent_win_amount = all(
                        close_enough(amount, observed_win_amounts[0]) for amount in observed_win_amounts
                    )
                    expected_delta = expected_deltas[0]
                    expected_win_amount = expected_win_amounts[0]
                    if len(numbers) > 1:
                        notes.append(
                            "Roll totals used: " + ", ".join(str(total) for total in expected_rolls)
                        )
                    if scenario == "loss" and bet_label == "Lay":
                        notes.append("Lay losses occur when the box number rolls (not on the 7).")
                    passed = (
                        consistent_delta
                        and consistent_win_amount
                        and close_enough(observed_deltas[0], expected_delta)
                        and close_enough(observed_win_amounts[0], expected_win_amount)
                    )
                    outcome_results.append(
                        OutcomeResult(
                            mode=mode_label,
                            bet_type=bet_label,
                            family=family_label,
                            numbers_tested=tuple(numbers),
                            scenario=scenario,
                            bankroll_delta_observed=observed_deltas[0],
                            bankroll_delta_expected=expected_delta,
                            win_amount_observed=observed_win_amounts[0],
                            win_amount_expected=expected_win_amount,
                            expected_notes=" ".join(notes),
                            passed=passed,
                        )
                    )

    output_path = Path(__file__).resolve().parent.parent / "REPORT-buy_lay.md"
    render_report(affordability_results, outcome_results, raw_logs, output_path)

    any_failures = any(not result.passed for result in affordability_results) or any(
        not result.passed for result in outcome_results
    )
    return 1 if any_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
