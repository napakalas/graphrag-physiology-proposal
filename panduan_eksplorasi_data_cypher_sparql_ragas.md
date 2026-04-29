# Panduan Eksplorasi Data: Cypher, SPARQL, dan Evaluasi RAGAS

Dokumen ini disiapkan untuk konteks batch aktif:
- Mahasiswa 1: Query Expansion berbasis LLM
- Mahasiswa 2: Implementasi RAG (retrieval + generation)
- Mahasiswa 4: Evaluasi sistem menggunakan RAGAS

## 1. Gambaran Besar: Kapan Cypher, Kapan SPARQL

- Gunakan Cypher bila data Anda berbentuk property graph/edge list (contoh workflow PrimeKG di Neo4j).
- Gunakan SPARQL bila data Anda berbentuk RDF/OWL (contoh SCKAN atau ontology endpoint).
- Bentuk head-relation-tail memang mirip RDF triple, tetapi tidak otomatis memiliki semantik formal RDF.

Ringkas:
- Cypher: cepat untuk traversal, analitik graf, dan pipeline AI/ML.
- SPARQL: kuat untuk interoperabilitas, constraint semantik, dan reasoning ontologis.

## 2. Alur Kolaborasi Batch Aktif

1. Mahasiswa 1 (Query Expansion):
   Ubah pertanyaan natural user menjadi daftar entitas kandidat + sinonim + ID standar.
2. Mahasiswa 2 (RAG Retrieval):
   Pakai entitas kandidat sebagai seed untuk query Cypher (atau SPARQL jika RDF) dan ambil subgraf relevan.
3. Mahasiswa 4 (RAGAS Evaluation):
   Nilai kualitas jawaban dan konteks retrieval dengan metrik RAGAS.

## 2a. Pemetaan ke File Implementasi

- Mahasiswa 1:
  - Dokumen konsep: `semantic_query_expansion_graphrag.md`
- Mahasiswa 2:
  - Dokumen konsep: `graph_extraction_matematika.md`
  - Script filter data: `filter_kg.py`
  - Script import database: `import_neo4j.py`
- Mahasiswa 3:
  - Slot Prompt Engineering (belum ada dokumen teknis aktif)
- Mahasiswa 4:
  - Dokumen evaluasi: `evaluasi_graphrag_ragas.md`

## 3. Mahasiswa 1: Template Query Expansion untuk Seed Entity

Tujuan:
- Meminimalkan miss-retrieval karena variasi istilah medis.

Output minimal dari modul query expansion:

```json
{
  "original_query": "apa terapi untuk inflamasi saraf vagus",
  "expanded_terms": [
    "vagus nerve inflammation",
    "neuritis of vagus nerve",
    "vagus neuritis",
    "nervus vagus inflammation"
  ],
  "entity_candidates": [
    {"label": "Vagus nerve", "type": "anatomy", "id": "UBERON:0002015", "score": 0.92},
    {"label": "Neuritis", "type": "disease", "id": "MONDO:...", "score": 0.71}
  ]
}
```

Checklist kualitas untuk Mahasiswa 1:
- Setiap kandidat punya `id`, `type`, `score`.
- Ada normalisasi sinonim (EN/ID jika perlu).
- Ada batas top-k kandidat (misalnya top-5) untuk mencegah noise.
- Kandidat dengan skor rendah dipisah sebagai cadangan, tidak langsung jadi seed utama.

## 4. Mahasiswa 2: Eksplorasi PrimeKG dengan Cypher

Catatan:
- PrimeKG umum dipakai sebagai edge list yang di-load ke graph database.
- Istilah relasi dan label node harus disesuaikan dengan skema hasil ingest Anda.

### 4.1 Query baseline eksplorasi

```cypher
MATCH (n)
RETURN count(n) AS total_nodes;
```

```cypher
MATCH ()-[r]->()
RETURN count(r) AS total_edges;
```

```cypher
MATCH (n)
RETURN labels(n) AS node_labels, count(*) AS c
ORDER BY c DESC
LIMIT 20;
```

```cypher
MATCH ()-[r]->()
RETURN type(r) AS rel_type, count(*) AS c
ORDER BY c DESC
LIMIT 30;
```

### 4.2 Query berbasis seed dari Mahasiswa 1

Contoh: dari seed `Vagus nerve`.

```cypher
MATCH (seed)
WHERE toLower(seed.name) CONTAINS toLower("vagus")
MATCH p = (seed)-[r*1..2]-(nbr)
RETURN seed.name, p
LIMIT 50;
```

Contoh: ambil penyakit/obat terdekat dari seed anatomi.

```cypher
MATCH (a)
WHERE toLower(a.name) CONTAINS toLower("vagus")
MATCH (a)-[*1..2]-(d:Disease)
OPTIONAL MATCH (drug:Drug)-[treatRel]->(d)
RETURN DISTINCT a.name AS anatomy, d.name AS disease, drug.name AS candidate_drug, type(treatRel) AS rel
LIMIT 100;
```

### 4.3 Pruning agar konteks tidak kebesaran

Strategi praktis:
- Batasi hop: 1..2 dulu, naikkan hanya jika recall terlalu rendah.
- Batasi relasi whitelist (contoh: `ASSOCIATED_WITH`, `TREATS`, `PART_OF`).
- Gunakan top-k node berdasarkan skor (pagerank/degree/evidence).
- Simpan provenance relasi yang dipilih untuk audit.

Contoh query pruning sederhana:

```cypher
MATCH (s {id: $seed_id})-[r*1..2]-(n)
WHERE all(x IN r WHERE type(x) IN ["ASSOCIATED_WITH", "TREATS", "PART_OF"])
RETURN n
LIMIT 200;
```

## 5. Mahasiswa 2 (Opsional): Eksplorasi RDF dengan SPARQL

Gunakan ini bila Anda bekerja dengan endpoint RDF (misalnya SCKAN/ontologi berbasis RDF).

### 5.1 Query baseline

```sparql
SELECT (COUNT(*) AS ?tripleCount)
WHERE { ?s ?p ?o . }
```

```sparql
SELECT ?p (COUNT(*) AS ?c)
WHERE { ?s ?p ?o . }
GROUP BY ?p
ORDER BY DESC(?c)
LIMIT 30
```

### 5.2 Query berbasis entitas seed

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?nbr ?nbrLabel
WHERE {
  <URI_SEED_ENTITY> ?rel ?nbr .
  OPTIONAL { ?nbr rdfs:label ?nbrLabel . }
}
LIMIT 100
```

### 5.3 Multi-hop (property path)

```sparql
SELECT ?x
WHERE {
  <URI_SEED_ENTITY> ( ?p1 | ?p2 ){1,2} ?x .
}
LIMIT 200
```

Catatan:
- Ganti `URI_SEED_ENTITY` dengan URI sebenarnya.
- Untuk query produksi, gunakan predicate yang spesifik, bukan variabel bebas, agar presisi naik.

## 6. Mahasiswa 4: Evaluasi RAGAS (Retrieval + Jawaban)

Target evaluasi:
- Kualitas konteks yang diambil (apakah relevan untuk menjawab?).
- Kualitas jawaban akhir (apakah sesuai konteks dan pertanyaan?).

### 6.1 Struktur dataset evaluasi minimal

```json
{
  "question": "Apa terapi lini awal untuk inflamasi nervus vagus?",
  "contexts": [
    "... potongan subgraf/teks hasil retrieval ..."
  ],
  "answer": "... jawaban sistem RAG ...",
  "ground_truth": "... jawaban rujukan ..."
}
```

### 6.2 Metrik RAGAS yang direkomendasikan

- `context_precision`: seberapa bersih konteks retrieval dari noise.
- `context_recall`: seberapa cukup konteks retrieval untuk menjawab.
- `faithfulness`: apakah jawaban konsisten dengan konteks.
- `answer_relevancy`: apakah jawaban benar-benar menjawab pertanyaan.

Interpretasi praktis:
- Jika `faithfulness` rendah: perbaiki prompt grounding dan batasi improvisasi model.
- Jika `context_recall` rendah: perbaiki query expansion atau naikkan hop secara terkendali.
- Jika `context_precision` rendah: tambah pruning/whitelist relasi.

## 7. Protokol Eksperimen End-to-End yang Disarankan

1. Tetapkan 50-100 pertanyaan uji per topik medis.
2. Jalankan 3 varian retrieval:
   - Baseline tanpa query expansion.
   - Query expansion sederhana (sinonim statis).
   - Query expansion berbasis LLM.
3. Untuk tiap varian, simpan:
   - seed entity,
   - subgraf yang diambil,
   - jawaban model,
   - skor RAGAS.
4. Bandingkan rata-rata metrik per varian.
5. Audit manual 20 sampel dengan skor terendah untuk analisis error.

## 8. Definisi Correctness untuk Sistem Expression-Based

Karena tidak ada jaminan logika formal bawaan seperti RDF, correctness dijaga lewat kontrol eksternal:
- Schema rule: domain-range relasi harus valid.
- Ontology anchoring: ID entitas wajib ditautkan ke standar (misalnya UMLS/GO/UBERON/MONDO sesuai kebutuhan).
- Provenance: setiap edge punya sumber data jelas.
- Evidence weighting: edge berbukti lemah diberi bobot rendah.
- Human review: sampling edge/jawaban untuk validasi pakar.

## 9. Deliverable per Mahasiswa

Mahasiswa 1:
- Modul query expansion (`query -> entity_candidates`) + laporan ablation.

Mahasiswa 2:
- Pipeline retrieval Cypher/SPARQL + strategi pruning + logging provenance.

Mahasiswa 3:
- Modul prompt engineering dan linearisasi konteks (slot terbuka pada batch aktif).

Mahasiswa 4:
- Pipeline evaluasi RAGAS + dashboard skor + error taxonomy.

## 10. Ringkasan

- Untuk PrimeKG, mulai dari Cypher karena cocok dengan workflow property graph.
- SPARQL dipakai saat data sudah RDF-native atau saat butuh reasoning semantik formal.
- Keberhasilan sistem bukan hanya dari jawaban akhir, tapi dari kualitas retrieval yang dapat diaudit (provenance) dan dievaluasi (RAGAS).