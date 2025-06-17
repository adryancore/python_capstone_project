import sqlite3

DB_FILE = "mlb_history.db"

def connect_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def run_query(conn, query, params=()):
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        if rows:
            # Print column names
            col_names = [desc[0] for desc in cur.description]
            print("\t".join(col_names))
            print("-" * 40)
            for row in rows:
                print("\t".join(str(cell) for cell in row))
        else:
            print("No results found.")
    except sqlite3.Error as e:
        print(f"Error executing query: {e}")

def main():
    conn = connect_db()
    if not conn:
        return

    print("Connected to MLB SQLite database.")
    print("Enter your SQL queries below (type 'exit' to quit).")
    print("Example: SELECT * FROM mlb_stats_summary WHERE Year = 1920;")
    print("You can join tables, filter by year, event, etc.\n")

    while True:
        user_input = input("SQL> ").strip()
        if user_input.lower() in ('exit', 'quit'):
            print("Goodbye!")
            break
        if not user_input:
            continue
        
        run_query(conn, user_input)

    conn.close()

if __name__ == "__main__":
    main()
