# Topik Tugas Akhir Mahasiswa 3: Generasi Teks dan Inferensi Lintas Domain Berbasis Bukti (Faithfulness)

## Deskripsi Singkat
*Large Language Model* tidak bisa mencerna gambar/struktur urat (graf) secara langsung. Mahasiswa 3 bertugas menukar (translasi linierisasi) hasil graf relasional rumit dari Mhs 2 menjadi sebuah cerita instruksi konkrit (Prompt), yang dapat memaksa LLM melakukan penalaran (inferensi) tanpa melakukan halusinasi medis. Fokus ini mencakup transisi pemahaman dari anatomi taksa non-manusia ke manusia.

## Fokus Eksplorasi (Rumusan Masalah)
1. Bagaimana dampak teknik rekayasa prompt berbasis bukti (*Evidence-based Chain-of-Thought Prompting*) terhadap penurunan kadar halusinasi informasi LLM di bidang anatomi saraf?
2. Bagaimana mengeksploitasi kemampuan mesin GraphRAG dalam menyeberangkan pengetahuan referensi riset penyakit model hewan (berbasis The Monarch Initiative - ontologi UBERON) agar diinterpretasikan sejalan dengan referensi anatomi manusia (ontologi FMA)?

## Tautan Sumber Daya (*Resources*) Utama
1. **SPOKE (Scalable Precision Medicine Open Knowledge Engine) & Monarch Initiative:** Penting untuk riset interaksi model hewan/lintas spesies.
   * *Tautan Monarch:* [Monarch Initiative Knowledge Graph](https://monarchinitiative.org/)
   * *Tautan UBERON Ontology:* [UBERON di GitHub](https://github.com/obophenotype/uberon)
   * *Tautan SPOKE:* [SPOKE UCSF](https://spoke.ucsf.edu/)
2. **LangChain / LlamaIndex:** *Framework* terpopuler untuk menghubungkan AI dengan database eksternal.
   * *Tautan:* [LlamaIndex (sangat mendukung GraphRAG)](https://www.llamaindex.ai/)
3. **Ontologi FMA (Human Anatomy):**
   * *Tautan:* [FMA on BioPortal](https://bioportal.bioontology.org/ontologies/FMA)

## Peran dalam Arsitektur Utama
Berada di lapisan belakang (**Generation & Output Tuning**). Mahasiswa meramu Prompt rahasia yang menggabungkan Subgraf relasi dari Mhs 2 + Pertanyaan Awal dari *User*. Sistem Mhs 3 akan mengeluarkan kalimat jawaban kedokteran akhir yang rapi dan memuaskan.

## Usulan Judul Skripsi
1. **Kajian Tingkat Halusinasi Medis (*Faithfulness*) pada *Retrieval-Augmented Generation* Menggunakan Taktik *Evidence-based Prompting***
2. **Pengaruh Linierisasi Relasi Subgraf terhadap Kemampuan Pemahaman *Large Language Model* Terbuka pada Domain Fisiologi Medis**
3. **Eksplorasi Kemampuan Penalaran Lintas Spesies dari UBERON menuju FMA Berbasis *Zero-Shot Inference* pada Sistem GraphRAG**
