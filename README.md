# Python Delivery Simulator

A Python command-line project that simulates package delivery for a fictional logistics company called **FastBox**.

The program reads warehouse, delivery agent, and package data from JSON files, assigns packages to the nearest available agent, simulates deliveries, calculates distance and efficiency, and prints a final best-performer summary.

## Features

- Reads delivery data from JSON files
- Runs the base case and all supplied test cases automatically
- Assigns each package to the nearest delivery agent
- Calculates total distance traveled by every agent
- Calculates delivery efficiency for each agent
- Selects the best agent for every test case
- Creates JSON report files
- Creates a combined best-performer CSV file
- Includes bonus output:
  - random delivery delays
  - ASCII route views
  - dynamic agent joining support
  - top-performer CSV export

## Project Structure

```text
.
├── delivery_system.py
├── base_case.json
├── base_case_report.json
├── best_performers_summary.csv
├── assignment_notes.txt
├── Python Assignment(Delivery System Test Cases)/
│   ├── test_case_1.json
│   ├── test_case_2.json
│   ├── ...
│   ├── test_case_10.json
│   └── generated report files
└── Python Assignment(Delivery System).pdf
```

## How To Run

Run all input files with bonus output enabled:

```bash
python3 delivery_system.py
```

Run all input files without bonus output:

```bash
python3 delivery_system.py --no-bonus
```

Run one specific input file:

```bash
python3 delivery_system.py base_case.json
```

Use a different random seed for delivery delays:

```bash
python3 delivery_system.py --seed 25
```

## How It Works

1. The program loads input data from JSON.
2. It converts warehouse and agent data into a consistent dictionary format.
3. For each package, it finds the nearest active agent to the package warehouse.
4. It simulates the delivery route:
   - agent current location to warehouse
   - warehouse to destination
5. It records each agent's total distance and number of packages delivered.
6. It calculates efficiency:

```text
efficiency = total_distance / packages_delivered
```

Lower efficiency is better because it means the agent traveled less distance per package.

## Output Files

The script generates:

- `base_case_report.json`
- `test_case_*_report.json`
- `*_top_performer.csv`
- `best_performers_summary.csv`
- `assignment_notes.txt`

## Best Performer Summary

Example output:

```text
Best performer from each file
------------------------------------------------------------
Case         | Best Agent | Packages | Distance | Efficiency
------------------------------------------------------------
base_case    | A3         | 1        | 14.14    | 14.14
test_case_1  | A1         | 4        | 75.83    | 18.96
test_case_9  | A3         | 2        | 25.4     | 12.7
test_case_10 | A4         | 6        | 77.55    | 12.93
```

The overall best performer is the agent with the lowest efficiency score across the cases.

## Bonus Features

### Random Delivery Delays

When bonus output is enabled, each delivered package can add a random delay between 5 and 30 minutes.

### ASCII Route View

The program prints a rough map for each active delivery agent:

```text
A = agent starting point
W = warehouse
D = destination
```

### Dynamic Agent Joining

The code supports input files that include `new_agent` or `new_agents`. A new agent can join after a chosen number of packages have already been assigned.

Example:

```json
{
  "new_agent": {
    "id": "A5",
    "location": [20, 30],
    "join_after_packages": 4
  }
}
```

### CSV Export

The program exports the best performer for each case and also creates one combined file:

```text
best_performers_summary.csv
```

## Assumptions

- Distance is calculated using Euclidean distance.
- Packages are assigned in the same order they appear in the JSON file.
- If two agents are equally close, the first one found in input order is selected.
- After a package is delivered, the agent's current location becomes that package's destination.
- Agents with zero delivered packages are not selected as best performer.
- Random delays are reported, but they do not change package assignment or best-agent selection.

## What I Learned

This project helped me practice:

- reading and writing JSON files
- working with dictionaries and lists
- applying Euclidean distance
- building a simple simulation
- generating reports
- exporting CSV files
- writing command-line Python programs

## Requirements

No external packages are required. The project uses Python standard libraries only.

Recommended Python version:

```text
Python 3.10+
```

