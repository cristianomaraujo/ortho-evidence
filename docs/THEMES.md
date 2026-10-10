# Classificação temática rules-v2
24 eixos, múltiplas categorias por revisão. Regras sobre título, objetivo extraído, resumo e descritores MeSH. Título/objetivo/MeSH exigem ao menos um termo; somente resumo exige dois termos distintos. Correspondência por limites de palavra, com normalização Unicode. O eixo principal é o primeiro na ordem da taxonomia; essa ordem não representa relevância.

O mapa e as fichas usam todas as categorias, com fontes e termos auditáveis. A contagem por eixo se sobrepõe. Falhas são separadas em informação insuficiente (sem resumo e MeSH) e tema não identificado pelas regras; nenhuma delas significa exclusão.

Coleção atual: 8.552 registros. Antes: 5.772 (67,5%) em Outros temas. Agora: 700 (8,2%) sem eixo, dos quais 2 com informação insuficiente. Esta é cobertura computacional, não acurácia. Categorias podem refletir menções incidentais, métodos ou achados e não o objetivo principal. As regras não avaliam relevância ortodôntica ou redundância.

Reclassificar sem recolher ou recalcular vetores: python scripts/reclassify_dataset.py. Publica taxonomy.json e theme-report.json; conserva rodada da coleta e hashes de origem. Não faz chamadas LLM. Revisar amostra independente por eixo, incluindo falhas e múltiplos rótulos, antes de interpretar distribuição temática. A taxonomia ainda não é uma ontologia validada.
