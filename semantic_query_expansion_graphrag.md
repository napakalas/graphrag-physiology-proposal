# Semantic Query Expansion Berbasis LLM untuk Disambiguasi Leksikal Istilah Medis pada Sistem GraphRAG

**Judul 2 – Proyek Mahasiswa S1**
Referensi diskusi: 28 April 2026

---

## 1. Latar Belakang & Motivasi

PrimeKG adalah *knowledge graph* (KG) presisi medis yang mengintegrasikan **20 sumber data biomedis berkualitas tinggi** menjadi satu graf dengan 17.080 node penyakit dan lebih dari 4 juta *edges*. Sumber ontologi utamanya:

| Ontologi / Sumber | Peran di PrimeKG |
|---|---|
| **MONDO** | Ontologi penyakit utama |
| **HPO** (Human Phenotype Ontology) | Node fenotip/gejala |
| **GO** (Gene Ontology) | Proses biologis, fungsi molekuler, komponen seluler |
| **UBERON** | Ontologi anatomi lintas-spesies |
| **UMLS** | Terminologi medis umum |
| DrugBank, DrugCentral | Data obat dan indikasi |
| DisGeNET, NCBI Gene, Bgee | Asosiasi gen-penyakit dan ekspresi gen |

> **Catatan Penting:** FMA dan ChEBI **tidak** digunakan sebagai kerangka utama PrimeKG. Untuk anatomi, PrimeKG menggunakan UBERON; untuk obat/kimia, menggunakan DrugBank dan DrugCentral, bukan ChEBI.

### Masalah yang Diselesaikan

Ketika pengguna memasukkan query ke sistem GraphRAG berbasis PrimeKG, muncul problem **ambiguitas leksikal dalam domain medis sendiri** (*within-domain lexical ambiguity*). Ini bukan masalah "medis vs. non-medis", melainkan **satu istilah medis yang merujuk ke beberapa node berbeda** di PrimeKG.

---

## 2. Tiga Tipe Ambiguitas Leksikal Medis

### Tipe 1 – Polisemi Medis (satu kata, banyak makna medis)

Contoh terbaik: **`"depression"`**

| Interpretasi | Node di PrimeKG | Tipe Node | Ontologi |
|---|---|---|---|
| Major Depressive Disorder | `MONDO:0002009` | Disease | MONDO |
| Respiratory depression | Efek samping opioid (mis. morfin) | Effect | Drug edge |
| ST-segment depression | Tanda EKG iskemia miokard | Phenotype | `HPO:0031547` |

**Tanpa ekspansi semantik:** query `"depression"` mengembalikan ketiga node sekaligus — sistem tidak tahu mana yang dimaksud.

**Dengan LLM Query Expansion:**

```python
user_query = "pasien mengalami depression setelah pemberian morfin"

# LLM membaca konteks kalimat → mengidentifikasi frasa "setelah pemberian morfin"
# → mengarah ke efek farmakologis, bukan gangguan psikiatri

expanded = {
    "primary_interpretation": "respiratory depression",
    "cypher_hint": "MATCH (d:Drug {name:'morphine'})-[:causes]->(:Effect {name:'respiratory depression'})",
    "exclude": ["major depressive disorder", "ST-segment depression"]
}
```

---

### Tipe 2 – Ambiguitas Akronim Medis

Contoh: **`"MS"`**

| Akronim | Kepanjangan | Node PrimeKG |
|---|---|---|
| MS | Multiple Sclerosis | `MONDO:0005301` (disease node) |
| MS | Mitral Stenosis | `HP:0001762` (phenotype/cardiac node) |

**Alur ekspansi:**

```text
Input: "Apa obat yang digunakan untuk MS?"

[LLM Expander]
  - Melihat konteks: kata "obat" → farmakologis → penyakit kronis
  - Menghasilkan dua kandidat:
      candidate_1: "Multiple Sclerosis" (confidence: 0.78)
      candidate_2: "Mitral Stenosis"    (confidence: 0.21)

[GraphRAG Retriever – menjalankan KEDUA query]
  candidate_1 → drug nodes: interferon-beta, natalizumab, fingolimod (sub-graf kaya)
  candidate_2 → drug nodes: diuretics, beta-blockers, warfarin

[Disambiguation Ranker]
  → Memilih candidate_1 (Multiple Sclerosis)
  → Alasan: sub-graf lebih kaya + konsisten dengan konteks kalimat
```

Contoh lain akronim ambigu:

| Akronim | Kemungkinan 1 | Kemungkinan 2 |
|---|---|---|
| PDA | Patent Ductus Arteriosus | Posterior Descending Artery |
| ALS | Amyotrophic Lateral Sclerosis | Advanced Life Support |
| MAT | Multifocal Atrial Tachycardia | Medication-Assisted Treatment |
| AML | Acute Myeloid Leukemia | Anterior Mitral Leaflet |

---

### Tipe 3 – Specificity Gap (Istilah Terlalu Umum)

Contoh: **`"sakit jantung"`**

Ini adalah kasus *underspecified query* — sangat umum dari pengguna awam atau non-klinis.

```text
Input: "sakit jantung"

[Tanpa ekspansi]
→ GraphRAG mencocokkan semua node dengan kata "heart" + "disease"
→ Hasil: 200+ node — tidak berguna

[Dengan LLM Expansion]
LLM menghasilkan candidate set:
  - "Coronary Artery Disease"  (MONDO:0005385)
  - "Heart Failure"            (MONDO:0005252)
  - "Myocardial Infarction"   (MONDO:0005068)
  - "Arrhythmia"              (MONDO:0006949)

LLM menghasilkan clarifying sub-query:
  → "Apakah gejala utamanya nyeri dada? Detak tidak teratur? Sesak napas?"

Jawaban pengguna → mempersempit ke 1 node spesifik di PrimeKG
```

---

## 3. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE (Streamlit / Gradio)              │
│            [ Input teks query ] ←→ [ Tampilan hasil subgraf ]           │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         QUERY SERVICE  (FastAPI)                        │
│  1. Normalisasi teks (lower-case, strip punctuation)                    │
│  2. Deteksi tipe ambiguitas (polisemi / akronim / specificity gap)      │
│  3. Routing ke LLM Expander                                             │
└───────────┬───────────────────────────────────────────────┬─────────────┘
            │                                               │
            ▼                                               ▼
┌───────────────────────────┐               ┌──────────────────────────────┐
│     LLM EXPANDER          │               │    CLARIFICATION MODULE      │
│  (Llama-2-7B / Mistral-7B │               │  (hanya aktif untuk Tipe 3)  │
│   / GPT-4o mini via API)  │               │  Menghasilkan follow-up      │
│                           │               │  question ke pengguna         │
│  Input : query + konteks  │               └──────────────────────────────┘
│  Output: JSON kandidat    │
│  {                        │
│    candidate_1: {...},    │
│    candidate_2: {...},    │
│    confidence: [0.78,0.21]│
│  }                        │
└───────────┬───────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     GRAPHRAG RETRIEVER  (Neo4j / LangChain)             │
│  - Menjalankan Cypher query untuk setiap kandidat                       │
│  - Mengekstrak sub-graf (node + edge) dari PrimeKG                      │
│  - Mengembalikan dua atau lebih sub-graf kandidat                       │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               DISAMBIGUATION RANKER  (Sentence-Transformer)             │
│  - Embedding query asli: E(query)                                       │
│  - Embedding setiap sub-graf: E(candidate_i)                            │
│  - Hitung cosine similarity                                             │
│  - Pilih kandidat dengan skor tertinggi                                 │
│  - Hasilkan penjelasan: "Dipilih karena..."                             │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   RESULT RENDERER  (NetworkX + Plotly)                  │
│  - Visualisasi sub-graf (node berwarna per tipe: disease, drug, gene)   │
│  - Teks penjelasan singkat (node terpilih + alasan disambiguasi)        │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    [Kembali ke UI]
```

---

## 4. Strategi Loading PrimeKG Secara Modular

`kg.csv` dari Harvard Dataverse berukuran ~1 GB dan memuat ~4 juta edge. Untuk S1, **tidak perlu load semuanya**. Strateginya:

### Langkah 1 — Download sekali, filter sekali

```python
import pandas as pd

# Relasi prioritas untuk proyek disambiguasi
PRIORITY_RELATIONS = [
    "disease_phenotype",      # gejala → penyakit (Tipe 1 & 3)
    "indication",             # penyakit → obat (Tipe 2)
    "contraindication",       # penyakit → obat (Tipe 2)
    "off-label use",          # penyakit → obat (opsional)
    "disease_protein",        # penyakit → protein (konteks biologis)
    "drug_effect",            # obat → efek samping (Tipe 1: respiratory depression)
]

# Baca kg.csv dalam chunk — tidak perlu load 1 GB sekaligus ke RAM
chunk_size = 100_000
filtered_chunks = []

for chunk in pd.read_csv("kg.csv", chunksize=chunk_size):
    filtered = chunk[chunk["relation"].isin(PRIORITY_RELATIONS)]
    filtered_chunks.append(filtered)

kg_subset = pd.concat(filtered_chunks, ignore_index=True)

print(f"Total edge asli  : ~4.000.000")
print(f"Total edge subset: {len(kg_subset):,}")

# Simpan subset — hanya perlu dilakukan SEKALI
kg_subset.to_csv("kg_subset.csv", index=False)
```

### Estimasi Ukuran Subset

| Relasi | Estimasi Jumlah Edge | Ukuran CSV |
|---|---|---|
| `disease_phenotype` | ~300.000 | ~25 MB |
| `indication` | ~18.000 | ~2 MB |
| `contraindication` | ~5.000 | ~0.5 MB |
| `disease_protein` | ~160.000 | ~14 MB |
| `drug_effect` | ~140.000 | ~12 MB |
| **Total subset** | **~623.000** | **~55 MB** |

> **Dari 1 GB turun ke ~55 MB** — jauh lebih manageable untuk Neo4j free tier.

### Langkah 2 — Import subset ke Neo4j

```python
from neo4j import GraphDatabase
import pandas as pd

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

df = pd.read_csv("kg_subset.csv")

def import_edge(tx, row):
    query = """
    MERGE (x {id: $x_id, name: $x_name, type: $x_type})
    MERGE (y {id: $y_id, name: $y_name, type: $y_type})
    MERGE (x)-[r:RELATION {type: $relation}]->(y)
    """
    tx.run(query,
           x_id=row["x_id"], x_name=row["x_name"], x_type=row["x_type"],
           y_id=row["y_id"], y_name=row["y_name"], y_type=row["y_type"],
           relation=row["relation"])

with driver.session() as session:
    for _, row in df.iterrows():
        session.write_transaction(import_edge, row)

print("Import selesai.")
```

### Langkah 3 — Verifikasi di Neo4j Browser

```cypher
-- Cek distribusi relasi yang berhasil diimport
MATCH ()-[r]->() RETURN r.type AS relasi, COUNT(*) AS jumlah
ORDER BY jumlah DESC

-- Contoh: cari penyakit dengan gejala "fatigue"
MATCH (d:Disease)-[:RELATION {type: 'disease_phenotype'}]->(p)
WHERE toLower(p.name) CONTAINS 'fatigue'
RETURN d.name, p.name
LIMIT 20
```

### Struktur File Proyek yang Disarankan

```
project/
├── data/
│   ├── kg.csv              # download sekali dari Harvard Dataverse (~1 GB)
│   └── kg_subset.csv       # hasil filter (~55 MB) — yang dipakai sehari-hari
├── scripts/
│   ├── filter_kg.py        # jalankan SEKALI untuk generate kg_subset.csv
│   └── import_neo4j.py     # import kg_subset.csv ke Neo4j
├── modules/
│   ├── expander.py         # LLM Query Expander
│   ├── retriever.py        # GraphRAG Retriever (Neo4j + LangChain)
│   └── ranker.py           # Disambiguation Ranker (sentence-transformer)
└── app.py                  # Streamlit UI
```

---

## 5. Stack Teknologi (rekomendasi untuk S1)

| Komponen | Pilihan Teknologi | Alasan |
|---|---|---|
| **LLM Expander** | Llama-2-7B-Chat (HuggingFace 🤗) *atau* GPT-4o mini API | Open-source tersedia; API sebagai fallback jika GPU terbatas |
| **Knowledge Graph** | PrimeKG subset (~55 MB) + Neo4j AuraDB (free tier) | Load modular, tidak butuh RAM besar |
| **GraphRAG Retriever** | LangChain `Neo4jGraph` + `GraphCypherQAChain` | Abstraksi mudah untuk mahasiswa S1 |
| **Query Language** | **Cypher** (bukan SPARQL) | Lebih intuitif, LLM bisa auto-generate, cocok dengan property graph PrimeKG |
| **Embedding / Ranker** | `sentence-transformers` (`all-mpnet-base-v2`) | Ringan, tidak butuh GPU besar |
| **API Layer** | FastAPI | Ringan, dokumentasi otomatis |
| **Frontend** | Streamlit | Mudah, Python-native, dapat di-deploy gratis |
| **Visualisasi Graf** | NetworkX + Plotly (atau pyvis) | Interaktif, mudah diintegrasikan ke Streamlit |

---

## 6. Roadmap Implementasi 12 Minggu

| Minggu | Kegiatan | Output |
|---|---|---|
| **1** | Setup: install Python 3.10, Neo4j AuraDB, LangChain. Unduh `kg.csv` dari Harvard Dataverse. | Lingkungan dev siap |
| **2** | Jalankan `filter_kg.py` → generate `kg_subset.csv` (~55 MB). Import ke Neo4j dengan `import_neo4j.py`. Verifikasi dengan Cypher sederhana. | Subset PrimeKG ter-load di Neo4j, query dasar berjalan |
| **3–4** | Implementasi LLM Expander: prompt template, parsing JSON, uji dengan 10 istilah ambigu | Modul `expander.py` berfungsi, output JSON valid |
| **5–6** | Bangun GraphRAG Retriever: Cypher query dari expanded term, ekstrak sub-graf | Modul `retriever.py`, sub-graf berhasil diekstrak |
| **7–8** | Disambiguation Ranker: embedding + cosine similarity, pemilihan kandidat otomatis | Modul `ranker.py`, akurasi internal >70% pada 10 kasus |
| **9–10** | Frontend & Visualisasi: Streamlit UI, tampil sub-graf interaktif, penjelasan disambiguasi | App dapat dijalankan, sub-graf tervisualisasi |
| **11** | Evaluasi formal: 30–50 query medis, hitung Precision@k, MRR, survey user | Tabel hasil evaluasi |
| **12** | Laporan & Demo: tulis laporan akhir, buat video demo | Laporan selesai, demo siap presentasi |

---

## 7. Metrik Evaluasi

| Metrik | Definisi | Target (S1) |
|---|---|---|
| **Precision@5** | Dari 5 node teratas, berapa % yang relevan dengan interpretasi yang benar | ≥ 0.70 |
| **Mean Reciprocal Rank (MRR)** | Rata-rata 1/rank node relevan pertama | ≥ 0.65 |
| **Disambiguation Accuracy** | % query di mana sistem memilih interpretasi yang benar (vs ground-truth manual) | ≥ 0.75 |
| **User Satisfaction Score** | Survey 1–5 pada 10 peserta: "Apakah hasil menjawab maksud Anda?" | ≥ 4.0 |

---

## 8. Kontribusi Ilmiah yang Bisa Diklaim

1. **Prompt engineering spesifik medis** — desain prompt yang mampu mengidentifikasi tipe ambiguitas (polisemi / akronim / specificity gap) secara otomatis.
2. **Integrasi LLM + GraphRAG** — pipeline end-to-end yang menghubungkan LLM expansion dengan Cypher query pada PrimeKG.
3. **Evaluasi disambiguasi berbasis embedding** — penggunaan sentence-transformer sebagai *reranker* pada sub-graf biomedis.
4. **Dataset benchmark** — kumpulan 30–50 query ambigu beserta ground-truth interpretasi pada PrimeKG (dapat dipublikasikan sebagai kontribusi dataset).

---

*Dokumen ini dibuat sebagai referensi diskusi Tugas Akhir S1 — 28 April 2026.*
