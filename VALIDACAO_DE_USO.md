# Validação de uso — roteiro e ficha de observação

**Situação em 20/11/2026: sessão com pessoa usuária ainda não realizada.** O solicitante confirmou nesta conversa que o projeto nunca foi usado dessa forma e autorizou executar o app e produzir prints. Foi realizada demonstração funcional automatizada com o aplicativo real e dados fictícios; o roteiro humano abaixo permanece disponível para aplicação futura. As 59 verificações gráficas executadas pelo agente são testes funcionais dos widgets, com respostas automáticas às confirmações. Elas não medem entendimento, satisfação ou dificuldade de uma pessoa. As imagens em `evidencias/` usam dados fictícios e não representam uma sessão com participante.

## Preparação

Usar uma cópia de demonstração, sem dados reais. Executar `python app.py`, criar o acesso e aceitar a carga fictícia, ou usar **Profissionais → Adicionar equipe fictícia** em uma base de ensaio já existente. Confirmar que há serviços e profissionais ativos. O observador lê uma tarefa de cada vez, deixa a pessoa tentar e anota qualquer ajuda; não deve conduzir os cliques nem inventar resultados. Não é necessário gravar nome completo nem imagem do participante.

## Tarefas e resultados esperados

| Tarefa para a pessoa | Resultado esperado / critério de sucesso | Registrar durante a sessão |
|---|---|---|
| T1. Cadastre um tutor fictício e um animal | Tutor salvo com CPF válido e animal vinculado corretamente. Usar, por exemplo, CPF de teste `98765432100`, se ainda não cadastrado. | Tempo; sucesso; erros; ajuda; observação literal |
| T2. Prepare um serviço de R$ 35,75 e duração de 45 min | Valor exibido como `R$ 35,75`; duração 45. Ao tentar `35,755`, recebe orientação e mantém o formulário. | Se entendeu vírgula/ponto e mensagem de erro |
| T3. Agende amanhã às 10h com Ana Souza | Reserva do animal com início 10h e fim 10h45. | Se identificou profissional e fim previsto |
| T4. Tente outro animal com Ana às 10h15; depois escolha Bruno | Ana é recusada por conflito. Bruno aceita trabalho paralelo. A função profissional é descritiva, sem restrição de especialidade. | Se entendeu o conflito e conseguiu corrigi-lo |
| T5. Cancele a reserva de Ana com motivo; tente ocupar o intervalo novamente | Registro cancelado permanece; profissional fica disponível nesse intervalo. | Se entendeu que cancelar preserva o registro |
| T6. Tente concluir um atendimento futuro; depois corrija com Reagendar para agora e conclua | Futuro é recusado. Correção confirmada permite concluir. Usar intervalo atual sem conflito com outro teste. | Se distinguiu reagendar de concluir e entendeu as confirmações |
| T7. Transfira o animal para outro tutor e consulte o histórico | Atendimento concluído conserva o tutor anterior. Outro atendimento, realizado e concluído depois da transferência, usa o novo tutor. | Se interpretou corretamente os dois registros |
| T8. Edite o nome de um tutor sem salvar e pesquise outro tutor | Se ocultar o registro em edição, a confirmação permite preservar ou descartar. Recusar mantém texto, seleção e filtro anterior; aceitar encerra edição. | Se o rótulo Editando #ID e o descarte foram compreendidos |

O observador deve anotar a sequência e os horários utilizados para evitar que reservas anteriores prejudiquem tarefas seguintes. Se isso ocorrer, registrar como interferência do roteiro e repetir com base limpa, sem apagar o resultado original.

## Ficha por participante — preencher somente após observar

| Campo | Registro |
|---|---|
| Código do participante e perfil | Pendente |
| Data, ambiente e versão do pacote | Pendente |
| Observador | Pendente |
| Experiência com pet shop ou sistemas semelhantes | Pendente |

| Tarefa | Sucesso sem ajuda / com ajuda / não concluiu | Tempo observado | Erros e ajuda prestada | Dificuldade ou fala observada |
|---|---|---|---|---|
| T1 | Pendente | Pendente | Pendente | Pendente |
| T2 | Pendente | Pendente | Pendente | Pendente |
| T3 | Pendente | Pendente | Pendente | Pendente |
| T4 | Pendente | Pendente | Pendente | Pendente |
| T5 | Pendente | Pendente | Pendente | Pendente |
| T6 | Pendente | Pendente | Pendente | Pendente |
| T7 | Pendente | Pendente | Pendente | Pendente |
| T8 | Pendente | Pendente | Pendente | Pendente |

## Síntese após a sessão

| Evidência observada | Interpretação limitada à sessão | Melhoria proposta | Prioridade e justificativa | Implementada? Como foi verificada? |
|---|---|---|---|---|
| Pendente | Pendente | Pendente | Pendente | Pendente |

Perguntas finais: em qual tarefa precisou pensar mais? O que esperava que acontecesse? Conseguiu identificar o horário reservado e o registro em edição? Registrar respostas reais, sem induzir aprovação. Uma sessão curta orienta a próxima iteração; não comprova usabilidade para todos os públicos.
