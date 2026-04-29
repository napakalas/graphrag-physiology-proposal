# Draft Proposal Tugas Akhir S1: Implementasi RAG Berbasis Knowledge Graph pada Domain Fisiologi dan Medis

## Navigasi Dokumen Proyek
- [Detail Proyek Mahasiswa 1: NLP & Entity Linking](proyek_mhs1.md)
- [Detail Proyek Mahasiswa 2: Graph Retrieval](proyek_mhs2.md)
- [Detail Proyek Mahasiswa 3: Prompt Engineering](proyek_mhs3.md)
- [Panduan Eksplorasi Data: Cypher, SPARQL, dan Evaluasi RAGAS](panduan_eksplorasi_data_cypher_sparql_ragas.md)
- [Detail Proyek Mahasiswa 4: QA & Evaluasi RAGAS](proyek_mhs4.md)
- [Detail Proyek Mahasiswa 5: Context & Semantic Caching](proyek_mhs5.md)
- [Panduan Manajemen Waktu & Alur Paralel](alur_kerja_paralel.md)
- [Daftar Lengkap Usulan Judul Skripsi Akademis](judul_skripsi.md)

---

## 1. Latar Belakang & Tujuan
Sistem *Retrieval-Augmented Generation* (RAG) konvensional yang berbasis dokumen teks (*vector search*) seringkali gagal menangkap relasi kompleks atau inferensi logis pada pengetahuan medis dan anatomis. Proyek ini bertujuan untuk mengimplementasikan **GraphRAG**—sebuah RAG yang mengintegrasikan *Knowledge Graph* (KG) dan ontologi—khususnya pada domain fisiologi, sistem saraf (*nerve*), dan medis.

Tujuan utamanya adalah membangun sistem tanya jawab (QA) biomedis yang mampu melakukan *inference* (penyimpulan) informasi multi-hop antar entitas anatomi, penyakit, dan biologi molekuler secara interaktif. Konstruksi proyek ini dibagi menjadi 5 jalur fokus (dikerjakan oleh 5 mahasiswa secara komprehensif dengan pendekatan *microservices/modular*).

### Dokumen Teknis Batch Aktif
Bagian ini dipisahkan dari navigasi inti agar struktur tetap stabil ketika mahasiswa bertambah atau judul riset berubah.

1. Batch aktif jalur Query Expansion:
  - [semantic_query_expansion_graphrag.md](semantic_query_expansion_graphrag.md)
2. Batch aktif jalur Graph Extraction:
  - [graph_extraction_matematika.md](graph_extraction_matematika.md)
3. Batch aktif jalur Prompt Engineering:
  - Belum ada dokumen teknis aktif (slot terbuka)
4. Batch aktif jalur Evaluasi RAGAS:
  - [evaluasi_graphrag_ragas.md](evaluasi_graphrag_ragas.md)
5. Batch aktif jalur Manajemen Konteks Multi-turn:
  - Belum ada dokumen teknis aktif (slot terbuka)

### Kode Program Unt8uk bantuan
- [filter_kg.py](filter_kg.py)
- [import_neo4j.py](import_neo4j.py)

---

## 2. Ketersediaan Knowledge Graph (KG) dan Ontologi di Dalamnya
Untuk mendukung inferensi (*multi-hop reasoning*), sistem akan menggunakan aset KG skala besar yang telah mengintegrasikan berbagai ontologi standar seperti **FMA** (anatomi manusia), **UBERON** (anatomi lintas spesies), **GO** (*Gene Ontology* untuk proses biologis molekuler), dan **ChEBI** (entitas kimia/obat).

1. **PrimeKG (Precision Medicine Knowledge Graph):**
   * **Ontologi yang terintegrasi:** PrimeKG **menggunakan UBERON dan FMA** sekaligus sebagai kerangka utama anatomi. Selain itu, **GO** digunakan untuk jaringan biologis, gen, dan molekuler, sedangkan **ChEBI** digunakan untuk menautkan senyawa/obat-obatan.
   * *Peruntukan:* Sangat cocok sebagai baseline utama untuk inference gabungan obat (ChEBI) -> target biologis (GO) -> penyakit di organ (FMA/UBERON).
2. **UMLS (Unified Medical Language System):**
   * **Ontologi yang terintegrasi:** **FMA, GO, dan ChEBI ada di dalam (ter-include)** sebagai kosokata standar UMLS. Namun, **UBERON secara historis bukan bagian inti langsung dari Metathesaurus UMLS**, melainkan biasanya dipetakan oleh peneliti secara terpisah atau lewat ontologi pihak ketiga (seperti NCI Thesaurus yang ada di UMLS).
   * *Peruntukan:* Digunakan untuk menstandarkan *query* dari bahasa natural (teks *user*) ke format entitas standar (CUI).
3. **Monarch Initiative KG / SPOKE:**
   * **Ontologi yang terintegrasi:** Monarch Initiative **sangat bergantung pada UBERON** sebagai fondasi lintas spesiesnya. Monarch juga mengintegrasikan **FMA, GO, dan ChEBI**, serta HPO (*Human Phenotype Ontology*).
   * *Peruntukan:* Sangat luar biasa jika mahasiswa ingin memodelkan penalaran komparatif (misal: bagaimana data eksperimentasi sistem saraf pada tikus bisa digunakan RAG untuk menjawab pertanyaan medis pada saraf fisiologis manusia).

---

## 3. Pembagian Fokus Proyek & Rumusan Masalah
Agar struktur fleksibel, pembagian berikut berbasis area proyek, bukan dikunci 1 mahasiswa = 1 area secara permanen. Satu area bisa diisi lebih dari satu mahasiswa dengan judul yang berbeda.

### Proyek Mahasiswa 1: Entity Extraction, Query Expansion, dan Disambiguasi (Fokus NLP)
* **Cakupan:** Menangkap teks pertanyaan medis, mengekstrak entitas, melakukan disambiguasi, dan menyiapkan *seed node* untuk retrieval graf.
* **Contoh Rumusan Masalah:**
  1. Bagaimana arsitektur *Hybrid Entity Linking* (kombinasi leksikal UMLS dan model semantik) meningkatkan akurasi pemetaan istilah medis ke entitas standar?
  2. Seberapa besar dampak *semantic query expansion* berbasis LLM terhadap presisi dan *recall* *seed node extraction*?

### Proyek Mahasiswa 2: Retrieval, Traversal, dan Pruning Subgraf (Fokus Algoritma Graf)
* **Cakupan:** Menelusuri graf (Cypher/SPARQL), membangun konteks subgraf, serta mengendalikan *noise* dan batas token untuk LLM.
* **Contoh Rumusan Masalah:**
  1. Bagaimana perbandingan *graph traversal* murni dan *vector-based retrieval* dalam akurasi konteks medis?
  2. Strategi *graph pruning* apa yang paling efektif menjaga kualitas konteks sekaligus efisiensi komputasi?

### Proyek Mahasiswa 3: Prompt Engineering dan Generasi Konteks (Fokus LLM)
* **Status:** Belum ada mahasiswa yang mengambil topik ini pada batch aktif saat ini.
* **Cakupan:** Menyusun strategi prompt, linearisasi subgraf, dan teknik grounding agar jawaban LLM tetap konsisten pada bukti retrieval.
* **Contoh Rumusan Masalah:**
  1. Bagaimana format linearisasi subgraf yang paling efektif untuk meningkatkan ketepatan jawaban LLM pada domain medis?
  2. Bagaimana desain prompt berbasis bukti dapat menurunkan tingkat halusinasi tanpa menurunkan kelengkapan jawaban?

### Proyek Mahasiswa 4: Evaluasi Sistem dan Validasi Klinis (Fokus RAGAS/MLOps)
* **Cakupan:** Menyusun *ground-truth dataset*, evaluasi RAGAS, integrasi *LLM-as-a-Judge*, validasi pakar (*human-in-the-loop*), dan observabilitas.
* **Contoh Rumusan Masalah:**
  1. Bagaimana profil skor *faithfulness*, *answer relevance*, *context precision*, dan *context recall* pada varian pipeline GraphRAG?
  2. Bagaimana korelasi hasil evaluasi otomatis dengan penilaian pakar medis pada skenario klinis nyata?

### Proyek Mahasiswa 5: Memori Konteks & Semantic Caching (Fokus Sistem Percakapan)
* **Status:** Belum ada mahasiswa yang mengambil topik ini pada batch aktif saat ini.
* **Cakupan:** *Coreference resolution*, *conversation memory*, dan caching semantik untuk mengurangi latensi dan menjaga konteks sesi.
* **Contoh Rumusan Masalah:**
  1. Seberapa besar dampak *conversation memory* terhadap kesinambungan QA medis multi-turn?
  2. Berapa pengurangan latensi yang dicapai dari *semantic caching* dibanding arsitektur tanpa cache?

---

## 4. Rangkuman Target Akhir Proyek (*Deliverables*) Berbantuan Moduler
Gabungan dari kelima area di atas menghasilkan 5 pilar sistem GraphRAG terpadu (microservices):
1. **Modul Parameter Query (Proyek 1):** *Entity linking*, disambiguasi, dan query expansion.
2. **Modul Retrieval Subgraf (Proyek 2):** Traversal, pruning, dan penyusunan konteks evidensial.
3. **Modul Prompting dan Grounding (Proyek 3):** Linearization, prompt template, dan kontrol halusinasi.
4. **Modul Evaluasi dan Governance (Proyek 4):** Harness RAGAS, audit klinis, observabilitas, dan validasi pakar.
5. **Modul Memori & Cache (Proyek 5):** Manajemen konteks percakapan dan optimasi latensi.
