import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -------------------- Page configuration --------------------
st.set_page_config(
    page_title="Cricket Batter Analytics",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- Styling --------------------
st.markdown("""
<style>
    .main {background: linear-gradient(180deg, #f5f7fb 0%, #eef2f8 100%);}
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.5rem 1.8rem;
        border-radius: 20px;
        background: linear-gradient(115deg, #111827, #1d4ed8 65%, #06b6d4);
        color: white;
        margin-bottom: 1.1rem;
        box-shadow: 0 10px 28px rgba(31, 41, 55, .18);
    }
    .hero h1 {margin: 0; font-size: 2.15rem;}
    .hero p {margin: .45rem 0 0 0; color: #e5efff; font-size: 1rem;}
    div[data-testid="stMetric"] {
        background: white; padding: 1rem 1.1rem; border-radius: 16px;
        border: 1px solid #e6eaf2; box-shadow: 0 5px 18px rgba(15, 23, 42, .05);
    }
    section[data-testid="stSidebar"] {background: #111827;}
    section[data-testid="stSidebar"] * {color: white;}
    .small-note {color: #64748b; font-size: .88rem;}
</style>
""", unsafe_allow_html=True)

# -------------------- Load CSV --------------------
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
    else:
        data = pd.read_csv("batter_player_stats.csv")
    data.columns = data.columns.str.strip()
    return data

st.sidebar.title("🏏 Cricket Analytics")
st.sidebar.caption("Explore player and team performance")

uploaded_file = st.sidebar.file_uploader("Upload your CSV (optional)", type=["csv"])
try:
    df = load_data(uploaded_file)
except FileNotFoundError:
    st.error("CSV file not found. Keep `batter_player_stats.csv` in the same folder as `app.py`, or upload it in the sidebar.")
    st.stop()
except Exception as e:
    st.error(f"Could not read the CSV: {e}")
    st.stop()

required = ["player_name", "role", "total_runs", "strike_rate", "total_matches_played",
            "player_of_match_awards", "team", "average"]
missing = [col for col in required if col not in df.columns]
if missing:
    st.error("Your CSV is missing required columns: " + ", ".join(missing))
    st.stop()

# Normalize text and numeric columns
for col in ["player_name", "role", "team"]:
    df[col] = df[col].fillna("Unknown").astype(str).str.strip()
numeric_cols = df.select_dtypes(include="number").columns.tolist()
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# -------------------- Sidebar filters --------------------
st.sidebar.subheader("🔎 Filters")
teams = sorted([x for x in df["team"].dropna().unique() if x != "Unknown"])
roles = sorted([x for x in df["role"].dropna().unique() if x != "Unknown"])

selected_teams = st.sidebar.multiselect("Team", teams, default=teams)
selected_roles = st.sidebar.multiselect("Player role", roles, default=roles)
search_name = st.sidebar.text_input("Search player", placeholder="e.g. V Kohli")

filtered = df.copy()
if selected_teams:
    filtered = filtered[filtered["team"].isin(selected_teams)]
else:
    filtered = filtered.iloc[0:0]
if selected_roles:
    filtered = filtered[filtered["role"].isin(selected_roles)]
else:
    filtered = filtered.iloc[0:0]
if search_name.strip():
    filtered = filtered[filtered["player_name"].str.contains(search_name.strip(), case=False, na=False)]

# -------------------- Header --------------------
st.markdown("""
<div class="hero">
  <h1>🏏 Cricket Batter Performance Dashboard</h1>
  <p>Explore player statistics, compare teams, and discover standout performances.</p>
</div>
""", unsafe_allow_html=True)

if filtered.empty:
    st.warning("No players match these filters. Select at least one team and one role, or clear the player search.")
    st.stop()

# -------------------- KPI cards --------------------
top_scorer = filtered.loc[filtered["total_runs"].idxmax()]
top_awards = filtered.loc[filtered["player_of_match_awards"].idxmax()]
avg_sr = filtered["strike_rate"].mean()
total_runs = filtered["total_runs"].sum()
total_players = filtered["player_name"].nunique()
total_awards = filtered["player_of_match_awards"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Players", f"{total_players:,}")
c2.metric("Combined Runs", f"{total_runs:,.0f}")
c3.metric("Average Strike Rate", f"{avg_sr:,.2f}" if pd.notna(avg_sr) else "N/A")
c4.metric("Player-of-Match Awards", f"{total_awards:,.0f}")
c5.metric("Top Run Scorer", str(top_scorer["player_name"]), f'{top_scorer["total_runs"]:,.0f} runs')

st.divider()

# -------------------- Charts --------------------
left, right = st.columns(2)

with left:
    st.subheader("🏆 Top 10 Run Scorers")
    top_runs = filtered.nlargest(10, "total_runs").sort_values("total_runs", ascending=True)
    fig_runs = px.bar(
        top_runs, x="total_runs", y="player_name", orientation="h",
        color="total_runs", color_continuous_scale="Blues",
        text="total_runs", hover_data=["team", "role", "strike_rate"],
        labels={"total_runs": "Total runs", "player_name": "Player"},
        template="plotly_white"
    )
    fig_runs.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    fig_runs.update_layout(height=440, coloraxis_showscale=False, margin=dict(l=10, r=35, t=20, b=10))
    st.plotly_chart(fig_runs, use_container_width=True)

with right:
    st.subheader("🌍 Team Comparison")
    team_stats = filtered.groupby("team", as_index=False).agg(
        total_runs=("total_runs", "sum"),
        avg_strike_rate=("strike_rate", "mean"),
        players=("player_name", "nunique"),
        awards=("player_of_match_awards", "sum")
    ).sort_values("total_runs", ascending=False)
    team_metric = st.selectbox(
        "Compare teams by",
        ["total_runs", "avg_strike_rate", "players", "awards"],
        format_func=lambda x: {
            "total_runs": "Combined runs",
            "avg_strike_rate": "Average strike rate",
            "players": "Number of players",
            "awards": "Total player-of-match awards"
        }[x]
    )
    fig_team = px.bar(
        team_stats.sort_values(team_metric, ascending=True),
        x=team_metric, y="team", orientation="h", color=team_metric,
        color_continuous_scale="Tealgrn", text_auto=".2f",
        labels={team_metric: team_metric.replace("_", " ").title(), "team": "Team"},
        template="plotly_white"
    )
    fig_team.update_layout(height=440, coloraxis_showscale=False, margin=dict(l=10, r=20, t=20, b=10))
    st.plotly_chart(fig_team, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.subheader("⚡ Strike Rate vs Total Runs")
    scatter_df = filtered.dropna(subset=["strike_rate", "total_runs"])
    fig_scatter = px.scatter(
        scatter_df, x="strike_rate", y="total_runs", color="team",
        size="total_matches_played", hover_name="player_name",
        hover_data=["role", "player_of_match_awards"],
        labels={"strike_rate": "Strike rate", "total_runs": "Total runs"},
        template="plotly_white"
    )
    fig_scatter.update_layout(height=430, legend_title_text="Team", margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

with right2:
    st.subheader("🎖️ Player-of-Match Awards")
    award_df = filtered.nlargest(10, "player_of_match_awards").sort_values("player_of_match_awards", ascending=True)
    fig_awards = px.bar(
        award_df, x="player_of_match_awards", y="player_name", orientation="h",
        color="player_of_match_awards", color_continuous_scale="Sunset",
        text="player_of_match_awards", hover_data=["team", "total_runs"],
        labels={"player_of_match_awards": "Awards", "player_name": "Player"},
        template="plotly_white"
    )
    fig_awards.update_traces(textposition="outside", cliponaxis=False)
    fig_awards.update_layout(height=430, coloraxis_showscale=False, margin=dict(l=10, r=30, t=20, b=10))
    st.plotly_chart(fig_awards, use_container_width=True)

# -------------------- Data table --------------------
st.divider()
st.subheader("📋 Player Statistics")
col_options = [c for c in [
    "player_name", "team", "role", "total_runs", "strike_rate", "average",
    "total_matches_played", "total_balls_faced", "total_wickets_taken",
    "matches_won", "matches_lost", "player_of_match_awards"
] if c in filtered.columns]
table_search = st.text_input("Quick search within the displayed table", placeholder="Type a player or team name")
table_df = filtered.copy()
if table_search.strip():
    mask = table_df.astype(str).apply(
        lambda col: col.str.contains(table_search.strip(), case=False, na=False)
    ).any(axis=1)
    table_df = table_df[mask]

st.dataframe(
    table_df[col_options].sort_values("total_runs", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "total_runs": st.column_config.NumberColumn("Total Runs", format="%d"),
        "strike_rate": st.column_config.NumberColumn("Strike Rate", format="%.2f"),
        "average": st.column_config.NumberColumn("Average", format="%.2f"),
        "player_of_match_awards": st.column_config.NumberColumn("POTM Awards", format="%d")
    }
)

csv_bytes = table_df[col_options].to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download filtered player data",
    data=csv_bytes,
    file_name="filtered_player_stats.csv",
    mime="text/csv"
)

st.caption("Dashboard powered by Streamlit, Pandas and Plotly. Statistics reflect the rows currently selected in the sidebar.")
