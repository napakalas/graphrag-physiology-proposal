# Implementasi Ekstraksi Pangkalan Pengetahuan Berbasis Graf untuk Pembangunan Konteks Relasi Penyakit dan Obat Secara Matematis

**Topik 2 – Judul 3 – Proyek Mahasiswa S1**
Referensi diskusi: 28 April 2026

---

## 1. Gambaran Umum & Motivasi

Proyek ini membangun sebuah **pipeline** yang mengekstrak relasi penyakit–obat dari PrimeKG dan merepresentasikannya secara matematis — sehingga sistem dapat melakukan **inferensi berbasis kemiripan**, bukan hanya pencarian kata kunci.

### Apa yang dikerjakan: Input → Proses → Output

| Tahap | Detail |
|---|---|
| **Input** | Sub-graf PrimeKG: node penyakit, obat, protein, fenotip + relasi antar mereka (indication, contraindication, drug_effect, disease_protein) |
| **Proses** | (1) Ekstraksi triple dari graf, (2) Pembangunan matriks adjacency, (3) Training model Knowledge Graph Embedding (KGE), (4) Ekstraksi path kontekstual |
| **Output** | Vektor embedding tiap entitas + tabel prediksi top-k obat untuk setiap penyakit |
| **Manfaat** | Sistem dapat menyarankan obat untuk penyakit yang belum punya entri eksplisit (*drug repurposing*), berdasarkan kemiripan matematis antar entitas |

### Apa maksud kata "Matematis" di sini?

> **Penting untuk penguji:** Kata "matematis" dalam judul ini bukan merujuk pada matematika tingkat lanjut (kalkulus, teori bilangan, dll). Yang dimaksud adalah **representasi numerik terstruktur** dari relasi dalam graf:
>
> - Relasi antar node diubah menjadi **matriks biner** (ada/tidak ada hubungan)
> - Setiap node (penyakit / obat) diubah menjadi **vektor bilangan riil** berdimensi rendah
> - Kemiripan antar entitas dihitung menggunakan **jarak Euclidean** atau **cosine similarity**
>
> Tujuannya: agar komputer dapat **membandingkan dan menyimpulkan** relasi yang tidak tertulis eksplisit di data.

### Pertanyaan Penelitian

> *"Bagaimana relasi antara penyakit dan obat dalam PrimeKG dapat diekstrak dan direpresentasikan secara matematis sehingga menghasilkan konteks yang berguna untuk inferensi biomedis?"*

---

## 2. Konsep Matematis yang Digunakan

### 2.1 Representasi Graf sebagai Matriks

PrimeKG sub-graf penyakit–obat dapat direpresentasikan sebagai:

```
G = (V, E, R)
  V = himpunan node (penyakit + obat)
  E = himpunan edge (indication, contraindication, drug_effect, ...)
  R = himpunan tipe relasi
```

**Adjacency Matrix** untuk satu tipe relasi `r`:

```
A_r[i][j] = 1  jika ada edge (disease_i) -[r]-> (drug_j)
           = 0  jika tidak ada edge
```

**Contoh numerik:**

```
           Morphine  Ibuprofen  Natalizumab
Pain       [  1          1          0     ]
MS         [  0          0          1     ]
Depression [  1          0          0     ]
```

### 2.2 Knowledge Graph Embedding (KGE)

KGE mengubah node dan relasi menjadi vektor kontinu di ruang berdimensi rendah (mis. d=128):

| Model | Formula Skor | Karakteristik |
|---|---|---|
| **TransE** | `score = -||h + r - t||` | Sederhana, cocok untuk S1 |
| **RotatE** | `score = -||h ∘ r - t||` | Lebih ekspresif, relasi simetris/asimetris |
| **ComplEx** | Skor berbasis bilangan kompleks | Menangani relasi asimetris dengan baik |
| **DistMult** | `score = h^T diag(r) t` | Efisien, tapi hanya relasi simetris |

> **Rekomendasi S1:** mulai dengan **TransE** (paling mudah dipahami dan diimplementasi), lalu bandingkan dengan **RotatE** untuk evaluasi.

### 2.3 Path-Based Context

Selain embedding, **konteks relasional** dapat dibangun dari jalur (path) antar node. Path menjelaskan *mengapa* suatu obat relevan untuk suatu penyakit — bukan hanya *bahwa* mereka terhubung.

#### Contoh Riil: Multiple Sclerosis (MS) dan Natalizumab

```
Path 1 (mekanisme kerja obat):
  Multiple Sclerosis
    --[disease_protein]-->  VLA-4 (integrin alpha-4, gen ITGA4)
    --[drug_target]-->      Natalizumab

Path 2 (risiko efek samping):
  Multiple Sclerosis
    --[indication]-->       Natalizumab
    --[drug_effect]-->      Progressive Multifocal Leukoencephalopathy (PML)

Path 3 (melalui fenotip):
  Multiple Sclerosis
    --[disease_phenotype]--> Spasticity
    <--[drug_effect]--       Baclofen
```

**Interpretasi Path 1:** Natalizumab bekerja untuk MS karena menarget protein VLA-4 yang terlibat dalam patologi MS. Ini adalah konteks *mekanistik*.

**Interpretasi Path 2:** Natalizumab memiliki risiko serius PML — konteks ini penting untuk evaluasi keamanan obat.

**Interpretasi Path 3:** Baclofen dapat relevan untuk MS karena keduanya terhubung melalui gejala spastisitas.

#### Representasi Matematis Path

Setiap node dan relasi direpresentasikan sebagai vektor. Path di-encode sebagai gabungan vektor:

```
Misalkan embedding_dim = 4 (disederhanakan, aslinya 128)

h_MS          = [0.8,  0.2, -0.3,  0.5]   # vektor penyakit MS
r_indication  = [0.1,  0.4,  0.2, -0.1]   # vektor relasi "indication"
h_Natalizumab = [0.9,  0.6, -0.1,  0.4]   # vektor obat
r_drug_effect = [-0.2, 0.3,  0.5,  0.1]   # vektor relasi "drug_effect"
h_PML         = [0.7,  0.9,  0.2,  0.5]   # vektor penyakit PML

# Path embedding = rata-rata semua vektor dalam path:
path_MS_Natalizumab_PML = mean(
    h_MS, r_indication, h_Natalizumab, r_drug_effect, h_PML
) = [0.46, 0.48, 0.10, 0.28]
```

Path yang **berbagi entitas serupa** akan menghasilkan vektor yang berdekatan dalam ruang berdimensi tinggi — inilah dasar matematis mengapa model dapat menyimpulkan relasi baru.

---

## 2a. Perbandingan: Tanpa vs Dengan Drug Repurposing

### Skenario: Penyakit Langka yang Belum Punya Obat Spesifik

**Tanpa pendekatan matematis (pencarian konvensional):**

```
Query: "Obat untuk Neuromyelitis Optica Spectrum Disorder (NMOSD)?"

Pencarian keyword di database:
  → Hanya mengembalikan obat yang SECARA EKSPLISIT
    tercatat sebagai indikasi NMOSD di PrimeKG
  → Jika data tidak lengkap → hasil kosong atau sangat terbatas
  → Tidak dapat menyimpulkan obat dari penyakit yang mirip
```

**Dengan pendekatan matematis (KGE + embedding):**

```
Query: "Obat untuk Neuromyelitis Optica Spectrum Disorder (NMOSD)?"

Sistem menghitung:
  embedding(NMOSD) ≈ embedding(Multiple Sclerosis)  → jarak Euclidean kecil
  embedding(NMOSD) ≈ embedding(SLE)                 → jarak Euclidean kecil

Karena NMOSD dekat dengan MS dan SLE dalam ruang embedding:
  → Obat MS: Rituximab, Natalizumab
  → Obat SLE: Azathioprine, Mycophenolate mofetil

Prediksi sistem: Rituximab dan Azathioprine kemungkinan relevan untuk NMOSD

Verifikasi literatur: BENAR — Rituximab memang digunakan off-label untuk NMOSD
                     dan tercatat sebagai salah satu terapi yang diteliti.
```

### Contoh Historis yang Terkenal: COVID-19

| Aspek | Tanpa KGE | Dengan KGE |
|---|---|---|
| **Situasi** | COVID-19 baru muncul, tidak ada obat yang terdaftar | Model mencari penyakit yang "mirip" COVID-19 dalam ruang embedding |
| **Proses** | Peneliti harus membaca ratusan paper secara manual | Sistem menemukan: COVID-19 ≈ SARS ≈ MERS dalam embedding |
| **Hasil** | Butuh waktu lama untuk menemukan kandidat obat | Prediksi cepat: Remdesivir (obat SARS) dan Dexamethasone (anti-inflamasi) |
| **Validasi** | — | Remdesivir dan Dexamethasone terbukti efektif untuk COVID-19 |

> **Pesan kunci untuk mahasiswa:** Proyek ini bukan hanya tentang membangun model — ini tentang membangun **infrastruktur inferensi** yang dapat digunakan untuk menjawab pertanyaan biomedis yang tidak terjawab secara eksplisit di data.

---

## 3. Modul yang Digunakan

| Modul | Fungsi di Proyek Ini |
|---|---|
| `filter_kg.py` | Filter `kg.csv` → `kg_subset.csv` (relasi: `indication`, `contraindication`, `disease_phenotype`, `drug_effect`, `disease_protein`) |
| `import_neo4j.py` | Import subset ke Neo4j untuk eksplorasi graf dan ekstraksi sub-graf |

---

## 4. Arsitektur Sistem

```
┌──────────────────────────────────────────────────────────────────┐
│                  DATA PREPARATION LAYER                          │
│   filter_kg.py ──> kg_subset.csv ──> import_neo4j.py ──> Neo4j  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                GRAPH EXTRACTION MODULE  (extractor.py)           │
│  - Ekstrak triple (head, relation, tail) dari Neo4j              │
│  - Bangun adjacency matrix per tipe relasi                       │
│  - Hitung statistik dasar: degree, density, connected components │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│              MATHEMATICAL CONTEXT BUILDER  (embedder.py)         │
│  - Train KGE model (TransE / RotatE) via PyKEEN                  │
│  - Hasilkan vektor embedding: E_disease, E_drug, E_relation      │
│  - Simpan embedding ke file (.npy / .pkl)                        │
└───────────────────┬──────────────────────────┬───────────────────┘
                    │                          │
                    ▼                          ▼
┌───────────────────────────┐    ┌─────────────────────────────────┐
│   EVALUATION MODULE       │    │   CONTEXT QUERY MODULE          │
│   (evaluator.py)          │    │   (context_query.py)            │
│   - Link prediction       │    │   - Cari N obat terdekat        │
│   - Hits@1, Hits@10, MRR  │    │     untuk suatu penyakit        │
│   - AUC-ROC               │    │   - Path extraction             │
└───────────────────────────┘    └─────────────────────────────────┘
                    │                          │
                    └──────────────┬───────────┘
                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                   VISUALIZATION & REPORT  (Streamlit / Jupyter)  │
│  - Plot embedding (t-SNE / UMAP) per node type                  │
│  - Heatmap adjacency matrix                                      │
│  - Tabel top-k prediksi drug untuk setiap penyakit              │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Contoh Nyata: Ekstraksi dan Representasi Matematis

### Langkah 1: Ekstraksi Triple dari Neo4j

```python
from neo4j import GraphDatabase
import pandas as pd

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

def extract_triples(relation_type: str) -> pd.DataFrame:
    with driver.session() as session:
        result = session.run("""
            MATCH (h)-[r:RELATION {type: $rel}]->(t)
            RETURN h.id AS head_id, h.name AS head_name,
                   r.type AS relation,
                   t.id AS tail_id, t.name AS tail_name
        """, rel=relation_type)
        return pd.DataFrame([dict(r) for r in result])

# Ekstrak relasi indication (penyakit -> obat)
df_ind = extract_triples("indication")
print(df_ind.head())
#    head_id          head_name  relation   tail_id    tail_name
#    MONDO:0005301  multiple sclerosis  indication  DB00068  Interferon beta-1b
```

### Langkah 2: Bangun Adjacency Matrix

```python
import numpy as np
from scipy.sparse import lil_matrix

def build_adjacency_matrix(df: pd.DataFrame):
    diseases = df["head_id"].unique().tolist()
    drugs    = df["tail_id"].unique().tolist()

    disease_idx = {d: i for i, d in enumerate(diseases)}
    drug_idx    = {d: i for i, d in enumerate(drugs)}

    A = lil_matrix((len(diseases), len(drugs)), dtype=np.int8)

    for _, row in df.iterrows():
        i = disease_idx[row["head_id"]]
        j = drug_idx[row["tail_id"]]
        A[i, j] = 1

    return A.tocsr(), diseases, drugs

A_indication, diseases, drugs = build_adjacency_matrix(df_ind)
print(f"Matriks: {A_indication.shape}  |  Non-zero: {A_indication.nnz}")
# Matriks: (8.000 x 2.200)  |  Non-zero: 18.000
```

### Langkah 3: Train KGE dengan PyKEEN (TransE)

```python
from pykeen.pipeline import pipeline
from pykeen.triples import TriplesFactory

# Gabungkan semua relasi
all_triples = pd.concat([
    extract_triples("indication"),
    extract_triples("contraindication"),
    extract_triples("drug_effect"),
    extract_triples("disease_protein"),
])

# Buat TriplesFactory
tf = TriplesFactory.from_labeled_triples(
    all_triples[["head_name", "relation", "tail_name"]].values
)
training, testing = tf.split([0.8, 0.2])

# Train TransE
result = pipeline(
    training          = training,
    testing           = testing,
    model             = "TransE",
    model_kwargs      = {"embedding_dim": 128},
    training_kwargs   = {"num_epochs": 100, "batch_size": 512},
    optimizer_kwargs  = {"lr": 0.01},
    evaluation_kwargs = {"batch_size": 128},
)

result.save_to_directory("output/transe_model")
print(f"Hits@10 : {result.metric_results.get_metric('hits@10'):.4f}")
print(f"MRR     : {result.metric_results.get_metric('mean_reciprocal_rank'):.4f}")
```

### Langkah 4: Gunakan Embedding untuk Drug Repurposing

```python
import torch

entity_repr  = result.model.entity_representations[0]
relation_repr = result.model.relation_representations[0]

entity_to_id = training.entity_to_id

def find_top_drugs(disease_name: str, k: int = 10):
    """Cari k obat yang paling 'dekat' dengan penyakit dalam ruang embedding."""
    if disease_name not in entity_to_id:
        return []

    disease_id  = entity_to_id[disease_name]
    disease_vec = entity_repr(torch.tensor([disease_id]))

    # Hitung skor untuk semua entitas
    scores = {}
    for entity_name, entity_id in entity_to_id.items():
        entity_vec = entity_repr(torch.tensor([entity_id]))
        score = -torch.norm(disease_vec - entity_vec).item()
        scores[entity_name] = score

    top_k = sorted(scores.items(), key=lambda x: -x[1])[:k]
    return top_k

results = find_top_drugs("multiple sclerosis", k=5)
for name, score in results:
    print(f"  {name:<30}  score: {score:.4f}")
```

---

## 6. Stack Teknologi (rekomendasi untuk S1)

| Komponen | Teknologi | Alasan |
|---|---|---|
| **Data pipeline** | `filter_kg.py` + `import_neo4j.py` (reuse) | Sudah tersedia, tidak perlu dibuat ulang |
| **Graph extraction** | Neo4j + `neo4j` Python driver | Query Cypher untuk ekstrak triple |
| **Matrix building** | `NumPy` + `SciPy` (sparse matrix) | Efisien untuk matriks besar dan sparse |
| **KGE training** | **PyKEEN** (library khusus KGE) | Menyediakan TransE, RotatE, ComplEx siap pakai |
| **Visualisasi embedding** | `UMAP` + `Matplotlib` / `Plotly` | Proyeksi 2D embedding untuk analisis cluster |
| **Visualisasi graf** | `NetworkX` + `Pyvis` | Tampilkan sub-graf interaktif |
| **Notebook / laporan** | Jupyter Notebook | Mudah untuk eksplorasi dan presentasi bertahap |
| **Dashboard opsional** | Streamlit | Jika ingin demo interaktif |

---

## 7. Roadmap Implementasi 12 Minggu

| Minggu | Kegiatan | Output |
|---|---|---|
| **1** | Setup: install Python 3.10, PyKEEN, Neo4j. Reuse `filter_kg.py` + `import_neo4j.py` untuk load subset PrimeKG. | Neo4j berisi sub-graf penyakit–obat |
| **2** | Implementasi `extractor.py`: ekstrak triple dari Neo4j, eksplorasi statistik dasar (degree distribution, density). | DataFrame triple, statistik graf |
| **3** | Bangun adjacency matrix (NumPy/SciPy) untuk relasi `indication` dan `contraindication`. Visualisasi heatmap. | Matriks sparse, heatmap |
| **4** | Train TransE dengan PyKEEN (epoch 50, embedding dim 64). Simpan model. | Model TransE tersimpan |
| **5** | Evaluasi TransE: Hits@1, Hits@10, MRR. Bandingkan dengan DistMult. | Tabel perbandingan model |
| **6** | Implementasi path extraction: cari jalur 2–3 hop antara penyakit dan obat. | Tabel path beserta interpretasi |
| **7** | Train RotatE, bandingkan dengan TransE. | Tabel evaluasi komparatif |
| **8** | Implementasi `context_query.py`: cari top-k obat terdekat untuk suatu penyakit. | Fungsi drug repurposing berjalan |
| **9** | Visualisasi embedding: t-SNE / UMAP, warnai per node type. | Plot 2D embedding |
| **10** | Bangun Streamlit dashboard: input penyakit → tampilkan top-k obat + path relasi. | App Streamlit berjalan |
| **11** | Evaluasi formal: 20–30 penyakit, hitung AUC-ROC prediksi drug. | Tabel evaluasi |
| **12** | Laporan & Demo. | Laporan + demo siap presentasi |

---

## 8. Metrik Evaluasi

| Metrik | Definisi | Target (S1) |
|---|---|---|
| **Hits@1** | % kasus di mana drug yang benar ada di posisi pertama prediksi | ≥ 0.20 |
| **Hits@10** | % kasus di mana drug yang benar ada di top-10 prediksi | ≥ 0.50 |
| **Mean Reciprocal Rank (MRR)** | Rata-rata 1/rank drug yang benar | ≥ 0.25 |
| **AUC-ROC (link prediction)** | Area Under Curve untuk prediksi ada/tidaknya edge | ≥ 0.75 |
| **Embedding Cluster Quality** | Silhouette score pada visualisasi UMAP (apakah Disease vs Drug terpisah?) | ≥ 0.40 |

---

## 9. Kontribusi Ilmiah yang Bisa Diklaim

1. **Representasi matematis sub-graf PrimeKG** — matriks relasi penyakit–obat yang dapat direproduksi.
2. **Perbandingan model KGE** — evaluasi TransE vs RotatE pada sub-graph PrimeKG terbatas.
3. **Pipeline ekstraksi modular** — dapat digunakan ulang oleh proyek lain yang menggunakan PrimeKG.
4. **Dataset prediksi drug** — daftar 20–30 penyakit dengan prediksi top-k obat beserta skor embedding (dapat dipublikasikan).

---

---

*Dokumen ini dibuat sebagai referensi diskusi Tugas Akhir S1 — 28 April 2026.*
