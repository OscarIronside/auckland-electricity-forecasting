# Setup and troubleshooting

The project uses Python 3.14. Verification records the exact environment in [VERIFICATION.md](VERIFICATION.md). Use the fixed package versions in the supplied requirements files when reproducing the reported results.

## Choose an installation

| Purpose | Install |
| --- | --- |
| Try the Streamlit app | `python -m pip install -r requirements-demo.txt` |
| Recreate either selected model | `python -m pip install -r requirements-evaluation.txt` |
| Run all notebook comparisons, tuning and SHAP | `python -m pip install -r requirements.txt` |

The full requirements include both smaller sets. The app does not need XGBoost, SHAP or a notebook server.

## Python and environment activation

On macOS or Linux, check `python3.14 --version`. On Windows, check `py -3.14 --version`. If the command is unavailable, install Python 3.14 from [python.org](https://www.python.org/downloads/), then create the environment described in the README.

After activation, `python --version` should report Python 3.14 and `python -m pip --version` should point inside the project's `.venv` folder. Always use `python -m pip` to install into the interpreter that runs the project.

If PowerShell blocks the activation script, run the environment's interpreter directly. No permanent execution-policy change is needed:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-demo.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

## Full notebook prerequisites

XGBoost uses a native OpenMP runtime. The app-only installation does not require it.

On macOS, install `libomp` with [Homebrew](https://brew.sh/) before running the full notebook:

```bash
brew install libomp
```

On Windows, XGBoost may require the [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). On Linux, an error mentioning `libgomp.so.1` indicates a missing OpenMP runtime; on Ubuntu/Debian the package is `libgomp1`.

See the [XGBoost installation guide](https://xgboost.readthedocs.io/en/stable/install.html) for platform-specific requirements. Local verification on an existing machine does not prove those system dependencies are present on another computer.

## Common issues

- **A requirements file cannot be found:** open a terminal in the extracted repository folder, where `app.py` is located. Do not run commands from the ZIP itself.
- **The app cannot load its data:** read the displayed filename or coverage error. Restore the original CSVs from the repository. Renaming columns, deleting dates or mixing exports from different runs can invalidate the demonstration. Restart the app after replacing inputs so its data cache is refreshed.
- **The notebook cannot find its input:** retain the `data/` directory and run the notebook from the project folder, or use `python scripts/run_notebook.py`.
- **A daylight-saving assertion fails in an older copy:** use the current notebook and its supplied requirements. The current calculation uses elapsed durations without assuming a timestamp integer unit.
- **The default Streamlit port is occupied:** run `python -m streamlit run app.py --server.port 8502` and open the address it prints.
- **You need the complete result rather than the app:** install the full requirements and run the notebook. The app displays saved predictions and does not retrain when a date is selected.

The scripts generate refreshed reports under `reports/`. Those generated files and virtual environments are excluded from Git. To save selected-model metrics without replacing the checked-in report:

```bash
python scripts/reproduce_results.py --output reports/metrics.json
```
