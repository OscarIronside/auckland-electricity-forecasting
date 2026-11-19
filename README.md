# Auckland electricity forecasting

A Python forecasting project with a Streamlit app for exploring daily electricity demand and simulating purchasing costs.

The project tests whether a model can predict Auckland regional demand more accurately than using demand from the same weekday a week earlier. The notebook compares linear regression, random forest and XGBoost. The app lets you explore forecasts and see how purchasing assumptions affect costs.

## Results

On the 218 test days from 28 May to 31 December 2025, the notebook's selected linear regression reduced RMSE by **41.2%** against the previous-week benchmark.

| Forecast | MAE (GWh) | RMSE (GWh) |
| --- | ---: | ---: |
| Previous-week benchmark | 1.198 | 1.614 |
| Notebook model | 0.658 | 0.949 |
| App model | 0.573 | 0.789 |

MAE is average absolute error. RMSE gives more weight to larger errors. Lower values mean the forecasts were closer to recorded demand.

The app uses a separate linear regression with additional weather and calendar features. **The 41.2% improvement refers to the notebook model.** Both models can be recreated using the included data and scripts.

## Try the app

Use **Python 3.14**. Download and extract the repository ZIP, or clone it:

```bash
git clone https://github.com/OscarIronside/auckland-electricity-forecasting.git
cd auckland-electricity-forecasting
```

Open a terminal in the project folder. On macOS or Linux:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
```

Then install the app dependencies and start it:

```bash
python -m pip install -r requirements-demo.txt
python -m streamlit run app.py
```

Open the local address printed by Streamlit. All data is included, and no API key or cloud account is needed. Press Ctrl+C to stop the app.

![Demand forecast view](docs/images/app-demand.jpg)

- **Demand forecast:** choose a historical date, view recent demand, compare the forecast with the previous week and reveal actual demand.
- **Purchasing simulation:** set the advance purchase price and resale rate, then compare the costs of using each forecast under the same rules.

Selecting a date displays a saved prediction. Purchasing costs are simulated. The app checks its inputs before showing results and displays an error if data is missing or inconsistent.

## Reproduce the models

With the environment active, install the modelling dependencies and run both scripts:

```bash
python -m pip install -r requirements-evaluation.txt
python scripts/reproduce_results.py
python scripts/reproduce_app_forecasts.py
```

The first script refits the notebook's selected model. Expected RMSE is `0.948777 GWh`, against `1.613599 GWh` for the benchmark. The second recreates all 218 app forecasts and compares them with the saved predictions; expected RMSE is `0.789128 GWh`.

### Run the full notebook

The full notebook also runs the model comparisons, tuning and SHAP explanations. It needs additional packages and an OpenMP runtime for XGBoost:

- **macOS:** install `libomp` with Homebrew: `brew install libomp`.
- **Windows:** XGBoost may need the [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist).
- **Ubuntu/Debian:** install `libgomp1` if an error mentions `libgomp.so.1`.

Then run:

```bash
python -m pip install -r requirements.txt
python scripts/run_notebook.py
```

This executes all 35 code cells and saves a copy to `reports/forecasting-executed.ipynb`. You can also open `forecasting.ipynb` in a notebook editor and run it from the project folder using this environment.

The full requirements include the app and modelling dependencies. See [verification](docs/VERIFICATION.md) for test commands and recorded checks.

## Data and limitations

The data covers 1,096 days from 2023 to 2025. Demand combines Electricity Authority records for Vector's Waitemata and Auckland reporting regions. Weather comes from Open-Meteo, and the purchasing simulation uses daily average prices at Otahuhu. See [data sources](docs/DATA.md) for the included files and their preparation.

Each forecast uses observations from before its date. The data includes later revisions, so these results do not show what would have been possible with information available at a real purchasing deadline. The simulation leaves out network charges, transaction costs and customer tariffs. Its savings depend on the selected assumptions. The [evaluation notes](docs/EVALUATION.md) explain these limits and the model-selection process.

## Development

I worked on the modelling and Streamlit app, using Codex for planning and debugging. I later added documentation, scripts to reproduce the results, input validation and automated tests with Codex's help.

## Project files

| File or folder | Purpose |
| --- | --- |
| `app.py`, `data_validation.py` | App and input checks |
| `forecasting.ipynb` | Modelling, evaluation and explanations |
| Root CSV files | Daily demand, saved forecasts and daily prices |
| `data/` | Half-hourly demand and hourly weather |
| `scripts/` | Model reproduction and notebook runner |
| `tests/`, `.github/workflows/` | Regression tests and automated checks |
| `docs/` | Data sources, evaluation and verification |

## Troubleshooting

- **Python is unavailable:** install Python 3.14 from [python.org](https://www.python.org/downloads/). Check with `python3.14 --version` on macOS/Linux or `py -3.14 --version` on Windows.
- **PowerShell blocks activation:** use `.venv\Scripts\python.exe` in place of `python` in the install and run commands.
- **Files cannot be found:** extract the whole ZIP and run commands from the folder containing `app.py`. Keep the supplied filenames and `data/` folder.
- **The app reports invalid data:** restore the original CSVs and restart the app.
- **The port is occupied:** add `--server.port 8502` to the app command.

After activating the environment, `python --version` should report 3.14 and `python -m pip --version` should point into `.venv`.
