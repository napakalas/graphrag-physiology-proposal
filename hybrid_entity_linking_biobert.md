# Analisis Kinerja Model BioBERT dalam Pendekatan Hybrid Entity Linking pada Knowledge Graph Anatomi Fisiologi

**Topik Mahasiswa 1 – NLP & Entity Linking Layer**  
Referensi kurikulum: Tugas Akhir / Skripsi S1 Teknik Informatika  

---

## 1. Gambaran Umum & Motivasi

Dalam pembangunan sistem **GraphRAG (Graph Retrieval-Augmented Generation)** pada domain fisiologi kedokteran dan sistem saraf, kendala utama pada tahapan awal (*ingestion/query parsing*) adalah **variasi leksikal yang ekstrem** saat pengguna menyebutkan nama organ, jalur saraf, atau fenotipe klinis.

Contoh tantangan nyata dalam domain anatomi saraf:
- Klinisi menyebut: *"Nervus Vagus"* (nomenklatur anatomis Latin).
- Buku ajar fisiologi menyebut: *"Cranial Nerve X"* atau *"CN X"*.
- Pasien/orang awam menyebut: *"Saraf pengatur detak jantung dan pencernaan"*.
- Database PrimeKG/UBERON memetakan ke entitas: `UBERON:0001759` (*vagus nerve*).

Jika sistem hanya mengandalkan pencarian leksikal (*exact keyword matching* / TF-IDF), kueri non-standar akan menghasilkan **zero retrieval**. Sebaliknya, jika hanya mengandalkan pencarian vektor padat (*dense embedding cosine similarity*), sering terjadi **false positive** karena istilah anatomi yang berdekatan secara semantik (misal *nervus vagus* vs *nervus glossopharyngeus*) memiliki representasi vektor yang sangat mirip namun secara klinis merupakan struktur anatomis yang berbeda.

Proyek ini mengusulkan arsitektur **Hybrid Entity Linking** yang menggabungkan:
1. **Dense Semantic Retrieval** menggunakan representasi vektor dari **BioBERT** (*Bidirectional Encoder Representations from Transformers for Biomedical Text Mining*).
2. **Sparse Lexical Retrieval** menggunakan algoritma **BM25 / Fuzzy N-Gram Matching** untuk menjamin presisi terminologi spesifik.
3. **Graph-Context Disambiguation** yang memanfaatkan ketetanggaan topologi graf ontologi (UBERON/FMA) untuk memecahkan ambiguitas entitas.

### Tabel Input → Proses → Output

| Parameter | Keterangan Rinci |
|---|---|
| **Input** | Teks kueri bebas pengguna (*unstructured medical text / clinical query*) & kamus ontologi anatomi UBERON / PrimeKG. |
| **Proses** | 1. Mention Detection (Spacy/BioBERT NER).<br>2. Candidate Generation Ganda (Dense BioBERT + Sparse BM25).<br>3. Normalisasi Skor Gabungan (*Reciprocal Rank Fusion / Weighted Sum*).<br>4. Re-ranking berbasis kedekatan graf (*graph neighborhood prior*). |
| **Output** | ID Entitas terverifikasi (`UBERON_ID` / `FMA_ID`), label kanonikal, skor keyakinan (*confidence score*), dan pemetaan ke node Knowledge Graph. |
| **Kontribusi Ilmiah** | Menganalisis trade-off antara akurasi linking (*Accuracy@k, MRR*) dan latensi komputasi pada skenario hybrid vs single-model. |

---

## 2. Posisi dalam Arsitektur GraphRAG

Mahasiswa 1 berada di gerbang terdepan dari arsitektur GraphRAG. Kegagalan pada tahap ini akan merusak seluruh tahapan retrieval di database graf (Neo4j) dan jawaban akhir LLM (*garbage in, garbage out*).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ARSITEKTUR GRAPHRAG                             │
│                                                                        │
│  [User Query: "Kerusakan nervus X memicu takikardia dan gastroparesis"]│
│                             │                                          │
│                             ▼                                          │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  MAHASISWA 1: HYBRID ENTITY LINKING (BIOBERT + SPARSE)       │◄────┘
│  │  1. Mention Extraction: ["nervus X", "takikardia"]           │     │
│  │  2. Dense Search (BioBERT) ──┐                               │     │
│  │  3. Sparse Search (BM25)   ──┴─► Fusion & Disambiguasi       │     │
│  │  Output: UBERON:0001759 (vagus nerve), HP:0001662            │     │
│  └──────────────────────────────┬───────────────────────────────┘     │
│                                 │ CUI / Ontology IDs                   │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Mahasiswa 2: Database Graf & Traversal (Neo4j / PrimeKG)    │     │
│  │  MATCH (n:Anatomy {id: 'UBERON:0001759'})-[r]-(m)            │     │
│  └──────────────────────────────┬───────────────────────────────┘     │
│                                 │ Subgraf Relasi                       │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Mahasiswa 3: Linearisasi Subgraf & LLM Prompting            │     │
│  └──────────────────────────────┬───────────────────────────────┘     │
│                                 │ Jawaban Final                        │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Mahasiswa 4: QA & Evaluasi RAGAS (Ground Truth Benchmark)   │     │
│  └──────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Landasan Teori & Formulasi Matematis

### 3.1 Representasi Vektor BioBERT (Dense Retrieval)

BioBERT adalah model transformer berbasis BERT yang telah dilatih ulang (*pre-trained*) menggunakan korpus biomedical skala masif (PubMed abstracts dan PMC full-text articles).

Diberikan teks sebutan entitas (*mention*) $m$ dan dokumen kandidat entitas $e \in \mathcal{E}$ dengan teks definisi/alias $d_e$. Vektor representasi $d$-dimensi diekstraksi dari representasi token `[CLS]`:

$$\mathbf{v}_m = \text{BioBERT}(m)_{[\text{CLS}]} \in \mathbb{R}^d$$
$$\mathbf{v}_e = \text{BioBERT}(d_e)_{[\text{CLS}]} \in \mathbb{R}^d$$

Kemiripan semantik padat (*dense similarity*) dihitung menggunakan *Cosine Similarity*:

$$S_{\text{dense}}(m, e) = \cos(\mathbf{v}_m, \mathbf{v}_e) = \frac{\mathbf{v}_m \cdot \mathbf{v}_e}{\|\mathbf{v}_m\| \|\mathbf{v}_e\|}$$

### 3.2 Pencarian Leksikal BM25 (Sparse Retrieval)

Untuk menangkap ketepatan ejaan kode anatomi (seperti "CN X", "T1-T4", "S2-S4"), algoritma BM25 menghitung bobot relevansi berbasis term frequency ($TF$) dan inverse document frequency ($IDF$):

$$S_{\text{sparse}}(m, e) = \sum_{t \in m \cap d_e} \text{IDF}(t) \cdot \frac{f(t, d_e) \cdot (k_1 + 1)}{f(t, d_e) + k_1 \cdot \left(1 - b + b \cdot \frac{|d_e|}{\text{avgdl}}\right)}$$

Di mana:
- $f(t, d_e)$ adalah frekuensi kemunculan token $t$ dalam definisi entitas $d_e$.
- $|d_e|$ adalah panjang token definisi $e$, dan $\text{avgdl}$ adalah rata-rata panjang dokumen.
- $k_1 \approx 1.5$ dan $b \approx 0.75$ adalah hiperparameter baku.

### 3.3 Penyatuan Skor Hybrid (Hybrid Scoring Fusion)

Agar skor dense dan sparse berada pada skala yang setara, dilakukan normalisasi min-max atau standardisasi Z-score:

$$\tilde{S}_{\text{dense}}(m, e) = \frac{S_{\text{dense}}(m, e) - \min(S_{\text{dense}})}{\max(S_{\text{dense}}) - \min(S_{\text{dense}})}$$
$$\tilde{S}_{\text{sparse}}(m, e) = \frac{S_{\text{sparse}}(m, e) - \min(S_{\text{sparse}})}{\max(S_{\text{sparse}}) - \min(S_{\text{sparse}})}$$

Skor akhir kandidat dihitung melalui kombinasi linier terbobot (*convex combination*):

$$S_{\text{hybrid}}(m, e) = \alpha \cdot \tilde{S}_{\text{dense}}(m, e) + (1 - \alpha) \cdot \tilde{S}_{\text{sparse}}(m, e)$$

Di mana parameter $\alpha \in [0, 1]$ adalah bobot kendali yang dioptimasi melalui *grid search* pada set validasi.

### 3.4 Disambiguasi Berbasis Topologi Graf (Graph Neighborhood Prior)

Ketika satu kueri menghasilkan beberapa kandidat sebutan $M = \{m_1, m_2, \dots, m_p\}$, keterkaitan antar entitas kandidat dalam struktur Knowledge Graph $\mathcal{G} = (\mathcal{V}, \mathcal{E})$ digunakan sebagai bobot penentu (*graph coherence*).

Jarak terpendek graf (*shortest path distance*) antara entitas kandidat $e_i$ dan entitas kandidat lain $e_j$:

$$\text{Coh}(e_i, e_j) = \frac{1}{1 + \text{dist}_{\mathcal{G}}(e_i, e_j)}$$

Skor akhir terdisamiguasi:

$$S_{\text{final}}(e_i) = S_{\text{hybrid}}(m, e_i) + \lambda \sum_{j \neq i} \text{Coh}(e_i, e_j)$$

---

## 4. Implementasi Kode Python

Berikut adalah implementasi modul hybrid entity linker yang dirancang khusus untuk memetakan kueri anatomi fisiologi ke node ontologi UBERON/PrimeKG. Kode menggunakan konvensi **Allman style** untuk penempatan tanda kurung kurawal.

```python
import torch
import numpy as np
from typing import List, Dict, Tuple
from transformers import AutoTokenizer, AutoModel
from rank_bm25 import BM25Okapi

class HybridEntityLinker:
{
    def __init__(self, model_name: str = "dmis-lab/biobert-base-cased-v1.2", alpha: float = 0.65) -> None:
    {
        self.alpha = alpha
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"[Init] Loading BioBERT model: {model_name} on {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.dense_model = AutoModel.from_pretrained(model_name).to(self.device)
        self.dense_model.eval()

        self.entities: List[Dict] = []
        self.entity_embeddings: np.ndarray = np.array([])
        self.bm25: BM25Okapi = None
    }

    def index_knowledge_base(self, ontology_records: List[Dict]) -> None:
    {
        """
        ontology_records format:
        [
            {"id": "UBERON:0001759", "name": "vagus nerve", "synonyms": ["cranial nerve X", "nervus vagus"]},
            ...
        ]
        """
        self.entities = ontology_records
        corpus_texts = []
        tokenized_corpus = []

        for item in ontology_records:
        {
            combined_text = f"{item['name']} " + " ".join(item.get("synonyms", []))
            corpus_texts.append(combined_text)
            tokenized_corpus.append(combined_text.lower().split())
        }

        # 1. Bangun Inverted Index BM25
        print(f"[Indexing] Building BM25 index over {len(corpus_texts)} anatomy concepts...")
        self.bm25 = BM25Okapi(tokenized_corpus)

        # 2. Bangun Dense Embeddings menggunakan BioBERT
        print(f"[Indexing] Computing BioBERT dense vectors...")
        embeddings = []
        with torch.no_grad():
        {
            for text in corpus_texts:
            {
                vec = self._encode_text(text)
                embeddings.append(vec)
            }
        }
        self.entity_embeddings = np.vstack(embeddings)
        print(f"[Indexing] Finished. Matrix shape: {self.entity_embeddings.shape}")
    }

    def _encode_text(self, text: str) -> np.ndarray:
    {
        inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=64,
            return_tensors="pt"
        ).to(self.device)

        outputs = self.dense_model(**inputs)
        # Menggunakan mean-pooling dari hidden states terakhir
        token_embeddings = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"].unsqueeze(-1)
        mean_pooled = torch.sum(token_embeddings * attention_mask, dim=1) / torch.clamp(attention_mask.sum(dim=1), min=1e-9)
        normalized = torch.nn.functional.normalize(mean_pooled, p=2, dim=1)
        return normalized.cpu().numpy().flatten()
    }

    def link_entity(self, mention: str, top_k: int = 5) -> List[Dict]:
    {
        mention_clean = mention.strip()
        tokens = mention_clean.lower().split()

        # 1. Sparse Scores (BM25)
        raw_sparse_scores = np.array(self.bm25.get_scores(tokens))
        sparse_norm = self._min_max_normalize(raw_sparse_scores)

        # 2. Dense Scores (Cosine Similarity)
        query_vec = self._encode_text(mention_clean)
        raw_dense_scores = np.dot(self.entity_embeddings, query_vec)
        dense_norm = self._min_max_normalize(raw_dense_scores)

        # 3. Hybrid Fusion
        hybrid_scores = (self.alpha * dense_norm) + ((1.0 - self.alpha) * sparse_norm)

        # 4. Ambil Top-K
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
        {
            entity_data = self.entities[idx]
            results.append(
            {
                "id": entity_data["id"],
                "canonical_name": entity_data["name"],
                "hybrid_score": float(hybrid_scores[idx]),
                "dense_score": float(dense_norm[idx]),
                "sparse_score": float(sparse_norm[idx])
            })
        }
        return results
    }

    @staticmethod
    def _min_max_normalize(scores: np.ndarray) -> np.ndarray:
    {
        denom = scores.max() - scores.min()
        if denom == 0:
        {
            return np.zeros_like(scores)
        }
        return (scores - scores.min()) / denom
    }
}

if __name__ == "__main__":
{
    mock_ontology = [
        {
            "id": "UBERON:0001759",
            "name": "vagus nerve",
            "synonyms": ["cranial nerve X", "nervus vagus", "parasympathetic nerve 10"]
        },
        {
            "id": "UBERON:0001758",
            "name": "glossopharyngeal nerve",
            "synonyms": ["cranial nerve IX", "nervus glossopharyngeus"]
        },
        {
            "id": "UBERON:0000948",
            "name": "heart",
            "synonyms": ["cardiac muscle organ", "cor"]
        },
        {
            "id": "UBERON:0002110",
            "name": "sinoatrial node",
            "synonyms": ["SA node", "pacemaker of heart"]
        }
    ]

    linker = HybridEntityLinker(alpha=0.6)
    linker.index_knowledge_base(mock_ontology)

    test_queries = [
        "nervus vagus",
        "cranial nerve 10",
        "SA node pacemaker"
    ]

    for q in test_queries:
    {
        print(f"\n[Query]: '{q}'")
        matches = linker.link_entity(q, top_k=2)
        for m in matches:
        {
            print(f"  -> {m['id']} | {m['canonical_name']} (Hybrid: {m['hybrid_score']:.3f}, Dense: {m['dense_score']:.3f}, Sparse: {m['sparse_score']:.3f})")
        }
    }
}
```

---

## 5. Desain Eksperimen & Metrik Evaluasi

### 5.1 Dataset Pengujian

1. **Subset UBERON & FMA**: 500 konsep anatomi saraf otonom (saraf kranial, pleksus, ganglion, organ efektor).
2. **Kueri Sintetis & Riil (Test Mentions)**: 150 penyebutan klinis yang mengandung:
   - Sinonim Latin murni (*nervus splanchnicus major*).
   - Akronim kedokteran (*ANS, CN X, GVE fibers*).
   - Typo leksikal (*vaggus nerve, hypoglosal*).

### 5.2 Metrik Evaluasi

1. **Accuracy@1 (Top-1 Accuracy)**:
   Persentase kueri di mana kandidat urutan teratas sama persis dengan entitas *ground truth*.
2. **Recall@5**:
   Persentase kueri di mana kandidat yang benar berada di dalam 5 kandidat teratas.
3. **Mean Reciprocal Rank (MRR)**:
   $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
4. **Latency (Rata-rata Waktu Inferensi)**: Diukur dalam milidetik ($ms$) per kueri.

### 5.3 Rencana Hasil Pengujian (Baseline vs Hybrid)

| Metode | Accuracy@1 | Recall@5 | MRR | Latensi (ms) |
|---|---|---|---|---|
| **Baseline 1: Pure BM25 (Sparse)** | 62.4% | 76.1% | 0.68 | **1.2 ms** |
| **Baseline 2: Pure BioBERT (Dense)** | 78.5% | 89.2% | 0.81 | 18.5 ms |
| **Usulan: Hybrid (BM25 + BioBERT)** | **88.7%** | **96.4%** | **0.91** | 19.8 ms |
| **Usulan: Hybrid + Graph Disambiguation** | **91.2%** | **97.8%** | **0.93** | 24.3 ms |

---

## 6. Struktur Direktori Proyek

```
mhs1_entity_linking/
├── data/
│   ├── anatomy_ontology_subset.json # 500+ entitas UBERON/FMA
│   ├── mentions_ground_truth.json   # 150 pasangan (mention, target_id)
│   └── test_queries_noisy.json      # data uji dengan typo/singkatan
├── models/
│   └── biobert_embeddings_cache.npy # cache vektor agar tidak re-encode
├── scripts/
│   ├── hybrid_linker.py             # core engine BioBERT + BM25
│   ├── graph_disambiguation.py      # re-ranker berbasis ketetanggaan UBERON
│   └── run_benchmark.py             # script evaluasi otomatis
├── results/
│   ├── ablation_alpha_tuning.png    # grafik akurasi vs nilai alpha
│   └── metrics_comparison.json      # tabel metrik final
└── requirements.txt
```

### `requirements.txt`
```
torch>=2.0.0
transformers>=4.30.0
rank-bm25>=0.2.2
numpy>=1.24.0
scikit-learn>=1.3.0
tqdm>=4.65.0
networkx>=3.0
```

---

## 7. Sistematika Penulisan Proposal Skripsi (Bab 1 – Bab 3)

Dokumen proposal skripsi berfokus pada pematangan masalah, landasan teori, dan metode yang dapat dipertanggungjawabkan:

### Bab 1: Pendahuluan
- **Latar Belakang**: Tantangan variasi leksikal anatomi medis (Latin vs vernacular) pada sistem GraphRAG dan kelemahan model leksikal tunggal maupun model vektor murni.
- **Rumusan Masalah**:
  1. Bagaimana merancang arsitektur *Hybrid Entity Linking* yang menggabungkan representasi padat BioBERT dan representasi jarang BM25 untuk entitas anatomi sistem saraf?
  2. Seberapa besar pengaruh integrasi *Graph Neighborhood Prior* terhadap akurasi disambiguasi entitas medis yang ambigu?
- **Batasan Masalah**:
  - Domain terbatas pada entitas anatomi fisiologi dan sistem saraf otonom berbasis PrimeKG / UBERON.
  - Model bahasa yang diuji difokuskan pada keluarga BioBERT (tidak melatih model dari nol/scratch).
- **Tujuan Penelitian**: Mengukur peningkatan metrik *Accuracy@1*, *MRR*, dan *Recall@5* serta latensi komputasi dari pendekatan hybrid dibanding baseline tunggal.

### Bab 2: Tinjauan Pustaka
- Teori *Knowledge Graph* dan *Entity Linking* biomedis.
- Mekanisme kerja Transformer & representasi vektor BioBERT.
- Teori Information Retrieval leksikal (BM25 Okapi).
- Struktur taksonomi dan hierarki ontologi UBERON/PrimeKG.
- *State-of-the-Art*: Komparasi penelitian entity linking biomedis terdahulu (mis. BioSyn, MedCAT, scispaCy).

### Bab 3: Metodologi Penelitian
- Alur penelitian terstruktur (Studi literatur $\to$ Akuisisi data ontologi $\to$ Pembangunan index ganda $\to$ Penyetelan bobot $\alpha \to$ Evaluasi performa).
- Spesifikasi instrumen pengujian (*hardware, software, environment*).
- Kriteria keberhasilan penelitian (*Success Criteria*).

---

## 8. Panduan Menghadapi Sidang Proposal (Sempro FAQ)

Berikut adalah antisipasi pertanyaan kritis yang lazim dilontarkan dosen penguji saat **Sidang Seminar Proposal**:

> **Tanya Dosen Penguji:** *"Apa urgensi dan nilai kebaruan (novelty) dari penelitian Anda? Bukankah BioBERT dan BM25 adalah algoritma yang sudah mapan?"*  
> **Jawab:** Kebaruan penelitian ini terletak pada **formulasi integrasi hybrid bertingkat (dual-stage scoring + topological prior)** yang dirancang khusus untuk menangani karakteristik unik ontologi anatomi fisiologi. Pada istilah anatomi saraf, model dense sering gagal membedakan entitas berdekatan fungsional (*nervus VII* vs *nervus VIII*), sedangkan model sparse gagal pada istilah Latin vs Inggris. Kebaruan terletak pada optimasi fungsi fusi bobot dinamis dan pembuktian empiris bahwa integrasi topologi graf ontologi mampu memecahkan ambiguitas lokal secara deterministik.

> **Tanya Dosen Penguji:** *"Bagaimana Anda menetapkan batasan masalah agar penelitian ini realistis diselesaikan dalam satu semester tanpa bantuan dokter spesialis setiap hari?"*  
> **Jawab:** Ruang lingkup dibatasi secara ketat pada subgraf anatomi sistem saraf otonom (500 entitas UBERON/FMA pada PrimeKG). Untuk *ground truth*, kami menggunakan data yang telah terkurasi secara baku dalam pangkalan data ontologi publik (UBERON dan UMLS Metathesaurus), sehingga verifikasi tidak bergantung pada opini subjektif dokter individu melainkan pada standar taksonomi biomedis internasional yang sudah *peer-reviewed*.

> **Tanya Dosen Penguji:** *"Apa kriteria keberhasilan dari proposal skripsi Anda? Kapan metode hybrid ini dianggap berhasil?"*  
> **Jawab:** Penelitian ini dinyatakan berhasil apabila:
> 1. Pendekatan Hybrid mampu menghasilkan peningkatan *Accuracy@1* minimal 10% absolut dibandingkan baseline leksikal murni (BM25) pada data kueri uji.
> 2. Peningkatan nilai *Mean Reciprocal Rank (MRR)* mencapai $\ge 0.85$.
> 3. Latensi inferensi rata-rata tetap berada di bawah ambang interaktif ($< 35\text{ ms}$ per kueri) sehingga layak diintegrasikan ke dalam pipeline GraphRAG secara *real-time*.
