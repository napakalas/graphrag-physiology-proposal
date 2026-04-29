# Pengembangan *Ground-Truth Dataset* Penyakit Fisiologis dan Evaluasi Akurasi Penalaran Sistem GraphRAG Berbasis Metrik RAGAS

**Proyek Mahasiswa 3 – QA Layer (Quality Assurance)**
Referensi diskusi: 28 April 2026

---

## 1. Gambaran Umum & Motivasi

Proyek ini membangun dua kontribusi utama yang saling melengkapi:

1. **Ground-Truth Dataset** — Kumpulan pasangan **(pertanyaan medis, jawaban referensi, konteks sumber)** yang dikurasi dari PrimeKG dan referensi akademis medis. Dataset ini berdiri sebagai standar pengujian independen.
2. **Evaluation Harness berbasis RAGAS** — Pipeline otomatis yang mengukur seberapa baik sistem GraphRAG menjawab pertanyaan medis, dibandingkan terhadap dataset di atas.

### Tabel Input → Proses → Output

| | Detail |
|---|---|
| **Input** | PrimeKG (`kg.csv`), MedQA (USMLE), referensi akademis medis |
| **Proses** | Kurasi QA dataset → Bangun evaluation harness → Uji pada mock baseline → Integrasi dengan pipeline utama |
| **Output** | Dataset ground-truth (50–100 QA pairs) + laporan skor RAGAS + analisis perbandingan LLM-as-Judge vs baseline |

---

## 2. Posisi dalam Arsitektur Proyek

Mahasiswa 3 berada di lapisan **Quality Assurance & Observabilitas** — lapisan yang paling independen secara teknis.

```
┌─────────────────────────────────────────────────────────┐
│                   ARSITEKTUR PROYEK                     │
│                                                         │
│  [User Query]                                           │
│       │                                                 │
│       ▼                                                 │
│  ┌──────────────────────────────────┐                   │
│  │  Mhs 1 – Query Expansion Layer   │                   │
│  │  (Semantic + Disambiguation)     │                   │
│  └──────────────────┬───────────────┘                   │
│                     │ expanded query                    │
│                     ▼                                   │
│  ┌──────────────────────────────────┐                   │
│  │  Mhs 2 – Graph Extraction Layer  │                   │
│  │  (Subgraf + KGE + Path Context)  │                   │
│  └──────────────────┬───────────────┘                   │
│                     │ subgraf + context                 │
│                     ▼                                   │
│  ┌──────────────────────────────────┐                   │
│  │  LLM Generation → Jawaban Akhir  │                   │
│  └──────────────────┬───────────────┘                   │
│                     │                                   │
│                     ▼                                   │
│  ┌─────────────────────────────────────────────────┐    │
│  │  MHS 3 – RAGAS EVALUATION LAYER  ◄── POSISI INI │    │
│  │  Ground-Truth Dataset                            │    │
│  │  + RAGAS Harness                                 │    │
│  │  + LLM-as-Judge Comparison                       │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Strategi Kerja Paralel (Tanpa Menunggu Pipeline Lain)

Mahasiswa 3 bekerja **independen** menggunakan pendekatan **mock baseline** sehingga tidak perlu menunggu sistem lain selesai.

```
Pipeline lain     ────────────────────────────► Integrasi (Minggu 10)
                                                      │
Mhs 3:                                                │
  Minggu 1-4:  Kurasi Ground-Truth Dataset  ──────┐   │
  Minggu 5-8:  Bangun RAGAS Harness +       ──────┤   │
               Uji pada Mock Baseline              │   │
  Minggu 9-10: Integrasi dengan pipeline    ◄──────┘◄──┘
  Minggu 11-12: Analisis & Laporan
```

**Mock Baseline** = sistem RAG sederhana yang dibangun sendiri oleh Mhs 3 sebagai pembanding awal:
- LangChain + PrimeKG CSV (cosine similarity biasa)
- Tanpa graph traversal, tanpa query expansion, tanpa Cypher
- Data: `kg_subset.csv` yang sama (dari `filter_kg.py`)

Mock baseline membuktikan secara kuantitatif seberapa besar keuntungan dari pipeline penuh.

---

## 4. Komponen A: Ground-Truth Dataset

### 4.1 Format Record Dataset

```python
{
  "question":  "Obat apa yang digunakan untuk menangani Multiple Sclerosis?",
  "answer":    "Natalizumab adalah agen imunomodulator yang digunakan sebagai terapi Multiple Sclerosis.",
  "contexts":  [
      "Multiple Sclerosis --[indication]--> Natalizumab (MONDO:0005301)",
      "Natalizumab --[mechanism]--> Integrin alpha-4 inhibition",
      "Natalizumab --[side_effect]--> Progressive Multifocal Leukoencephalopathy"
  ],
  "source":    "PrimeKG + Harrison's Principles of Internal Medicine ed.21",
  "category":  "disease-drug",
  "difficulty": "medium"
}
```

Format ini adalah **format resmi RAGAS** — dataset langsung dapat dijalankan tanpa konversi tambahan.

### 4.2 Sumber Data untuk Kurasi

| Sumber | Tipe QA | Cara Ekstraksi |
|---|---|---|
| **PrimeKG `kg_subset.csv`** | Faktual relasional | Filter relasi prioritas → generate QA otomatis |
| **MedQA (USMLE)** | Klinis multi-choice | Ambil subset relevan dengan penyakit di PrimeKG |
| **Harrison's / Robbins** | Konseptual | Kurasi manual 20–30 QA dari bab penyakit relevan |
| **PrimeKG node descriptions** | Definisi entitas | Generate: "Apa itu {node_name}?" → atribut node |

### 4.3 Distribusi Dataset yang Disarankan (50–100 QA Pairs)

| Kategori | Jumlah | Contoh Pertanyaan |
|---|---|---|
| Disease–Drug | 25 | "Apa indikasi utama Metformin?" |
| Disease–Phenotype | 20 | "Gejala apa yang dikaitkan dengan Diabetes Type 2?" |
| Drug–Side Effect | 15 | "Apa efek samping serius Natalizumab?" |
| Disease–Gene | 15 | "Gen apa yang berkaitan dengan Alzheimer's Disease?" |
| Definisi Entitas | 10 | "Apa yang dimaksud dengan Autoimmune Hepatitis?" |
| Lintas Domain | 15 | "Bagaimana hubungan antara Multiple Sclerosis dan depresi?" |

### 4.4 Script Generator QA dari PrimeKG

```python
# generate_qa_dataset.py
import pandas as pd
import json
from tqdm import tqdm

TEMPLATES = {
    "indication": {
        "question": "Obat apa yang digunakan untuk menangani {disease}?",
        "answer":   "{drug} digunakan sebagai terapi untuk {disease}."
    },
    "contraindication": {
        "question": "Mengapa {drug} dikontraindikasikan pada {disease}?",
        "answer":   "{drug} dikontraindikasikan pada {disease} karena risiko komplikasi serius."
    },
    "disease_phenotype": {
        "question": "Gejala apa yang berkaitan dengan {disease}?",
        "answer":   "{phenotype} merupakan fenotip yang berkaitan dengan {disease}."
    }
}

def generate_qa_from_kg(kg_subset_path: str, output_path: str, max_per_relation: int = 25):
    kg = pd.read_csv(kg_subset_path)
    records = []

    for relation, template in TEMPLATES.items():
        subset = kg[kg["relation"] == relation]
        subset = subset.sample(min(max_per_relation, len(subset)), random_state=42)

        for _, row in tqdm(subset.iterrows(), desc=f"Generating {relation}"):
            try:
                q = template["question"].format(
                    disease=row.get("x_name", ""),
                    drug=row.get("y_name", ""),
                    phenotype=row.get("y_name", "")
                )
                a = template["answer"].format(
                    disease=row.get("x_name", ""),
                    drug=row.get("y_name", ""),
                    phenotype=row.get("y_name", "")
                )
                context = (
                    f"{row['x_name']} --[{relation}]--> {row['y_name']} "
                    f"(x_type: {row['x_type']}, y_type: {row['y_type']})"
                )
                records.append({
                    "question":   q,
                    "answer":     a,
                    "contexts":   [context],
                    "source":     "PrimeKG",
                    "category":   relation,
                    "difficulty": "easy"
                })
            except KeyError:
                continue

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(records)} QA pairs → {output_path}")

if __name__ == "__main__":
    generate_qa_from_kg("data/kg_subset.csv", "data/ground_truth_dataset.json")
```

---

## 5. Komponen B: RAGAS Evaluation Harness

### 5.1 Metrik RAGAS dan Apa yang Diukur

| Metrik | Apa yang Diukur | Relevansi ke Proyek |
|---|---|---|
| **Faithfulness** | Apakah jawaban LLM sesuai konteks? (tidak halusinasi) | Mengukur kejujuran generasi LLM |
| **Answer Relevance** | Apakah jawaban menjawab pertanyaan? | Mengukur relevansi end-to-end |
| **Context Precision** | Seberapa presisi konteks yang diambil? | Mengukur kualitas retrieval |
| **Context Recall** | Apakah semua fakta penting terambil? | Mengukur kelengkapan retrieval |

> **Catatan untuk penguji:** Skor RAGAS bukan satu angka tunggal. Dihitung per-metrik, per-pertanyaan, lalu dirata-ratakan. Rentang 0.0–1.0. Sistem yang baik harus mencapai ≥ 0.7 di semua metrik untuk dapat dianggap layak di domain medis.

### 5.2 Script Evaluasi Utama

```python
# evaluate_graphrag.py
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset
import json

def load_ground_truth(path: str) -> Dataset:
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)
    return Dataset.from_list(records)

def evaluate_system(ground_truth_path: str, system, system_name: str) -> dict:
    gt_dataset = load_ground_truth(ground_truth_path)

    answers  = []
    contexts = []

    for record in gt_dataset:
        output = system.query(record["question"])
        answers.append(output["answer"])
        contexts.append(output["contexts"])

    eval_dataset = Dataset.from_dict(
        {
            "question":     gt_dataset["question"],
            "answer":       answers,
            "contexts":     contexts,
            "ground_truth": gt_dataset["answer"]
        }
    )

    result = evaluate(
        eval_dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
    )

    print(f"\n{'='*50}")
    print(f"Hasil Evaluasi: {system_name}")
    print(f"{'='*50}")
    print(result)
    return result

# Cara pakai:
# from mock_baseline import MockRAGSystem
# evaluate_system("data/ground_truth_dataset.json", MockRAGSystem(), "Mock Baseline")
```

### 5.3 Mock Baseline System

```python
# mock_baseline.py
# Naive RAG tanpa graph traversal — pembanding awal yang dibangun sendiri
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class MockRAGSystem:
    """
    Baseline sederhana: embedding cosine similarity pada kg_subset.csv.
    Tidak menggunakan Neo4j atau query expansion.
    """
    def __init__(self, kg_path: str = "data/kg_subset.csv"):
        self.kg = pd.read_csv(kg_path)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.edge_texts = [
            f"{row['x_name']} {row['relation']} {row['y_name']}"
            for _, row in self.kg.iterrows()
        ]
        self.embeddings = self.model.encode(self.edge_texts, show_progress_bar=True)

    def query(self, question: str, top_k: int = 5) -> dict:
        q_emb  = self.model.encode([question])
        scores = cosine_similarity(q_emb, self.embeddings)[0]
        top_idx = np.argsort(scores)[-top_k:][::-1]

        contexts = [self.edge_texts[i] for i in top_idx]
        answer   = "Berdasarkan data yang ditemukan: " + ". ".join(contexts[:2])

        return {"answer": answer, "contexts": contexts}
```

---

## 6. Komponen C: LLM-as-Judge vs Validasi Manual

### 6.1 Dua Mode Evaluasi

```
Mode A — RAGAS Otomatis (LLM-as-Judge):
  [question + answer + contexts + ground_truth]
           │
           ▼
    [RAGAS LLM Evaluator]
           │
           ▼
  Skor: Faithfulness=0.82, Relevance=0.74, ...

Mode B — Validasi Manual (Human-in-the-Loop):
  Penguji/dosen membaca jawaban + ground_truth
           │
           ▼
  Skor manual 1–5 per dimensi
           │
           ▼
  Analisis korelasi: apakah RAGAS setuju dengan manusia?
```

### 6.2 Rubrik Validasi Manual

| Dimensi | Skor 1 | Skor 3 | Skor 5 |
|---|---|---|---|
| **Akurasi Faktual** | Salah/halusinasi | Sebagian benar | Sepenuhnya akurat |
| **Kelengkapan** | Informasi kurang | Cukup tapi tidak lengkap | Semua fakta kunci tercakup |
| **Keselamatan** | Berpotensi berbahaya secara klinis | Netral | Aman dan tidak menyesatkan |
| **Kejelasan Bahasa** | Tidak dapat dipahami | Cukup dipahami | Jelas dan terstruktur |

### 6.3 Analisis Korelasi

```python
# correlation_analysis.py
from scipy.stats import pearsonr, spearmanr

def compare_judges(ragas_scores: list, human_scores: list) -> dict:
    pearson_r, p1  = pearsonr(ragas_scores, human_scores)
    spearman_r, p2 = spearmanr(ragas_scores, human_scores)

    print(f"Pearson r  = {pearson_r:.3f}  (p={p1:.4f})")
    print(f"Spearman ρ = {spearman_r:.3f}  (p={p2:.4f})")

    if pearson_r >= 0.7:
        print("→ Korelasi KUAT: LLM-as-Judge dapat diandalkan untuk domain ini.")
    elif pearson_r >= 0.4:
        print("→ Korelasi SEDANG: Perlu validasi manusia untuk kasus borderline.")
    else:
        print("→ Korelasi LEMAH: LLM-as-Judge tidak menggantikan evaluasi pakar.")

    return {"pearson": pearson_r, "spearman": spearman_r}
```

---

## 7. Contoh Riil: Alur Evaluasi Satu Pertanyaan

**Pertanyaan:** *"Apa efek samping serius dari Natalizumab pada pasien Multiple Sclerosis?"*

**Ground-Truth:**
> Natalizumab dapat menyebabkan Progressive Multifocal Leukoencephalopathy (PML), infeksi otak serius yang disebabkan reaktivasi virus JC pada pasien immunocompromised.

---

**Skenario A — Mock Baseline:**

```
Konteks diambil (cosine similarity):
  1. "Natalizumab contraindication Multiple Sclerosis"  ← tidak relevan
  2. "Natalizumab side_effect Depression"               ← kurang spesifik
  3. "Natalizumab indication Multiple Sclerosis"        ← salah relasi

Jawaban: "Natalizumab digunakan untuk Multiple Sclerosis dan berkaitan dengan depresi."

RAGAS Scores:
  Faithfulness:      0.41  ✗
  Answer Relevance:  0.38  ✗
  Context Precision: 0.20  ✗
  Context Recall:    0.15  ✗
```

**Skenario B — Full GraphRAG Pipeline (setelah integrasi):**

```
Query Expansion:
  "Natalizumab" + expand relasi: ["side_effect", "contraindication", "adverse_event"]

Graph Retrieval:
  Path 1: Natalizumab --[side_effect]--> PML
  Path 2: PML --[caused_by]--> JC Virus
  Path 3: Natalizumab --[risk_factor]--> immunosuppression

Jawaban LLM: "Efek samping serius Natalizumab adalah Progressive Multifocal
  Leukoencephalopathy (PML), infeksi otak yang disebabkan reaktivasi virus JC
  pada pasien dengan sistem imun yang ditekan."

RAGAS Scores:
  Faithfulness:      0.91  ✅
  Answer Relevance:  0.88  ✅
  Context Precision: 0.85  ✅
  Context Recall:    0.87  ✅
```

**Nilai kontribusi:** Tanpa dataset ground-truth dan harness ini, tidak ada cara objektif untuk membuktikan bahwa pipeline lengkap benar-benar lebih baik dari sistem sederhana.

---

## 8. Struktur Folder Proyek

```
mhs3_evaluasi/
├── data/
│   ├── kg_subset.csv              # dari filter_kg.py (shared)
│   ├── ground_truth_dataset.json  # output generate_qa_dataset.py
│   └── manual_scores.csv          # hasil validasi manual penguji
├── scripts/
│   ├── generate_qa_dataset.py     # generator QA dari PrimeKG
│   ├── mock_baseline.py           # mock RAG system
│   ├── evaluate_graphrag.py       # RAGAS harness utama
│   └── correlation_analysis.py   # LLM-Judge vs human
├── results/
│   ├── baseline_scores.json
│   ├── graphrag_scores.json
│   └── comparison_report.md
└── requirements.txt
```

### `requirements.txt`

```
ragas>=0.1.0
datasets>=2.14.0
sentence-transformers>=2.2.2
pandas>=2.0.0
scipy>=1.11.0
scikit-learn>=1.3.0
tqdm>=4.65.0
openai>=1.0.0
```

---

## 9. Keputusan Teknis

| Pertanyaan | Keputusan | Alasan |
|---|---|---|
| **Framework evaluasi** | RAGAS | Standar industri untuk RAG, metriknya sesuai domain medis, open-source |
| **LLM untuk RAGAS evaluator** | GPT-3.5 / Llama-2-7B | Mendukung keduanya — GPT-3.5 untuk baseline cepat, Llama untuk versi lokal |
| **Jumlah QA dataset** | 50–100 pairs | Cukup untuk analisis statistik S1, tidak berlebihan untuk kurasi manual |
| **Mock baseline** | Naive RAG (cosine sim) | Dibangun sendiri, tidak bergantung sistem lain |
| **Validasi manual** | 20–30 sampel subset | Hanya sampel untuk analisis korelasi, tidak semua 100 QA |
| **Observabilitas** | TruLens (opsional) | Dapat ditambahkan sebagai dashboard monitoring di atas RAGAS |

---

## 10. Roadmap 12 Minggu

| Minggu | Target | Output |
|---|---|---|
| 1–2 | Setup environment + eksplorasi PrimeKG & MedQA | `kg_subset.csv`, daftar relasi yang dikurasi |
| 3–4 | Kurasi ground-truth dataset | `ground_truth_dataset.json` (50+ QA pairs) |
| 5–6 | Bangun mock baseline + uji RAGAS pertama kali | `baseline_scores.json`, laporan baseline |
| 7–8 | Validasi manual 20–30 QA + analisis korelasi | `manual_scores.csv`, korelasi awal |
| 9–10 | Integrasi dengan pipeline lengkap | `graphrag_scores.json` |
| 11 | Perbandingan baseline vs GraphRAG + analisis | `comparison_report.md` |
| 12 | Penulisan laporan & presentasi | Skripsi bab 4–5 |

---

## 11. Pertanyaan Penelitian & Hipotesis

**RQ1:** Apakah sistem GraphRAG mencapai skor RAGAS ≥ 0.7 pada domain penyakit fisiologis?

**RQ2:** Seberapa besar peningkatan skor RAGAS antara mock baseline (naive RAG) vs pipeline GraphRAG penuh?

**RQ3:** Apakah skor LLM-as-Judge (RAGAS) berkorelasi signifikan (r ≥ 0.6) dengan penilaian manual untuk domain medis faktual?

**Hipotesis:**
- H1: Pipeline GraphRAG penuh menghasilkan Context Recall lebih tinggi ≥ 0.2 poin dibanding naive RAG
- H2: LLM-as-Judge memiliki korelasi Pearson ≥ 0.6 untuk pertanyaan faktual (disease-drug), namun lebih rendah untuk pertanyaan klinis kompleks

---

## 12. Mengapa Judul Ini Penting

Tanpa evaluasi yang terstandarisasi, sebuah sistem AI medis hanyalah program yang menghasilkan teks — tidak ada jaminan keakuratan atau keamanannya. Kontribusi mahasiswa ini adalah **menetapkan standar pengukuran** yang membuat seluruh proyek GraphRAG dapat dipertanggungjawabkan secara saintifik. Dataset ground-truth yang dihasilkan dapat digunakan kembali oleh penelitian selanjutnya sebagai benchmark terbuka untuk GraphRAG di domain fisiologi.
