import sqlite3

def print_rows(rows, headers):
    # Print rows in a readable table format
    col_widths = [max(len(str(cell)) for cell in col) for col in zip(*([headers] + rows))]
    row_format = " | ".join(["{:<" + str(width) + "}" for width in col_widths])
    print(row_format.format(*headers))
    print("-" * (sum(col_widths) + 3 * (len(headers) - 1)))
    for row in rows:
        print(row_format.format(*row))

def run_query(conn, query, params=()):
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
        if rows:
            print_rows(rows, headers)
        else:
            print("No results found.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

def main():
    print("Connecting to baseball.db...")
    conn = sqlite3.connect("baseball.db")
    print("Connected. Enter your queries or type 'help' or 'exit'.")

    help_text = """
Commands you can try:

1. Show all teams and their wins/losses in a year:
   > teams YEAR
   Example: teams 1885

2. Show all events for a given year:
   > events YEAR
   Example: events 1885

3. Join team stats with event data by year:
   > join YEAR
   Example: join 1885

4. Filter teams by name substring:
   > filterteam YEAR TEAM_SUBSTRING
   Example: filterteam 1885 yankees

5. Exit the program:
   > exit
"""

    while True:
        user_input = input("Query> ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        elif user_input.lower() == "help":
            print(help_text)
            continue
        elif user_input.startswith("teams "):
            parts = user_input.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("Invalid input. Usage: teams YEAR")
                continue
            year = int(parts[1])
            query = "SELECT team, wins, losses FROM team_stats WHERE year = ?"
            run_query(conn, query, (year,))
        elif user_input.startswith("events "):
            parts = user_input.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("Invalid input. Usage: events YEAR")
                continue
            year = int(parts[1])
            query = "SELECT section, content FROM event_data WHERE year = ?"
            run_query(conn, query, (year,))
        elif user_input.startswith("join "):
            parts = user_input.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("Invalid input. Usage: join YEAR")
                continue
            year = int(parts[1])
            query = """
            SELECT ts.team, ts.wins, ts.losses, ed.section, ed.content
            FROM team_stats ts
            LEFT JOIN event_data ed ON ts.year = ed.year
            WHERE ts.year = ?
            ORDER BY ts.team
            """
            run_query(conn, query, (year,))
        elif user_input.startswith("filterteam "):
            parts = user_input.split(maxsplit=2)
            if len(parts) != 3 or not parts[1].isdigit():
                print("Invalid input. Usage: filterteam YEAR TEAM_SUBSTRING")
                continue
            year = int(parts[1])
            team_sub = parts[2].lower()
            query = "SELECT team, wins, losses FROM team_stats WHERE year = ? AND LOWER(team) LIKE ?"
            run_query(conn, query, (year, f"%{team_sub}%"))
        else:
            print("Unknown command. Type 'help' for commands.")

    conn.close()

if __name__ == "__main__":
    main()