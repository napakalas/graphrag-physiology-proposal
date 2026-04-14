# Topik Tugas Akhir Mahasiswa 4: Standardisasi Uji Kelayakan Klinis dan Pembuatan Dataset Referensi (Ground Truth)

## Deskripsi Singkat
Sebuah asisten dokter (bot medis) tidak akan pernah digunakan institusi medis jika keselamatannya (Safety) tidak terkalibrasi secara saintifik. Riset dari Mhs 1, 2, dan 3 bersifat komputasional murni. Mahasiswa 4 harus menginjakkan kaki pada sisi biologi/klinikal. Tugas utamanya adalah menilai aplikasi dari teman-temannya layaknya memeriksa obat yang akan lolos sertifikasi: membuat *dataset* standar, melatih parameter pengujian, dan menvalidasi jawaban terhadap pakar medis.

## Fokus Eksplorasi (Rumusan Masalah)
1. Bagaimana mengotomatisasi penilaian tingkat rasio faktualitas konteks fisiologi (*Context Relevance*) pada sistem GraphRAG dengan memakai *dataset baseline* dari buku teks akademis.
2. Bagaimana perbandingan korelasi hasil skor evaluasi kecerdasan buatan (*Evaluator LLMs as a Judge*) dibandingkan dengan parameter validasi manual oleh tenaga pakar biomedik untuk mendeteksi potensi keliruan diagnosis?

## Tautan Sumber Daya (*Resources*) Utama
1. **RAGAS (RAG Assessment):** Pustaka populer berprinsip LLM-as-a-Judge untuk menguji kualitas Retrieval dan Generasi.
   * *Tautan:* [RAGAS Documentation](https://docs.ragas.io/en/stable/)
2. **TruLens:** Alat observabilitas untuk mengevaluasi proyek RAG.
   * *Tautan:* [TruLens Evaluation](https://www.trulens.org/)
3. **Medical Benchmarking Datasets (Opsional sebagai referensi bentuk soal uji):**
   * *Tautan:* [MedQA (USMLE Medical Questions)](https://github.com/jind11/MedQA)

## Peran dalam Arsitektur Utama
Berada di lapisan independen pengawas mutu (**Quality Assurance & MLOps**). Mahasiswa mendesain metrik saintifik sebagai bahan ujian skripsi teman-temannya. Ia membuktikan bahwa GraphRAG ini bukan sekadar sek kumpulan kode biasa, melainkan produk uji validitas biomedis yang sah.

## Usulan Judul Skripsi
1. **Pengembangan *Ground-Truth Dataset* Penyakit Fisiologis dan Evaluasi Akurasi Penalaran GraphRAG Menggunakan Metrik RAGAS**
2. **Analisis Perbandingan Keandalan Penilai Medis Algoritmik (*LLM-as-a-Judge*) terhadap Validasi Manual Pakar (*Human-in-the-Loop*)**
3. **Standarisasi Pengujian Tingkat Keselamatan Respon Sistem Tanya Jawab Kesehatan GraphRAG Berbantuan *Framework* Observabilitas TruLens**
