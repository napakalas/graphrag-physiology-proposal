"""
filter_kg.py
============
Script untuk memfilter kg.csv dari PrimeKG (Harvard Dataverse) menjadi
subset kecil yang hanya berisi relasi yang relevan untuk proyek
Semantic Query Expansion & Disambiguasi Leksikal (Tugas Akhir S1).

Cara pakai:
    python filter_kg.py
    python filter_kg.py --input data/kg.csv --output data/kg_subset.csv
    python filter_kg.py --list-relations   # lihat semua relasi yang ada di kg.csv

Requirements:
    pip install pandas tqdm
"""

import argparse
import os
import sys
import pandas as pd
from tqdm import tqdm


# -----------------------------------------------------------------------
# KONFIGURASI: ubah sesuai kebutuhan proyek
# -----------------------------------------------------------------------

# Relasi yang diprioritaskan untuk proyek disambiguasi leksikal medis.
# Komentar menjelaskan tipe ambiguitas yang didukung masing-masing.
PRIORITY_RELATIONS = [
    "disease_phenotype",    # gejala -> penyakit      (Tipe 1: polisemi, Tipe 3: specificity gap)
    "indication",           # penyakit -> obat         (Tipe 2: akronim via konteks obat)
    "contraindication",     # penyakit -> obat         (Tipe 2: akronim)
    "off-label use",        # penyakit -> obat         (opsional, tambah konteks drug)
    "disease_protein",      # penyakit -> protein/gen  (konteks biologis untuk ranker)
    "drug_effect",          # obat -> efek samping     (Tipe 1: mis. respiratory depression)
]

# Kolom wajib yang harus ada di kg.csv
REQUIRED_COLUMNS = [
    "relation", "display_relation",
    "x_id", "x_type", "x_name", "x_source",
    "y_id", "y_type", "y_name", "y_source",
]

DEFAULT_INPUT  = "kg.csv"
DEFAULT_OUTPUT = "kg_subset.csv"
CHUNK_SIZE     = 100_000   # jumlah baris per chunk — turunkan jika RAM < 8 GB


# -----------------------------------------------------------------------
# FUNGSI UTAMA
# -----------------------------------------------------------------------

def list_relations(input_path: str, chunk_size: int) -> None:
    """
    Baca kg.csv secara chunked dan tampilkan semua tipe relasi beserta
    jumlah edge-nya. Berguna untuk eksplorasi sebelum menentukan filter.
    """
    print(f"\n[INFO] Membaca relasi dari: {input_path}")
    print(f"[INFO] Chunk size: {chunk_size:,} baris\n")

    relation_counts: dict = {}
    total_rows = 0

    for chunk in tqdm(
        pd.read_csv(input_path, chunksize=chunk_size, low_memory=False),
        desc="Scanning"
    ):
        total_rows += len(chunk)
        counts = chunk["relation"].value_counts()
        for rel, cnt in counts.items():
            relation_counts[rel] = relation_counts.get(rel, 0) + cnt

    print(f"\n{'='*55}")
    print(f"  Total baris di kg.csv : {total_rows:>12,}")
    print(f"  Jumlah tipe relasi    : {len(relation_counts):>12,}")
    print(f"{'='*55}")
    print(f"  {'Relasi':<40} {'Jumlah Edge':>12}")
    print(f"  {'-'*40} {'-'*12}")

    for rel, cnt in sorted(relation_counts.items(), key=lambda x: -x[1]):
        marker = " <-- DIPILIH" if rel in PRIORITY_RELATIONS else ""
        print(f"  {rel:<40} {cnt:>12,}{marker}")

    print(f"{'='*55}\n")


def filter_kg(input_path: str, output_path: str, chunk_size: int) -> None:
    """
    Baca kg.csv dalam chunk, filter berdasarkan PRIORITY_RELATIONS,
    dan simpan hasilnya ke output_path.
    """
    # --- validasi file input ---
    if not os.path.exists(input_path):
        print(f"[ERROR] File tidak ditemukan: {input_path}")
        print( "        Unduh kg.csv dari https://doi.org/10.7910/DVN/IXA7BM")
        sys.exit(1)

    print(f"\n[INFO] Input  : {input_path}  ({os.path.getsize(input_path)/1e6:.1f} MB)")
    print(f"[INFO] Output : {output_path}")
    print(f"[INFO] Chunk  : {chunk_size:,} baris per iterasi")
    print(f"[INFO] Relasi yang disimpan:")
    for r in PRIORITY_RELATIONS:
        print(f"         - {r}")
    print()

    # --- validasi kolom ---
    header = pd.read_csv(input_path, nrows=0)
    missing = [c for c in REQUIRED_COLUMNS if c not in header.columns]
    if missing:
        print(f"[ERROR] Kolom berikut tidak ditemukan di kg.csv: {missing}")
        print(f"        Kolom yang ada: {list(header.columns)}")
        sys.exit(1)

    # --- chunked filtering ---
    filtered_chunks = []
    total_in  = 0
    total_out = 0

    reader = pd.read_csv(input_path, chunksize=chunk_size, low_memory=False)

    for chunk in tqdm(reader, desc="Filtering"):
        total_in += len(chunk)
        filtered = chunk[chunk["relation"].isin(PRIORITY_RELATIONS)].copy()
        total_out += len(filtered)
        if not filtered.empty:
            filtered_chunks.append(filtered)

    if not filtered_chunks:
        print("[WARNING] Tidak ada baris yang cocok dengan PRIORITY_RELATIONS.")
        print("          Periksa kembali nama relasi di PRIORITY_RELATIONS.")
        sys.exit(1)

    # --- gabung dan simpan ---
    kg_subset = pd.concat(filtered_chunks, ignore_index=True)
    kg_subset.to_csv(output_path, index=False)

    output_size_mb = os.path.getsize(output_path) / 1e6

    # --- laporan statistik ---
    print(f"\n{'='*55}")
    print(f"  HASIL FILTER")
    print(f"{'='*55}")
    print(f"  Total baris input   : {total_in:>12,}")
    print(f"  Total baris output  : {total_out:>12,}  ({total_out/total_in*100:.1f}%)")
    print(f"  Ukuran output       : {output_size_mb:>11.1f} MB")
    print(f"{'='*55}")
    print(f"\n  Distribusi per relasi:")
    print(f"  {'-'*50}")

    dist = kg_subset["relation"].value_counts()
    for rel, cnt in dist.items():
        print(f"  {rel:<35} {cnt:>10,} edge")

    print(f"\n  Node types dalam subset:")
    for ntype, cnt in kg_subset["x_type"].value_counts().items():
        print(f"    x_type = {ntype:<20} {cnt:>10,}")

    print(f"\n[OK] Subset disimpan ke: {output_path}\n")
    print("[LANGKAH BERIKUTNYA]")
    print("  1. Jalankan import_neo4j.py untuk load subset ke Neo4j")
    print("  2. Verifikasi di Neo4j Browser:")
    print("     MATCH ()-[r]->() RETURN r.type, COUNT(*) ORDER BY COUNT(*) DESC")
    print()


# -----------------------------------------------------------------------
# ENTRY POINT
# -----------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter kg.csv PrimeKG menjadi subset relasi prioritas."
    )
    parser.add_argument(
        "--input", default=DEFAULT_INPUT,
        help=f"Path ke kg.csv (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT,
        help=f"Path output subset CSV (default: {DEFAULT_OUTPUT})"
    )
    parser.add_argument(
        "--chunk-size", type=int, default=CHUNK_SIZE,
        help=f"Baris per chunk (default: {CHUNK_SIZE})"
    )
    parser.add_argument(
        "--list-relations", action="store_true",
        help="Tampilkan semua tipe relasi di kg.csv lalu keluar"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.list_relations:
        list_relations(args.input, args.chunk_size)
    else:
        filter_kg(args.input, args.output, args.chunk_size)
