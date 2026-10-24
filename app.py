import streamlit as st
import pandas as pd
from pathlib import Path

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Cricket Player Analytics",
    page_icon="🏏",
    layout="wide"
)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "batter_player_stats.csv"
    df = pd.read_csv(file_path)

    # Clean column names and text values
    df.columns = df.columns.str.strip()
    for col in ["player_name", "role", "team"]:
        df[col] = df[col].astype("string").str.strip()

    # Convert numeric columns safely
    numeric_cols = [
        "total_runs", "strike_rate", "total_balls_faced",
        "total_wickets_taken", "total_runs_conceded",
        "total_overs_bowled", "total_matches_played",
        "matches_played_as_batter", "matches_played_as_bowler",
        "matches_won", "matches_lost", "player_of_match_awards",
        "average"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["player_name", "team"])
    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "CSV file not found. Keep app.py and "
        "batter_player_stats.csv in the same folder."
    )
    st.stop()
except Exception as e:
    st.error(f"Unable to load data: {e}")
    st.stop()

# ---------------- HEADER ----------------
st.title("🏏 Cricket Player Analytics Dashboard")
st.caption(
    "Explore player performance, team statistics, batting "
    "records and match awards."
)

st.divider()

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("🔎 Dashboard Filters")

teams = sorted(df["team"].dropna().unique().tolist())
roles = sorted(df["role"].dropna().unique().tolist())

selected_teams = st.sidebar.multiselect(
    "Select Team",
    teams,
    default=teams
)

selected_roles = st.sidebar.multiselect(
    "Select Player Role",
    roles,
    default=roles
)

min_matches = st.sidebar.slider(
    "Minimum Matches Played",
    min_value=0,
    max_value=int(df["total_matches_played"].max()),
    value=0
)

search_player = st.sidebar.text_input("Search Player Name")

# Apply filters
filtered_df = df[
    df["team"].isin(selected_teams)
    & df["role"].isin(selected_roles)
    & (df["total_matches_played"] >= min_matches)
]

if search_player:
    filtered_df = filtered_df[
        filtered_df["player_name"].str.contains(
            search_player, case=False, na=False
        )
    ]

if filtered_df.empty:
    st.warning("No players match these filters.")
    st.stop()

# ---------------- KPI CARDS ----------------
total_players = filtered_df["player_name"].nunique()
total_runs = filtered_df["total_runs"].sum()
total_wickets = filtered_df["total_wickets_taken"].sum()
total_awards = filtered_df["player_of_match_awards"].sum()
avg_strike_rate = filtered_df["strike_rate"].mean()

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Total Players", f"{total_players:,}")
c2.metric("Total Runs", f"{total_runs:,.0f}")
c3.metric("Total Wickets", f"{total_wickets:,.0f}")
c4.metric("Player of Match Awards", f"{total_awards:,.0f}")
c5.metric(
    "Average Strike Rate",
    f"{avg_strike_rate:.2f}" if pd.notna(avg_strike_rate) else "N/A"
)

st.divider()

# ---------------- TOP BATTERS ----------------
st.subheader("🏆 Top 10 Players by Total Runs")

top_batters = (
    filtered_df.groupby("player_name", as_index=False)["total_runs"]
    .sum()
    .sort_values("total_runs", ascending=False)
    .head(10)
    .set_index("player_name")
)

st.bar_chart(top_batters, y="total_runs")

# ---------------- TEAM ANALYSIS ----------------
left, right = st.columns(2)

with left:
    st.subheader("🌍 Runs by Team")

    team_runs = (
        filtered_df.groupby("team", as_index=False)["total_runs"]
        .sum()
        .sort_values("total_runs", ascending=False)
        .set_index("team")
    )

    st.bar_chart(team_runs, y="total_runs")

with right:
    st.subheader("⚡ Strike Rate by Player")

    strike_rate_df = filtered_df.dropna(subset=["strike_rate"])
    top_strike_rate = (
        strike_rate_df.sort_values("strike_rate", ascending=False)
        .head(10)
        .set_index("player_name")[["strike_rate"]]
    )

    st.bar_chart(top_strike_rate, y="strike_rate")

st.divider()

# ---------------- BOWLING ANALYSIS ----------------
left, right = st.columns(2)

with left:
    st.subheader("🎯 Top 10 Wicket Takers")

    top_bowlers = (
        filtered_df.groupby("player_name", as_index=False)
        ["total_wickets_taken"]
        .sum()
        .sort_values("total_wickets_taken", ascending=False)
        .head(10)
        .set_index("player_name")
    )

    st.bar_chart(top_bowlers, y="total_wickets_taken")

with right:
    st.subheader("🥇 Player of the Match Awards")

    top_awards = (
        filtered_df.groupby("player_name", as_index=False)
        ["player_of_match_awards"]
        .sum()
        .sort_values("player_of_match_awards", ascending=False)
        .head(10)
        .set_index("player_name")
    )

    st.bar_chart(top_awards, y="player_of_match_awards")

st.divider()

# ---------------- PLAYER PERFORMANCE TABLE ----------------
st.subheader("📋 Player Performance Details")

display_columns = [
    "player_name",
    "team",
    "role",
    "total_runs",
    "strike_rate",
    "total_wickets_taken",
    "total_matches_played",
    "matches_won",
    "matches_lost",
    "player_of_match_awards"
]

st.dataframe(
    filtered_df[display_columns].sort_values(
        "total_runs", ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

# ---------------- DOWNLOAD FILTERED DATA ----------------
csv_data = filtered_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Download Filtered Player Data",
    data=csv_data,
    file_name="filtered_cricket_player_stats.csv",
    mime="text/csv"
)

st.caption("Cricket Player Analytics | Built with Python, Pandas and Streamlit")
