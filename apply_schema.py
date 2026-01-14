import psycopg2
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

def apply_schema():
    db_conn_string = os.getenv("DATABASE_CONN_STRING")
    if not db_conn_string:
        print("DATABASE_CONN_STRING not found.")
        return

    try:
        conn = psycopg2.connect(db_conn_string)
        cur = conn.cursor()
        
        with open('schema.sql', 'r') as f:
            schema = f.read()
            
        print("Applying schema...")
        cur.execute(schema)
        conn.commit()
        cur.close()
        conn.close()
        print("Schema applied successfully.")
    except Exception as e:
        print(f"Error applying schema: {e}")

if __name__ == "__main__":
    apply_schema()
