import psycopg2
try:
    # Establish connection
    database_url = "postgresql://postgres:postgres@localhost:5432/experimentation" 
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    # Execute a basic query
    cur.execute("SELECT 1;")
    result = cur.fetchone()
    print("Connection successful. Query result:", result)
    cur.close()
    conn.close()
except Exception as e:
    print("Error connecting to Aurora PostgreSQL:", e)
