# CSC 540: Freight Tracking and Delivery Management

Regional logistics carrier database application. Project for CSC 540 (Database Application Development).

## Repository Layout

```
csc540-logistics-project/
├── db/
│   ├── queries/       # required_queries.sql (the six required queries; the app reads this file)
│   └── ddl/           # Deliverable 1 schema (kept for reference)
├── src/
│   ├── db/            # connection.py, helpers.py
│   ├── models/        # data layer: all INSERT/UPDATE/SELECT for each screen
│   ├── reports/       # data layer: report and required-query SQL
│   └── ui/            # Streamlit screens (no SQL here)
├── tests/             # manual_connection_test.py
├── .streamlit/        # Streamlit settings
├── config/db_config.example.ini
├── requirements.txt
└── environment.yml
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

### 5. Run the application

First build the database: schema, booking procedure, triggers, then the
official sample data. Re-running it resets everything to the sample data.

```bash
python -m db.load_database --reset
```

**This deletes all of the project's tables and data** in the database
`config/db_config.ini` points at, then rebuilds them.

Every sample account logs in with its sample id as the User ID (`SH1`–`SH4`,
`C1`–`C3`, `VW1`) and the password `password`.

```bash
streamlit run src/ui/app.py
```

It opens in your browser at http://localhost:8501.
