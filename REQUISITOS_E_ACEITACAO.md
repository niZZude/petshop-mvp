# Requisitos e critérios de aceitação — revisão DRAP de 20/11/2026

Escopo: aplicação desktop local de gestão de atendimentos de pet shop, com Python, CustomTkinter e SQLite. Esta matriz explicita o comportamento implementado a partir dos arquivos disponíveis e do retorno do solicitante nesta revisão. Não substitui uma rubrica oficial da disciplina, que não foi fornecida. A numeração RF abaixo é desta revisão; as notas antigas RN13/RN14 não constituem um catálogo completo de requisitos.

## Matriz de rastreabilidade

Os nomes `Sistema` e `Recuperacao` remetem a [test_sistema.py](petshop/tests/test_sistema.py); `Revisao`, a [test_revisao.py](petshop/tests/test_revisao.py). Os fluxos de widgets estão em [smoke_interface.py](petshop/tests/smoke_interface.py) e [smoke_revisao.py](petshop/tests/smoke_revisao.py).

| ID / necessidade | Regra e critério observável de aceitação | Tela | Evidência automatizada |
|---|---|---|---|
| RF01 — Criar acesso e autenticar | Primeiro uso não tem senha padrão. Credencial válida entra; inválida é recusada. Cinco erros bloqueiam a janela por 30 s. | Primeiro acesso / Login | `Sistema.test_usuario_hash_login_normalizado`; smoke original: primeiro acesso e bloqueio |
| RF02 — Recuperar acesso | Código válido troca senha uma vez; código expirado, consumido ou com cinco erros não troca. | Esqueci minha senha | `Recuperacao.test_fluxo_uso_unico`, `test_expiracao`, `test_limite_falhas`; smoke original: nova senha |
| RF03 — Identificar tutores | CPF obrigatório e válido em novo cadastro; CPF e e-mail são únicos separadamente; telefone/nome/endereço podem repetir. | Clientes | `Sistema.test_cpf_repetido_email_diferente`, `test_email_repetido_cpf_diferente`, `test_demais_dados_iguais` |
| RF04 — Vincular animais | Animal tem tutor existente. Exclusão de tutor com animais e de animal com atendimentos é recusada. | Animais / Clientes | `Sistema.test_fk_invalida`, `test_cliente_vinculado_nao_exclui`, `test_animal_com_historico_nao_exclui` |
| RF05 — Precificar serviços | `50,05` e `50.05` viram 5005 centavos; `0,005` é recusado; preço e total são exibidos com duas casas. Duração é inteira e positiva. | Serviços / Histórico | `Revisao.test_centavos_entrada_exibicao_e_soma`, `test_fracao_de_centavo_e_formato_ambiguo_recusados`, `test_centavos_soma_historico`; smoke novo: preço e total |
| RF06 — Manter profissionais | Nome e função são obrigatórios; nome não se repete; inativação remove das novas reservas sem apagar histórico. Equipe fictícia pode ser adicionada sem duplicar ou criar login. | Profissionais | `Revisao.test_profissional_obrigatorio_ativo_e_unico`, `test_equipe_demo_repetivel_e_sem_logins`; smoke novo: inativar/reativar |
| RF07 — Agendar | Novo atendimento exige horário futuro, animal existente, serviço ativo e profissional ativo. Copia preço, descrição e duração contratados. | Atendimentos | `Sistema.test_data_passada_e_servico_inativo`; `Revisao.test_profissional_obrigatorio_ativo_e_unico`, `test_reagendar_preserva_preco_duracao_e_descricao` |
| RF08 — Reservar o profissional | Mesmo profissional não atende dois animais em intervalos sobrepostos. Reserva vai do início ao fim estimado; início no fim exato é permitido. | Atendimentos / filtro de profissional | `Revisao.test_mesmo_profissional_outro_animal_bloqueia_intervalo`, `test_inicio_no_fim_exato_permitido`, `test_intervalo_atravessa_meia_noite` |
| RF09 — Permitir trabalho paralelo | Profissionais diferentes atendem animais diferentes no mesmo horário. O mesmo animal não pode ter duas reservas sobrepostas. | Atendimentos | `Revisao.test_profissionais_distintos_podem_atender_em_paralelo`, `test_mesmo_animal_outro_profissional_continua_bloqueado` |
| RF10 — Reagendar e concluir | Agendado pode ter horário corrigido para o passado/agora, com confirmação na tela. Futuro não conclui. Após o início pode concluir; conclusão antecipada não libera o restante da reserva. | Atendimentos / Reagendar para agora / Concluir | `Revisao.test_reagendar_passado_e_concluir`, `test_reagendar_minuto_atual_e_concluir`, `test_conclusao_futura_recusada_sem_mudar_estado`, `test_concluir_antes_do_fim_nao_libera_reserva`; smoke novo |
| RF11 — Cancelar sem apagar | Cancelamento exige motivo, conserva registro e libera intervalo. Estados finais não podem ser editados pela API. | Atendimentos / Cancelar | `Sistema.test_cancelar_exige_motivo`, `test_status_final_bloqueia_mutacoes`; `Revisao.test_cancelar_libera_profissional`; smoke original |
| RF12 — Preservar realização | Conclusão guarda o nome do tutor e profissional da realização. Transferência posterior não altera o passado; nova realização usa o novo tutor. Descrição contratada é preservada. | Histórico | `Revisao.test_tutor_historico_e_novo_atendimento`, `test_tutor_da_realizacao_e_nao_so_do_agendamento`, `test_servico_e_profissional_historicos_preservados`; smoke novo: dois tutores |
| RF13 — Editar sem seleção oculta | Busca mantém destaque e edição enquanto o registro está visível. Se o ocultar, encerra edição; alterações não salvas exigem confirmação de descarte, que pode ser recusada. | Todas as listas com formulário | Smoke novo: busca mantém seleção; recusar descarte; aceitar encerra; pesquisa não grava |
| RF14 — Proteger reservas simultâneas | Duas gravações concorrentes no mesmo intervalo/profissional têm um único vencedor, mesmo com animais distintos. | Camada de dados de Atendimentos | `Revisao.test_concorrencia_mesmo_profissional_animais_distintos`; `Sistema.test_concorrencia_agenda` |
| RF15 — Migrar e copiar dados | Preserva IDs e vínculos; profissionais desconhecidos não são inventados. Origem legada é indicada. Ajustes monetários conservam valor anterior. Backup consistente não sobrescreve arquivo. | Inicialização / Histórico / Backup | `Revisao.test_migracao_legada_preserva_ids_e_indica_origem`; `Sistema.test_backup`, `test_migracao_conflito_nao_exclui` |

## Decisões explícitas de negócio

- O horário corrigido é informado pelo operador. O MVP não verifica presença física, não modela pagamentos e não comprova prestação de serviço.
- O tutor da realização é o tutor vinculado ao animal quando o operador conclui. Para registrar uma troca de responsável, atualize o animal antes de concluir o novo atendimento. Depois da conclusão, renomear ou transferir não reescreve o nome gravado.
- A reserva considera `[início, fim estimado)`. Atendimentos agendados e concluídos ocupam esse intervalo; cancelados não. Alterar a duração no catálogo não encurta uma reserva já contratada.
- Profissional e usuário de login são entidades diferentes. A função do profissional é descritiva: não há regra de habilitação por serviço, expediente, pausas ou férias nesta entrega.
- Novos preços com fração de centavo são recusados. Valores legados são arredondados por metade para cima, com registro de ajustes. Totais somam inteiros em centavos.
- A migração não reconstrói uma identidade histórica que nunca foi armazenada: usa os nomes disponíveis e marca a origem como migração. Agendados legados exigem atribuição de profissional antes da conclusão.

## Evidência e limite

A revisão executou 78 testes automatizados e 59 verificações gráficas com dados fictícios. As capturas são do aplicativo real. Entrega de e-mail real, ensaio no Windows e observação de uma pessoa usando o sistema não foram comprovados nesta execução. O [roteiro de uso](VALIDACAO_DE_USO.md) define como registrar essa última evidência sem confundi-la com automação.
