# Protocolo de avaliação

Perguntas em `questions.json`. Os casos de teste foram definidos antes de sua primeira
execução; uma pergunta ampla de desenvolvimento foi acrescentada durante a inspeção de
dev. Dev e test têm casos distintos. Os parâmetros iniciais são top-k = 6, mínimo de 2 evidências e
cosseno mínimo 0,42. Estes valores são heurísticos, não probabilidades calibradas.

1. Executar dev em modo somente recuperação. Qualquer ajuste motivado por dev deve
   ser registrado antes de observar test.
2. Congelar configuração e executar test com recuperação e com o LLM real.
3. Guardar IDs, textos, scores, filtros, status, tempo e resposta de cada caso.
4. Inspecionar relevância e suporte das respostas separadamente; a métrica automática
   de gate compara apenas a presença/ausência de evidências com a expectativa.

O conjunto é autoral e pequeno, não um benchmark independente. Não contém julgamentos
exaustivos de todos os documentos: **não se estima recall documental**. Questões fora
do domínio são exemplos, não uma certificação de resistência a todos os ataques.

Métricas automáticas: acurácia do gate, cobertura nas perguntas respondíveis, taxa de
abstenção nas não respondíveis e número de respostas com referências aceitas. Uma
abstenção por formatação inválida do LLM não equivale a ausência de documentos relevantes.

Na revisão de relevância, julgar se cada trecho sustenta a pergunta. Na revisão factual,
conferir se cada afirmação da síntese decorre dos comentários citados. IDs existentes
e boa redação, isoladamente, não atendem a esse critério. Os julgamentos feitos pelo
desenvolvedor são identificados como tal, sem atribuí-los a avaliadores externos.

## Ajustes usando somente desenvolvimento

A recuperação inicial gerou contextos repetitivos. A primeira execução foi preservada
em `reports/evaluation_dev_initial_rag.json`. Antes de executar test, acrescentamos MMR
entre os 100 candidatos distintos mais próximos, com lambda 0,7. A similaridade exibida
continua sendo o cosseno original; MMR altera a ordem de seleção para diversificar.

A pergunta ampla de dev recuperou um título genérico como “avaliação do vendedor”.
Foi definida uma expansão lexical somente para perguntas sobre “principais problemas”
ou “principais reclamações” sem tema específico: compra, produto, entrega e atendimento.
Não se infere a frequência de cada tema. A inspeção e a nova execução dev constam em
`reports/dev_broad_refinement.json` e `reports/evaluation_dev_rag.json`.

O corte 0,42 e o mínimo de duas evidências foram mantidos. A primeira avaliação test
teve 8/9 decisões corretas de presença de evidência: uma pergunta eleitoral recuperou
comentários com “Brasil” e gerou uma resposta irrelevante. O resultado foi preservado em
`reports/evaluation_test_before_scope_fix.json`.

Após essa falha, acrescentamos um gate lexical conservador que exige vocabulário de
experiência de compra antes da busca. Essa é uma **correção motivada pelo teste**.
O conjunto test foi reutilizado como **regressão**, com 9/9 decisões de gate corretas.
Não se apresenta essa segunda execução como avaliação independente ou garantia de
generalização. Os hashes do código usado em cada execução estão nos relatórios.

A cobertura de geração é uma medida distinta: somente 3 das 4 perguntas respondíveis
receberam uma síntese aceita; a quarta apresentou evidências, mas o LLM não passou na
checagem de referências. O relatório de inspeção de relevância deve ser lido junto às
métricas de gate: uma pergunta pode recuperar documentos irrelevantes mesmo passando.
