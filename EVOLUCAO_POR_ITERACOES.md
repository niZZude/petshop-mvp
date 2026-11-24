# Evolução por iterações — evidências disponíveis

Registro preparado em 20/11/2026. Esta linha do tempo separa o que os documentos anteriores relatam do que foi observado nesta revisão. Não há histórico Git disponível nem registros suficientes para reconstruir sprints, entrevistas ou a participação individual dos autores.

| Marco verificável | Evidência disponível | Retorno / problema constatado | Resultado |
|---|---|---|---|
| Entrega documentada em 07/11/2026 | ZIP original, código, apresentação e documento de validação datado | O material já documentava limitações de conclusão futura, agenda sem profissional e nomes históricos derivados de vínculos atuais | Linha de base com cadastros, agenda, recuperação e backup. A data e as 31 verificações gráficas pertencem ao registro anterior; não demonstram sozinhas um processo de iterações. |
| Revisão crítica em 20/11/2026, antes das mudanças | 52 testes executados com sucesso; inspeção dos 15 slides; reprodução de conclusão futura, mudança de tutor histórico e fração de centavo | A análise identificou regras incompletas e rastreabilidade acadêmica insuficiente | Proposta de correções apresentada ao solicitante. |
| Retorno do solicitante nesta conversa | Pedido explícito para reagendar sem concluir futuro; preservar tutor de cada realização; executar e demonstrar a correção da seleção; corrigir centavos; vincular agenda ao profissional; registrar evidências | O solicitante não havia percebido o problema da seleção e pediu verificação. Solicitou profissionais fictícios para experimentar a solução | Escopo da revisão definido por esse retorno, sem atribuir entrevistas não realizadas. |
| Iteração implementada em 20/11/2026 | Código revisado; 78 testes automatizados; 59 verificações gráficas; capturas reais com dados fictícios | Problemas reproduzidos viraram critérios de aceitação e testes | Profissionais e reserva por duração; reagendamento para horário realizado; conclusão futura recusada; tutor histórico; dinheiro em centavos; seleção consistente. |
| Próxima avaliação com pessoa usuária | [Roteiro e ficha](VALIDACAO_DE_USO.md) prontos | O solicitante confirmou que não houve uso observado por uma pessoa e pediu execução e prints | Pendente de aplicação; conclusões de usabilidade não são inferidas dos testes automatizados. |

## Reprodução do problema de seleção

Foi executada a interface anterior com banco temporário e dados fictícios. Depois de selecionar Maria e pesquisar Carlos, o resultado foi:

```text
ANTES: seleção visual ('1',); ID em edição 1; nome Maria Oliveira
APÓS FILTRAR CARLOS: seleção visual (); ID em edição 1; nome Maria Oliveira
```

Isso confirma a inconsistência de estado; não demonstra que uma pessoa tenha efetivamente alterado o cliente errado. Na revisão, a pesquisa preserva a seleção quando o cliente continua visível e encerra a edição quando o oculta. Se houver mudança não salva, é possível recusar o descarte e voltar ao filtro anterior. Esses caminhos passaram no teste gráfico.

## Identificação da linha de base

Arquivo original preservado na pasta superior: `petshop_entrega_atualizada.zip`.

SHA-256:

```text
8bab1191fa2236b9a15ee2df8e0b6106a0052076e464fab6d942651760190c57
```

Na inspeção anterior às mudanças, seus 20 arquivos correspondiam aos arquivos extraídos. A entrega revisada tem outro nome (`petshop_entrega_revisada_drap.zip`). O [patch da revisão](evidencias/revisao_2026-11-20.patch) permite comparar os arquivos de texto com a linha de base.

## O que ainda precisa ser registrado

Após aplicar o roteiro com uma pessoa: identificar o perfil por um código, anotar tarefas, resultado, ajuda necessária e observações literais. Só então registrar uma nova iteração com o retorno real e as mudanças efetivamente implementadas. Não preencher datas, tempos, satisfação ou dificuldades por suposição.
