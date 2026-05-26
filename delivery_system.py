import argparse
import csv
import glob
import json
import math
import os
import random
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(ROOT, "Python Assignment(Delivery System Test Cases)")


def distance(a, b):
    return math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)


def items_to_dict(records):
    if isinstance(records, dict):
        return dict(records)

    converted = {}
    for row in records:
        converted[row["id"]] = row["location"]
    return converted


def read_joining_agents(raw, package_count):
    if not raw:
        return []

    if isinstance(raw, dict) and "id" in raw:
        raw = [raw]
    elif isinstance(raw, dict):
        raw = [{"id": agent_id, "location": location} for agent_id, location in raw.items()]

    fallback_time = max(1, package_count // 2)
    joiners = []
    for agent in raw:
        joiners.append({
            "id": agent["id"],
            "location": agent["location"],
            "join_after_packages": int(agent.get("join_after_packages", fallback_time)),
        })
    return joiners


def load_case(path):
    with open(path, "r") as file:
        data = json.load(file)

    warehouses = items_to_dict(data["warehouses"])
    agents = items_to_dict(data["agents"])

    packages = []
    for package in data["packages"]:
        packages.append({
            "id": package["id"],
            "warehouse": package.get("warehouse") or package.get("warehouse_id"),
            "destination": package["destination"],
        })

    joiners = read_joining_agents(data.get("new_agent"), len(packages))
    joiners.extend(read_joining_agents(data.get("new_agents"), len(packages)))
    joiners.sort(key=lambda agent: agent["join_after_packages"])

    return warehouses, agents, packages, joiners


def all_input_files():
    files = []
    for path in glob.glob(os.path.join(TEST_DIR, "test_case_*.json")):
        if not os.path.basename(path).endswith("_report.json"):
            files.append(path)

    files.sort(key=lambda path: int(os.path.basename(path).split("_")[2].split(".")[0]))
    return [os.path.join(ROOT, "base_case.json")] + files


def resolve_input(name):
    if name.lower() in ("all", "--all"):
        return all_input_files()
    if os.path.isabs(name):
        return [name]
    return [os.path.join(ROOT, name)]


def assign_packages(packages, warehouses, agents, joiners):
    assigned = {agent_id: [] for agent_id in agents}
    for agent in joiners:
        assigned.setdefault(agent["id"], [])

    active = dict(agents)
    waiting = list(joiners)

    for index, package in enumerate(packages):
        while waiting and waiting[0]["join_after_packages"] <= index:
            agent = waiting.pop(0)
            active[agent["id"]] = agent["location"]
            agents[agent["id"]] = agent["location"]
            print(f"  New agent joined: {agent['id']} at {agent['location']}")

        warehouse = warehouses[package["warehouse"]]
        best_agent = None
        best_distance = float("inf")

        for agent_id, start in active.items():
            trip = distance(start, warehouse)
            if trip < best_distance:
                best_distance = trip
                best_agent = agent_id

        assigned[best_agent].append(package)
        print(
            f"  {package['id']} from {package['warehouse']} -> {best_agent} "
            f"(warehouse distance {best_distance:.2f})"
        )

    return assigned


def simulate(assigned, agents, warehouses, add_delays, rng):
    report = {}

    for agent_id, packages in assigned.items():
        current = agents[agent_id]
        total = 0.0
        delay = 0

        for package in packages:
            warehouse = warehouses[package["warehouse"]]
            destination = package["destination"]

            total += distance(current, warehouse)
            total += distance(warehouse, destination)
            current = destination

            if add_delays:
                delay += rng.randint(5, 30)

        delivered = len(packages)
        efficiency = total / delivered if delivered else 0.0
        report[agent_id] = {
            "packages_delivered": delivered,
            "total_distance": round(total, 2),
            "efficiency": round(efficiency, 2),
        }

        if add_delays:
            report[agent_id]["delay_minutes"] = delay

    return report


def best_agent(report):
    winner = None
    winner_score = float("inf")

    for agent_id, stats in report.items():
        if stats["packages_delivered"] == 0:
            continue
        if stats["efficiency"] < winner_score:
            winner = agent_id
            winner_score = stats["efficiency"]

    return winner


def save_report(report, input_path):
    output_path = os.path.splitext(input_path)[0] + "_report.json"
    with open(output_path, "w") as file:
        json.dump(report, file, indent=2)
    print(f"  Saved report: {output_path}")


def route_map(assigned, agents, warehouses):
    points = list(agents.values()) + list(warehouses.values())
    for packages in assigned.values():
        for package in packages:
            points.append(package["destination"])

    if not points:
        return

    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    width = 37
    height = 13

    def spot(point):
        if max_x == min_x:
            x = width // 2
        else:
            x = round((point[0] - min_x) / (max_x - min_x) * (width - 1))

        if max_y == min_y:
            y = height // 2
        else:
            y = round((max_y - point[1]) / (max_y - min_y) * (height - 1))

        return x, y

    print("\n  ASCII route view: A=start, W=warehouse, D=destination")
    for agent_id, packages in assigned.items():
        if not packages:
            continue

        grid = [["." for _ in range(width)] for _ in range(height)]
        x, y = spot(agents[agent_id])
        grid[y][x] = "A"

        for package in packages:
            x, y = spot(warehouses[package["warehouse"]])
            grid[y][x] = "W"
            x, y = spot(package["destination"])
            grid[y][x] = "D"

        print(f"\n  Route for {agent_id}")
        for row in grid:
            print("  " + "".join(row))


def print_report(report, show_delays):
    print("\n  Report")
    print("  " + "-" * 38)

    for agent_id, stats in report.items():
        if agent_id == "best_agent":
            continue

        line = (
            f"  {agent_id}: {stats['packages_delivered']} packages, "
            f"distance {stats['total_distance']}, "
            f"efficiency {stats['efficiency']}"
        )
        if show_delays:
            line += f", delay {stats['delay_minutes']} min"
        print(line)

    print(f"  Best agent: {report['best_agent']}")


def top_row(case_path, report):
    case_name = os.path.splitext(os.path.basename(case_path))[0]
    agent_id = report["best_agent"]

    if not agent_id:
        return {
            "case": case_name,
            "best_agent": "None",
            "packages": 0,
            "total_distance": 0,
            "efficiency": 0,
            "delay_minutes": 0,
        }

    stats = report[agent_id]
    return {
        "case": case_name,
        "best_agent": agent_id,
        "packages": stats["packages_delivered"],
        "total_distance": stats["total_distance"],
        "efficiency": stats["efficiency"],
        "delay_minutes": stats.get("delay_minutes", 0),
    }


def save_top_agent_csv(row, input_path):
    output_path = os.path.splitext(input_path)[0] + "_top_performer.csv"
    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def save_summary_csv(rows):
    output_path = os.path.join(ROOT, "best_performers_summary.csv")
    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "case",
            "best_agent",
            "packages",
            "total_distance",
            "efficiency",
            "delay_minutes",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nCombined CSV saved: {output_path}")


def print_top_table(rows, show_delays):
    if not rows:
        return

    columns = [
        ("case", "Case"),
        ("best_agent", "Best Agent"),
        ("packages", "Packages"),
        ("total_distance", "Distance"),
        ("efficiency", "Efficiency"),
    ]
    if show_delays:
        columns.append(("delay_minutes", "Delay"))

    widths = []
    for key, title in columns:
        values = [str(row[key]) for row in rows]
        widths.append(max(len(title), max(len(value) for value in values)))

    print("\nBest performer from each file")
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))
    print(" | ".join(title.ljust(widths[i]) for i, (_, title) in enumerate(columns)))
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))

    for row in rows:
        print(" | ".join(str(row[key]).ljust(widths[i]) for i, (key, _) in enumerate(columns)))

    overall = min(rows, key=lambda row: float(row["efficiency"]))
    print(
        f"\nOverall best performer: {overall['best_agent']} in {overall['case']} "
        f"(efficiency {overall['efficiency']})"
    )


def write_notes():
    notes = """FastBox notes
==============

Bonus work included:
- random delivery delays
- ASCII route display
- dynamic agent joining if the input has new_agent/new_agents
- CSV export
- one table comparing the best performer in every case

Hardest part:
The base case and test cases did not use the exact same JSON format. I fixed
that by converting warehouses, agents and packages into one common structure
inside load_case().

Main assumptions:
- distance is Euclidean
- ties go to the first agent found in the input order
- packages are delivered in the JSON order
- after a delivery, the agent is located at the destination
- random delays are extra information and do not change the best-agent choice
"""
    path = os.path.join(ROOT, "assignment_notes.txt")
    with open(path, "w") as file:
        file.write(notes)


def run_case(path, bonus, seed):
    warehouses, agents, packages, joiners = load_case(path)
    print(f"\nRunning {os.path.basename(path)}")
    print(f"  Warehouses: {', '.join(warehouses.keys())}")
    print(f"  Agents: {', '.join(agents.keys())}")
    print(f"  Packages: {len(packages)}")

    if joiners:
        print(f"  Dynamic joining: {len(joiners)} new agent(s) scheduled")
    elif bonus:
        print("  Dynamic joining: supported, but this file has no joining agents")

    assigned = assign_packages(packages, warehouses, agents, joiners)
    rng = random.Random(seed)
    report = simulate(assigned, agents, warehouses, bonus, rng)
    report["best_agent"] = best_agent(report)

    print_report(report, bonus)
    if bonus:
        route_map(assigned, agents, warehouses)

    total_delivered = sum(
        stats["packages_delivered"]
        for agent_id, stats in report.items()
        if agent_id != "best_agent"
    )
    print(f"\n  Delivered {total_delivered}/{len(packages)} packages")

    save_report(report, path)
    row = top_row(path, report)
    if bonus:
        save_top_agent_csv(row, path)

    return total_delivered == len(packages), row


def parse_args():
    parser = argparse.ArgumentParser(description="FastBox delivery simulator")
    parser.add_argument(
        "input",
        nargs="?",
        default="all",
        help="JSON file to run, or 'all' for base_case plus every test case",
    )
    parser.add_argument("--no-bonus", action="store_true", help="turn off delays, maps and CSV files")
    parser.add_argument("--seed", type=int, default=7, help="seed used for repeatable delay minutes")
    return parser.parse_args()


def main():
    args = parse_args()
    bonus = not args.no_bonus
    files = resolve_input(args.input)

    missing = [path for path in files if not os.path.exists(path)]
    if missing:
        print("Missing input file(s):")
        for path in missing:
            print(f"  {path}")
        sys.exit(1)

    if bonus:
        print("Bonus output is on. Use --no-bonus for the basic report only.")

    rows = []
    passed = 0
    for index, path in enumerate(files):
        ok, row = run_case(path, bonus, args.seed + index)
        rows.append(row)
        if ok:
            passed += 1

    print(f"\nPassed {passed}/{len(files)} input files")
    print_top_table(rows, show_delays=bonus)
    save_summary_csv(rows)
    write_notes()


if __name__ == "__main__":
    main()
