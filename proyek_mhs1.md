# Topik Tugas Akhir Mahasiswa 1: Akurasi Pemetaan Entitas Bahasa Medis Natural ke Konsep Ontologi Standar

## Deskripsi Singkat
Sistem GraphRAG tidak akan bisa memulai pencarian jika mesin tidak tahu persis "apa yang dicari". Mahasiswa 1 bertanggung jawab pada porsi *Natural Language Processing* (NLP) lapis depan. Sekilas *Entity Linking* terlihat ringan, namun mengurai teks medis di dunia nyata sangat rentan ambiguitas (misal kependekan medis atau kesalahan ketik pengguna). 
Mahasiswa ini **tidak hanya** melakukan *mapping* kata kunci ke *ID Node* (FMA/UBERON), melainkan juga membangun modul **Query Expansion** (menerjemahkan gejala natural *"sakit lambung ke atas pinggang"* menjadi sekumpulan *node* anatomi terstandar) dan **Semantic Disambiguation** (menyelesaikan kebingungan algoritma saat satu kata medis punya arti cabang yang berbeda). Permasalahan NLP medis khusus fisiologi ini sangat dalam dan bernilai tinggi untuk S1.

## Fokus Eksplorasi (Rumusan Masalah)
1. Bagaimana arsitektur *Hybrid Entity Linking* (kombinasi leksikal UMLS dan pemahaman semantik via BioBERT/SciBERT) mengatasi ambiguitas dan singkatan dalam mengekstrak konsep anatomi FMA/UBERON dari teks kueri pengguna?
2. Bagaimana mekanisme *Query Expansion* (meluaskan kata kunci pengguna berdasarkan sinonim medis) mampu memperbaiki probabilitas ekstraksi simpul awal (*seed nodes*) sebelum dikirim ke mesin Graph database?

## Tautan Sumber Daya (*Resources*) Utama
1. **UMLS (Unified Medical Language System):** Sebagai kamus leksikal utama untuk standarisasi bahasa medis.
   * *Tautan:* [UMLS Terminology Services](https://uts.nlm.nih.gov/uts/)
2. **NCBO BioPortal:** Pusat repositori ribuan ontologi (termasuk FMA, UBERON, GO, ChEBI). Berguna untuk riset pemetaan struktur hirarkinya.
   * *Tautan:* [BioPortal](https://bioportal.bioontology.org/)
3. **Pustaka NLP Medis:** Mahasiswa dapat mengeksplor modul Python standar untuk ekstraksi biomedis.
   * *Tautan:* [scispaCy (spaCy for Biomed/Science)](https://allenai.github.io/scispacy/)

## Peran dalam Arsitektur Utama
Berada di lapisan terdepan (**Input Processing**). Modul buatan mahasiswa ini mencegat teks *user*, menyaringnya menjadi kumpulan "Entity ID", lalu menyerahkan kumpulan ID tersebut ke skrip Mahasiswa 2.

## Usulan Judul Skripsi
1. **Analisis Kinerja Model BioBERT dalam Pendekatan *Hybrid Entity Linking* pada *Knowledge Graph* Anatomi Fisiologi**
2. **Penerapan *Semantic Query Expansion* Berbasis LLM untuk Disambiguasi Leksikal Istilah Medis pada Sistem GraphRAG**
3. **Ekstraksi Entitas Sistem Saraf Otonom Berbasis Ontologi FMA Menggunakan Model Bahasa Alami Terlatih (*Pre-trained NLP*)**
