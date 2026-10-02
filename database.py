import sqlite3
import xml.etree.ElementTree as ET
import pathlib as Path

DB_ROOT = Path.Path(__file__).resolve().parent

class Database:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def create_table(self, table_name, columns):
        columns_str = ', '.join([f"{col} {dtype}" for col, dtype in columns.items()])
        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
        self.cursor.execute(create_table_query)
        self.conn.commit()

    def insert_data(self, table_name, data):
        placeholders = ', '.join(['?' for _ in data])
        insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"
        self.cursor.execute(insert_query, data)
        self.conn.commit()

    def fetch_data(self, table_name):
        fetch_query = f"SELECT * FROM {table_name}"
        self.cursor.execute(fetch_query)
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

def date_exists(data, date):
    for index, points in enumerate(data):
        if points["date"] == date:
            return index
    return -1

def get_steps(): 
    root = ET.parse("export.xml").getroot()
    data = []
    for child in root:
        record_type = child.get("type")
        name = child.get("sourceName")
        if (record_type == "HKQuantityTypeIdentifierStepCount" and (name == "Dani" or name == "Dc")):
            date = child.get("endDate", "").split(" ")[0]
            value = int(child.get("value"))

            index = date_exists(data, date)
            if (index != -1):
                data[index]["steps"] += value
            else:
                data.append({
                    "date": date,
                    "steps": value,
                })

    with open("data.csv", "w") as f:
       for record in data:
           f.write(f"{record['date']},{record['steps']}\n")

def commands():
    dbName = DB_ROOT / 'health_data.db'
    conn = sqlite3.connect(dbName)
    cursor = conn.cursor()

    cursor.execute("SELECT ROW_NUMBER() OVER (ORDER BY steps DESC) AS number, date, steps FROM steps ORDER BY steps DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()

    print("Top 100 days with the most steps:")
    for row in rows:
        print(f"Rank: {row[0]}, Date: {row[1]}, Steps: {row[2]}")

def main():
    dbName = DB_ROOT / 'health_data.db'
    db = Database(dbName)
    db.create_table("steps", {"date": "TEXT PRIMARY KEY", "steps": "INTEGER"})
    
    with open("data.csv", "r") as f:
        for line in f:
            date, steps = line.strip().split(",")
            db.insert_data("steps", (date, int(steps)))
 
    db.close()
 
if __name__ == "__main__":
    commands()