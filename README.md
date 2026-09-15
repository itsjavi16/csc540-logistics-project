# CSC 540: Freight Tracking and Delivery Management

Regional logistics carrier database application. Project for CSC 540 (Database Application Development).

## Repository Layout

```
csc540-logistics-project/
├── db/
│   ├── ddl/
│   ├── procedures/
│   ├── triggers/
│   └── seed/
├── src/
│   ├── db/
│   ├── cli/
│   ├── models/
│   └── reports/
├── docs/
│   ├── er-diagram/
│   └── deliverable1/
├── tests/
├── config/
│   └── db_config.example.ini
├── requirements.txt
├── environment.yml
└── .gitignore
```

## Setup

Works on Windows, macOS, and Linux. Pick one environment option.

### 1. Clone the repo

```bash
git clone <repo-url>
cd csc540-logistics-project
```

### 2. Set up your Python environment

**Conda: Windows, macOS, Linux (same commands on all three)**

```bash
conda env create -f environment.yml
conda activate csc540-logistics
```

To update the environment later after `requirements.txt` changes:
```bash
conda env update -f environment.yml --prune
```

### 3. Configure your local DB credentials

macOS / Linux:
```bash
cp config/db_config.example.ini config/db_config.ini
```

Windows (PowerShell or cmd):
```cmd
copy config\db_config.example.ini config\db_config.ini
```

Edit `config/db_config.ini` with your own `unityid` and password. This file is gitignored **(it will never commit real credentials)**.

### 4. Verify your connection works

```bash
python -m tests.manual_connection_test
```

### 5. Run the CLI

```bash
python -m src.cli.main
```
