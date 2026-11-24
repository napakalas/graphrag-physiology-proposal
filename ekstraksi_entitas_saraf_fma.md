# Ekstraksi Entitas Sistem Saraf Otonom Berbasis Ontologi FMA Menggunakan Model Bahasa Alami Terlatih (Pre-trained NLP)

**Topik Mahasiswa 1 – Named Entity Recognition (NER) & Ontologi FMA Layer**  
Referensi kurikulum: Tugas Akhir / Skripsi S1 Teknik Informatika  

---

## 1. Gambaran Umum & Motivasi

Sistem Saraf Otonom (*Autonomic Nervous System* / ANS) adalah bagian dari sistem saraf perifer yang mengatur fungsi visceral involunter tubuh manusia (seperti denyut jantung, motilitas gastrointestinal, vasokonstriksi, dan sekresi kelenjar). Informasi mengenai ANS tersebar luas dalam teks laporan medis, buku ajar neuroanatomi, dan publikasi ilmiah kedokteran dalam format teks bebas tidak terstruktur (*unstructured clinical text*).

Untuk dapat dimasukkan ke dalam arsitektur **GraphRAG**, teks mentah tersebut harus diekstraksi menjadi entitas terstruktur yang patuh pada standar ontologi formal. Ontologi yang paling otoritatif dan terperinci untuk anatomi manusia adalah **Foundational Model of Anatomy (FMA)**.

### Tantangan Ekstraksi Entitas Medis Sistem Saraf
1. **Entitas Bertingkat (*Nested Entities*)**: Contoh frasa *"ganglion servikal superior sistem saraf simpatis"* mengandung entitas organ (*ganglion*), lokasi regional (*servikal superior*), dan divisi fungsional (*sistem saraf simpatis*).
2. **Nomenklatur Campuran (Latin, Inggris, Bahasa Indonesia)**: Penggunaan istilah seperti *"rami communicantes albus"*, *"white communicating ramus"*, dan *"cabang penghubung putih"*.
3. **Keterbatasan Rule-Based Regex**: Pola leksikal manual gagal menangani variasi sintaksis dan ambiguitas konteks kalimat klinis.

Proyek ini membangun dan menganalisis pipeline **Named Entity Recognition (NER)** berbasis model bahasa alami teruji (**BioBERT / PubMedBERT**) yang di-*fine-tune* khusus untuk mengenali entitas ANS, kemudian memetakannya secara otomatis ke kode identifikasi formal **FMA**.

### Tabel Input → Proses → Output

| Komponen | Keterangan |
|---|---|
| **Input** | Teks medis/fisiologi bebas (paragraf patofisiologi saraf otonom). |
| **Proses** | Tokenisasi WordPiece/BPE → Kontekstual Embedding Transformer → Klasifikasi Token (skema BIO) → Ekstraksi Batas Entitas (*Span Boundary*) → Normalisasi ke FMA ID. |
| **Output** | Entitas berlabel `NERVE`, `GANGLION`, `PLEXUS`, atau `ANAT_TARGET` lengkap dengan kode FMA terasosiasi. Label diturunkan dari hierarki *is_a* (subClassOf) FMA (lihat Bagian 3.1). |
| **Manfaat** | Mengotomatisasi kurasi dan populasi Knowledge Graph sistem saraf otonom dari literatur ilmiah tanpa intervensi manual yang lambat. |

---

## 2. Posisi dalam Arsitektur GraphRAG

Pipeline ekstraksi ini berperan sebagai **Information Extraction Ingestion Engine** yang memasok data fakta relasional ke dalam database graf (*Knowledge Graph Construction & Dynamic Knowledge Ingestion*).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ALUR EKSTRAKSI PENGETAHUAN                      │
│                                                                        │
│  [Artikel / Teks: "Nervus vagus melepaskan asetilkolin ke nodus SA..."]│
│                              │                                         │
│                              ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  MAHASISWA 1 (NER LAYER - PRE-TRAINED BIOBERT + FMA)         │◄─────┘
│  │                                                              │
│  │  - NER Token Classifier:                                     │
│  │    [Nervus vagus]        -> B-NERVE, I-NERVE                 │
│  │    [asetilkolin]         -> O (bukan entitas anatomi FMA)    │
│  │    [nodus SA]            -> B-ANAT_TARGET, I-ANAT_TARGET     │
│  │                                                              │
│  │  - Ontological Mapping:                                      │
│  │    "Nervus vagus" -> FMA:5731                                │
│  │    "Nodus SA"     -> FMA:9477                                │
│  └──────────────────────────────┬───────────────────────────────┘      │
│                                 │ Entitas Terekstraksi & FMA ID        │
│                                 ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  Pembangunan Triple Relasi (Graph Ingestion ke Neo4j):       │      │
│  │  (:Anatomy {fma: 5731})-[:INNERVATES]->(:Target {fma: 9477}) │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Landasan Teori & Formulasi Matematis

### 3.1 Skema Anotasi BIO (Begin-Inside-Outside)

Diberikan sekuens token kalimat $X = (x_1, x_2, \dots, x_T)$. Setiap token $x_t$ dipetakan ke sebuah label $y_t \in \mathcal{Y}$ dari himpunan label diskrit:

$$\mathcal{Y} = \{\text{O}\} \cup \{\text{B-}C, \text{I-}C \mid C \in \mathcal{C}\}$$

Himpunan kelas target $\mathcal{C}$ **tidak dibuat sendiri**, melainkan diturunkan dari hierarki *is_a* (rdfs:subClassOf berantai) FMA. Setiap kelas dikaitkan dengan satu atau lebih **kelas jangkar** (*anchor class*) di FMA:

| Label | Kelas Jangkar FMA | Contoh (rantai *is_a*) |
|---|---|---|
| `GANGLION` | *Ganglion* (FMA:5884) | *Celiac ganglion* (FMA:77570) → *Collateral ganglion* → *Sympathetic ganglion* → *Autonomic ganglion* → *Ganglion* |
| `PLEXUS` | *Nerve plexus* (FMA:5901) | *Cardiac nerve plexus* (FMA:6628) → *Autonomic nerve plexus* → *Nerve plexus* |
| `NERVE` | *Neural tree organ* (FMA:61284) **dan** *Nerve* (FMA:65132) | *Vagus nerve* (FMA:5731) → *Cranial nerve* → *Neural tree organ*; *Cardiac branch of vagus nerve* → *Branch of vagus nerve* → *Nerve* |
| `ANAT_TARGET` | Struktur anatomi lain yang tidak berada di bawah ketiga jangkar di atas | *Sinuatrial node* (FMA:9477) → *Conducting system node* → *Conducting tissue of heart* → *Cardiac muscle tissue* |

**Aturan pelabelan:**
1. Label sebuah konsep FMA ditentukan dari himpunan leluhur *is_a*-nya (*transitive closure* subClassOf).
2. Jika leluhurnya memuat lebih dari satu jangkar (pewarisan ganda), dipakai urutan prioritas `GANGLION` > `PLEXUS` > `NERVE` > `ANAT_TARGET`.
3. `NERVE` membutuhkan dua jangkar karena keunikan pemodelan FMA: saraf yang bernama (misalnya *Vagus nerve*, *Greater splanchnic nerve*) berada di bawah *Neural tree organ*, sedangkan cabang saraf berada di bawah *Nerve*. Jangkar yang lebih umum, *Segment of neural tree organ*, **tidak** dipakai karena juga mencakup *Ganglion*.
4. Untuk korpus ini, `ANAT_TARGET` dibatasi pada struktur yang dipersarafi sistem saraf otonom (organ, bagian organ, jaringan, otot polos/jantung, kelenjar), sesuai *annotation guidelines*.

**Mengapa tidak memakai label `EFFECTOR`?** FMA hanya memodelkan **struktur**, bukan **fungsi**. Status "efektor" adalah peran fungsional, yaitu struktur yang menjadi target relasi persarafan (*nerve supply*), sehingga tidak dapat diturunkan dari *is_a*. Peran tersebut diambil dari relasi FMA saat graf dibangun, bukan dari label NER. Dengan alasan yang sama, kategori fungsional seperti aksi fisiologis atau neurotransmiter tidak termasuk cakupan NER berbasis FMA ini.

**Konsekuensi:** tipe entitas hasil NER dapat dicek konsistensinya dengan tipe yang diturunkan dari ID FMA hasil normalisasi. Ketidakcocokan menandakan kesalahan pada salah satu tahap (lihat kode di Bagian 4). Kamus label FMA juga dapat dipakai untuk pra-anotasi otomatis (*dictionary-based pre-annotation*) yang kemudian dikoreksi anotator, sehingga proses anotasi lebih cepat.

### 3.2 Arsitektur Transformer Token Classification

Model Transformer (BioBERT/PubMedBERT) memproses token masukan $X$ dan menghasilkan vektor hidden representation $\mathbf{h}_t \in \mathbb{R}^H$ untuk setiap token $t$:

$$\mathbf{H} = \text{Encoder}(x_1, x_2, \dots, x_T) = [\mathbf{h}_1, \mathbf{h}_2, \dots, \mathbf{h}_T]$$

Vektor representasi dilewatkan ke linear projection layer diikuti fungsi aktivasi softmax untuk memperoleh probabilitas distribusi kelas:

$$P(y_t = c \mid x_t) = \text{Softmax}(\mathbf{W}_c \mathbf{h}_t + \mathbf{b}_c) = \frac{\exp(\mathbf{W}_c \mathbf{h}_t + b_c)}{\sum_{k \in \mathcal{Y}} \exp(\mathbf{W}_k \mathbf{h}_t + b_k)}$$

Fungsi kerugian (*Loss Function*) pelatihan menggunakan *Cross-Entropy Loss* bertingkat sekuens:

$$\mathcal{L}_{\text{CE}}(\theta) = -\sum_{i=1}^{N} \sum_{t=1}^{T_i} \log P(y_{i,t} = y_{i,t}^* \mid X_i; \theta)$$

Di mana $y_{i,t}^*$ adalah label *ground truth* token ke-$t$ pada kalimat ke-$i$.

### 3.3 Normalisasi Entitas ke Ontologi FMA (FMA Entity Normalization)

Setelah span teks entitas $E = x_{i \dots j}$ berhasil diekstrak, dilakukan pemetaan ke ID FMA menggunakan jarak kemiripan leksiko-semantik terbobot:

$$\hat{e}_{\text{FMA}} = \arg\max_{f \in \mathcal{F}_{\text{ANS}}} \left[ \beta \cdot \text{JaroWinkler}(E, \text{Label}(f)) + (1 - \beta) \cdot \cos(\mathbf{v}_E, \mathbf{v}_f) \right]$$

Di mana $\mathcal{F}_{\text{ANS}}$ adalah himpunan konsep anatomi sistem saraf otonom dalam basis data FMA.

---

## 4. Implementasi Kode Python

Berikut adalah modul inferensi *token classification* berbasis Hugging Face Transformers dan PyTorch, beserta normalisasi entitas ke FMA. Kode pelatihan (*fine-tuning*) disusun terpisah memakai `Trainer` dari Transformers pada korpus beranotasi BIO.

```python
from typing import Any, Dict, List, Set

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer

# ---------------------------------------------------------------------------
# Label NER diturunkan dari kelas jangkar FMA (lihat Bagian 3.1).
# Urutan dict = urutan prioritas bila leluhur memuat lebih dari satu jangkar.
# ---------------------------------------------------------------------------
FMA_LABEL_ANCHORS: Dict[str, Set[str]] = {
    "GANGLION": {"FMA:5884"},              # Ganglion
    "PLEXUS": {"FMA:5901"},                # Nerve plexus
    "NERVE": {"FMA:61284", "FMA:65132"},   # Neural tree organ (saraf bernama), Nerve (cabang saraf)
}
DEFAULT_LABEL = "ANAT_TARGET"

ENTITY_CLASSES = list(FMA_LABEL_ANCHORS) + [DEFAULT_LABEL]
LABEL_LIST = ["O"] + [f"{prefix}-{c}" for c in ENTITY_CLASSES for prefix in ("B", "I")]


def derive_label(ancestor_ids: Set[str]) -> str:
    """Menentukan label NER dari himpunan leluhur is_a sebuah konsep FMA."""
    for label, anchors in FMA_LABEL_ANCHORS.items():
        if ancestor_ids & anchors:
            return label
    return DEFAULT_LABEL


def fma_ancestors(graph, fma_id: str, base: str = "http://purl.org/sig/ont/fma/fma") -> Set[str]:
    """Leluhur is_a (rdfs:subClassOf transitif) sebuah konsep FMA.

    graph: rdflib.Graph hasil parsing berkas OWL FMA, cukup di-parse SEKALI
    (berkasnya besar), misalnya: graph = rdflib.Graph().parse("fma.owl").
    Dipakai saat membangun data/fma_ans_ontology.json. Pola IRI berbeda antar
    distribusi FMA (BioPortal/OLS: http://purl.org/sig/ont/fma/fma5731,
    OBO: http://purl.obolibrary.org/obo/FMA_5731); sesuaikan `base`.
    Hanya kelas bernama yang diambil; restriksi OWL (blank node) diabaikan.
    """
    from rdflib import URIRef
    from rdflib.namespace import RDFS

    start = URIRef(base + fma_id.split(":")[1])
    return {
        "FMA:" + str(node)[len(base):]
        for node in graph.transitive_objects(start, RDFS.subClassOf)
        if isinstance(node, URIRef) and str(node).startswith(base) and node != start
    }


# Mock kamus FMA: ID dan label resmi sudah dicek di EBI OLS. Perhatikan ejaan label FMA,
# misalnya "Sinuatrial node" dan "Cardiac nerve plexus". Kolom "ancestors" hanya memuat
# leluhur yang relevan untuk penurunan label; versi lengkapnya dihasilkan fma_ancestors().
FMA_KB: Dict[str, Dict[str, Any]] = {
    "vagus nerve": {"fma_id": "FMA:5731", "preferred_term": "Vagus nerve",
                    "ancestors": {"FMA:5865", "FMA:61284"}},
    "greater splanchnic nerve": {"fma_id": "FMA:6281", "preferred_term": "Greater splanchnic nerve",
                                 "ancestors": {"FMA:5866", "FMA:61284"}},
    "celiac ganglion": {"fma_id": "FMA:77570", "preferred_term": "Celiac ganglion",
                        "ancestors": {"FMA:5884"}},
    "stellate ganglion": {"fma_id": "FMA:6469", "preferred_term": "Cervicothoracic ganglion",
                          "ancestors": {"FMA:5884"}},
    "cardiac plexus": {"fma_id": "FMA:6628", "preferred_term": "Cardiac nerve plexus",
                       "ancestors": {"FMA:5901"}},
    "sinoatrial node": {"fma_id": "FMA:9477", "preferred_term": "Sinuatrial node",
                        "ancestors": {"FMA:321959", "FMA:14068"}},  # Conducting system node, Cardiac muscle tissue
}


class ANSNeuralExtractor:
    """NER entitas sistem saraf otonom (skema BIO) + normalisasi ke ID FMA."""

    def __init__(self, model_checkpoint: str = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract") -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[ANS-Extractor] Initializing model on device: {self.device}")

        self.id2label = {i: label for i, label in enumerate(LABEL_LIST)}
        self.label2id = {label: i for i, label in enumerate(LABEL_LIST)}

        # Catatan: kepala klasifikasi token masih acak sampai model di-fine-tune
        # pada korpus beranotasi BIO; sebelum itu hasil predict_entities tidak bermakna.
        self.tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
        self.model = AutoModelForTokenClassification.from_pretrained(
            model_checkpoint,
            num_labels=len(LABEL_LIST),
            id2label=self.id2label,
            label2id=self.label2id,
        ).to(self.device)

    def predict_entities(self, text: str) -> List[Dict[str, Any]]:
        """Mengubah prediksi label per token menjadi span entitas (start/end karakter)."""
        self.model.eval()
        inputs = self.tokenizer(
            text,
            return_offsets_mapping=True,
            return_tensors="pt",
            truncation=True,
            max_length=128,
        )
        offset_mapping = inputs.pop("offset_mapping")[0].tolist()
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self.model(**inputs).logits
        predictions = torch.argmax(logits, dim=-1)[0].tolist()

        entities: List[Dict[str, Any]] = []
        current = None

        for (start_char, end_char), label_id in zip(offset_mapping, predictions):
            if start_char == end_char:  # token khusus [CLS], [SEP], [PAD]
                continue

            label = self.id2label[label_id]

            if label.startswith("B-"):
                if current:
                    entities.append(current)
                current = {"label": label[2:], "start": start_char, "end": end_char}
            elif label.startswith("I-") and current and label[2:] == current["label"]:
                current["end"] = end_char  # perpanjang span entitas yang sedang berjalan
            else:
                if current:
                    entities.append(current)
                current = None

        if current:
            entities.append(current)

        for ent in entities:
            ent["text"] = text[ent["start"]:ent["end"]]
        return entities

    @staticmethod
    def map_to_fma_ontology(entity_text: str, ner_label: str) -> Dict[str, Any]:
        """Normalisasi entitas ke FMA (pencocokan persis, mock) + cek konsistensi label.

        Implementasi sebenarnya memakai skor gabungan Jaro-Winkler + kemiripan
        kosinus embedding terhadap seluruh konsep FMA (lihat rumus di Bagian 3.3).
        """
        matched = FMA_KB.get(entity_text.lower().strip())
        if matched is None:
            return {"entity": entity_text, "ner_label": ner_label, "fma_id": "FMA:UNKNOWN",
                    "fma_preferred": None, "fma_label": None, "consistent": None}

        fma_label = derive_label(matched["ancestors"])
        return {
            "entity": entity_text,
            "ner_label": ner_label,
            "fma_id": matched["fma_id"],
            "fma_preferred": matched["preferred_term"],
            "fma_label": fma_label,
            "consistent": fma_label == ner_label,  # False = salah tipe di NER atau salah tautan FMA
        }


if __name__ == "__main__":
    sample_clinical_text = (
        "Stimulation of the vagus nerve releases neurotransmitters onto the sinoatrial node, "
        "modulating cardiac output via the cardiac plexus and celiac ganglion pathways."
    )
    print(f"\n[Raw Text Input]:\n{sample_clinical_text}\n")

    # Hasil NER disimulasikan karena model belum di-fine-tune.
    # Setelah fine-tuning: mentions = ANSNeuralExtractor().predict_entities(sample_clinical_text)
    # Entri terakhir sengaja salah tipe untuk menunjukkan cek konsistensi.
    simulated_mentions = [
        {"text": "vagus nerve", "label": "NERVE"},
        {"text": "sinoatrial node", "label": "ANAT_TARGET"},
        {"text": "cardiac plexus", "label": "PLEXUS"},
        {"text": "celiac ganglion", "label": "NERVE"},
    ]

    print("[Extracted Entities & FMA Ontology Normalization]:")
    for m in simulated_mentions:
        r = ANSNeuralExtractor.map_to_fma_ontology(m["text"], m["label"])
        flag = "OK" if r["consistent"] else f"TIDAK KONSISTEN (FMA: {r['fma_label']})"
        print(f"  [{r['ner_label']:<11}] '{r['entity']}' -> {r['fma_id']} ({r['fma_preferred']})  {flag}")
```

---

## 5. Desain Eksperimen & Metrik Evaluasi

### 5.1 Korpus Data Anotasi
Untuk tugas akhir S1, data anotasi dapat dikurasi dari buku teks kedokteran terbuka (*Guyton & Hall Physiology*, *Gray's Anatomy Chapter on Autonomic Nervous System*) dan abstrak PubMed bertema *autonomic neuropathy*.
- Total kalimat anotasi: 600–800 kalimat.
- Pembagian data: 70% Train, 15% Validation, 15% Test.

### 5.2 Metrik Pengukuran (Per-Class & Overall)

1. **Precision (P)**:
   $$P = \frac{TP}{TP + FP}$$
2. **Recall (R)**:
   $$R = \frac{TP}{TP + FN}$$
3. **F1-Score**:
   $$F_1 = 2 \cdot \frac{P \cdot R}{P + R}$$
4. **Strict vs Relaxed Matching**:
   - *Strict Matching*: Batas span token dan kelas entitas harus tepat sama persis.
   - *Relaxed Matching*: Terjadi tumpang tindih (*overlap*) minimal 1 token dan kelas entitas sama.

### 5.3 Desain Perbandingan Model (Ablation Study)

> Angka hasil **tidak** dicantumkan sebelum eksperimen dijalankan. Yang dirumuskan di proposal adalah model pembanding, protokol, dan hipotesis.

**Model yang dibandingkan:**

| Model | Peran |
|---|---|
| Rule-based: spaCy EntityRuler dengan kamus label dan sinonim FMA | Baseline tanpa pembelajaran; memanfaatkan kamus yang sama dengan penurunan label (Bagian 3.1) |
| BERT-base (domain umum) | Pembanding tanpa adaptasi domain |
| SciBERT (domain sains) | Pembanding adaptasi domain sebagian |
| PubMedBERT (domain biomedis) | Model utama |
| BioBERT + lapisan CRF | Menguji pengaruh CRF terhadap konsistensi batas span |

**Protokol:**
- Semua model memakai pembagian data yang sama (70/15/15) dan *hyperparameter* dipilih pada data validasi.
- Setiap model di-*fine-tune* minimal 3 kali dengan *random seed* berbeda; dilaporkan rata-rata ± simpangan baku.
- Metrik: Precision, Recall, F1 (*strict* dan *relaxed*), keseluruhan dan per kelas, dihitung dengan `seqeval`.
- Perbedaan antar model diuji dengan *paired bootstrap resampling* pada data uji.
- Normalisasi FMA dievaluasi terpisah: akurasi ID FMA (Top-1 / Top-5) dan tingkat konsistensi label NER vs. label turunan FMA.

**Hipotesis:**
- **H1:** Model biomedis (PubMedBERT, BioBERT) menghasilkan F1 *strict* lebih tinggi daripada BERT-base dan baseline rule-based.
- **H2:** Selisih antar model lebih besar pada pencocokan *strict* daripada *relaxed*, karena kesulitan utama ada pada batas span entitas bertingkat.
- **H3:** Lapisan CRF memberi peningkatan kecil, terutama pada konsistensi transisi label B/I.
- **H4:** Kelas `ANAT_TARGET` memiliki F1 terendah karena isinya paling heterogen (organ, jaringan, otot, kelenjar).

---

## 6. Struktur Direktori Proyek

```
mhs1_ans_ner_fma/
├── data/
│   ├── raw_text_corpus/             # teks bab sistem saraf otonom
│   ├── annotated_ner_conll.txt      # format CoNLL-2003 (token BIO)
│   ├── fma_ans_ontology.json        # kamus istilah, sinonim, dan leluhur is_a FMA
│   └── fma_label_anchors.json       # pemetaan kelas jangkar FMA -> label NER
├── models/
│   └── fine_tuned_pubmedbert_ans/   # checkpoint model PyTorch
├── scripts/
│   ├── convert_annotations.py       # script konversi format Doccano ke CoNLL
│   ├── train_ner.py                 # script training Transformer + CrossEntropy (multi-seed)
│   ├── evaluate_ner.py              # script kalkulasi seqeval classification report
│   ├── fma_normalizer.py            # modul pemetaan entitas ke ID FMA
│   └── derive_labels.py             # penurunan label dari hierarki is_a FMA (rdflib)
├── results/
│   ├── confusion_matrix.png         # heatmap kebingungan antar kelas
│   └── per_class_metrics.csv        # skor presisi/recall per entitas
└── requirements.txt
```

### `requirements.txt`
```
torch>=2.0.0
transformers>=4.30.0
datasets>=2.14.0
seqeval>=1.2.2
accelerate>=0.20.0
scikit-learn>=1.3.0
pandas>=2.0.0
rdflib>=7.0.0
```

---

## 7. Sistematika Penulisan Proposal Skripsi (Bab 1 – Bab 3)

Dokumen proposal skripsi berfokus pada pematangan masalah, landasan teori, dan metode yang dapat dipertanggungjawabkan:

### Bab 1: Pendahuluan
- **Latar Belakang**: Kebutuhan ekstraksi otomatis pengetahuan anatomi saraf otonom (ANS) dari literatur teks bebas untuk pembangunan Knowledge Graph, serta keterbatasan pendekatan *rule-based* regex konvensional.
- **Rumusan Masalah**:
  1. Bagaimana merancang skema anotasi token dan melatih model Transformer (*PubMedBERT / BioBERT*) untuk mengenali entitas bertingkat pada sistem saraf otonom?
  2. Bagaimana memetakan span entitas teks terekstraksi ke dalam kode ontologi formal *Foundational Model of Anatomy (FMA)* secara akurat?
- **Batasan Masalah**:
  - Ruang lingkup entitas difokuskan pada 4 kelas yang diturunkan dari kelas jangkar FMA: `NERVE`, `GANGLION`, `PLEXUS`, dan `ANAT_TARGET`.
  - Entitas fungsional (neurotransmiter, aksi fisiologis) tidak termasuk cakupan.
  - Korpus teks bersumber dari teks ajar fisiologi terbuka (*open-source neuroanatomy chapters*) dan abstrak PubMed.
- **Tujuan Penelitian**: Menghasilkan model ekstraktor entitas sistem saraf otonom dengan label berbasis FMA, membandingkannya secara empiris dengan baseline, dan membangun pipeline normalisasi FMA otomatis. Target kinerja (misalnya F1 *strict*) ditetapkan bersama pembimbing berdasarkan hasil penelitian NER biomedis terdahulu.

### Bab 2: Tinjauan Pustaka
- Teori *Information Extraction* & *Named Entity Recognition (NER)* biomedis.
- Konsep dasar dan struktur ontologi *Foundational Model of Anatomy (FMA)*.
- Arsitektur Transformer, mekanisme *Self-Attention*, dan tokenisasi WordPiece/BPE pada korpus biomedis.
- Perbandingan model pre-trained: BERT umum vs SciBERT vs BioBERT/PubMedBERT.
- Evaluasi sekuens label dengan skema BIO dan metrik *SeqEval*.

### Bab 3: Metodologi Penelitian
- Tahapan penelitian: (1) Pengumpulan Korpus $\to$ (2) Penyusunan *Annotation Guidelines* $\to$ (3) Anotasi Data format CoNLL $\to$ (4) Fine-tuning Model $\to$ (5) Integrasi Modul Pemetaan FMA $\to$ (6) Evaluasi Kinerja.
- Strategi penanganan ketidakseimbangan kelas (*class imbalance*) dan *subword token alignment*.
- Kriteria keberhasilan penelitian (*Success Criteria*).

---

## 8. Panduan Menghadapi Sidang Proposal (Sempro FAQ)

Berikut adalah antisipasi pertanyaan kritis yang lazim dilontarkan dosen penguji saat **Sidang Seminar Proposal**:

> **Tanya Dosen Penguji:** *"Mengapa Anda memilih ontologi FMA (*Foundational Model of Anatomy*) daripada ontologi UBERON atau SNOMED-CT?"*  
> **Jawab:** UBERON dirancang untuk perbandingan lintas spesies (*cross-species*), sehingga detail divisi anatomi spesifik manusia disederhanakan. Sedangkan SNOMED-CT berfokus pada istilah billing rumah sakit dan prosedur klinis. FMA adalah satu-satunya ontologi referensi anatomi manusia murni yang memodelkan relasi struktural secara ketat: hierarki *is_a* dan *part_of*, percabangan saraf (*branch of*), serta persarafan organ (*nerve supply*). Hierarki *is_a* FMA bahkan dipakai langsung untuk menurunkan label NER.

> **Tanya Dosen Penguji:** *"Mengapa label entitas diturunkan dari hierarki FMA, bukan dirancang sendiri?"*  
> **Jawab:** Label yang dirancang sendiri sulit dipertanggungjawabkan dan sering tidak konsisten dengan ontologi tujuan normalisasi. Dengan menurunkan label dari kelas jangkar FMA (*Ganglion*, *Nerve plexus*, *Neural tree organ*/*Nerve*), definisi setiap label bisa dirujuk ke ontologi, tipe entitas hasil NER bisa dicek terhadap ID FMA hasil normalisasi, dan kamus FMA bisa dipakai untuk pra-anotasi. Kategori fungsional seperti "efektor" sengaja tidak dijadikan label karena FMA hanya memodelkan struktur; peran efektor diambil dari relasi persarafan FMA.

> **Tanya Dosen Penguji:** *"Proses anotasi data secara manual sering memakan waktu lama dan rentan bias. Bagaimana Anda menjamin kualitas dan reliabilitas dataset yang Anda buat?"*  
> **Jawab:** Untuk menjamin reliabilitas data anotasi, kami menyusun *Annotation Guidelines* formal berbasis definisi eksplisit FMA sebelum melabeli data. Anotasi dilakukan menggunakan platform terstandar (Doccano/Label Studio). Selain itu, untuk mengukur konsistensi pelabelan, kami menghitung metrik kesepakatan *Inter-Annotator Agreement* menggunakan koefisien **Cohen's Kappa ($\kappa \ge 0.75$)** pada subset data uji silang.

> **Tanya Dosen Penguji:** *"Apa kontribusi ilmiah Anda dalam proposal ini jika Anda hanya melakukan fine-tuning pada model PubMedBERT yang sudah ada?"*  
> **Jawab:** Kontribusi ilmiah penelitian ini bukan pada pembuatan arsitektur Transformer dari nol, melainkan pada:
> 1. Formulasi skema anotasi domain-spesifik pertama untuk relasi struktural sistem saraf otonom berbasis FMA.
> 2. Analisis komparatif empiris pengaruh adaptasi domain korpus medis terhadap penanganan entitas anatomi bertingkat (*nested anatomy entities*).
> 3. Pembangunan jembatan normalisasi otomatis dari span teks hasil prediksi model menuju graf ontologi formal yang siap diimpor ke Neo4j.
