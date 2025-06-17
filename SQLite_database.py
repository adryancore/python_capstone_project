import sqlite3
import csv
import os

def infer_sqlite_type(value):
    """Infer SQLite column type from a sample value."""
    if value.isdigit():
        return "INTEGER"
    try:
        float(value)
        return "REAL"
    except ValueError:
        return "TEXT"

def create_table_from_csv(cursor, table_name, csv_path):
    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)
        sample_row = next(reader, None)
        if not sample_row:
            raise ValueError(f"CSV file {csv_path} is empty beyond header")

        # Infer column types based on sample row
        col_types = []
        for val in sample_row:
            col_types.append(infer_sqlite_type(val))

        # Build CREATE TABLE statement
        columns = [
            f'"{header}" {col_type}'
            for header, col_type in zip(headers, col_types)
        ]
        create_stmt = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(columns)});'
        cursor.execute(create_stmt)

        # Insert the sample row, then the rest
        column_names = ', '.join(f'"{h}"' for h in headers)
        placeholders = ', '.join('?' for _ in headers)
        insert_stmt = f'INSERT INTO "{table_name}" ({column_names}) VALUES ({placeholders});'
        
        cursor.execute(insert_stmt, sample_row)
        for row in reader:
            cursor.execute(insert_stmt, row)

def import_csvs_to_sqlite(db_path, csv_files):
    if not csv_files:
        print("No CSV files provided to import.")
        return

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for csv_file in csv_files:
            table_name = os.path.splitext(os.path.basename(csv_file))[0]
            try:
                print(f"Importing {csv_file} into table '{table_name}'")
                create_table_from_csv(cursor, table_name, csv_file)
                conn.commit()
                print(f"Successfully imported {csv_file}")
            except Exception as e:
                print(f"Error importing {csv_file}: {e}")

if __name__ == "__main__":
    # Example usage - update these paths as needed
    database_path = "mlb_data.db"
    csv_files_to_import = ["mlb_history_sections.csv", "mlb_stats_summary.csv"]

    import_csvs_to_sqlite(database_path, csv_files_to_import)
