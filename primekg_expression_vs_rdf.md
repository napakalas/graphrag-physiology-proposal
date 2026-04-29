# PrimeKG: Expression-Based vs RDF-Based

## 1) Apa itu PrimeKG
PrimeKG (Precision Medicine Knowledge Graph) adalah knowledge graph biomedis untuk precision medicine yang menghubungkan entitas seperti penyakit, obat, gen/protein, jalur biologis, fenotipe, dan anatomi.

Ciri penting PrimeKG:
- Integrasi multi-sumber data biomedis ke satu graf terpadu.
- Memudahkan query lintas-domain (misal: penyakit -> gen -> target obat -> senyawa).
- Umumnya dipakai untuk analisis jaringan biomedis, drug repurposing, dan pipeline AI/ML berbasis graf.

## 2) Contoh data di PrimeKG
Secara praktis, data PrimeKG sering dipakai sebagai tripel/edge-list dengan pola:
- Head entity
- Relation
- Tail entity

Poin penting:
- Benar bahwa format ini terlihat seperti RDF triple.
- Namun, "mirip bentuk" tidak sama dengan "mirip semantik". Pada expression-based, relasi sering diperlakukan sebagai label operasional, bukan predicate formal berbasis ontologi.

Contoh sederhana (ilustratif):

| head | relation | tail |
|---|---|---|
| Parkinson disease | associated_with_gene | SNCA |
| SNCA | participates_in | protein folding pathway |
| Levodopa | treats | Parkinson disease |
| Vagus nerve | anatomically_related_to | brainstem |
| Acetylcholine | has_ontology_mapping | ChEBI:15355 |

Catatan:
- Banyak entitas di PrimeKG dipetakan ke identifier/ontology term standar agar interoperabel.
- Jadi, representasi operasionalnya bisa expression-based, sementara kosakatanya tetap bertumpu pada standar ontology.

### Contoh fakta yang sama dalam dua representasi
Fakta biologis: "Lisinopril treats Hypertension"

Contoh expression-based (property graph / edge list):

| head_id | head_name | relation | tail_id | tail_name | evidence |
|---|---|---|---|---|---|
| DB00722 | Lisinopril | treats | DOID:10763 | Hypertension | FDA_label |

Contoh RDF-based (triple dengan URI):

```turtle
@prefix drugbank: <https://identifiers.org/drugbank:> .
@prefix doid: <https://identifiers.org/doid:> .
@prefix exrel: <https://example.org/relation/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

drugbank:DB00722 exrel:treats doid:10763 .
drugbank:DB00722 rdfs:label "Lisinopril" .
doid:10763 rdfs:label "Hypertension" .
```

Intinya:
- Keduanya bisa merepresentasikan fakta yang sama.
- RDF memberi identitas global (URI) dan landasan semantik formal untuk reasoning lintas dataset.
- Expression-based biasanya lebih sederhana untuk komputasi AI/ML.

## 3) Apa beda expression-based vs RDF-based
Expression-based (umum pada pipeline data science):
- Data relasi disimpan sebagai tabel/tripel/edge list yang fleksibel.
- Skema dapat lebih mudah disesuaikan untuk kebutuhan eksperimen.
- Sangat praktis untuk feature engineering, graph embedding, GNN, dan workflow AI/ML.
- Tidak ada jaminan semantik formal bawaan jika dibanding RDF/OWL.

RDF-based (umum pada semantic web/ontology engineering):
- Data dan makna semantik mengikuti model RDF/OWL yang formal.
- Relasi, class, constraint, dan inferensi mengikuti aturan ontologi yang eksplisit.
- Lebih ketat (rigid) sehingga konsistensi semantik lebih terjaga.
- Dapat memanfaatkan SPARQL dan reasoner untuk validasi/inferensi berbasis logika.

Ringkasnya:
- Expression-based menekankan kemudahan komputasi dan eksperimen.
- RDF-based menekankan formalisme pengetahuan, interoperabilitas semantik, dan validitas inferensi.

## 3a) Apakah keduanya interchangeable?
Secara konsep: ya, sampai tingkat tertentu.
- RDF -> expression-based: biasanya terjadi "flattening" (meringkas struktur semantik menjadi edge/fitur operasional).
- Expression-based -> RDF: biasanya terjadi "lifting" (memetakan ID lokal/relasi lokal ke URI dan ontologi formal).

Tetapi, konversi hampir selalu ada trade-off:
- Bisa kehilangan detail semantik (saat flattening).
- Bisa menambah biaya kurasi/mapping (saat lifting).
- Jadi interchangeable secara representasi data, namun tidak sepenuhnya ekuivalen dalam kemampuan reasoning dan governance.

## 4) Mengapa menggunakan expression-based, dan mengapa menggunakan RDF-based
Mengapa expression-based:
- Cepat untuk eksplorasi data, eksperimen model, dan iterasi AI/ML.
- Mudah diproses oleh library data science (pandas, PyTorch Geometric, DGL, dsb).
- Cocok untuk downstream task seperti link prediction, node classification, ranking, dan retrieval.

Mengapa RDF-based:
- Memiliki semantik formal dan dapat memanfaatkan reasoner ontologi.
- Sangat baik untuk knowledge governance, data integration lintas institusi, dan audit makna relasi.
- Inferensi cenderung lebih terkontrol karena mengikuti skema ontologi yang eksplisit.

## 5) Ontology apa yang digunakan PrimeKG
Berdasarkan pipeline/sumber primer resmi PrimeKG (README dan skrip konstruksi), yang eksplisit dipakai antara lain:
- UBERON
- Gene Ontology (GO)
- Human Phenotype Ontology (HPO)
- MONDO
- UMLS (untuk harmonisasi terminologi)

Catatan penting untuk FMA dan ChEBI:
- UBERON: jelas eksplisit dipakai dalam pipeline PrimeKG.
- FMA dan ChEBI: tidak tampak sebagai sumber primer eksplisit pada daftar pipeline resmi yang dipublikasikan PrimeKG.
- FMA/ChEBI tetap bisa muncul secara tidak langsung lewat mapping lintas sumber (misalnya via UMLS/ontology cross-reference), tetapi ini berbeda dari klaim "dipakai langsung sebagai sumber primer".

## 6) RDF-based seperti UMLS: struktur rigid dan ground truth
RDF-based knowledge (atau knowledge yang sangat ontology-driven, termasuk ekosistem terminologi seperti UMLS saat dimodelkan sebagai RDF/ontology mapping) biasanya:
- Lebih rigid secara struktur.
- Berfungsi baik sebagai ground truth semantik (rujukan makna istilah dan relasi).
- Menghasilkan inferensi dengan validitas tinggi karena dibatasi oleh aturan dan hierarki ontologi.

Konsekuensi:
- Kualitas semantik naik.
- Fleksibilitas eksperimen kadang lebih rendah dibanding format expression-based.

## 7) Expression-based tidak benar-benar "memahami" biologi, tapi kuat untuk AI/ML
Poin penting:
- Expression-based merepresentasikan pola relasi sebagai data komputasional, bukan pemahaman biologis kausal secara intrinsik.
- Model AI/ML di atas expression-based belajar pola statistik/topologi, bukan "mengerti" mekanisme biologis seperti pakar domain.

Namun, expression-based sangat cocok untuk:
- Tahap lanjutan AI/ML (embedding, prediksi relasi, rekomendasi kandidat obat).
- Skalabilitas komputasi dan eksperimen cepat.
- Integrasi dengan pipeline modern LLM + GraphRAG.

## 8) Bagaimana validasi di PrimeKG
Validasi PrimeKG biasanya dilakukan berlapis:
- Validasi struktur data: cek duplikasi edge, node orphan, konsistensi tipe relasi.
- Validasi semantik: cek kesesuaian identifier ke ontology/terminologi standar.
- Validasi provenance: setiap relasi ditautkan ke sumber data yang jelas.
- Validasi task-level: uji pada tugas nyata (misal link prediction atau drug repurposing) menggunakan metrik seperti AUROC, AUPRC, Hits@K, MRR.
- Validasi pakar/domain: sampling relasi penting untuk ditinjau manual oleh ahli biomedis.

Jika pertanyaannya adalah "bagaimana menjamin correctness pada sistem expression-based seperti PrimeKG?", jawabannya: melalui kontrol eksternal yang ketat, bukan dari format datanya sendiri.

Lapisan kontrol yang disarankan:
- Schema enforcement: definisikan domain-range relasi yang boleh (misal `treats` harus Drug -> Disease).
- Ontology anchoring: node/edge wajib punya mapping ke ID standar (GO, ChEBI, UBERON, FMA, MONDO, UMLS CUI sesuai kebutuhan).
- Provenance + evidence score: simpan sumber dan bobot bukti per relasi.
- Rule-based QA: blokir typo relasi, blokir kombinasi tipe yang tidak sah, dan tandai konflik antar-sumber.
- Benchmark eksternal: uji pada dataset pembanding dan review ahli pada sampel high-impact.

Praktik terbaik:
- Kombinasikan validasi statistik (ML metrics) dengan validasi ontologis (consistency check) agar hasil tidak hanya akurat secara angka, tetapi juga masuk akal secara biologi.

## 9) Kaitan dengan knowledge base dan knowledge graph
Hubungannya dapat dipahami seperti ini:
- Knowledge base adalah kumpulan pengetahuan terstruktur (fakta, istilah, relasi, aturan).
- Knowledge graph adalah bentuk representasi knowledge base sebagai graf (node-entitas dan edge-relasi).

Secara konseptual (bukan aturan mutlak):
- RDF/ontology-heavy cenderung lebih dekat ke orientasi knowledge base (fakta + aturan + deduksi).
- Expression-based/property graph cenderung lebih dekat ke orientasi knowledge graph analitik (struktur jaringan + komputasi + AI/ML).

PrimeKG berada di irisan keduanya:
- Sebagai knowledge base: ia menyimpan fakta biomedis terintegrasi.
- Sebagai knowledge graph: ia memodelkan fakta tersebut dalam struktur graf untuk query, reasoning, dan AI/ML.

Jadi, PrimeKG dapat dipakai sebagai:
- Sumber pengetahuan (knowledge base) untuk aplikasi klinis/riset.
- Struktur graf (knowledge graph) untuk inferensi, retrieval, dan GraphRAG.

---

## Kesimpulan singkat
- PrimeKG praktis untuk AI/ML karena format operasionalnya cenderung expression-based.
- RDF-based unggul pada precision semantik dan validitas inferensi formal.
- Keduanya dapat saling dikonversi, tetapi ada trade-off (kecepatan/fleksibilitas vs ketelitian semantik).
- Pada expression-based, correctness dijaga lewat kurasi, schema rule, ontology mapping, provenance, dan evaluasi eksternal.