#!/usr/bin/env python3
"""Offline scenario arithmetic. No provider calls, billing reconciliation or launch authority."""
import argparse
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
import json
from pathlib import Path
import re


def amount(value, field):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{field}: expected a non-negative decimal")
    raw = str(value)
    if len(raw) > 40 or not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", raw):
        raise ValueError(f"{field}: expected a finite non-negative plain decimal")
    try:
        result = Decimal(raw)
    except InvalidOperation as error:
        raise ValueError(f"{field}: invalid decimal") from error
    return result


def integer(value, field, minimum):
    if type(value) is not int or value < minimum or value > 1000000:
        raise ValueError(f"{field}: expected integer in [{minimum}, 1000000]")
    return value


def fields(value, expected, field):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"{field}: expected fields {', '.join(sorted(expected))}")


def decimal_text(value):
    return format(value, "f")


def estimate(config):
    fields(config, {
        "schema_version", "currency", "rate_source", "rate_as_of", "product", "budget_usd",
        "gpu_count", "billed_cpu_cores", "billed_memory_gib", "rates_per_second",
        "scenarios", "extras_usd", "contingency_fraction",
    }, "config")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("schema_version: expected 1")
    if config["currency"] != "USD" or config["product"] not in ("functions", "sandbox"):
        raise ValueError("Expected USD and explicit functions/sandbox rate basis")
    if not isinstance(config["rate_source"], str) or not config["rate_source"].strip():
        raise ValueError("rate_source: required")
    if not isinstance(config["rate_as_of"], str):
        raise ValueError("rate_as_of: expected ISO date")
    date.fromisoformat(config["rate_as_of"])
    fields(config["rates_per_second"], {"gpu", "cpu_core", "memory_gib"}, "rates_per_second")
    fields(config["scenarios"], {"low", "base", "high"}, "scenarios")
    if not isinstance(config["extras_usd"], dict):
        raise ValueError("extras_usd: explicit mapping required; use null for unknown")
    if any(not isinstance(key, str) or not key.strip() for key in config["extras_usd"]):
        raise ValueError("extras_usd: non-empty names required")
    with localcontext() as context:
        context.prec = 200
        rates = {key: amount(value, key) for key, value in config["rates_per_second"].items()}
        gpu_count = integer(config["gpu_count"], "gpu_count", 0)
        cpu = amount(config["billed_cpu_cores"], "billed_cpu_cores")
        memory = amount(config["billed_memory_gib"], "billed_memory_gib")
        budget = amount(config["budget_usd"], "budget_usd")
        contingency = amount(config["contingency_fraction"], "contingency_fraction")
        if contingency > 1:
            raise ValueError("contingency_fraction: expected [0, 1]")
        rate = gpu_count * rates["gpu"] + cpu * rates["cpu_core"] + memory * rates["memory_gib"]
        unknown = sorted(key for key, value in config["extras_usd"].items() if value is None)
        extras = sum((amount(value, key) for key, value in config["extras_usd"].items()
                      if value is not None), Decimal(0))
        scenarios = {}
        previous = Decimal(-1)
        for name in ("low", "base", "high"):
            scenario = config["scenarios"][name]
            fields(scenario, {"seconds_per_attempt", "attempts"}, name)
            seconds = amount(scenario["seconds_per_attempt"], f"{name}.seconds_per_attempt")
            attempts = integer(scenario["attempts"], f"{name}.attempts", 1)
            compute = rate * seconds * attempts
            if compute < previous:
                raise ValueError("Scenarios must have nondecreasing total compute exposure")
            previous = compute
            scenarios[name] = {
                "compute_usd": decimal_text(compute),
                "known_subtotal_usd": decimal_text(compute + extras),
                "total_usd": None if unknown else decimal_text(compute + extras),
            }
        reserve = (previous + extras) * (1 + contingency)
        return {
            "schema_version": 1, "kind": "scenario_estimate_not_invoice",
            "currency": "USD", "product": config["product"],
            "rate_source": config["rate_source"], "rate_as_of": config["rate_as_of"],
            "compute_rate_usd_per_second": decimal_text(rate), "scenarios": scenarios,
            "unknown_extras": unknown, "known_reserve_usd": decimal_text(reserve),
            "reserve_usd": None if unknown else decimal_text(reserve),
            "budget_usd": decimal_text(budget),
            "within_budget": None if unknown else reserve <= budget,
            "launch_authorized": False, "hard_spending_guarantee": False,
        }


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(), object_pairs_hook=unique_object)
        report = estimate(config)
    except (OSError, ValueError, TypeError) as error:
        parser.exit(2, f"Cost estimate failed: {error}\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
