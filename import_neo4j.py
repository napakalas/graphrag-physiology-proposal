"""
import_neo4j.py
==============
Script untuk mengimport kg_subset.csv (hasil filter_kg.py) ke Neo4j.
Menggunakan batched transactions untuk performa optimal.

Cara pakai:
    # Neo4j lokal (Docker)
    python import_neo4j.py

    # Neo4j AuraDB (cloud)
    python import_neo4j.py --uri neo4j+s://xxxx.databases.neo4j.io --user neo4j --password <password>

    # Mode cepat: generate Cypher LOAD CSV (jalankan langsung di Neo4j Browser)
    python import_neo4j.py --generate-cypher

Requirements:
    pip install neo4j pandas tqdm
"""

import argparse
import os
import sys
import time
import pandas as pd
from tqdm import tqdm


# -----------------------------------------------------------------------
# KONFIGURASI DEFAULT
# -----------------------------------------------------------------------

DEFAULT_URI      = "bolt://localhost:7687"
DEFAULT_USER     = "neo4j"
DEFAULT_PASSWORD = "password"
DEFAULT_INPUT    = "kg_subset.csv"
BATCH_SIZE       = 1_000   # edge per batch — turunkan ke 500 jika koneksi lambat

# Mapping x_type / y_type dari PrimeKG ke label Neo4j
# Disesuaikan dengan nama kolom x_type dan y_type di kg.csv
NODE_LABEL_MAP = {
    "disease"             : "Disease",
    "drug"                : "Drug",
    "gene/protein"        : "Protein",
    "protein"             : "Protein",
    "biological_process"  : "BiologicalProcess",
    "molecular_function"  : "MolecularFunction",
    "cellular_component"  : "CellularComponent",
    "anatomy"             : "Anatomy",
    "phenotype"           : "Phenotype",
    "symptom"             : "Phenotype",
    "exposure"            : "Exposure",
    "pathway"             : "Pathway",
    "effect/phenotype"    : "Phenotype",
}


# -----------------------------------------------------------------------
# FUNGSI: Buat index Neo4j (jalankan SEKALI sebelum import)
# -----------------------------------------------------------------------

def create_indexes(driver) -> None:
    """
    Buat index pada properti `id` untuk setiap label node.
    Ini mempercepat MERGE secara signifikan.
    """
    labels = list(set(NODE_LABEL_MAP.values()))
    print("\n[INFO] Membuat index Neo4j...")

    with driver.session() as session:
        for label in labels:
            try:
                session.run(
                    f"CREATE INDEX {label.lower()}_id IF NOT EXISTS "
                    f"FOR (n:{label}) ON (n.id)"
                )
                print(f"  Index created: {label}(id)")
            except Exception as e:
                print(f"  [WARNING] Index {label}: {e}")

    print("[OK] Index selesai.\n")


# -----------------------------------------------------------------------
# FUNGSI: Dapatkan label Neo4j dari tipe node PrimeKG
# -----------------------------------------------------------------------

def get_label(node_type: str) -> str:
    """Konversi x_type / y_type PrimeKG ke label Neo4j."""
    return NODE_LABEL_MAP.get(node_type.strip().lower(), "BioEntity")


# -----------------------------------------------------------------------
# FUNGSI: Import satu batch ke Neo4j
# -----------------------------------------------------------------------

def import_batch(session, batch: list) -> int:
    """
    Import satu batch edge menggunakan MERGE.
    Setiap edge diproses dengan label dinamis sesuai tipe node.
    Mengembalikan jumlah edge yang berhasil diimport.
    """
    count = 0

    for row in batch:
        x_label = get_label(row["x_type"])
        y_label = get_label(row["y_type"])

        query = f"""
        MERGE (x:{x_label} {{id: $x_id}})
          ON CREATE SET x.name = $x_name, x.source = $x_source
        MERGE (y:{y_label} {{id: $y_id}})
          ON CREATE SET y.name = $y_name, y.source = $y_source
        MERGE (x)-[r:RELATION {{type: $relation, display: $display}}]->(y)
        """

        session.run(
            query,
            x_id     = str(row["x_id"]),
            x_name   = str(row["x_name"]),
            x_source = str(row.get("x_source", "")),
            y_id     = str(row["y_id"]),
            y_name   = str(row["y_name"]),
            y_source = str(row.get("y_source", "")),
            relation = str(row["relation"]),
            display  = str(row.get("display_relation", row["relation"])),
        )
        count += 1

    return count


# -----------------------------------------------------------------------
# FUNGSI: Import seluruh kg_subset.csv ke Neo4j
# -----------------------------------------------------------------------

def import_kg(uri: str, user: str, password: str, input_path: str) -> None:
    """Baca kg_subset.csv dan import ke Neo4j dalam batch."""

    # Cek file
    if not os.path.exists(input_path):
        print(f"[ERROR] File tidak ditemukan: {input_path}")
        print(        "        Jalankan filter_kg.py terlebih dahulu.")
        sys.exit(1)

    df = pd.read_csv(input_path, low_memory=False)
    total = len(df)
    print(f"[INFO] File    : {input_path}  ({os.path.getsize(input_path)/1e6:.1f} MB)")
    print(f"[INFO] Total   : {total:,} edge akan diimport")
    print(f"[INFO] Neo4j   : {uri}")
    print(f"[INFO] Batch   : {BATCH_SIZE} edge per transaksi\n")

    # Sambung ke Neo4j
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("[OK] Koneksi Neo4j berhasil.\n")
    except Exception as e:
        print(f"[ERROR] Gagal konek ke Neo4j: {e}")
        print( "        Pastikan Neo4j berjalan dan kredensial benar.")
        sys.exit(1)

    # Buat index dulu
    create_indexes(driver)

    # Import dalam batch
    records = df.to_dict("records")
    batches  = [records[i:i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]

    total_imported = 0
    start_time     = time.time()

    with driver.session() as session:
        for batch in tqdm(batches, desc="Importing"):
            total_imported += import_batch(session, batch)

    elapsed = time.time() - start_time

    # Statistik akhir
    print(f"\n{'='*55}")
    print(f"  HASIL IMPORT")
    print(f"{'='*55}")
    print(f"  Edge diimport       : {total_imported:>12,}")
    print(f"  Waktu               : {elapsed:>11.1f} detik")
    print(f"  Throughput          : {total_imported/elapsed:>11.0f} edge/detik")
    print(f"{'='*55}")

    # Verifikasi langsung di Neo4j
    print("\n[INFO] Verifikasi di Neo4j...")
    with driver.session() as session:
        result = session.run(
            "MATCH ()-[r]->() RETURN r.type AS relasi, COUNT(*) AS n "
            "ORDER BY n DESC"
        )
        print(f"\n  {'Relasi':<35} {'Edge':>10}")
        print(f"  {'-'*35} {'-'*10}")
        for record in result:
            print(f"  {record['relasi']:<35} {record['n']:>10,}")

        node_result = session.run("MATCH (n) RETURN labels(n)[0] AS label, COUNT(*) AS n ORDER BY n DESC")
        print(f"\n  {'Node Label':<35} {'Jumlah':>10}")
        print(f"  {'-'*35} {'-'*10}")
        for record in node_result:
            print(f"  {record['label']:<35} {record['n']:>10,}")

    driver.close()
    print(f"\n[OK] Import selesai.\n")
    print("[CONTOH CYPHER YANG BISA DICOBA]")
    print("""
  -- Obat untuk Multiple Sclerosis
  MATCH (d:Disease)-[r:RELATION {type: 'indication'}]->(drug:Drug)
  WHERE toLower(d.name) CONTAINS 'multiple sclerosis'
  RETURN d.name, drug.name LIMIT 10

  -- Gejala dari Depression (MDD)
  MATCH (d:Disease)-[r:RELATION {type: 'disease_phenotype'}]->(p:Phenotype)
  WHERE toLower(d.name) CONTAINS 'depressive'
  RETURN d.name, p.name LIMIT 15

  -- Efek samping Morphine
  MATCH (drug:Drug)-[r:RELATION {type: 'drug_effect'}]->(e)
  WHERE toLower(drug.name) CONTAINS 'morphine'
  RETURN drug.name, e.name LIMIT 10
    """)


# -----------------------------------------------------------------------
# FUNGSI: Generate Cypher LOAD CSV (mode alternatif — lebih cepat)
# -----------------------------------------------------------------------

def generate_cypher(input_path: str) -> None:
    """
    Cetak perintah Cypher LOAD CSV yang bisa dijalankan langsung
    di Neo4j Browser atau neo4j-shell. Jauh lebih cepat dari Python driver
    karena dieksekusi langsung di server Neo4j.

    CATATAN: kg_subset.csv harus bisa diakses oleh server Neo4j.
    Untuk Neo4j lokal, taruh file di folder `import/` Neo4j.
    Untuk AuraDB, upload file ke tempat yang bisa diakses via URL (mis. GitHub raw).
    """
    abs_path = os.path.abspath(input_path)
    file_uri = f"file:///{abs_path.replace(chr(92), '/')}"

    cypher = f"""
// ============================================================
// LOAD CSV: Import kg_subset.csv ke Neo4j
// Jalankan di Neo4j Browser atau cypher-shell
// File: {abs_path}
// ============================================================

// STEP 1: Buat index (jalankan terpisah dulu)
CREATE INDEX disease_id IF NOT EXISTS FOR (n:Disease) ON (n.id);
CREATE INDEX drug_id    IF NOT EXISTS FOR (n:Drug)    ON (n.id);
CREATE INDEX protein_id IF NOT EXISTS FOR (n:Protein) ON (n.id);
CREATE INDEX phenotype_id IF NOT EXISTS FOR (n:Phenotype) ON (n.id);

// STEP 2: Load CSV dan buat node + edge
// (ganti file URI sesuai lokasi file)
LOAD CSV WITH HEADERS FROM '{file_uri}' AS row
CALL {{
  WITH row
  MERGE (x {{id: row.x_id, type: row.x_type}})
    ON CREATE SET x.name = row.x_name, x.source = row.x_source
  MERGE (y {{id: row.y_id, type: row.y_type}})
    ON CREATE SET y.name = row.y_name, y.source = row.y_source
  MERGE (x)-[:RELATION {{type: row.relation, display: row.display_relation}}]->(y)
}} IN TRANSACTIONS OF 1000 ROWS;
"""
    print(cypher)
    cypher_file = "import_kg.cypher"
    with open(cypher_file, "w") as f:
        f.write(cypher)
    print(f"[OK] Cypher disimpan ke: {cypher_file}")


# -----------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import kg_subset.csv ke Neo4j."
    )
    parser.add_argument("--uri",      default=DEFAULT_URI,      help=f"URI Neo4j (default: {DEFAULT_URI})")
    parser.add_argument("--user",     default=DEFAULT_USER,     help=f"Username (default: {DEFAULT_USER})")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Password Neo4j")
    parser.add_argument("--input",    default=DEFAULT_INPUT,    help=f"Path kg_subset.csv (default: {DEFAULT_INPUT})")
    parser.add_argument(
        "--generate-cypher", action="store_true",
        help="Generate file Cypher LOAD CSV saja (tanpa koneksi Neo4j)"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.generate_cypher:
        generate_cypher(args.input)
    else:
        import_kg(args.uri, args.user, args.password, args.input)
