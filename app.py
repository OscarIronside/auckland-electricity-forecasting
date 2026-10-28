from pathlib import Path
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="YORICast | Auckland demand", layout="centered")
st.markdown("""
<style>
.block-container { max-width: 1100px; }
</style>
<div style="text-align: center;">
    <h1>YORICast Energy Saving</h1>
    <p style="color: #b4ceca; font-size: 0.875rem;">Explore demand and purchasing decisions using historical data.</p>
</div>
""", unsafe_allow_html=True)
st.divider()

ROOT = Path(__file__).resolve().parent

@st.cache_data
def load_forecasts():
    daily = pd.read_csv(ROOT / "daily_demand.csv", parse_dates=["Date"]).set_index("Date")["energy_gwh"]
    results = pd.read_csv(ROOT / "historical_forecasts.csv", parse_dates=["Date"]).set_index("Date")
    if not daily.index.is_unique or not results.index.is_unique:
        raise ValueError("Duplicate dates in historical inputs.")
    if results[["Actual", "Forecast", "Last week"]].isna().any().any():
        raise ValueError("Incomplete historical forecasts.")
    return daily, results

daily, results = load_forecasts()

forecast_tab, savings_tab = st.tabs(["Demand forecast", "Purchasing simulation"])
with forecast_tab:
    st.subheader("Demand overview")
    chosen = st.date_input("Choose a forecast date", value=results.index[0].date(),
                           min_value=results.index[0].date(), max_value=results.index[-1].date())
    date = pd.Timestamp(chosen)
    row = results.loc[date]
    difference = 100 * (row.Forecast / row["Last week"] - 1)
    cards = st.columns(3)
    cards[0].metric("Forecast demand", f"{row.Forecast:.2f} GWh", border=True)
    cards[1].metric("Same weekday last week", f"{row['Last week']:.2f} GWh", border=True)
    cards[2].metric("Predicted change from last week", f"{difference:+.1f}%", border=True)

    st.subheader("Demand trend")
    history = daily.loc[(daily.index >= date - pd.Timedelta(days=14)) & (daily.index < date)]
    chart_data = pd.DataFrame({"Date": history.index, "Energy": history.values, "Series": "Previous demand"})
    chart_data = pd.concat([chart_data, pd.DataFrame({"Date": [date], "Energy": [row.Forecast], "Series": ["Forecast"]})])
    show_actual = st.checkbox("Show actual electricity use")
    if show_actual:
        chart_data = pd.concat([chart_data, pd.DataFrame({"Date": [date], "Energy": [row.Actual], "Series": ["Actual"]})])
    chart = alt.Chart(chart_data).mark_line(point=alt.OverlayMarkDef(size=50), strokeWidth=2.5).encode(
        x=alt.X("Date:T", axis=alt.Axis(format="%d %b", tickCount=5)),
        y=alt.Y("Energy:Q", title="Daily energy (GWh)", scale=alt.Scale(zero=False)),
        color=alt.Color("Series:N", scale=alt.Scale(domain=["Previous demand", "Forecast", "Actual"], range=["#48ccc5", "#c7f35b", "#f1f7f4"])),
        tooltip=[alt.Tooltip("Date:T", format="%d %b %Y"), "Series:N", alt.Tooltip("Energy:Q", format=".2f")],
    ).properties(height=330, background="#103b3b").configure_view(strokeWidth=0).configure_axis(gridColor="#2b5555", labelColor="#c4d9d5", titleColor="#c4d9d5").configure_legend(title=None, orient="bottom", labelColor="#c4d9d5")
    st.altair_chart(chart, width="stretch")

    if show_actual:
        st.write(f"- {row.Actual:.2f} GWh: actual electricity use")
        st.write(f"- {row.Forecast - row.Actual:+.2f} GWh: forecast minus actual")


with savings_tab:
    st.subheader("Plan Better. Spend less.")
    st.caption("Auckland regional demand · 28 May to 31 December 2025 · 218 days")
    with st.container(border=True):
        st.markdown("**1. Set your example prices**")
        buying, selling = st.columns(2)
        with buying:
            contract = st.number_input("Buy ahead (NZD/MWh)", min_value=0.0, value=200.0, step=10.0)
            st.caption("NZD 200/MWh: illustrative contract price from the [Electricity Authority (2026)](https://www.ea.govt.nz/news/eye-on-electricity/are-asx-futures-prices-too-high/).")
        with selling:
            resale = st.slider("Sell unused electricity (% of market price)", min_value=0, max_value=100, value=100, step=10)
            st.caption(f"Receive {resale}% of the day's market price")
    st.markdown("**2. Compare the simulated costs**")
    price_file = Path(__file__).with_name("otahuhu_daily_prices.csv")
    prices = pd.read_csv(price_file, parse_dates=["Date"]).set_index("Date")
    comparison = results.join(prices[["price_nzd_mwh"]], validate="one_to_one")
    needed = comparison.Actual * 1000
    for name, column in [("Baseline", "Last week"), ("Model", "Forecast")]:
        bought = comparison[column].clip(lower=0) * 1000
        shortfall = (needed - bought).clip(lower=0)
        surplus = (bought - needed).clip(lower=0)
        comparison[f"{name} cost (NZ$)"] = bought * contract + shortfall * comparison.price_nzd_mwh - surplus * comparison.price_nzd_mwh * resale / 100
    baseline_cost = comparison["Baseline cost (NZ$)"].sum()
    model_cost = comparison["Model cost (NZ$)"].sum()
    saving = baseline_cost - model_cost
    st.caption("Simulated costs using **our forecast** VS using **last week's value**")
    cards = st.columns(3)
    cards[0].metric("Cost using simple benchmark", f"NZ${baseline_cost / 1_000_000:.2f}m", border=True)
    cards[1].metric("Cost using our model", f"NZ${model_cost / 1_000_000:.2f}m", border=True)
    cards[2].metric("Simulated saving" if saving >= 0 else "Extra cost vs benchmark", f"NZ${abs(saving):,.0f}", border=True)
    if saving < 0:
        st.write("- Under these assumptions, the more accurate forecast does not reduce total purchasing costs.")
    with st.expander("How this works"):
        st.write("- Buy electricity based on the forecast.\n- Used less than predicted? Sell what's left at your chosen selling rate.\n- Total cost = money spent buying minus money received from selling.\n- Repeat for all 218 days with our forecast and the simple forecast based on last week's usage.\n- Simulated saving = how much less our forecast costs overall.")
        st.markdown("[Electricity Authority price source](https://www.emi.ea.govt.nz/Wholesale/Datasets/DispatchAndPricing/FinalEnergyPrices/ByMonth)")

st.divider()
st.caption("YORICast · Historical data, not live forecasts · Final course-model outputs")
st.markdown("[Electricity demand source: Electricity Authority EMI](https://www.emi.ea.govt.nz/Wholesale/Datasets/Volumes/Reconciliation)")
