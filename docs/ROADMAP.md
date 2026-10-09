# OrthoEvidence: desenvolvimento

Implementado: busca PubMed versionada, snapshots XML, deduplicação por PMID, hashes, temas por regras, similaridade TF-IDF, extração LLM com schema e trechos literais, cache por texto/modelo/prompt, avaliação local exportável. CI e coleta manual separados do site.

## Próximas entregas
1. Piloto LLM e validação independente; arquivo privado persistente das respostas e tentativas.
2. Embeddings abertos de objetivos/PICO; comparação com TF-IDF em pares independentes.
3. Mapa de perguntas repetidas e agrupamentos, com limiares calibrados. Similaridade não comprova redundância ou certeza da evidência.
4. PostgreSQL para histórico, avaliações independentes e adjudicação.
5. Atualização agendada, monitoramento de falhas e publicação revisada dos snapshots.
6. Railway sempre ativo, armazenamento durável e processamento pago somente de textos novos/modificados.

## Referências de arquitetura
[ES3](https://github.com/evidence-surveillance/es3): similaridade textual e tarefas de processamento separadas. Adaptaremos a relação para revisão–revisão, sem misturar ensaios.

[NDC-SOLES](https://github.com/camaradesuk/NDC-SOLES): coleta periódica, validação de ML/regex e correção de erros. O README registra exclusão de resumos do repositório por direitos autorais e indisponibilidade do classificador. Não incorporamos código desses projetos.

Ainda não há embeddings, classificador treinado, banco compartilhado, agendamento ou validação publicada. Não há aprendizagem por reforço.
