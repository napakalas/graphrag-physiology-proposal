# Topik Tugas Akhir Mahasiswa 2: Strategi Penelusuran Subgraf (Graph Traversal) pada Knowledge Graph Medis

## Deskripsi Singkat
Setelah Mahasiswa 1 memberikan informasi berupa "*User* menanyakan entitas Saraf X dan Organ Y", Mahasiswa 2 bertanggung jawab mengembangkan skrip ekstraksi relasi. Tugasnya mengambil rute koneksi logis paling relevan di dalam sebuah *Knowledge Graph* raksasa tanpa menarik terlalu banyak sampah referensi (*noise*). Fokusnya sangat bersinggungan dengan arsitektur memori database graf.

## Fokus Eksplorasi (Rumusan Masalah)
1. Bagaimana perbandingan rasio akurasi (Precision/Recall) algoritma telusur murni (*Graph Traversal*, Cypher) dibandingkan pencarian vektor (*Vector-embedded Graph Search*) dalam mengekstrak jalur fisiologi saraf?
2. Bagaimana efektivitas *Graph Pruning* agar subgraf yang dikembalikan tidak "membanjiri" (melebihi bataan *token limit*) memori LLM pada fase generasi?

## Tautan Sumber Daya (*Resources*) Utama
1. **PrimeKG (Precision Medicine Knowledge Graph):** Mengandung jutaan interaksi penyakit, anatomi, gen, obat, secara lengkap.
   * *Tautan:* [PrimeKG Repository (Harvard)](https://github.com/mims-harvard/PrimeKG) 
   * *Dataset:* [PrimeKG di Harvard Dataverse](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/IXA7BM)
2. **Neo4j (atau NebulaGraph):** Alat database graf standar industri.
   * *Tautan:* [Neo4j AuraDB / Desktop](https://neo4j.com/)

## Peran dalam Arsitektur Utama
Berada di lapisan inti (**Context Retrieval**). Modul buatan mahasiswa menerima *Entity ID* dari Mhs 1, mencari relasi yang merekatkan ID tersebut dengan penyakit fisiologi lainnya dari database Neo4j, lalu merangkumnya menjadi "Konteks Latar Belakang (Subgraph)" untuk diberikan ke Mahasiswa 3.

## Usulan Judul Skripsi
1. **Analisis Optimasi Arsitektur *Graph Traversal* dan Algoritma Pemangkasan Celah (*Pruning*) pada PrimeKG untuk Penelusuran Konteks Medis**
2. **Perbandingan Rasio Ketepatan *Vector Search* dan *Cypher Traversal* dalam Mengakuisisi Subgraf Relasi Penyakit dan Anatomi Saraf**
3. **Implementasi Ekstraksi Pangkalan Pengetahuan Berbasis Graf untuk Pembangunan Konteks Relasi Penyakit dan Obat Secara Matematis**
