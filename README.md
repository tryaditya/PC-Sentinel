# PC Sentinel

**A lightweight Windows system monitoring and process management application.**

PC Sentinel is a desktop application built with Python and PySide6 that helps users monitor system performance, inspect running processes, and track network activity through a modern interface.

## Features

- **Dashboard** — Monitor CPU, RAM, and disk utilization with system statistics and graphs.
- **Diagnostics** — Access system diagnostic information and troubleshooting tools.
- **Process Manager** — View and search running processes, with confirmation before ending a task.
- **Network Monitor** — Track live download and upload speeds, total data usage, connection status, and recent network activity through a live graph.

## Screenshots

Screenshots of the application will be added here.

## Download and Installation

### For Windows users

1. Visit the [Latest Release](https://github.com/tryaditya/PC-Sentinel/releases/latest).
2. Download the Windows ZIP package.
3. Extract the ZIP file.
4. Open the extracted folder.
5. Run `PC Sentinel.exe`.

The packaged application is intended to run without a separate Python installation.

### For developers

**Requirements**
- Python 3.12 (development environment)
- Git

**Setup**

1. Clone the repository:

   ```bash
   git clone https://github.com/tryaditya/PC-Sentinel.git
   cd PC-Sentinel
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate it on Windows:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Run the application:

   ```bash
   python app.py
   ```

## Contributing

Contributions, bug reports, and improvement suggestions are welcome.

Before submitting a pull request, please read [CONTRIBUTING.md](CONTRIBUTING.md).

**Every pull request must explain:**
- What was changed.
- Why the change was necessary or useful.
- How the change was tested.
- Any known limitations or potential side effects.

Pull requests without a clear explanation may be asked for additional details before review.

## Technology Stack

- Python
- PySide6
- psutil
- PyInstaller

## Project Status

PC Sentinel v1.0.0 is the first public release. The project may evolve as bugs are fixed and improvements are reviewed.

## License

No license has been specified yet. Until a license is added to this repository, please do not assume that the project is open for unrestricted reuse, modification, or redistribution.
