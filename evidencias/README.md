# Evidências funcionais — 20/11/2026

Aplicativo real executado com banco temporário e dados fictícios. Os testes acionam os widgets e simulam as respostas das confirmações. Não houve participante humano nem envio real de e-mail. As imagens mostram o estado final dos cenários de demonstração e foram conferidas visualmente.

| Arquivo | O que documenta |
|---|---|
| [cadastro_cliente.png](cadastro_cliente.png) | Formulário de tutor e identificação da edição |
| [servicos_centavos.png](servicos_centavos.png) | Serviço de R$ 19,95, com edição e exibição de centavos |
| [profissionais.png](profissionais.png) | Equipe fictícia inicial e Diego, cadastrado/editado no teste gráfico |
| [agenda_profissionais.png](agenda_profissionais.png) | Reservas agendadas por profissional, com início e fim previsto |
| [historico_tutores.png](historico_tutores.png) | Thor com Maria na realização anterior e Carlos na posterior; soma em centavos |
| [cancelamento.png](cancelamento.png) | Atendimento cancelado preservado em consulta, com estado final na lista |
| [testes_automatizados.txt](testes_automatizados.txt) | 78 testes aprovados, incluindo migração e concorrência |
| [testes_interface.txt](testes_interface.txt) | 31 verificações da regressão gráfica original |
| [testes_revisao_interface.txt](testes_revisao_interface.txt) | 28 verificações gráficas da revisão, incluindo cancelamento |
| [revisao_2026-11-20.patch](revisao_2026-11-20.patch) | Alterações de texto em relação ao ZIP original preservado |

A transferência de Thor é uma alteração de exemplo feita durante o teste; o primeiro atendimento concluído conserva Maria e o seguinte conserva Carlos. O filtro e a ordem das capturas não indicam ordem de execução das tarefas. Os logs registram as verificações efetivamente realizadas. Para repetir, siga `../VALIDACAO_ETAPA4.md`.
