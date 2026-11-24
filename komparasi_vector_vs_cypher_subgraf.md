# Perbandingan Rasio Ketepatan Vector Search dan Cypher Traversal dalam Mengakuisisi Subgraf Relasi Penyakit dan Anatomi Saraf

**Topik Mahasiswa 2 – Database Graf & Retrieval Layer**
Referensi kurikulum: Tugas Akhir / Skripsi S1 Teknik Informatika

---

## 1. Gambaran Umum & Motivasi

Pada arsitektur sistem **GraphRAG**, tahapan pengambilan konteks (*retrieval*) menentukan kualitas fakta yang disajikan kepada *Large Language Model* (LLM). Terdapat dua paradigma mendasar dalam mengakuisisi subgraf pengetahuan dari pangkalan data:

1. **Vector-Only Search (Unstructured Embedding Similarity)**:
   Setiap relasi atau node diubah menjadi vektor numerik padat (*embeddings*). Sistem mencari entitas yang paling mirip dengan kueri pengguna menggunakan metrik jarak (misalnya *Cosine Similarity* atau $L_2$ distance) via indeks HNSW / FAISS.
   - *Kelebihan*: Sangat toleran terhadap sinonim leksikal dan kueri bahasa alami non-formal.
   - *Kelemahan*: **Kebutaan Relasional Multi-Hop (*Multi-Hop Relational Blindness*)**. Vektor search sering mengumpulkan node-node yang semantik katanya mirip namun sebenarnya terputus (*disconnected fragments*), sehingga menghasilkan hubungan palsu (*hallucinated path*).

2. **Cypher Graph Traversal (Structured Topology Matching)**:
   Sistem mengeksekusi kueri terstruktur berbasis pola deklaratif Cypher pada pangkalan data graf (Neo4j) untuk menelusuri jalur yang benar-benar ada di graf, misalnya: `(Disease)-[disease_protein]-(Protein)-[anatomy_protein_present]-(Anatomy)<-[innervates]-(Nerve)`.
   - *Kelebihan*: **Keterhubungan terjamin**. Setiap edge yang diambil pasti ada dan terhubung di Knowledge Graph (meskipun belum tentu relevan dengan pertanyaan, sehingga presisi terhadap *ground truth* tetap perlu diukur).
   - *Kelemahan*: Sangat rentan terhadap kegagalan sintaksis jika entitas awal kueri (*seed node*) tidak ditemukan secara presisi (*zero recall problem*).

Proyek ini bertujuan menguji dan membandingkan secara kuantitatif **Rasio Ketepatan (*Precision Ratio*)**, **Keutuhan Jalur (*Path Preservation Ratio*)**, serta **Efisiensi Waktu Pengambilan (*Retrieval Latency*)** antara pendekatan *Pure Vector Search*, *Pure Cypher Traversal*, dan *Hybrid Traversal* pada studi kasus penyakit saraf otonom, menggunakan graf gabungan PrimeKG + FMA.

### Tabel Input → Proses → Output

| Parameter | Keterangan Rinci |
|---|---|
| **Input** | Kueri klinis fisiologi/penyakit saraf (contoh: sindrom Horner, penyakit Hirschsprung) & graf gabungan PrimeKG + FMA di Neo4j. |
| **Proses** | 1. Eksekusi Vector Search (HNSW Top-K node/edges).<br>2. Eksekusi Cypher Pattern Traversal (1-hop s.d. 3-hop traversal).<br>3. Eksekusi Hybrid (Vector Entry Point + Cypher Neighborhood Expansion).<br>4. Evaluasi topologi subgraf terhadap *ground truth*. |
| **Output** | Subgraf terambil ($V_{\text{ret}}, E_{\text{ret}}$), metrik ketepatan edge, rasio konektivitas jalur, dan waktu eksekusi ($ms$). |
| **Kontribusi Ilmiah** | Mengukur batas hop kritis (*critical hop boundary*) ketika vector search mulai kehilangan keterhubungan jalur, serta menguji apakah arsitektur hybrid dapat menutup kelemahan kedua metode. |

---

## 2. Posisi dalam Arsitektur GraphRAG

Mahasiswa 2 berada di lapisan **Pangkalan Data Graf dan Akuisisi Konteks Subgraf**. Lapisan ini menjembatani entitas yang diparsing oleh Mahasiswa 1 dengan modul linearisasi konteks milik Mahasiswa 3.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ARSITEKTUR RETRIEVAL SUBGRAF                    │
│                                                                        │
│  [Entitas Masukan dari Mhs 1: "Horner Syndrome" (MONDO:0001294)]       │
│                               │                                        │
│                               ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  MAHASISWA 2: RETRIEVAL & TRAVERSAL COMPARISON LAYER         │◄─────┘
│  │                                                              │
│  │  ┌───────────────────────┐       ┌────────────────────────┐  │
│  │  │ JALUR A: Vector Search│       │ JALUR B: Cypher Engine │  │
│  │  │ (Dense Top-K FAISS)   │       │ (Neo4j Multi-Hop Path) │  │
│  │  └───────────┬───────────┘       └───────────┬────────────┘  │
│  │              │                               │               │
│  │              ▼                               ▼               │
│  │     [Koleksi Node Acak]             [Jalur Graf Utuh]        │
│  │              │                               │               │
│  │              └───────────────┬───────────────┘               │
│  │                              ▼                               │
│  │               [Kalkulasi Rasio Ketepatan Topologi]           │
│  └──────────────────────────────┬───────────────────────────────┘      │
│                                 │ Subgraf Terpilih & Terverifikasi     │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Mahasiswa 3: Linearisasi Subgraf untuk Konteks LLM          │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Landasan Teori & Formulasi Matematis

### 3.1 Representasi Pengetahuan Graf dan Subgraf Acuan

Pangkalan data direpresentasikan sebagai graf berarah terlabel (*labeled directed multi-graph*):

$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{R})$$

Untuk kueri $q$ yang menanyakan mekanisme kausal penyakit terhadap organ target, terdapat subgraf acuan kebenaran (*ground truth subgraph*):

$$\mathcal{G}^{*}_{q} = (\mathcal{V}^{*}_{q}, \mathcal{E}^{*}_{q}) \subseteq \mathcal{G}$$

Di mana $\mathcal{E}^{*}_{q}$ memuat jalur inferensi medis yang sah:

$$\mathcal{P}^{*} = (v_{\text{disease}} \xrightarrow{r_1} v_{\text{nerve}} \xrightarrow{r_2} v_{\text{ganglion}} \xrightarrow{r_3} v_{\text{effector}})$$

### 3.2 Formalisasi Pengambilan Berbasis Vektor (Vector Retrieval)

Dalam pencarian vektor murni, setiap edge $e = (u, r, v)$ dienkodekan menjadi vektor representasi $\mathbf{z}_e \in \mathbb{R}^d$. Diberikan vektor kueri $\mathbf{z}_q$, sistem mengambil top-$K$ edge dengan skor kemiripan tertinggi:

$$\mathcal{E}_{\text{vec}}(K) = \text{top-}K_{e \in \mathcal{E}} \left( \frac{\mathbf{z}_q \cdot \mathbf{z}_e}{\|\mathbf{z}_q\| \|\mathbf{z}_e\|} \right)$$

Himpunan node terinduksi adalah $\mathcal{V}_{\text{vec}} = \{u, v \mid (u, r, v) \in \mathcal{E}_{\text{vec}}\}$.

### 3.3 Formalisasi Pengambilan Berbasis Cypher Traversal

Dalam penelusuran graf deterministik, kueri Cypher menelusuri lingkungan ketetanggaan $k$-hop dari entitas awal $v_0$:

$$\mathcal{E}_{\text{cyp}}(k) = \{(u, r, v) \in \mathcal{E} \mid \text{dist}_{\mathcal{G}}(v_0, u) < k \land (u, r, v) \text{ memenuhi batasan pola } \mathcal{R}\}$$

### 3.4 Metrik Evaluasi Komparasi Topologi

1. **Rasio Presisi Edge (Edge Precision Ratio)**:
   Mengukur proporsi edge yang diambil yang benar-benar relevan dengan fakta medis ground truth:

   $$\text{Precision}_{\text{edge}} = \frac{|\mathcal{E}_{\text{ret}} \cap \mathcal{E}^{*}_{q}|}{|\mathcal{E}_{\text{ret}}|}$$

2. **Rasio Kelengkapan Edge (Edge Recall Ratio)**:
   Mengukur seberapa lengkap fakta ground truth yang berhasil terambil:

   $$\text{Recall}_{\text{edge}} = \frac{|\mathcal{E}_{\text{ret}} \cap \mathcal{E}^*_q|}{|\mathcal{E}^{*}_{q}|}$$

3. **Indeks Keutuhan Jalur (Path Preservation Index / PPI)**:
   Mengukur apakah relasi multi-hop yang diambil membentuk rantai penalaran utuh atau terfragmentasi:

   $$\text{PPI} = \frac{|\{p \in \mathcal{P}(\mathcal{G}_{\text{ret}}) \mid p \subseteq \mathcal{G}^{*}_{q}\}|}{|\mathcal{P}(\mathcal{G}^{*}_{q})|}$$

   Jika $\text{PPI} = 0$, artinya subgraf terambil tidak memiliki jalur penghubung antara penyakit dan organ target, meskipun banyak node individual terambil.

4. **Kepadatan Informasi (Graph Density of Relevance)**:

   $$\rho_{\text{rel}} = \frac{|\mathcal{E}_{\text{ret}} \cap \mathcal{E}^{*}_{q}|}{|\mathcal{V}_{\text{ret}}|}$$

---

## 4. Implementasi Kode Python & Cypher

Berikut adalah modul perbandingan yang mengeksekusi kedua strategi pengambilan data pada Neo4j dan FAISS/Embedding store. Kueri Cypher mengikuti skema hasil `import_neo4j.py` (satu tipe relasi `:RELATION` dengan properti `type`).

```python
import time
from typing import Dict, List, Set, Tuple

from neo4j import GraphDatabase

Edge = Tuple[str, str, str]  # (source, relation, target)

# Relasi yang boleh dilalui traversal: nama relasi asli PrimeKG + relasi persarafan FMA
# (diimpor sebagai :RELATION {type: 'innervates'}, arah saraf -> struktur target).
DEFAULT_ALLOWED_RELATIONS = [
    "disease_phenotype_positive",
    "disease_protein",
    "anatomy_protein_present",
    "innervates",
]


class RetrievalComparator:
    """Membandingkan retrieval subgraf berbasis traversal Cypher dan vector search."""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_pass: str) -> None:
        print("[Comparator] Connecting to Neo4j instance...")
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))

    def close(self) -> None:
        self.driver.close()

    def cypher_traversal_retrieval(
        self,
        seed_mondo_id: str,
        max_depth: int = 2,
        allowed_relations: List[str] = DEFAULT_ALLOWED_RELATIONS,
    ) -> Tuple[Set[Edge], float]:
        """Mengambil subgraf terhubung hingga max_depth hop dari node penyakit seed.

        Skema hasil import_neo4j.py memakai satu tipe relasi :RELATION dengan
        properti `type` berisi nama relasi PrimeKG, sehingga filter relasi
        dilakukan pada properti tersebut, bukan pada tipe relasi Neo4j.
        """
        # Panjang path variabel tidak bisa dijadikan parameter, sehingga disisipkan
        # sebagai integer (int() mencegah injeksi string ke dalam kueri).
        cypher_query = f"""
        MATCH path = (d:Disease {{id: $seed_id}})-[rels:RELATION*1..{int(max_depth)}]-(target)
        WHERE all(rel IN rels WHERE rel.type IN $allowed)
        UNWIND relationships(path) AS rel
        RETURN DISTINCT startNode(rel).name AS source, rel.type AS predicate, endNode(rel).name AS target
        """

        t_start = time.perf_counter()
        retrieved_edges: Set[Edge] = set()

        with self.driver.session() as session:
            for record in session.run(cypher_query, seed_id=seed_mondo_id, allowed=allowed_relations):
                retrieved_edges.add((record["source"], record["predicate"], record["target"]))

        latency_ms = (time.perf_counter() - t_start) * 1000.0
        return retrieved_edges, latency_ms

    @staticmethod
    def mock_vector_retrieval(query_text: str, top_k: int = 15) -> Set[Edge]:
        """Simulasi vector search (Top-K edge berdasarkan kemiripan kosinus).

        Implementasi riil: embed query_text, lalu ambil top_k edge terdekat dari
        indeks vektor (FAISS / Milvus / Qdrant) yang berisi verbalisasi tiap edge.
        """
        simulated_vector_edges = [
            ("Hirschsprung disease", "disease_protein", "RET"),
            ("colon", "anatomy_protein_present", "RET"),
            ("Hirschsprung disease", "disease_phenotype_positive", "Constipation"),  # relevan topik, bukan ground truth
            ("Chagas disease", "disease_phenotype_positive", "Megacolon"),          # mirip semantik, terputus
            ("Vagus nerve", "innervates", "Stomach"),                               # mirip semantik, terputus
        ]
        return set(simulated_vector_edges[:top_k])

    @staticmethod
    def compute_metrics(retrieved_edges: Set[Edge], ground_truth_edges: Set[Edge]) -> Dict[str, float]:
        true_positives = retrieved_edges & ground_truth_edges
        precision = len(true_positives) / len(retrieved_edges) if retrieved_edges else 0.0
        recall = len(true_positives) / len(ground_truth_edges) if ground_truth_edges else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "total_retrieved": len(retrieved_edges),
            "true_positives": len(true_positives),
        }


if __name__ == "__main__":
    # Ground truth 3-hop (pola Bagian 5.1) dengan nama relasi asli PrimeKG + FMA.
    # Ilustratif: setiap edge harus diverifikasi keberadaannya di graf sebelum dipakai.
    ground_truth = {
        ("Hirschsprung disease", "disease_protein", "RET"),
        ("Hirschsprung disease", "disease_protein", "EDNRB"),
        ("colon", "anatomy_protein_present", "RET"),
        ("Pelvic splanchnic nerve", "innervates", "colon"),
    }

    print("=== PENGUJIAN METRIK RETRIEVAL SUBGRAF ===")

    # Jalur vector (simulasi, tanpa koneksi database)
    vec_edges = RetrievalComparator.mock_vector_retrieval("Hirschsprung disease colon innervation", top_k=5)
    vec_metrics = RetrievalComparator.compute_metrics(vec_edges, ground_truth)
    print("\n[Vector Search]")
    print(f"  Precision: {vec_metrics['precision']:.3f} | Recall: {vec_metrics['recall']:.3f} | F1: {vec_metrics['f1']:.3f}")

    # Jalur Cypher (simulasi hasil traversal dengan max_depth=2, sehingga hop ke-3
    # dari FMA belum terambil). Dengan Neo4j aktif:
    #   comparator = RetrievalComparator("bolt://localhost:7687", "neo4j", "<password>")
    #   cyp_edges, cyp_latency = comparator.cypher_traversal_retrieval("<MONDO id>")
    #   comparator.close()
    simulated_cypher_edges = {
        ("Hirschsprung disease", "disease_protein", "RET"),
        ("Hirschsprung disease", "disease_protein", "EDNRB"),
        ("colon", "anatomy_protein_present", "RET"),
    }
    cyp_metrics = RetrievalComparator.compute_metrics(simulated_cypher_edges, ground_truth)
    print("\n[Cypher Traversal]")
    print(f"  Precision: {cyp_metrics['precision']:.3f} | Recall: {cyp_metrics['recall']:.3f} | F1: {cyp_metrics['f1']:.3f}")
```

---

## 5. Desain Eksperimen & Analisis Hop Kritis

### 5.1 Skenario Pengujian Kedalaman Hop
Pengujian dilakukan pada 3 tingkat kedalaman hop. Setiap skenario memakai **pola relasi yang benar-benar ada** di graf gabungan PrimeKG + FMA. Ini penting karena PrimeKG tidak memiliki relasi langsung penyakit–anatomi maupun relasi persarafan; jalur penyakit → anatomi hanya bisa lewat protein, dan persarafan hanya dari FMA.

| Skenario | Pola Jalur | Contoh |
|---|---|---|
| **1-Hop** | `(Disease)-[disease_phenotype_positive]-(Phenotype)` | Horner syndrome – Ptosis |
| **2-Hop** | `(Disease)-[disease_protein]-(Protein)-[anatomy_protein_present]-(Anatomy)` | Hirschsprung disease – RET – (struktur anatomi tempat RET terekspresi) |
| **3-Hop** | Pola 2-hop + `(Anatomy)<-[innervates]-(Nerve)` dari FMA | Hirschsprung disease – RET – colon – (saraf yang mempersarafi colon menurut FMA) |

Contoh di atas harus diverifikasi keberadaannya di graf sebelum dijadikan kasus uji. Kasus uji yang jalurnya terputus di graf tidak dipakai, karena akan membatasi recall Cypher karena data, bukan karena metodenya. Nama relasi `innervates` mengikuti relasi kanonik untuk edge persarafan FMA yang dipakai bersama dengan Mahasiswa 3.

### 5.2 Desain Eksperimen dan Hipotesis

> Angka hasil **tidak** dicantumkan sebelum eksperimen dijalankan. Yang dirumuskan di proposal adalah desain, protokol, dan hipotesis.

**Desain:** 3 metode (Vector Search, Cypher Traversal, Hybrid) × 3 skenario hop (Bagian 5.1), masing-masing pada kasus uji yang sama. Metrik: Edge Precision, Edge Recall, PPI, $\rho_{\text{rel}}$, dan latensi (Bagian 3.4).

**Protokol agar perbandingan adil:**
- Indeks vektor dibangun dari verbalisasi edge graf yang **sama** dengan yang ditelusuri Cypher.
- Vector Search dievaluasi pada beberapa nilai $k$ (misalnya $k = |\mathcal{E}^{*}_{q}|$, $2|\mathcal{E}^{*}_{q}|$, dan 20), karena precision dan recall sangat bergantung pada $k$.
- Latensi diukur setelah *warm-up*, sebagai median dari minimal 10 pengulangan, pada perangkat keras yang sama.
- Kasus ketika *seed node* gagal ditemukan dicatat terpisah, karena di sinilah kelemahan Cypher dan keunggulan Hybrid diharapkan muncul.
- Perbedaan antar metode per skenario hop diuji dengan uji Wilcoxon *signed-rank* berpasangan per kasus uji. **Hop kritis** didefinisikan di awal sebagai hop pertama ketika PPI Vector Search berbeda signifikan dan lebih rendah daripada Cypher.

**Hipotesis:**
- **H1:** Selisih PPI antara Cypher dan Vector Search makin besar seiring bertambahnya hop.
- **H2:** Pada 1-hop, recall Vector Search sebanding dengan Cypher.
- **H3:** Hybrid mempertahankan PPI mendekati Cypher dan memiliki recall lebih tinggi pada kasus yang *seed node*-nya tidak ditemukan persis.
- **H4:** Latensi Cypher naik lebih cepat daripada Vector Search seiring bertambahnya hop.

---

## 6. Struktur Direktori Proyek

```
mhs2_vector_vs_cypher/
├── data/
│   ├── ground_truth_subgraphs.json   # 50 kasus uji subgraf fisiologis saraf
│   └── primekg_ans_subset.dump       # backup database Neo4j saraf otonom
├── scripts/
│   ├── build_vector_index.py         # membangun indeks HNSW untuk edge PrimeKG
│   ├── run_cypher_traversals.py      # kueri traversal 1-hop s.d. 3-hop
│   ├── run_vector_search.py          # pencarian kemiripan kosinus
│   └── evaluate_subgraph_metrics.py  # kalkulator Precision, Recall, PPI
├── results/
│   ├── precision_decay_curve.png     # grafik penurunan presisi terhadap hop
│   └── latency_tradeoff_table.csv    # komparasi waktu eksekusi
└── requirements.txt
```

### `requirements.txt`
```
neo4j>=5.10.0
faiss-cpu>=1.7.4
sentence-transformers>=2.2.2
networkx>=3.0
pandas>=2.0.0
matplotlib>=3.7.0
scikit-learn>=1.3.0
```

---

## 7. Sistematika Penulisan Proposal Skripsi (Bab 1 – Bab 3)

Dokumen proposal skripsi berfokus pada pematangan masalah, landasan teori, dan metode yang dapat dipertanggungjawabkan:

### Bab 1: Pendahuluan
- **Latar Belakang**: Fenomena fragmentasi semantik dan *multi-hop relational blindness* pada *Vector Search* dalam GraphRAG medis, dibandingkan kekakuan sintaksis *Cypher Traversal* deterministik.
- **Rumusan Masalah**:
  1. Bagaimana perbandingan rasio presisi edge dan keutuhan jalur (*Path Preservation Index*) antara *Vector Search* dan *Cypher Traversal* pada variasi kedalaman penelusuran (1-hop, 2-hop, 3-hop)?
  2. Pada ambang batas hop ke berapa pencarian vektor mengalami degradasi topologi kritis dalam mengakuisisi subgraf relasi penyakit dan anatomi saraf?
  3. Bagaimana arsitektur *Hybrid Retrieval* dapat memitigasi kelemahan kedua metode tersebut?
- **Batasan Masalah**:
  - Pangkalan data graf menggunakan graf gabungan PrimeKG (relasi penyakit–fenotipe, penyakit–protein, anatomi–protein) dan FMA (relasi persarafan), ditautkan melalui rujukan silang UBERON–FMA dan di-host pada Neo4j.
  - Vektor embedding edge diindeks menggunakan FAISS (IndexFlatIP/HNSW).
- **Tujuan Penelitian**: Menyediakan analisis empiris kuantitatif rasio ketepatan, integritas jalur kausal, dan latensi komputasi antara kedua paradigma pengambilan data.

### Bab 2: Tinjauan Pustaka
- Teori *Graph Database* & Bahasa Kueri Deklaratif Cypher.
- Konsep *Dense Vector Search*, *Approximate Nearest Neighbor (ANN)*, dan indeks HNSW.
- Paradigma *Graph Retrieval-Augmented Generation (GraphRAG)* dan tantangan penalaran multi-tahap.
- Penelitian Terkait: Evaluasi komparatif metode retrieval berbasis graf vs vektor pada domain biomedis.

### Bab 3: Metodologi Penelitian
- Tahapan penelitian: (1) Setup Instance Neo4j & PrimeKG $\to$ (2) Pembuatan Indeks Vektor FAISS $\to$ (3) Kurasi 50 Kasus Uji Subgraf *Ground Truth* $\to$ (4) Desain Skenario Hop (1, 2, 3-hop) $\to$ (5) Kalkulasi Metrik Evaluasi Topologi.
- Formulasi matematis metrik: *Edge Precision*, *Edge Recall*, *Path Preservation Index (PPI)*, dan *Latency*.
- Kriteria keberhasilan proposal (*Success Criteria*).

---

## 8. Panduan Menghadapi Sidang Proposal (Sempro FAQ)

Berikut adalah antisipasi pertanyaan kritis yang lazim dilontarkan dosen penguji saat **Sidang Seminar Proposal**:

> **Tanya Dosen Penguji:** *"Mengapa Anda membandingkan Vector Search dan Cypher Traversal? Bukankah keduanya dirancang untuk keperluan yang berbeda?"*
> **Jawab:** Dalam arsitektur GraphRAG modern, terjadi perdebatan arsitektural: apakah kita cukup menggunakan *Vector Search* sederhana (menyimpan triple graf sebagai teks biasa) ataukah investasi infrastruktur pangkalan data graf (Neo4j Cypher) mutlak diperlukan. Penelitian ini hadir untuk menjawab perdebatan tersebut secara saintifik dan empiris pada domain spesifik fisiologi saraf, dengan mengukur secara kuantitatif pada kedalaman hop berapa vector search mulai kehilangan keterhubungan jalur.

> **Tanya Dosen Penguji:** *"Bagaimana Anda menentukan ground truth subgraf secara objektif agar komparasi ini valid dan tidak bias terhadap Cypher?"*
> **Jawab:** *Ground truth* disusun dari jalur yang benar-benar ada di graf gabungan PrimeKG + FMA, dengan nama relasi asli (misalnya `disease_phenotype_positive`, `disease_protein`, `anatomy_protein_present`, dan relasi persarafan FMA), lalu diperiksa kesesuaiannya dengan literatur medis standar. Kedua metode mengakses graf yang sama: indeks vektor dibangun dari verbalisasi edge graf tersebut, dan kueri bahasa alaminya sama untuk kedua sistem. Kasus uji yang jalurnya terputus di graf dikeluarkan agar tidak ada metode yang dirugikan oleh kekurangan data.

> **Tanya Dosen Penguji:** *"Apa manfaat praktis hasil penelitian ini bagi pengembangan sistem AI kesehatan?"*
> **Jawab:** Manfaat utamanya adalah panduan arsitektur (*architectural guideline*). Pengembang sistem AI medis akan mengetahui kapan harus mengalokasikan memori untuk graf traversal dan kapan cukup menggunakan pencarian vektor murah, serta menjadi dasar implementasi modul *Hybrid Retrieval Router* yang efisien token dan bebas dari halusinasi relasional.
