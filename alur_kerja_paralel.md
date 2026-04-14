# Alur Kerja Paralel Proyek GraphRAG untuk 5 Mahasiswa

Tentu saja proyek ini dapat dikerjakan secara paralel. Meskipun sistem komputasi (RAG) berjalan secara sekuensial pada produk akhirnya (Tanya -> Esktrak Entitas -> Cek Cache -> Cari Graf -> Prompt LLM -> Simpan Jawaban), **proses penelitian dan pengembangannya (development) dapat dilakukan secara simultan** sejak hari pertama dengan menerapkan konsep *Mock Data* atau *Dummy Input*.

Berikut adalah desain manajemen proyek pembagian kerja selama 4-5 bulan untuk 5 orang anggota tim:

## Fase 1: Setup & Riset Dasar (Bulan 1) - **100% Paralel**
Pada fase ini, kelima mahasiswa tidak ada yang memiliki ketergantungan erat (blocker). Mereka bekerja menguji coba teknologi (tools) mereka secara di luar jaringan (lokal).

*   **Mahasiswa 1 (NLP & Entity Linking):** Mencari dan mengeksplorasi model BioBERT/SciBERT. Mereka melatih skrip untuk menangkap kata kunci penyakit, mengembangkannya secara sinonim (Query Expansion), dan memetakannya ke standar UMLS menggunakan teks buatan (*dummy text*).
*   **Mahasiswa 2 (Retrieval Graf):** Mengunduh set dataset PrimeKG atau Monarch Initiative. Memasukkannya ke dalam Graph Database (seperti Neo4j). Mulai berlatih menulis kueri Cypher/SPARQL secara manual di konsol database-nya tanpa aplikasi Python.
*   **Mahasiswa 3 (Prompt LLM):** Membuat kerangka LangChain/LlamaIndex. Bermain dengan instruksi sistem bot (*System Prompt*). Menggunakan struktur graf JSON palsu untuk menguji rasa bahasa LLM, guna melihat seberapa parah bot medis ChatGPT/LLaMA ini berhalusinasi.
*   **Mahasiswa 4 (Evaluasi E2E):** Melakukan studi literatur ke perpustakaan/jurnal klinis. Menyusun *Ground Truth Dataset* secara manual/independen. Selain itu, mereka menyiapkan skrip instalasi untuk alat skoring seperti *TruLens* atau *RAGAS*.
*   **Mahasiswa 5 (Memori & Caching):** Menyiapkan arsitektur database sesi (*Vector Store Cache*). Ia mencoba menyiapkan memori sementara. Skrip Mhs 5 dilatih menerima "kalimat palsu" dan membandingkan apakah kalimat itu memiliki kesamaan inti makna (*semantic similarity*) dengan memori pertanyaan kemarin.

## Fase 2: Integrasi Tengah Komponen (Bulan 2 - 3) - **Paralel Fusi**
Di sini mahasiswa mulai menyambungkan modul skrip python mereka masing-masing menjadi satu *pipeline* RAG utuh.

*   **Integrasi Awal (Input & Cek Sesi):** Modul NLP (Mhs 1) menangkap *"Bagaimana anatomi saraf x?"*. Sebelum masuk ke jaringan relasi graf pusat, modul Memori (Mhs 5) mencegat dan mengecek mesin caching-nya. Bila kosong, jalankan fase berikutnya.
*   **Integrasi Inti (Pencarian & Generasi):** Skrip pencarian Neo4j (Mhs 2) mencari akar kueri dan memastikan sambungan relasinya ditemukan, lalu diumpan ke LangChain Prompter (Mhs 3). Mhs 3 mengembalikan jawaban bahasa natural ke pengguna (dan tak lupa membocorkan sesinya untuk didikte ulang ke basis memori Mhs 5 agar diingat di siklus yang akan datang). 
*   **Integrasi Pengawas (Mhs 4):** Sepanjang integrasi berlangsung secara otomatis, Mhs 4 akan memasang mesin ukur (*probe*) RAGAS miliknya untuk menjaring nilai kesalahan, latensi kembalian data, dan *faithfulness* LLM yang berjalan. Data skor ini akan diberikan ke rekan-rekan untuk di-_tuning_ ulang.

## Fase 3: Eksperimen Utama & Analisis Akhir (Bulan 4) - **Analisis Paralel**
Sistem utuh *(End-to-End Pipeline)* sudah berjalan dalam satu aplikasi *backend* interaktif (walau belum dirilis). Di sinilah tiap peran mulai menyempurnakan jawaban atas rumusan masalah skripsi masing-masing secara bersamaan (karena data log interaksi sudah mulai terkumpul banyak).

*   **Mahasiswa 1** berfokus bereksperimen mana yang lebih akurat: model NLP Leksikal atau Model Semantik BioBERT di sistem saraf.
*   **Mahasiswa 2** mencoba memotong / pemangkasan (*pruning*) relasi database graf 3 *hop* vs 1 *hop*; untuk melihat dampaknya.
*   **Mahasiswa 3** bereksperimen mengganti-ganti skenario *prompt* hingga mengalibrasi kemampuan antar LLM berbeda (misal GPT-4 melawan LLaMA) untuk lintas spesies UBERON.
*   **Mahasiswa 4** menghimpun dosen / asisten lab Fisiologi, dan mengeksekusi penilaian kuantitatif akhir seputar keselamatan *Ground Truth* skripsi ini.
*   **Mahasiswa 5** mengumpulkan statistik kalkulasi penghematan waktu server (*latency saved*) sejak dihidupkannya *Semantic Caching* buatannya, sekaligus mengukur seberapa efisien arsitektur ini merespons referensi pertanyaan berturut-turut.

## Kesimpulan
Desain komponen berbasis antarmuka microservices ini berarti rekan tim **tidak pernah akan saling menunggu (blocking)** jika skrip di salah satu bagian rusak karena mereka mengandalkan *mock test*/data tiruan sebagai API. Jika proyek Mhs 2 (Cyphernya) ngadat, integrasi Mhs 3 bisa tetap lanjut jalan menggunakan *dummy subgraph*.
