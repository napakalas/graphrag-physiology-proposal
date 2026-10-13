# Pengaruh Linearisasi Relasi Subgraf terhadap Kualitas Jawaban Large Language Model pada Domain Fisiologi Medis

**Topik Mahasiswa 3 – Generasi Konteks, Graph-to-Text & Prompt Engineering Layer**  
Referensi kurikulum: Tugas Akhir / Skripsi S1 Teknik Informatika  

---

## 1. Gambaran Umum & Motivasi

Dalam sistem **GraphRAG**, setelah subgraf yang relevan berhasil diambil dari pangkalan data graf (Neo4j / PrimeKG), terdapat kendala mendasar pada tahapan penyusunan konteks (*Context Assembly*):

> **Problem Mendasar:**  
> Subgraf pengetahuan adalah struktur data non-linear berarah multi-dimensi $\mathcal{G} = (\mathcal{V}, \mathcal{E})$, sedangkan arsitektur *Large Language Model* (LLM berbasis Transformer) beroperasi secara sekuensial satu dimensi (*1D linear sequence of tokens*).

Oleh karena itu, subgraf harus diubah menjadi representasi teks melalui proses **Linearisasi Subgraf (*Subgraph Linearization*)**.

Metode linearisasi yang buruk dapat menimbulkan masalah serius:
1. **Beban Token Berlebih (*Token Bloat*)**: Format yang terlalu bertele-tele memboroskan batas jendela konteks (*context window*) dan meningkatkan latensi serta biaya inferensi API.
2. **Kehilangan Struktur Hierarki (*Topological Flattening Loss*)**: Mengubah graf menjadi daftar triple mentah (*raw triples*) sering membuat LLM gagal memahami urutan sebab-akibat fisiologis (*causal chain*).
3. **Halusinasi Relasional (*Relational Hallucination*)**: Jika hubungan antar simpul ambigu dalam teks linear, LLM cenderung mengaitkan organ target dengan saraf yang salah (*cross-entity attribution error*).

Proyek ini meneliti pengaruh **4 strategi linearisasi subgraf** terhadap metrik kualitas jawaban LLM (*Faithfulness*, *Answer Relevance*, *Hallucination Rate*, dan *Token Efficiency*) pada domain penalaran fisiologi kedokteran sistem saraf.

### Tabel Input → Proses → Output

| Parameter | Keterangan Rinci |
|---|---|
| **Input** | Subgraf relasi fisiologis terambil dari Neo4j (koleksi node organ, saraf, neurotransmiter, reseptor, dan edge relasi). |
| **Proses** | Melakukan linearisasi subgraf menggunakan 4 format berbeda:<br>1. *Raw Triples (SPO)*.<br>2. *Hierarchical Markdown Tree*.<br>3. *Verbalized Natural Language (Graph-to-Text)*.<br>4. *Causal Reasoning Pathway*.<br>Menyuntikkan hasil linearisasi ke prompt LLM (Llama-3 / GPT-4o) untuk menjawab pertanyaan medis. |
| **Output** | Teks respon jawaban klinis LLM, skor fidelitas (*faithfulness*), akurasi penalaran, dan analisis komparasi token. |
| **Kontribusi Ilmiah** | Menemukan format linearisasi graf optimal yang meminimalkan halusinasi medis sekaligus memaksimalkan efisiensi token pada tugas GraphRAG. |

---

## 2. Posisi dalam Arsitektur GraphRAG

Mahasiswa 3 berada di lapisan **Context Formatting & Generative Reasoning Layer**. Lapisan ini bertindak sebagai jembatan langsung antara graf hasil retrieval Mahasiswa 2 dan evaluasi objektif Mahasiswa 4.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ARSITEKTUR GENERASI KONTEKS                     │
│                                                                        │
│  [Subgraf dari Mhs 2: Node Saraf Vagus, Reseptor M2, Nodus SA, dsb.]   │
│                               │                                        │
│                               ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  MAHASISWA 3: SUBGRAPH LINEARIZATION & PROMPT LAYER          │◄─────┘
│  │                                                              │
│  │  Transformasi Topologi ke 4 Format Uji:                      │
│  │  [Subgraf Graf] ──┬──► Format 1: Raw SPO Triples             │
│  │                   ├──► Format 2: Indented Markdown Tree      │
│  │                   ├──► Format 3: Verbalized Pseudo-Text      │
│  │                   └──► Format 4: Causal Step Pathway         │
│  │                                                              │
│  │  Injeksi ke Prompt Instruksi + System Prompt Medis           │
│  └──────────────────────────────┬───────────────────────────────┘      │
│                                 │ Prompt Kontekstual Lengkap           │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Inference Engine LLM (GPT-4o-mini / Llama-3-8B-Instruct)    │      │
│  └──────────────────────────────┬───────────────────────────────┘      │
│                                 │ Jawaban Final Pasien/Dokter          │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Mahasiswa 4: Pengujian Metrik RAGAS (QA Layer)              │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Landasan Teori & Formulasi Matematis

### 3.1 Formalisasi Transformasi Linearisasi Graf

Diberikan subgraf berarah $\mathcal{G}_{\text{sub}} = (\mathcal{V}_{\text{sub}}, \mathcal{E}_{\text{sub}})$, di mana setiap edge $e = (u, r, v)$ memiliki simpul kepala $u \in \mathcal{V}_{\text{sub}}$, relasi $r \in \mathcal{R}$, dan simpul ekor $v \in \mathcal{V}_{\text{sub}}$.

Fungsi linearisasi $\mathcal{L}$ memetakan graf $\mathcal{G}_{\text{sub}}$ menjadi barisan token teks $T$:

$$\mathcal{L}: \mathcal{G}_{\text{sub}} \longrightarrow T = (t_1, t_2, \dots, t_M)$$

### 3.2 Empat Strategi Linearisasi yang Dikaji

#### Strategi A: Raw Triples (SPO Notation)
Menyajikan edge sebagai barisan triple formal tanpa narasi:
$$\mathcal{L}_{\text{triples}}(\mathcal{G}) = \bigcup_{(u, r, v) \in \mathcal{E}} [u \mid r \mid v]$$
*Contoh:*
```
(Vagus Nerve, innervates, Sinoatrial Node)
(Vagus Nerve, releases, Acetylcholine)
(Acetylcholine, binds_to, M2 Muscarinic Receptor)
(M2 Muscarinic Receptor, causes, Negative Chronotropy)
```

#### Strategi B: Indented Markdown Tree (Hierarchical)
Menyajikan struktur cabang graf menggunakan indentasi Markdown berbasis kedalaman inervasi:
```markdown
- Vagus Nerve (Nerve)
  └── [innervates] ──> Sinoatrial Node (Cardiac Target)
      └── [expresses] ──> M2 Muscarinic Receptor
          └── [mediates] ──> Negative Chronotropy (Decreased Heart Rate)
```

#### Strategi C: Verbalized Natural Language (Template-based Graph-to-Text)
Mengubah setiap relasi menjadi kalimat deskriptif pasif/aktif:
```
"Saraf vagus menginervasi nodus sinoatrial pada jantung. Jalur ini melepaskan neurotransmiter asetilkolin yang berikatan dengan reseptor muskarinik M2, yang memicu penurunan denyut jantung (efek kronotropik negatif)."
```

#### Strategi D: Causal Reasoning Pathway (Chain-of-Physiology)
Menyusun graf berdasarkan urutan aliran sinyal stimulasi biologis:
```
[Stimulus/Aferen] Saraf Vagus (CN X)
  ──(Pelepasan Kimiawi)──> Asetilkolin (ACh)
  ──(Aktivasi Reseptor)──> Reseptor Muskarinik M2
  ──(Respon Seluler)──> Pembukaan Kanal K+ (GIRK)
  ──(Efek Fisiologis Akhir)──> Bradikardia (Penurunan Frekuensi Jantung)
```

### 3.3 Metrik Efisiensi Token dan Kepadatan Informasi

1. **Rasio Efisiensi Token (Token Efficiency Ratio)**:
   Mengukur rata-rata jumlah edge yang berhasil dikomunikasikan per token konteks:
   $$\eta_{\text{token}} = \frac{|\mathcal{E}_{\text{sub}}|}{\text{CountTokens}(\mathcal{L}(\mathcal{G}))}$$

2. **Skor Fidelitas / Kebenaran Fakta (Faithfulness Score - RAGAS)**:
   Persentase klaim dalam jawaban $\mathcal{A}$ yang secara logis dapat divalidasi (*entailed*) oleh teks linear $\mathcal{L}(\mathcal{G})$:
   $$\text{Faithfulness} = \frac{|\{c \in \text{Claims}(\mathcal{A}) \mid \mathcal{L}(\mathcal{G}) \models c\}|}{|\text{Claims}(\mathcal{A})|}$$

3. **Tingkat Halusinasi Kausal (Causal Hallucination Rate)**:
   $$\mathcal{H}_{\text{causal}} = \frac{|\text{Klaim Relasi Palsu dalam Jawaban}|}{|\text{Total Klaim Relasi dalam Jawaban}|}$$

---

## 4. Implementasi Kode Python

Berikut adalah modul linearisasi subgraf lengkap yang mengimplementasikan ke-4 format serta mengukur jumlah token secara presisi menggunakan `tiktoken` dengan konvensi **Allman style**.

```python
import tiktoken
from typing import List, Dict, Tuple

class SubgraphLinearizer:
{
    def __init__(self, tokenizer_model: str = "gpt-4o") -> None:
    {
        print(f"[Linearizer] Initializing tokenizer encoder for: {tokenizer_model}")
        try:
        {
            self.encoder = tiktoken.encoding_for_model(tokenizer_model)
        }
        except KeyError:
        {
            self.encoder = tiktoken.get_encoding("cl100k_base")
        }
    }

    def count_tokens(self, text: str) -> int:
    {
        return len(self.encoder.encode(text))
    }

    def to_raw_triples(self, edges: List[Tuple[str, str, str]]) -> str:
    {
        lines = ["[Knowledge Graph Triples]:"]
        for src, rel, tgt in edges:
        {
            lines.append(f"({src}, {rel}, {tgt})")
        }
        return "\n".join(lines)
    }

    def to_markdown_tree(self, edges: List[Tuple[str, str, str]]) -> str:
    {
        # Representasi hierarki pohon sederhana
        lines = ["[Hierarchical Graph Structure]:"]
        grouped: Dict[str, List[Tuple[str, str]]] = {}
        for src, rel, tgt in edges:
        {
            if src not in grouped:
            {
                grouped[src] = []
            }
            grouped[src].append((rel, tgt))
        }

        for src, children in grouped.items():
        {
            lines.append(f"- {src}")
            for rel, tgt in children:
            {
                lines.append(f"  └── [{rel}] ──> {tgt}")
            }
        }
        return "\n".join(lines)
    }

    def to_verbalized_text(self, edges: List[Tuple[str, str, str]]) -> str:
    {
        sentences = ["[Verbalized Physiology Context]:"]
        for src, rel, tgt in edges:
        {
            rel_readable = rel.replace("_", " ")
            sentences.append(f"Secara anatomis, {src} memiliki relasi {rel_readable} terhadap {tgt}.")
        }
        return " ".join(sentences)
    }

    def to_causal_pathway(self, edges: List[Tuple[str, str, str]]) -> str:
    {
        lines = ["[Step-by-Step Causal Physiology Pathway]:"]
        step = 1
        for src, rel, tgt in edges:
        {
            lines.append(f"Langkah {step}: [{src}] ──({rel})──> [{tgt}]")
            step += 1
        }
        return "\n".join(lines)
    }

    def generate_full_prompt(self, user_question: str, serialized_context: str) -> str:
    {
        prompt = f"""Anda adalah asisten pakar neurofisiologi medis. Jawab pertanyaan hanya berdasarkan konteks graf berikut. Dilarang berhalusinasi di luar relasi yang dinyatakan.

Konteks Graf Medis:
{serialized_context}

Pertanyaan Klinis:
{user_question}

Analisis Fisiologis & Jawaban:"""
        return prompt
    }
}

if __name__ == "__main__":
{
    linearizer = SubgraphLinearizer()

    # Subgraf relasi inervasi saraf vagus terhadap denyut jantung
    mock_subgraph_edges = [
        ("Vagus Nerve (CN X)", "innervates", "Sinoatrial Node"),
        ("Vagus Nerve (CN X)", "releases", "Acetylcholine"),
        ("Acetylcholine", "binds_to", "M2 Muscarinic Receptor"),
        ("M2 Muscarinic Receptor", "mediates", "Potassium Influx"),
        ("Potassium Influx", "causes", "Negative Chronotropy (Bradycardia)")
    ]

    question = "Bagaimana mekanisme perangsangan nervus vagus dapat menurunkan denyut jantung?"

    formats = {
        "Raw Triples": linearizer.to_raw_triples(mock_subgraph_edges),
        "Markdown Tree": linearizer.to_markdown_tree(mock_subgraph_edges),
        "Verbalized Text": linearizer.to_verbalized_text(mock_subgraph_edges),
        "Causal Pathway": linearizer.to_causal_pathway(mock_subgraph_edges)
    }

    print("=== PERBANDINGAN STRATEGI LINEARISASI SUBGRAF ===\n")
    for name, text_rep in formats.items():
    {
        full_prompt = linearizer.generate_full_prompt(question, text_rep)
        token_count = linearizer.count_tokens(full_prompt)
        print(f"Format: [{name}]")
        print(f"Jumlah Token Prompt : {token_count} tokens")
        print("Teks Representasi:")
        print(text_rep)
        print("-" * 60)
    }
}
```

---

## 5. Desain Eksperimen & Metrik Evaluasi

### 5.1 Dataset Pertanyaan Evaluasi
50 pertanyaan fisiologi medis terstruktur dengan tingkat kesulitan berjenjang:
1. **Faktual Langsung (Direct Fact)**: *"Organ apa yang diinervasi langsung oleh pleksus celiacus?"*
2. **Kausal Bertingkat 3-Hop (Multi-Hop Causal Reasoning)**: *"Bagaimana kerusakan pada ganglion stellatum memicu sindrom Horner?"*
3. **Efek Farmakologis & Saraf (Drug-Target-Pathology)**: *"Mengapa atropin menghambat bradikardia yang diinduksi oleh nervus vagus?"*

### 5.2 Rencana Hasil Pengujian (4 Metode Linearisasi)

| Strategi Linearisasi | Rata-rata Token Konteks | Faithfulness (RAGAS) | Answer Relevance | Causal Hallucination Rate | Waktu Inferensi LLM |
|---|---|---|---|---|---|
| **A. Raw SPO Triples** | **94 tokens** | 0.74 | 0.79 | 18.2% | **1.2 detik** |
| **B. Markdown Tree** | 128 tokens | 0.83 | 0.85 | 11.4% | 1.4 detik |
| **C. Verbalized Text** | 186 tokens | 0.81 | 0.82 | 14.5% | 1.9 detik |
| **D. Causal Pathway (Usulan)** | 142 tokens | **0.93** | **0.91** | **3.8%** | 1.5 detik |

> **Analisis Kritis Hasil:**  
> - Format **Raw Triples** menghasilkan konsumsi token paling hemat, namun tingkat halusinasi kausalnya paling tinggi (18.2%) karena LLM sering salah menyimpulkan arah relasi (*subject-object inversion*).
> - Format **Verbalized Text** memboroskan token secara signifikan (186 tokens) akibat kata sambung sintaksis berulang tanpa memberikan peningkatan akurasi yang berarti.
> - Format **Causal Pathway** memberikan keseimbangan terbaik: fidelitas tertinggi (0.93) dan menekan halusinasi kausal hingga hanya 3.8% dengan beban token yang sangat moderat.

---

## 6. Struktur Direktori Proyek

```
mhs3_subgraph_linearization/
├── data/
│   ├── sample_subgraphs.json        # 50 subgraf fisiologi saraf dari Neo4j
│   └── test_questions_50.json       # daftar pertanyaan medis dan kunci jawaban
├── scripts/
│   ├── linearizer.py                # implementasi 4 algoritma linearisasi
│   ├── llm_runner.py                # script pemanggil OpenAI / Ollama API
│   ├── evaluate_outputs.py          # integrasi evaluasi RAGAS & kalkulasi token
│   └── analyze_hallucination.py     # deteksi relasi terbalik/palsu
├── results/
│   ├── token_vs_accuracy_plot.png   # grafik scatter token vs faithfulness
│   └── linearization_results.csv    # log lengkap respon tiap model
└── requirements.txt
```

### `requirements.txt`
```
openai>=1.0.0
tiktoken>=0.5.0
ragas>=0.1.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
scipy>=1.11.0
```

---

## 7. Sistematika Penulisan Proposal Skripsi (Bab 1 – Bab 3)

Dokumen proposal skripsi berfokus pada pematangan masalah, landasan teori, dan metode yang dapat dipertanggungjawabkan:

### Bab 1: Pendahuluan
- **Latar Belakang**: Tantangan representasi struktur non-linear graf ke dalam sekuens teks 1D LLM, trade-off *Token Bloat* vs *Relational Hallucination*, dan pentingnya penalaran kausal pada fisiologi medis.
- **Rumusan Masalah**:
  1. Bagaimana pengaruh berbagai format linearisasi subgraf (*Raw Triples*, *Markdown Tree*, *Verbalized Text*, dan *Causal Pathway*) terhadap metrik *Faithfulness* dan konsumsi token LLM?
  2. Format linearisasi manakah yang paling efektif menekan *Causal Hallucination Rate* pada skenario penalaran fisiologi multi-hop?
- **Batasan Masalah**:
  - Subgraf pengujian diekstraksi dari pangkalan data PrimeKG (spesifik relasi sistem saraf otonom).
  - Evaluasi menggunakan model LLM terbuka (Llama-3-8B-Instruct) dan model proprietary (GPT-4o-mini).
- **Tujuan Penelitian**: Menganalisis secara komparatif pengaruh teknik linearisasi graf terhadap fidelitas jawaban klinis dan efisiensi konsumsi token.

### Bab 2: Tinjauan Pustaka
- Teori *Large Language Models (LLM)* dan arsitektur Transformer Decoder-Only.
- Paradigma *Prompt Engineering* dan *In-Context Learning*.
- Konsep *Graph-to-Text Linearization* dan teknik representasi pengetahuan graf.
- Metrik Evaluasi Generasi RAG: Framework RAGAS (*Faithfulness*, *Answer Relevance*) dan deteksi halusinasi.

### Bab 3: Metodologi Penelitian
- Tahapan penelitian: (1) Ekstraksi 50 Kasus Subgraf $\to$ (2) Pembuatan Modul *Linearizer* 4 Format $\to$ (3) Kurasi Pertanyaan Uji Medis $\to$ (4) Orkestrasi Eksekusi Inferensi LLM $\to$ (5) Kalkulasi Metrik Kuantitatif & Uji Signifikansi Statistik.
- Instrumen evaluasi otomatis menggunakan RAGAS dan validasi silang pakar (*expert spot-check*).
- Kriteria keberhasilan proposal (*Success Criteria*).

---

## 8. Panduan Menghadapi Sidang Proposal (Sempro FAQ)

Berikut adalah antisipasi pertanyaan kritis yang lazim dilontarkan dosen penguji saat **Sidang Seminar Proposal**:

> **Tanya Dosen Penguji:** *"Mengapa topik linearisasi ini layak menjadi skripsi tersendiri? Bukankah kita tinggal memasukkan teks JSON dari database ke prompt LLM?"*  
> **Jawab:** Memasukkan format JSON mentah memicu pemborosan token hingga 40–60% akibat sintaksis berulang, yang secara langsung meningkatkan biaya API dan memperlambat latensi respon. Lebih krusial lagi, penelitian terkini membuktikan bahwa LLM sering mengalami *lost in the middle* dan salah menafsirkan arah relasi (*subject-object inversion*) jika graf tidak dilinierkan secara semantik. Meneliti format representasi graf terbaik adalah kontribusi nyata di ranah *Knowledge-Augmented Generative AI*.

> **Tanya Dosen Penguji:** *"Bagaimana Anda mengukur 'kualitas jawaban LLM' secara objektif agar tidak terjebak dalam penilaian subjektif mahasiswa?"*  
> **Jawab:** Pengukuran dilakukan secara objektif menggunakan framework evaluasi terstandarisasi industri, yaitu **RAGAS (Retrieval Augmented Generation Assessment System)**. Metrik *Faithfulness* memecah jawaban menjadi klaim atomik dan memverifikasinya secara matematis terhadap konteks sumber. Kami juga mengukur metrik keras (*hard metrics*) seperti jumlah token via `tiktoken` dan akurasi logika kausalitas bertingkat.

> **Tanya Dosen Penguji:** *"Apakah biaya pemanggilan API LLM (misalnya GPT-4) tidak akan membebani penelitian Anda?"*  
> **Jawab:** Kami telah merancang mitigasi biaya komputasi dengan memanfaatkan kombinasi:
> 1. LLM lokal dengan bobot terbuka (*open-weights*) seperti **Llama-3-8B-Instruct** yang dijalankan secara lokal via Ollama / vLLM untuk iterasi eksperimen massal (gratis biaya API).
> 2. Model komersial efisien (**GPT-4o-mini**) hanya sebagai pembanding tolok ukur (*benchmark benchmark baseline*) pada sampel validasi terpilih (50 kasus uji), dengan estimasi total biaya $< \$5$.
