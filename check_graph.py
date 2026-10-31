import sqlite3

conn = sqlite3.connect("edugraph.db")

for material_id in [2, 4, 5]:
    print(f"\n--- Material ID {material_id} ---")

    rows = conn.execute(
        """
        SELECT name
        FROM graph_nodes
        WHERE material_id = ?
        AND (
            lower(name) LIKE '%person%'
            OR lower(name) LIKE '%student%'
            OR lower(name) LIKE '%entity%'
            OR lower(name) LIKE '%general%'
        )
        ORDER BY name
        """,
        (material_id,)
    ).fetchall()

    for row in rows:
        print(row[0])

    if not rows:
        print("No matching concepts found.")

conn.close()