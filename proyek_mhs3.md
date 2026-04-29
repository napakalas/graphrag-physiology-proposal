# Topik Tugas Akhir Mahasiswa 3: Prompt Engineering dan Generasi Konteks Berbasis Bukti

## Status Topik
Topik ini **belum ada yang mengambil** pada batch aktif saat ini.

## Deskripsi Singkat
*Large Language Model* tidak dapat membaca struktur graf secara langsung. Proyek ini berfokus pada cara menerjemahkan subgraf hasil retrieval menjadi prompt yang terstruktur, ringkas, dan berbasis bukti agar LLM menghasilkan jawaban yang relevan dengan risiko halusinasi serendah mungkin.

## Fokus Eksplorasi (Rumusan Masalah)
1. Bagaimana strategi linearisasi subgraf memengaruhi kualitas pemahaman LLM pada domain fisiologi dan medis?
2. Bagaimana desain prompt berbasis bukti (*evidence-grounded prompting*) menurunkan halusinasi tanpa mengorbankan kelengkapan jawaban?

## Tautan Sumber Daya (*Resources*) Utama
1. **LangChain / LlamaIndex:** Framework untuk orkestrasi prompt dan komponen RAG.
   * *Tautan:* [LlamaIndex](https://www.llamaindex.ai/)
2. **Prompting Guides (OpenAI/Anthropic):** Referensi praktik baik prompt engineering.
   * *Tautan:* [OpenAI Prompting Guide](https://platform.openai.com/docs/guides/prompt-engineering)
3. **PrimeKG + Neo4j:** Sumber konteks subgraf untuk bahan linearisasi prompt.
   * *Tautan:* [PrimeKG Repository](https://github.com/mims-harvard/PrimeKG)

## Peran dalam Arsitektur Utama
Berada di lapisan generasi (**Generation & Prompt Control**). Proyek ini menerima output subgraf dari retrieval, lalu membentuk prompt final yang dipakai model bahasa untuk menghasilkan jawaban medis yang *faithful* terhadap konteks.

## Usulan Judul Skripsi
1. **Kajian Tingkat Halusinasi Medis (*Faithfulness*) pada *Retrieval-Augmented Generation* Menggunakan Taktik *Evidence-Based Prompting***
2. **Pengaruh Linearisasi Relasi Subgraf terhadap Kualitas Jawaban *Large Language Model* pada Domain Fisiologi Medis**
3. **Optimasi Template Prompt Berbasis Bukti untuk Menjaga Konsistensi Jawaban pada Sistem GraphRAG Medis**
