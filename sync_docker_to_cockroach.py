import os
import psycopg
from psycopg.rows import dict_row

COCKROACH = 'postgresql://modini:G7ngThrPrQlY_kii_qBoig@cesar-ecosystem-10552.jxf.gcp-us-east1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full'

print("Connecting to CockroachDB...")
conn = psycopg.connect(COCKROACH)
cur = conn.cursor()

print("Creating agents table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    status VARCHAR(50),
    metadata JSONB DEFAULT '{}'
)
""")
conn.commit()
print("Table created!")
conn.close()
print("Done!")
