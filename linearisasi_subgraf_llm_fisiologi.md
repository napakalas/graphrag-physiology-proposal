# Pengaruh Linearisasi Relasi Subgraf terhadap Kualitas Jawaban Large Language Model pada Domain Fisiologi Medis

**Topik Mahasiswa 3 – Generasi Konteks, Graph-to-Text & Prompt Engineering Layer**  
Referensi kurikulum: Tugas Akhir / Skripsi S1 Teknik Informatika  

---

## 1. Gambaran Umum & Motivasi

Dalam sistem **GraphRAG**, setelah subgraf yang relevan berhasil diambil dari pangkalan data graf (Neo4j), terdapat kendala mendasar pada tahapan penyusunan konteks (*Context Assembly*):

> **Problem Mendasar:**  
> Subgraf pengetahuan adalah struktur data non-linear berarah $\mathcal{G} = (\mathcal{V}, \mathcal{E})$, sedangkan *Large Language Model* (LLM berbasis Transformer) menerima masukan berupa barisan token satu dimensi (*1D linear sequence of tokens*).

Oleh karena itu, subgraf harus diubah menjadi representasi teks melalui proses **Linearisasi Subgraf (*Subgraph Linearization*)**.

Metode linearisasi yang buruk dapat menimbulkan masalah:
1. **Beban Token Berlebih (*Token Bloat*)**: Format yang bertele-tele memboroskan jendela konteks (*context window*) serta meningkatkan latensi dan biaya inferensi.
2. **Kehilangan Struktur (*Topological Flattening Loss*)**: Daftar triple mentah (*raw triples*) menghilangkan informasi jalur, sehingga LLM kesulitan merangkai penalaran multi-hop.
3. **Halusinasi Relasional (*Relational Hallucination*)**: Jika hubungan antar simpul ambigu dalam teks linear, LLM cenderung mengaitkan entitas dengan entitas yang salah (*cross-entity attribution error*) atau membalik arah relasi (*subject-object inversion*).

Proyek ini meneliti pengaruh **4 strategi linearisasi subgraf** terhadap akurasi jawaban, *faithfulness*, tingkat halusinasi relasional, dan jumlah token, pada pertanyaan fisiologi sistem saraf otonom. Pengaruh tersebut dibandingkan terhadap **baseline tanpa konteks**, dan diuji pada beberapa tingkat **edge pengecoh (*noise*)** di dalam subgraf.

### Tabel Input → Proses → Output

| Parameter | Keterangan Rinci |
|---|---|
| **Input** | Subgraf dari graf gabungan **FMA** (inervasi dan percabangan saraf) dan **PrimeKG** (anatomi–protein–proses biologis–jalur), berikut pertanyaan uji. |
| **Proses** | Melakukan linearisasi subgraf menggunakan 4 format:<br>1. *Raw Triples (SPO)*.<br>2. *Hierarchical Markdown Tree*.<br>3. *Verbalized Natural Language (Template-based Graph-to-Text)*.<br>4. *Path-Ordered Chain* (usulan).<br>Hasil linearisasi disisipkan ke prompt LLM untuk menjawab pertanyaan. |
| **Output** | Jawaban LLM, skor akurasi dan *faithfulness*, tingkat halusinasi relasional, jumlah token, serta analisis statistik perbandingan format. |
| **Kontribusi Ilmiah** | Bukti empiris mengenai format linearisasi yang paling menjaga ketepatan jawaban dan efisiensi token pada GraphRAG domain fisiologi, termasuk bagaimana pengaruh format berubah ketika subgraf mengandung *noise*. |

---

## 2. Posisi dalam Arsitektur GraphRAG

Mahasiswa 3 berada di lapisan **Context Formatting & Generative Reasoning Layer**. Lapisan ini bertindak sebagai jembatan antara graf hasil retrieval Mahasiswa 2 dan evaluasi Mahasiswa 4.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ARSITEKTUR GENERASI KONTEKS                     │
│                                                                        │
│  [Subgraf dari Mhs 2 / Gold Subgraph: Saraf Vagus, Nodus SA, CHRM2]    │
│                               │                                        │
│                               ▼                                        │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  MAHASISWA 3: SUBGRAPH LINEARIZATION & PROMPT LAYER          │◄─────┘
│  │                                                              │
│  │  Transformasi Topologi ke 4 Format Uji:                      │
│  │  [Subgraf Graf] ──┬──► Format 1: Raw SPO Triples             │
│  │                   ├──► Format 2: Indented Markdown Tree      │
│  │                   ├──► Format 3: Verbalized Text             │
│  │                   └──► Format 4: Path-Ordered Chain          │
│  │                                                              │
│  │  Injeksi ke Prompt Instruksi + System Prompt Medis           │
│  └──────────────────────────────┬───────────────────────────────┘      │
│                                 │ Prompt Kontekstual Lengkap           │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Inference Engine LLM (GPT-4o-mini / Llama-3-8B-Instruct)    │      │
│  └──────────────────────────────┬───────────────────────────────┘      │
│                                 │ Jawaban Final                        │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Mahasiswa 4: Pengujian Metrik RAGAS (QA Layer)              │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

> **Kemandirian dari Mahasiswa 2:** Untuk eksperimen, Mahasiswa 3 menggunakan ***gold subgraph*** yang disusun sendiri untuk setiap pertanyaan (lihat Bagian 5.1). Dengan demikian, kualitas retrieval Mahasiswa 2 tidak memengaruhi hasil, dan yang diukur murni pengaruh format linearisasi. Integrasi dengan retrieval Mahasiswa 2 dilakukan setelah eksperimen inti selesai.

---

## 3. Sumber Data: Graf Gabungan FMA + PrimeKG

PrimeKG tidak memiliki relasi inervasi. Relasi `anatomy_anatomy` di PrimeKG hanya berisi hierarki UBERON (*is_a* / *part_of*). Karena itu, graf penelitian ini disusun dari dua sumber:

| Sumber | Relasi yang Digunakan | Peran |
|---|---|---|
| **FMA** (*Foundational Model of Anatomy*, OWL dari BioPortal) | Relasi persarafan (*nerve supply*) dan percabangan saraf (*branch of*). Nama properti persis mengikuti versi FMA yang diunduh. | Menyediakan edge **saraf → organ/struktur target** (sistem saraf otonom). |
| **PrimeKG** | `anatomy_protein_present`, `protein_protein`, `bioprocess_protein`, `pathway_protein`, `molfunc_protein`, `cellcomp_protein`, serta relasi hierarki `bioprocess_bioprocess`, `pathway_pathway`, `molfunc_molfunc`, `cellcomp_cellcomp`. | Menyediakan konteks fisiologi molekuler: protein yang diekspresikan di struktur anatomi, interaksinya, dan proses/jalur biologis yang melibatkannya. |

**Penautan kedua sumber.** Node anatomi PrimeKG memakai ID UBERON, sedangkan FMA memakai ID FMA. UBERON menyimpan rujukan silang (*cross-reference*, `hasDbXref "FMA:..."`) ke FMA, sehingga node FMA dapat dipetakan ke node anatomi PrimeKG melalui rujukan silang tersebut. Node FMA yang tidak memiliki padanan UBERON tetap disimpan, tetapi tidak terhubung ke data protein.

**Arah relasi.** Edge PrimeKG tidak berarah dan tercatat dua kali (dua arah) di `kg.csv`. Sebelum dipakai, edge dideduplikasi dan diberi **arah kanonik** per tipe relasi:

| Relasi Kanonik | Asal | Arah |
|---|---|---|
| `innervates` | FMA (relasi persarafan, dibalik bila perlu) | saraf → struktur target |
| `branch_of` | FMA | cabang saraf → saraf induk |
| `expresses` | PrimeKG `anatomy_protein_present` | anatomi → protein |
| `participates_in` | PrimeKG `bioprocess_protein`, `pathway_protein` | protein → proses/jalur |
| `interacts_with` | PrimeKG `protein_protein` | mengikuti urutan pada jalur *gold subgraph* |

Arah kanonik ini menjadi acuan saat mendeteksi relasi terbalik (*subject-object inversion*) di jawaban LLM.

**Keterbatasan yang harus dinyatakan:** cakupan relasi persarafan di FMA tidak lengkap untuk semua organ, dan tidak semua struktur FMA memiliki data ekspresi protein di PrimeKG. Pertanyaan uji hanya disusun dari bagian graf yang datanya tersedia.

---

## 4. Landasan Teori & Formulasi Matematis

### 4.1 Formalisasi Transformasi Linearisasi Graf

Diberikan subgraf berarah $\mathcal{G}_{\text{sub}} = (\mathcal{V}_{\text{sub}}, \mathcal{E}_{\text{sub}})$, di mana setiap edge $e = (u, r, v)$ memiliki simpul kepala $u \in \mathcal{V}_{\text{sub}}$, relasi $r \in \mathcal{R}$, dan simpul ekor $v \in \mathcal{V}_{\text{sub}}$.

Fungsi linearisasi $\mathcal{L}$ memetakan graf $\mathcal{G}_{\text{sub}}$ menjadi barisan token teks $T$:

$$\mathcal{L}: \mathcal{G}_{\text{sub}} \longrightarrow T = (t_1, t_2, \dots, t_M)$$

**Syarat kesetaraan informasi:** keempat fungsi linearisasi harus memuat **himpunan edge yang persis sama**. Tidak boleh ada format yang menambahkan informasi di luar graf (misalnya label penjelas seperti "pelepasan kimiawi"). Dengan begitu, perbedaan hasil hanya dapat disebabkan oleh cara penyajian, bukan oleh perbedaan isi.

### 4.2 Empat Strategi Linearisasi yang Dikaji

Seluruh contoh di bawah memakai subgraf ilustratif yang sama (5 edge), dengan simpul awal (*seed*) pertanyaan **Vagus nerve**. Edge pertama berasal dari FMA, sisanya dari PrimeKG. Label di sini hanya ilustrasi; edge sesungguhnya diambil dari data.

#### Strategi A: Raw Triples (SPO Notation)
Menyajikan edge sebagai barisan triple sesuai urutan hasil retrieval, tanpa struktur tambahan:
$$\mathcal{L}_{\text{triples}}(\mathcal{G}) = \big( [u \mid r \mid v] \big)_{(u, r, v) \in \mathcal{E}}$$
*Contoh:*
```
(CHRM2, interacts_with, KCNJ3)
(Vagus nerve, innervates, Sinoatrial node)
(KCNJ3, participates_in, regulation of heart rate)
(Sinoatrial node, expresses, CHRM2)
(CHRM2, participates_in, G protein-coupled acetylcholine receptor signaling pathway)
```

#### Strategi B: Indented Markdown Tree (Hierarchical)
Menyajikan graf sebagai daftar Markdown bersarang, ditelusuri secara *depth-first* dari simpul akar:
```markdown
- Vagus nerve
  - [innervates] -> Sinoatrial node
    - [expresses] -> CHRM2
      - [interacts_with] -> KCNJ3
        - [participates_in] -> regulation of heart rate
      - [participates_in] -> G protein-coupled acetylcholine receptor signaling pathway
```

#### Strategi C: Verbalized Natural Language (Template-based Graph-to-Text)
Mengubah setiap edge menjadi satu kalimat berdasarkan template per relasi:
```
Protein CHRM2 berinteraksi dengan protein KCNJ3. Vagus nerve menginervasi Sinoatrial node. Protein KCNJ3 terlibat dalam regulation of heart rate. Sinoatrial node mengekspresikan protein CHRM2. Protein CHRM2 terlibat dalam G protein-coupled acetylcholine receptor signaling pathway.
```

#### Strategi D: Path-Ordered Chain (Usulan)
Menyusun edge menjadi **rantai jalur** yang dimulai dari simpul *seed* pertanyaan, lalu dari simpul lain sesuai urutan topologis. Setiap edge muncul tepat satu kali. Format ini mempertahankan informasi jalur multi-hop secara eksplisit tanpa menambah informasi:
```
Jalur 1: Vagus nerve --(innervates)--> Sinoatrial node --(expresses)--> CHRM2 --(interacts_with)--> KCNJ3 --(participates_in)--> regulation of heart rate
Jalur 2: CHRM2 --(participates_in)--> G protein-coupled acetylcholine receptor signaling pathway
```

> **Catatan penamaan:** Format ini **tidak** disebut "kausal". Relasi seperti `expresses` dan `interacts_with` tidak menyatakan sebab-akibat, sehingga urutan jalur hanya mencerminkan keterhubungan dalam graf.

### 4.3 Metrik Evaluasi

1. **Akurasi Jawaban (*Answer Entity Recall*)**: Proporsi entitas jawaban acuan $\mathcal{Y}^{*}_{q}$ yang disebut dalam jawaban LLM $\mathcal{A}$:
   $$\text{Acc}_{q} = \frac{|\mathcal{Y}^{*}_{q} \cap \text{Entities}(\mathcal{A})|}{|\mathcal{Y}^{*}_{q}|}$$

2. **Rasio Efisiensi Token (*Token Efficiency Ratio*)**: Rata-rata jumlah edge yang dikomunikasikan per token konteks:
   $$\eta_{\text{token}} = \frac{|\mathcal{E}_{\text{sub}}|}{\text{CountTokens}(\mathcal{L}(\mathcal{G}_{\text{sub}}))}$$
   Token dihitung dengan tokenizer milik masing-masing model (tiktoken untuk GPT-4o-mini, tokenizer Llama untuk Llama-3).

3. **Skor Fidelitas (*Faithfulness* – RAGAS)**: Persentase klaim dalam jawaban $\mathcal{A}$ yang dapat disimpulkan (*entailed*) dari teks konteks $\mathcal{L}(\mathcal{G}_{\text{sub}})$:
   $$\text{Faithfulness} = \frac{|\{c \in \text{Claims}(\mathcal{A}) \mid \mathcal{L}(\mathcal{G}_{\text{sub}}) \models c\}|}{|\text{Claims}(\mathcal{A})|}$$

4. **Tingkat Halusinasi Relasional (*Relational Hallucination Rate*)**: Proporsi klaim relasi dalam jawaban yang tidak ada di *gold subgraph* atau arahnya terbalik:
   $$\mathcal{H}_{\text{rel}} = \frac{|\{c \in \text{RelClaims}(\mathcal{A}) \mid c \notin \mathcal{E}^{*}_{q} \ \lor \ \text{inverted}(c)\}|}{|\text{RelClaims}(\mathcal{A})|}$$
   Prosedur anotasinya dijelaskan di Bagian 6.4.

---

## 5. Implementasi Kode Python

Modul berikut mengimplementasikan ke-4 format linearisasi, penambahan edge pengecoh, dan penghitungan token.

Catatan implementasi:
- *Markdown Tree* dan *Path-Ordered Chain* memanfaatkan **urutan topologis** (algoritma Kahn), sehingga keduanya mengikuti struktur graf, bukan urutan baris hasil query Neo4j (yang bisa acak).
- `tiktoken` adalah tokenizer milik OpenAI. Untuk Llama-3, jumlah token dihitung dengan tokenizer Llama sendiri (misalnya `AutoTokenizer` dari `transformers`), karena hasilnya berbeda.

```python
import random
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple

import tiktoken

Edge = Tuple[str, str, str]  # (simpul kepala, relasi kanonik, simpul ekor)

# Template verbalisasi per relasi kanonik (lihat Bagian 3).
RELATION_TEMPLATES: Dict[str, str] = {
    "innervates": "{h} menginervasi {t}.",
    "branch_of": "{h} merupakan cabang dari {t}.",
    "expresses": "{h} mengekspresikan protein {t}.",
    "interacts_with": "Protein {h} berinteraksi dengan protein {t}.",
    "participates_in": "Protein {h} terlibat dalam {t}.",
}
DEFAULT_TEMPLATE = "{h} memiliki relasi '{r}' dengan {t}."


def topological_order(edges: List[Edge]) -> List[str]:
    """Mengurutkan simpul dari hulu ke hilir (algoritma Kahn).

    Simpul yang berada di dalam siklus ditambahkan di akhir sesuai urutan kemunculannya.
    """
    nodes = list(dict.fromkeys(n for h, _, t in edges for n in (h, t)))
    indegree = {n: 0 for n in nodes}
    children = defaultdict(list)
    for h, _, t in edges:
        children[h].append(t)
        indegree[t] += 1

    queue = deque(n for n in nodes if indegree[n] == 0)
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for child in children[node]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)

    placed = set(order)
    order += [n for n in nodes if n not in placed]
    return order


def add_distractors(gold: List[Edge], candidate_pool: List[Edge],
                    ratio: float, seed: int = 42) -> List[Edge]:
    """Menambahkan edge pengecoh sebanyak ratio × |gold|, lalu mengacak urutan edge.

    candidate_pool sebaiknya berisi edge dari lingkungan 2-hop simpul gold subgraph,
    agar pengecoh relevan secara topik tetapi tidak dibutuhkan untuk menjawab.
    """
    rng = random.Random(seed)
    gold_set = set(gold)
    pool = [e for e in candidate_pool if e not in gold_set]
    k = min(len(pool), round(ratio * len(gold)))
    edges = list(gold) + rng.sample(pool, k)
    rng.shuffle(edges)
    return edges


class SubgraphLinearizer:
    """Mengubah subgraf (daftar edge berarah) menjadi teks dalam 4 format."""

    def __init__(self, tokenizer_model: str = "gpt-4o") -> None:
        try:
            self.encoder = tiktoken.encoding_for_model(tokenizer_model)
        except KeyError:
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    # Strategi A: daftar triple apa adanya (urutan sesuai hasil retrieval)
    def to_raw_triples(self, edges: List[Edge]) -> str:
        lines = ["[Knowledge Graph Triples]:"]
        lines += [f"({h}, {r}, {t})" for h, r, t in edges]
        return "\n".join(lines)

    # Strategi B: pohon bersarang, ditelusuri secara DFS dari simpul akar
    def to_markdown_tree(self, edges: List[Edge]) -> str:
        children = defaultdict(list)
        for h, r, t in edges:
            children[h].append((r, t))

        order = topological_order(edges)
        has_parent = {t for _, _, t in edges}
        roots = [n for n in order if n not in has_parent] or order[:1]

        lines = ["[Hierarchical Graph Structure]:"]
        visited = set()

        def visit(node: str, depth: int) -> None:
            for rel, tgt in children[node]:
                lines.append(f"{'  ' * depth}- [{rel}] -> {tgt}")
                if tgt not in visited:  # cegah perulangan tak hingga pada siklus
                    visited.add(tgt)
                    visit(tgt, depth + 1)

        for root in roots:
            visited.add(root)
            lines.append(f"- {root}")
            visit(root, 1)
        return "\n".join(lines)

    # Strategi C: satu kalimat per edge berdasarkan template relasi
    def to_verbalized_text(self, edges: List[Edge]) -> str:
        sentences = [
            RELATION_TEMPLATES.get(r, DEFAULT_TEMPLATE).format(h=h, r=r.replace("_", " "), t=t)
            for h, r, t in edges
        ]
        return "[Verbalized Physiology Context]:\n" + " ".join(sentences)

    # Strategi D: rantai jalur dari simpul seed, lalu dari simpul lain sesuai urutan topologis.
    # Setiap edge dipakai tepat satu kali.
    def to_path_chain(self, edges: List[Edge], seed: Optional[str] = None) -> str:
        outgoing = defaultdict(deque)
        for h, r, t in edges:
            outgoing[h].append((r, t))

        starts = topological_order(edges)
        if seed in starts:
            starts = [seed] + [n for n in starts if n != seed]

        lines = ["[Path-Ordered Reasoning Chains]:"]
        for start in starts:
            while outgoing[start]:
                node, parts = start, [start]
                while outgoing[node]:
                    rel, tgt = outgoing[node].popleft()
                    parts.append(f"--({rel})--> {tgt}")
                    node = tgt
                lines.append(f"Jalur {len(lines)}: " + " ".join(parts))
        return "\n".join(lines)

    def generate_full_prompt(self, user_question: str, serialized_context: Optional[str]) -> str:
        """serialized_context=None menghasilkan prompt baseline tanpa konteks."""
        instruction = "Anda adalah asisten pakar neurofisiologi medis. "
        if serialized_context is None:
            return f"{instruction}\n\nPertanyaan:\n{user_question}\n\nJawaban:"
        return (
            f"{instruction}"
            "Jawab pertanyaan hanya berdasarkan konteks graf berikut. "
            "Jangan menambahkan relasi yang tidak dinyatakan dalam konteks.\n\n"
            f"Konteks Graf:\n{serialized_context}\n\n"
            f"Pertanyaan:\n{user_question}\n\n"
            "Jawaban:"
        )


if __name__ == "__main__":
    linearizer = SubgraphLinearizer()

    # Gold subgraph ilustratif; urutan sengaja diacak seperti hasil query Neo4j.
    # Edge 'innervates' berasal dari FMA, sisanya dari PrimeKG (relasi kanonik).
    gold_edges = [
        ("CHRM2", "interacts_with", "KCNJ3"),
        ("Vagus nerve", "innervates", "Sinoatrial node"),
        ("KCNJ3", "participates_in", "regulation of heart rate"),
        ("Sinoatrial node", "expresses", "CHRM2"),
        ("CHRM2", "participates_in", "G protein-coupled acetylcholine receptor signaling pathway"),
    ]
    seed_entity = "Vagus nerve"
    question = ("Melalui protein apa persarafan nervus vagus pada nodus sinoatrial "
                "dapat terkait dengan pengaturan denyut jantung?")

    formats = {
        "Raw Triples": linearizer.to_raw_triples(gold_edges),
        "Markdown Tree": linearizer.to_markdown_tree(gold_edges),
        "Verbalized Text": linearizer.to_verbalized_text(gold_edges),
        "Path-Ordered Chain": linearizer.to_path_chain(gold_edges, seed=seed_entity),
    }

    print("=== PERBANDINGAN STRATEGI LINEARISASI SUBGRAF ===\n")
    baseline = linearizer.generate_full_prompt(question, None)
    print(f"Baseline tanpa konteks : {linearizer.count_tokens(baseline)} token\n")
    for name, text_rep in formats.items():
        full_prompt = linearizer.generate_full_prompt(question, text_rep)
        print(f"Format: [{name}]")
        print(f"Jumlah token prompt : {linearizer.count_tokens(full_prompt)}")
        print("Teks representasi:")
        print(text_rep)
        print("-" * 60)
```

---

## 6. Desain Eksperimen & Metrik Evaluasi

### 6.1 Dataset Pertanyaan dan Gold Subgraph

50 pertanyaan fisiologi sistem saraf otonom, dibagi menjadi tiga kategori:

| Kategori | Contoh Pertanyaan | Sumber Edge |
|---|---|---|
| **1. Faktual langsung (1-hop)** | *"Struktur apa saja yang dipersarafi oleh pleksus celiacus?"* | FMA |
| **2. Multi-hop lintas sumber (2–3 hop)** | *"Protein apa yang diekspresikan di nodus sinoatrial dan terlibat dalam pengaturan denyut jantung?"* | FMA + PrimeKG |
| **3. Multi-hop dengan jalur bercabang (3–4 hop)** | *"Proses biologis apa yang melibatkan protein yang diekspresikan di organ yang dipersarafi ganglion stellatum?"* | FMA + PrimeKG |

Untuk setiap pertanyaan, mahasiswa menyusun:
- ***Gold subgraph*** $\mathcal{E}^{*}_{q}$: himpunan edge minimal yang dibutuhkan untuk menjawab, diambil langsung dari graf gabungan FMA + PrimeKG.
- **Entitas jawaban acuan** $\mathcal{Y}^{*}_{q}$ dan jawaban acuan dalam bentuk kalimat.
- **Simpul seed**: entitas yang disebut dalam pertanyaan (dipakai oleh Strategi D).

Pertanyaan dipilih agar jawabannya **bergantung pada fakta di graf** (misalnya nama protein atau proses spesifik), bukan pengetahuan buku teks yang sudah dihafal LLM. Sebagian sampel diperiksa silang oleh pembimbing atau pakar (*expert spot-check*).

### 6.2 Variabel Penelitian

| Variabel | Level |
|---|---|
| **Format linearisasi** (variabel bebas utama) | A. Raw Triples, B. Markdown Tree, C. Verbalized Text, D. Path-Ordered Chain |
| **Tingkat noise** (variabel bebas kedua) | 0× (gold saja), 1× (gold + pengecoh sebanyak \|gold\|), 3× (gold + pengecoh 3 × \|gold\|) |
| **Baseline** | Tanpa konteks (mengukur pengetahuan bawaan LLM) |
| **Model LLM** | GPT-4o-mini, Llama-3-8B-Instruct |

Edge pengecoh diambil dari lingkungan 2-hop simpul gold subgraph (fungsi `add_distractors`), sehingga relevan secara topik tetapi tidak dibutuhkan untuk menjawab.

Total pemanggilan LLM: $50 \text{ pertanyaan} \times (4 \text{ format} \times 3 \text{ noise} + 1 \text{ baseline}) \times 2 \text{ model} = 1.300$ pemanggilan.

**Variabel yang dikontrol:** himpunan edge identik di semua format pada level noise yang sama, template prompt tetap, *temperature* = 0, dan *random seed* tetap untuk pengambilan pengecoh.

### 6.3 Metrik

Akurasi jawaban, *faithfulness* (RAGAS), tingkat halusinasi relasional, dan jumlah token (Bagian 4.3). Versi pustaka `ragas` dikunci di `requirements.txt` karena API-nya sering berubah antar versi.

### 6.4 Prosedur Anotasi Halusinasi Relasional

1. Klaim relasi dalam jawaban diekstraksi menjadi triple (*head, relation, tail*) dengan bantuan LLM-judge.
2. Setiap triple dicocokkan dengan gold subgraph dan diberi label: **benar**, **tidak ada di graf**, atau **arah terbalik**.
3. Mahasiswa memeriksa ulang secara manual minimal 20% sampel berdasarkan rubrik tertulis, lalu melaporkan tingkat kesepakatan (*agreement*) antara LLM-judge dan anotasi manual.

### 6.5 Analisis Statistik

- Perbandingan 4 format pada setiap level noise: **uji Friedman** (data berpasangan per pertanyaan), dilanjutkan **uji Wilcoxon signed-rank** berpasangan dengan **koreksi Holm**.
- Pengaruh noise: membandingkan penurunan akurasi dari 0× ke 3× untuk setiap format.
- Setiap format juga dibandingkan dengan baseline tanpa konteks untuk memastikan bahwa konteks graf memang dipakai oleh LLM.

### 6.6 Hipotesis

> Angka hasil **tidak** dicantumkan sebelum eksperimen dijalankan. Yang dirumuskan di proposal adalah hipotesis.

- **H1:** Format terstruktur (B dan D) menghasilkan akurasi dan *faithfulness* yang lebih tinggi daripada Raw Triples (A) pada pertanyaan multi-hop (kategori 2 dan 3).
- **H2:** Perbedaan antar format makin besar ketika tingkat noise naik.
- **H3:** Verbalized Text (C) memakai token paling banyak, tetapi tidak selalu memberi akurasi paling tinggi.
- **H4:** Semua format berkonteks lebih akurat daripada baseline tanpa konteks. Jika tidak, pertanyaan uji terlalu mudah dijawab dari pengetahuan bawaan LLM dan perlu direvisi.

---

## 7. Struktur Direktori Proyek

```
mhs3_subgraph_linearization/
├── data/
│   ├── fma_innervation_edges.csv    # edge persarafan & percabangan saraf dari FMA
│   ├── uberon_fma_xref.csv          # pemetaan ID FMA ↔ UBERON (anatomi PrimeKG)
│   ├── primekg_subset.csv           # subset relasi PrimeKG (Bagian 3), dideduplikasi & berarah
│   ├── gold_subgraphs.json          # gold subgraph + seed per pertanyaan
│   └── test_questions_50.json       # pertanyaan, entitas jawaban, dan jawaban acuan
├── scripts/
│   ├── build_graph.py               # gabung FMA + PrimeKG, tetapkan arah kanonik
│   ├── linearizer.py                # implementasi 4 strategi linearisasi + pengecoh
│   ├── llm_runner.py                # pemanggil OpenAI API / Ollama
│   ├── evaluate_outputs.py          # RAGAS, akurasi, dan penghitungan token
│   ├── annotate_hallucination.py    # ekstraksi klaim relasi & pencocokan gold subgraph
│   └── stats_tests.py               # uji Friedman, Wilcoxon, koreksi Holm
├── results/
│   ├── linearization_results.csv    # log lengkap respon tiap model & kondisi
│   └── accuracy_vs_noise_plot.png   # grafik akurasi per format terhadap tingkat noise
└── requirements.txt
```

### `requirements.txt`
Kunci versi persis (misalnya hasil `pip freeze`) setelah lingkungan berjalan, terutama `ragas`.
```
openai>=1.0.0
tiktoken>=0.5.0
transformers>=4.40.0
ragas            # kunci ke versi persis yang dipakai
rdflib>=7.0.0
pandas>=2.0.0
matplotlib>=3.7.0
scipy>=1.11.0
```

---

## 8. Sistematika Penulisan Proposal Skripsi (Bab 1 – Bab 3)

Dokumen proposal skripsi berfokus pada pematangan masalah, landasan teori, dan metode yang dapat dipertanggungjawabkan:

### Bab 1: Pendahuluan
- **Latar Belakang**: Tantangan menyajikan struktur graf non-linear sebagai teks untuk LLM, *trade-off* antara jumlah token dan ketepatan penalaran, serta kebutuhan penalaran multi-hop pada fisiologi sistem saraf otonom.
- **Rumusan Masalah**:
  1. Bagaimana pengaruh format linearisasi subgraf (*Raw Triples*, *Markdown Tree*, *Verbalized Text*, dan *Path-Ordered Chain*) terhadap *faithfulness*, akurasi jawaban, dan jumlah token, dibandingkan dengan baseline tanpa konteks?
  2. Apakah pengaruh tersebut berubah ketika ukuran subgraf atau jumlah edge pengecoh bertambah?
- **Batasan Masalah**:
  - Relasi persarafan diambil dari FMA. Relasi fisiologi molekuler diambil dari PrimeKG (anatomi, protein, proses biologis, jalur, fungsi molekuler, komponen seluler). Kedua sumber ditautkan melalui rujukan silang UBERON–FMA.
  - Relasi penyakit dan obat di PrimeKG tidak digunakan.
  - Domain dibatasi pada sistem saraf otonom.
  - Eksperimen memakai *gold subgraph*, bukan hasil retrieval otomatis.
  - Evaluasi menggunakan satu model terbuka (Llama-3-8B-Instruct) dan satu model komersial (GPT-4o-mini).
- **Tujuan Penelitian**: Menganalisis secara komparatif pengaruh format linearisasi graf terhadap ketepatan jawaban dan efisiensi token, serta ketahanannya terhadap *noise* pada subgraf.

### Bab 2: Tinjauan Pustaka
- Teori *Large Language Models (LLM)* dan arsitektur Transformer Decoder-Only.
- Paradigma *Prompt Engineering* dan *In-Context Learning*.
- Konsep *Graph-to-Text Linearization* dan pengodean graf untuk LLM (misalnya Fatemi et al., *"Talk like a Graph: Encoding Graphs for Large Language Models"*, ICLR 2024).
- Pengaruh posisi informasi dalam konteks panjang (Liu et al., *"Lost in the Middle: How Language Models Use Long Contexts"*, TACL 2024).
- Ontologi anatomi FMA dan UBERON, serta knowledge graph PrimeKG.
- Metrik evaluasi RAG: RAGAS (*Faithfulness*, *Answer Relevance*) dan deteksi halusinasi.

### Bab 3: Metodologi Penelitian
- Tahapan penelitian: (1) Pembangunan graf gabungan FMA + PrimeKG $\to$ (2) Penyusunan 50 pertanyaan dan *gold subgraph* $\to$ (3) Pembuatan modul *linearizer* 4 format dan generator pengecoh $\to$ (4) Eksekusi inferensi LLM pada seluruh kondisi $\to$ (5) Evaluasi metrik, anotasi halusinasi, dan uji statistik.
- Instrumen evaluasi otomatis menggunakan RAGAS dan LLM-judge, dengan validasi manual dan *expert spot-check*.
- Kriteria keberhasilan (*success criteria*), misalnya: seluruh 1.300 pemanggilan selesai, kesepakatan anotasi manual dan LLM-judge dilaporkan, dan uji statistik dijalankan untuk kedua rumusan masalah.

---

## 9. Panduan Menghadapi Sidang Proposal (Sempro FAQ)

Berikut adalah antisipasi pertanyaan kritis yang lazim dilontarkan dosen penguji saat **Sidang Seminar Proposal**:

> **Tanya Dosen Penguji:** *"Mengapa topik linearisasi ini layak menjadi skripsi tersendiri? Bukankah kita tinggal memasukkan teks JSON dari database ke prompt LLM?"*  
> **Jawab:** Penelitian sebelumnya menunjukkan bahwa cara graf dikodekan menjadi teks berpengaruh besar terhadap kemampuan LLM menalar atas graf tersebut (Fatemi et al., 2024). Format JSON juga memiliki *overhead* sintaksis (kurung dan kunci berulang) yang menambah jumlah token. Penelitian ini mengukur kedua aspek tersebut secara langsung pada domain fisiologi, termasuk ketika subgraf mengandung *noise*, kondisi yang lazim terjadi pada retrieval sungguhan.

> **Tanya Dosen Penguji:** *"Mengapa tidak memakai PrimeKG saja?"*  
> **Jawab:** PrimeKG tidak memiliki relasi persarafan; relasi anatomi di PrimeKG hanya berupa hierarki *is_a*/*part_of*. FMA menyediakan relasi persarafan dan percabangan saraf untuk anatomi manusia. Keduanya ditautkan melalui rujukan silang UBERON–FMA, sehingga pertanyaan dapat menghubungkan saraf, organ target, dan protein/proses biologis.

> **Tanya Dosen Penguji:** *"Bagaimana Anda tahu LLM benar-benar memakai konteks graf, bukan menjawab dari hafalan?"*  
> **Jawab:** Ada dua mekanisme. Pertama, baseline tanpa konteks: selisih akurasi antara kondisi berkonteks dan baseline menunjukkan kontribusi konteks. Kedua, pertanyaan disusun agar jawabannya bergantung pada fakta spesifik di graf (nama protein atau proses), bukan pengetahuan buku teks.

> **Tanya Dosen Penguji:** *"Bagaimana Anda mengukur 'kualitas jawaban LLM' secara objektif?"*  
> **Jawab:** Akurasi diukur terhadap entitas jawaban acuan pada *gold subgraph*. *Faithfulness* diukur dengan RAGAS, yang memecah jawaban menjadi klaim dan memeriksanya terhadap konteks. Halusinasi relasional dianotasi dengan rubrik tertulis, dibantu LLM-judge, dan divalidasi manual pada sampel. Jumlah token dihitung dengan tokenizer masing-masing model.

> **Tanya Dosen Penguji:** *"Apakah biaya pemanggilan API LLM tidak akan membebani penelitian Anda?"*  
> **Jawab:** Sebagian besar eksperimen dijalankan dengan model terbuka (**Llama-3-8B-Instruct**) secara lokal via Ollama/vLLM, tanpa biaya API. Model komersial **GPT-4o-mini** dipakai sebagai pembanding (*benchmark baseline*) dengan 650 pemanggilan berprompt pendek, sehingga biayanya kecil. Estimasi biaya dihitung dari jumlah token aktual pada uji coba awal.
