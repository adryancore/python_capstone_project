import streamlit as st
import pandas as pd
import altair as alt

# --- Load & Prepare Data ---
df = pd.read_csv("mlb_stats_summary.csv")
df.columns = df.columns.str.strip().str.lower()  # Normalize column names

# Confirm data columns
required_cols = ['year', 'most wins', 'most losses', 'champion']
if not all(col in df.columns for col in required_cols):
    st.error(f"CSV must contain columns: {required_cols}")
    st.stop()

# --- Page Setup ---
st.set_page_config(page_title="MLB Summary Dashboard", layout="centered")
st.title("🏟️ MLB Season Summary Dashboard")
st.markdown("""
Explore Major League Baseball season summaries by year.

**Instructions**:
- Use the sidebar to select a year.
- Adjust the chart size with the slider.
- Visualizations will update automatically.
""")

# --- Sidebar Interactions ---
year = st.sidebar.selectbox("Select Season Year", sorted(df['year'].unique()))
chart_size = st.sidebar.slider("Adjust Chart Size", min_value=200, max_value=600, value=400)

# --- Filter Data ---
year_data = df[df['year'] == year].copy()

# --- Extract Key Info ---
most_wins_team = year_data['most wins'].values[0]
most_losses_team = year_data['most losses'].values[0]
champion_team = year_data['champion'].values[0]

# --- Display Summary Info ---
st.subheader(f"📊 {year} Season Summary")
st.markdown(f"""
- 🥇 **Champion:** {champion_team}
- ✅ **Most Wins:** {most_wins_team}
- ❌ **Most Losses:** {most_losses_team}
""")

# --- Visualization 1: Champion Count Over Time ---
st.subheader("🏆 Champions Over Time")
champ_counts = df['champion'].value_counts().reset_index()
champ_counts.columns = ['champion', 'count']
bar_chart = alt.Chart(champ_counts).mark_bar().encode(
    x=alt.X('champion:N', title='Champion Team', sort='-y'),
    y=alt.Y('count:Q', title='Number of Championships'),
    tooltip=['champion', 'count'],
    color='champion:N'
).properties(width=chart_size, height=chart_size)
st.altair_chart(bar_chart, use_container_width=True)

# --- Visualization 2: Win vs Loss Team Mentions Over Time ---
st.subheader("📈 Most Wins vs Losses Mentions")
# Combine counts of teams that had most wins and most losses
mentions = pd.concat([
    df['most wins'].rename('team'),
    df['most losses'].rename('team')
])
mention_counts = mentions.value_counts().reset_index()
mention_counts.columns = ['team', 'mentions']

team_mentions_chart = alt.Chart(mention_counts).mark_bar().encode(
    x=alt.X('team:N', title='Team', sort='-y'),
    y=alt.Y('mentions:Q', title='Mentions (Wins/Losses)'),
    color='team:N',
    tooltip=['team', 'mentions']
).properties(width=chart_size, height=chart_size)
st.altair_chart(team_mentions_chart, use_container_width=True)

# --- Visualization 3: Year-by-Year Champions (Line Chart) ---
st.subheader("📅 Yearly Champion Timeline")
champ_line = alt.Chart(df).mark_line(point=True).encode(
    x=alt.X('year:O', title='Year'),
    y=alt.Y('champion:N', title='Champion'),
    color='champion:N',
    tooltip=['year', 'champion']
).properties(width=chart_size + 200, height=300)
st.altair_chart(champ_line, use_container_width=True)

# --- Footer ---
st.markdown("---")
st.markdown("Made with ❤️ using Streamlit | Data: `mlb_stats_summary.csv`")
