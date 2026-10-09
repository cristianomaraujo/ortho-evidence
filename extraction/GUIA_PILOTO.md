# OrthoEvidence — piloto de extração por LLM

## O que está preparado
100 registros reais da coleta 20261009T175739Z. Semente 20261009. Estratos: 60 registros classificados por regras como alinhadores com resumo, 30 de outros temas com resumo e 10 sem resumo. Amostragem aleatória dentro de estratos escolhidos para um piloto operacional; não representa a coleção inteira, não constitui cálculo amostral e não é o conjunto final independente de validação. Os 10 sem resumo são controles de informação ausente e não geram chamadas.

Objetivo, população, intervenção/exposição, comparador, desfechos, contexto, tipo autodeclarado de revisão e contagens de estudos/artigos/ensaios/publicações são armazenados em campos distintos. Todos os campos reportados exigem trechos literais do título ou resumo. Contagens distinguem total da revisão, subconjunto e escopo incerto. Dados ausentes recebem valor nulo; não serão inferidos a partir de conhecimentos do modelo. PICO não é obrigatório para revisões de escopo ou narrativas.

## Execução atual
Nenhuma chamada paga efetuada. Nenhuma extração por LLM ou embedding semântico publicada. Os campos disponíveis no catálogo continuam sendo a extração por regras e o TF-IDF. Dados do piloto e resultado das extrações ficam separados da coleção automática. O prompt e o schema são versionados. A integração preparada usa OpenAI Responses com saída estruturada; outro provedor requer adaptação explícita.

## Como executar depois
1. Escolher um modelo que suporte Structured Outputs e registrar tarifas vigentes e data.
2. Copiar config.example.json para uma configuração privada com modelo, tarifas de entrada/saída por milhão de tokens e limites. O segredo fica apenas em OPENAI_API_KEY no ambiente; nunca em JSON, frontend ou repositório.
3. Rodar `python scripts/extract_reviews.py --config /caminho/privado/config.json` para prévia offline.
4. Com execução autorizada e api_execution_enabled=true, rodar primeiro `python scripts/extract_reviews.py --config /caminho/privado/config.json --execute --max-requests 5`. Isso limita o lote a cinco pedidos. Não são ativadas chamadas por visitas ao dashboard.
5. Conferir os cinco resultados e os tokens efetivamente cobrados. Ampliar o lote somente após essa avaliação.

A estimativa prévia usa bytes UTF-8/4 + 25% de margem para entrada e uma hipótese de saída. É uma aproximação, não uma contagem pelo tokenizer nem um teto financeiro garantido. A saída tem limite configurado de 4096 tokens por pedido, incluindo o orçamento utilizado pelo modelo. Não pressupõe desconto Batch nem de cache. Modelos/tarifas ausentes geram custo monetário nulo (não calculado, não gratuito).

## Rastreabilidade e recuperação
A chave de cache usa título, resumo, modelo, prompt, schema e limite de saída. PMID, hash do registro, lote de coleta, modelo retornado, ID de resposta e uso de tokens são preservados. Mudanças nesses insumos relevantes requerem nova extração; mudanças apenas em metadados não forçam processamento textual. Respostas brutas são mantidas separadamente, sem cabeçalhos de autorização.

Recusas, respostas incompletas, citações não encontradas literalmente no material de origem ou estruturas inválidas não entram no cache válido. Falhas e tentativas iniciadas são registradas antes do pedido; não há novas tentativas automáticas, pois uma falha de comunicação pode ter gerado cobrança. A retomada de uma falha exige examinar a resposta disponível e o registro da tentativa. Não apagar o histórico para repetir sem investigar.

Validação de schema e de trechos confirma formato e existência textual, não a interpretação. Dois pesquisadores devem avaliar uma amostra independente e resolver discordâncias. Medir separadamente identificação/ausência de cada campo, correção das contagens e atribuição ao escopo da própria revisão. Fixar prompt antes do teste independente; não ajustar usando esse teste. A amostra de pares de equivalência de objetivos é outra tarefa, com outro padrão humano.

## Próxima entrega após o piloto
Revisar os resultados de extração, escolher representação por embeddings abertos, comparar com TF-IDF e montar mapa de perguntas e diferenças de escopo. Não rotular saturação, redundância ou lacunas automaticamente antes dessa validação.

## Documentação usada
https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses
