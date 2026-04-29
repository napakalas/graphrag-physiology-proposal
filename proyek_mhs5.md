# Topik Tugas Akhir Mahasiswa 5: Manajemen Konteks Multi-turn (Memorisation) dan Semantic Caching pada GraphRAG Saraf

## Status Topik
Topik ini **belum ada yang mengambil** pada batch aktif saat ini.

## Deskripsi Singkat
Pada kenyataannya, interaksi pengguna jarang berupa satu pertanyaan putus. User kerap bertanya "Bagaimana anatominya?", lalu diikuti "Lalu apa bahayanya baginya?". Mahasiswa 5 bertanggung jawab mengelola ingatan percakapan (*Context & Memorisation*) di mana sistem harus tahu bahwa "baginya" merujuk pada *node graf anatomi* spesifik dari tanya jawab sebelumnya. Selain itu, mengeksplorasi *Semantic Caching* (menyimpan vektor interaksi ke memori sementara) agar RAG tidak perlu melakukan kueri ulang ke Graph Database berat untuk pertanyaan yang polanya mirip.

## Fokus Eksplorasi (Rumusan Masalah)
1. Bagaimana pengaruh penambahan metode pelacakan referensi inti (*Coreference Resolution* dan *ConversationBufferMemory*) pada sistem tanya jawab multi-sesi terhadap kesinambungan relasi subgraf berturut-turut pada domain sistem saraf?
2. Bagaimana perbandingan rasio beban latensi (waktu komputasi) antara GraphRAG yang melakukan penelusuran murni ke Neo4j setiap *turn* dibandingkan dengan yang dioptimasikan memakai *Semantic Caching* (pengindeksan vektor memori Q&A sebelumnya)?

## Tautan Sumber Daya (*Resources*) Utama
1. **Langchain Memory & Zep:** Perangkat standar industri untuk *LLM Long-term memory*.
   * *Tautan Zep (Memory Analytics):* [Zep AI](https://www.getzep.com/)
2. **GPTCache atau Redis:** Sistem pengindeksan untuk menyimpan kemiripan *embedding* semantik pertanyaan sebelumnya agar Graph Query dapat dibypass jika pertanyaan dirasa sama.
   * *Tautan:* [GPTCache Repo](https://github.com/zilliztech/GPTCache)

## Peran dalam Arsitektur Utama
Berada pada lapisan (**Session State & Caching Data**). Modul buatan mahasiswa menyimpan jejak rekam *node graph* yang sudah ditelusuri di sesi 1. Jika *user* memberikan klausa lanjutan di sesi 2, sistem Mhs 5 akan "menyela" skrip NLP Mhs 1 dan memaksa sistem langsung menarik *node* tersimpan, membuat Chatbot terasa sangat cerdas, responsif, dan layaknya manusia.

## Usulan Judul Skripsi
1. **Pengaruh Pendekatan *Vector Semantic Caching* terhadap Peningkatan Reduksi Waktu Merespons (*Latency*) pada Sesi GraphRAG Interaktif**
2. **Penanganan *Coreference Resolution* Berbasis *Conversation Buffer Memory* untuk Integritas Konteks Tanya Jawab Fisiologi Medis Berkelanjutan**
3. **Optimasi Beban Siklus Pangkalan Data Graf Menggunakan Pengindeksan *Cache* Semantik Multi-Kueri pada Arsitektur GraphRAG**
