import sqlite3
import csv

conn = sqlite3.connect("baseball.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS team_stats")
cursor.execute("""
    CREATE TABLE team_stats (
        year INTEGER,
        most_wins TEXT,
        most_losses TEXT,
        champion TEXT
    )
""")

with open("mlb_stats_summary.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    rows = [(int(row["Year"]), row["Most Wins"], row["Most Losses"], row["Champion"]) for row in reader]

cursor.executemany("INSERT INTO team_stats VALUES (?, ?, ?, ?)", rows)

# Keep event_data as before
cursor.execute("DROP TABLE IF EXISTS event_data")
cursor.execute("""
    CREATE TABLE event_data (
        year INTEGER,
        section TEXT,
        content TEXT
    )
""")

with open("mlb_history_sections.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    rows = [(int(row["Year"]), row["Section"], row["Content"]) for row in reader]

cursor.executemany("INSERT INTO event_data VALUES (?, ?, ?)", rows)

conn.commit()
conn.close()

print("Database setup complete.")
