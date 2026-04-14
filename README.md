# Draft Proposal Tugas Akhir S1: Implementasi RAG Berbasis Knowledge Graph pada Domain Fisiologi dan Medis

## Navigasi Dokumen Proyek
- [Detail Proyek Mahasiswa 1: NLP & Entity Linking](proyek_mhs1.md)
- [Detail Proyek Mahasiswa 2: Graph Retrieval](proyek_mhs2.md)
- [Detail Proyek Mahasiswa 3: Prompt Engineering](proyek_mhs3.md)
- [Detail Proyek Mahasiswa 4: QA & Evaluasi MLOps](proyek_mhs4.md)
- [Detail Proyek Mahasiswa 5: Context & Semantic Caching](proyek_mhs5.md)
- [Panduan Manajemen Waktu & Alur Paralel](alur_kerja_paralel.md)
- [Daftar Lengkap Usulan Judul Skripsi Akademis](judul_skripsi.md)

---

## 1. Latar Belakang & Tujuan
Sistem *Retrieval-Augmented Generation* (RAG) konvensional yang berbasis dokumen teks (*vector search*) seringkali gagal menangkap relasi kompleks atau inferensi logis pada pengetahuan medis dan anatomis. Proyek ini bertujuan untuk mengimplementasikan **GraphRAG**—sebuah RAG yang mengintegrasikan *Knowledge Graph* (KG) dan ontologi—khususnya pada domain fisiologi, sistem saraf (*nerve*), dan medis. 

Tujuan utamanya adalah membangun sistem tanya jawab (QA) biomedis yang mampu melakukan *inference* (penyimpulan) informasi multi-hop antar entitas anatomi, penyakit, dan biologi molekuler secara interaktif. Konstruksi proyek ini dibagi menjadi 5 jalur fokus (dikerjakan oleh 5 mahasiswa secara komprehensif dengan pendekatan *microservices/modular*).

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

## 3. Pembagian Fokus 5 Mahasiswa & Rumusan Masalah
Agar penelitian S1 tidak sekadar menjadi pembuatan aplikasi, proyek ini dipecah menjadi 5 area eksplorasi spesifik. Masing-masing mahasiswa akan memiliki 1 poin riset mendalam.

### Mahasiswa 1: Entity Extraction & Query Disambiguation (Fokus NLP)
* **Tugas:** Menangkap teks pertanyaan panjang dari dokter/user ("Apa efek molekul X pada nyeri saraf *Nervus Vagus*?"), mendeteksi entitasnya, memecahkan ambiguitas (Semantic Disambiguation), dan melebarkan pencarian (*Query Expansion*) menggunakan NLP AI sebelum menautkannya ke *node* resmi di FMA/UBERON.
* **Rumusan Masalah Penelitian:** 
  1. Bagaimana arsitektur *Hybrid Entity Linking* (kombinasi leksikal UMLS dan pemahaman semantik via BioBERT/SciBERT) mengatasi ambiguitas dan kependekan istilah medis dalam mengekstrak hirarki konsep anatomi dari teks kueri pengguna?
  2. Bagaimana pengaruh mekanisme *Query Expansion* (melatih LLM untuk meramalkan sinonim penyakit khusus saraf) terhadap perbaikan presisi *seed node extraction*?

### Mahasiswa 2: Strategi Retrieval pada Knowledge Graph (Fokus Algoritma Graf)
* **Tugas:** Setelah *node* awal ditemukan di KG (misal Node Saraf Tepi), menelusuri graf tersebut (Cypher query atau SPARQL) sejauh 2-3 lompatan (*hop*) untuk mengambil informasi penyakit dan obat secara matematis tanpa menarik terlalu banyak data *noise*.
* **Rumusan Masalah Penelitian:** 
  1. Bagaimana perbandingan antara metode pencarian subgraf murni (*graph traversal query*) dengan pencarian kemiripan vektor (*vector search*) dalam mengakuisisi konteks fisiologi saraf yang divalidasi presisi-reaksinya (Precision/Recall).
  2. Algoritma pemangkasan graf (*graph pruning*) apa yang paling efisien untuk membatasi pengambilan konteks agar tidak melebihi batasan *token* input memori pada fase generasi?

### Mahasiswa 3: Cross-Domain Inference & Prompt Engineering (Fokus Generasi Teks)
* **Tugas:** Menyusun hasil tarikan KG (berupa struktur *node-edge-node*) menjadi urutan teks logis (*linearization*). Mahasiswa ini meracik rekayasa *Prompt* agar LLM bisa menyimpulkan kaitan lintas ontologi.
* **Rumusan Masalah Penelitian:** 
  1. Bagaimana metode *linearization* (format perubahan struktur subgraf menjadi naratif teks) memengaruhi dan meringankan metrik penyimpangan klaim medis (halusinasi) dari LLM target (seperti LLaMA 3 atau GPT-4)?
  2. Sejauh mana GraphRAG mendemonstrasikan kemampuan *zero-shot inference* menyeberangkan pengetahuan referensi riset penyakit khusus hewan (ontologi UBERON) agar tepat guna sejalan dengan referensi tubuh manusia (ontologi FMA)?

### Mahasiswa 4: Evaluasi End-to-End & Uji Sistem Medis (Fokus Quality Assurance / MLOps)
* **Tugas:** Membuat alat pembuktian. Menyusun *golden dataset* mandiri yang ditarik dari *Textbook* Fisiologi dasar. Kemudian membuktikan kelayakan jawaban GraphRAG ini dengan parameter medis terhadap penilaian otomatis dari pakar medis (*LLM-as-a-Judge* dan *Human-in-the-loop*).
* **Rumusan Masalah Penelitian:** 
  1. Bagaimana tingkat akurasi penalaran sistem *GraphRAG* sistem saraf dapat dievaluasi secara otonom menggunakan kerangka *Retrieval-Augmented Generation Assessment* (seperti metrik RAGAS dan TruLens)?
  2. Bagaimana perbandingan korelasi indeks validitas klinikal yang dikeluarkan oleh *LLM-Evaluator* dibandingkan dengan penilaian manual *rating* keamanan medis dari tenaga ahli di bidang kesehatan?

### Mahasiswa 5: Multi-Turn Memorisation & Semantic Caching (Fokus Sesi Konteks)
* **Tugas:** Mengelola kesinambungan interaksi beruntun (*Context Memory*). Jika *user* berkata "Apa pengobatannya untuk saraf tersebut?", sistem harus otomatis menghubungkan *saraf tersebut* ke riwayat pencarian sebelumnya. Menghemat waktu penelusuran kembali ke Graph Database melalui *Semantic Cache*.
* **Rumusan Masalah Penelitian:** 
  1. Bagaimana pengaruh integrasi arsitektur penalaran *ConversationBufferMemory* dan *Coreference Resolution* terhadap tingkat kesinambungan pencarian konteks medis berturut-turut pada sesi GraphRAG multi-turn?
  2. Berapa laju penghematan *latency* (latensi respons LLM) yang diperoleh memori sistem ketika Graph Query diatur untuk dilewati via penerapan pelacakan *Vector Semantic Caching* dibanding tanpa caching?

---

## 4. Rangkuman Target Akhir Proyek (*Deliverables*) Berbantuan Moduler
Gabungan dari kelima riset di atas menghasilkan 5 pilar sistem GraphRAG terpadu (Microservices):
1. **Modul Pengambil Parameter (Mhs 1):** *NLP Entity Linker* cerdas yang tahan salah ketik medis.
2. **Modul Pengais Informasi (Mhs 2):** Mekanisme *cypher traversal* pada GraphDB secara komputasional tak berlebihan (*pruning* optimal).
3. **Modul Resistor Fakta (Mhs 3):** Mesin peracik Prompt *anti-halusinasi* (Faithful Translator).
4. **Modul Pengawas Mutu (Mhs 4):** Pustaka evalusi keamanan teknikal yang bisa diotorisasi jurnal klinis.
5. **Modul Memori Persisten (Mhs 5):** Layanan penyinggahan (*Caching*) cepat untuk meladeni percakapan tanpa *delay* berlebih dari server utama.
