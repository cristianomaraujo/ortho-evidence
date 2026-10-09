# OrthoEvidence — research prototype

PubMed review observatory. Raw collection, objective/count extraction rules and exploratory TF-IDF recommendations. No automated claim of saturation, redundancy, eligibility or clinical certainty.

## Reproduce
Use `--from-cache` to rebuild from the latest saved XML batches without new requests. PubMed book/report records are logged separately and not rendered by the journal-article parser.
Python 3.12 and scikit-learn. `python scripts/update_pubmed.py` retrieves all PubMed IDs matching the versioned query, fetches records through NCBI history, saves XML batches, extracts objective sentences and explicit included-count patterns, and regenerates `dist/data.json`. No model/API billing. Respect NCBI rate limits; script is sequential. Failures stop publication; inspect before updating the dashboard.

The default performs full recollection; an explicit reuse-cache option supports query expansion from a previous snapshot without refreshing old metadata. PMID + record hash support later change detection. Scheduling is not configured. Retrieval strategy is an initial broad strategy, not a validated final search. The expanded query combines Orthodontics, Orthodontic Appliances, Malocclusion and Tooth Movement Techniques MeSH with free terms for orthodontics, dentofacial orthopedics, malocclusion, aligners, Invisalign and orthognathic topics. It combines Review, Systematic Review, Meta-Analysis publication types and systematic[sb], without date/language restrictions. Review labels can overlap and do not reliably distinguish narrative or integrative reviews. Sensitivity and relevance still require validation.

## Methods
Themes: title keyword rules, multi-label. Objectives: labelled sections or aim/purpose/objective sentences. Counts: numeric patterns + source sentence + unit; ambiguity and meta-analysis subsets require human assessment. Similarity: TF-IDF English stop words, unigram/bigram, min_df=2, max_df=.95, max_features=30000; cosine. Use as baseline for comparison with open embeddings, not validated objective equivalence. Query uses identical vocabulary/IDF, with limited visible PT→EN substitutions. No paid inference.

## Validation required
Independent eligibility/field reviewers, adjudication, independent known-review retrieval set, held-out objective-equivalence pairs, retrieval metrics, extraction accuracy and temporal validation. No validated saturation threshold. Recovered records are candidates and PubMed-only coverage is explicit. Abstract absence is missing information, not a negative finding.

## Railway
Dockerfile serves static dashboard on PORT; model processing is separate. Disable Serverless/App Sleep for dashboard availability. Set up persistent raw-data storage and reviewed publication jobs before activating updates. There are no Railway account integrations or credentials here; current deployment is private Sites, not Railway.

## Data and versions
`dist/data.json`: collection metadata and TF-IDF index; `dist/records-*.json`: processed record batches (2,000 per file). `data/raw/<UTC-run>/`: raw XML and search result. Public abstracts may have copyright restrictions; do not assume redistribution rights for a public release. Current dashboard is owner-private. Validation decisions should be stored separately from machine outputs in the production database.

## Human annotation pilot
Evaluation screen records eligibility, objective/count verification and pair objective equivalence. Browser-local storage only: no server database, team synchronization, authentication, adjudication or automatic retraining. Reviewer codes are self-declared. Export JSON backup and CSV event history each session. Import merges validated event IDs without replacing previous decisions. Source run and per-record hashes tie annotations to the collection; prior rounds remain exported but progress is scoped to current run and reviewer. Revisions append events; analysis must select latest decisions per reviewer/task/run, rather than treat revisions as independent observations. Use separate browser profiles for independent reviewers. Pair queues use closest stored lexical neighbor or deterministic dispersed pairs; neither is representative or a held-out validation design. The annotation screen hides similarity scores and other reviewer judgments, though reviewers can still access exploratory pages. Corrections do not overwrite machine fields.

## Expanded scope/mapping retrieval
The review block also accepts scoping review*, scoping literature review*, systematic scoping review*, mapping review*, systematic map* and evidence map* in Title/Abstract. Exact PMID membership of three component searches is preserved in retrieval_sets.json: publication types, systematic[sb], scope/mapping expressions. Routes overlap. free_text_only means recovered solely by the scope/mapping expression block, not by either of the other two blocks. Review-family signals are unvalidated expression matches across title/abstract and may refer to cited methods rather than the article's design. `--reuse-cache` reuses raw records from the preceding snapshot for IDs still returned by the expanded query and downloads only additional IDs. It does not refresh previously cached metadata; run without this flag for full refresh.

## LLM extraction preparation
Offline pilot: `python scripts/prepare_extraction.py` creates a seeded stratified operational sample of 100 records and the strict JSON schema. `python scripts/extract_reviews.py` only writes a preflight estimate by default, with no network requests. See extraction/GUIA_PILOTO.md. Execution requires an explicitly enabled private config, chosen model, dated rates, OPENAI_API_KEY and --execute --max-requests N. There is no model selected and no paid extraction yet. Cache invalidates on text/model/prompt/schema/output-limit changes; API attempts and raw responses stay in ignored extraction/results. No API secrets in website assets.

Configured operational candidate: GPT-5.6 Luna, reasoning low, tariffs checked 2026-10-09. extraction/config.luna.json keeps execution disabled. Self-contained Colab notebook fixes the first five abstract-bearing pilot PMIDs, accepts a key via getpass and downloads results for manual review. No API execution occurred in preparation. Alias is not an immutable model snapshot; preserve returned model metadata and revalidate across later rounds.

## GitHub: uso prático
Repositório público com código. A coleção de resumos, o notebook que os incorpora, respostas LLM e anotações não foram publicados. A implantação privada permanece separada. Não há licença de redistribuição do código definida.

Abra **Actions → Collect PubMed snapshot → Run workflow** para coletar, gerar dashboard e preparar piloto/estimativa offline. Não chama API paga. O artifact gerado contém resumos e fica disponível temporariamente a quem possui acesso de leitura ao repositório. Para controle de acesso, execute localmente ou em repositório privado. Artifacts expiram em sete dias: arquive snapshots em armazenamento privado durável.

Localmente: `pip install -r requirements.txt`, `python scripts/update_pubmed.py`, `python scripts/prepare_extraction.py`, `python serve.py`. O clone depende da geração de dados antes de servir o dashboard. Execução paga somente em ambiente privado conforme `extraction/GUIA_PILOTO.md`, com chave em variável de ambiente e cache persistente. Nenhum workflow atual executa extração paga.

CI verifica testes de extração e sintaxe. Issues possuem formulário de correções. Veja `docs/ROADMAP.md` para implementado e planejado.
