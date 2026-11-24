# Análise do fluxo — revisão de 20/11/2026

O sistema é um MVP acadêmico local de gestão de pet shop. A revisão transforma o retorno do solicitante em regras observáveis: reagendar para o horário realizado, recusar conclusão futura, preservar o tutor da realização, reservar cada profissional pelo intervalo do serviço e calcular valores em centavos. Python, CustomTkinter e SQLite continuam adequados ao escopo.

## Jornada implementada

| Etapa | Comportamento atual | Observação crítica |
|---|---|---|
| Preparação | Primeiro acesso, tutores, animais, serviços e profissionais | Profissional executa serviços; usuário entra no sistema. Não são a mesma entidade. |
| Agenda | Novo agendamento futuro exige profissional e serviço ativos | Protege animal e profissional, não apenas o horário pontual. |
| Reagendamento | Só agendados; permite corrigir horário para passado/agora com confirmação | O operador informa o horário real. O sistema não comprova execução física. |
| Conclusão | Exige início já alcançado e profissional atribuído | Pode terminar antes da duração prevista, mas a reserva segue até o fim estimado. |
| Cancelamento | Exige motivo, mantém registro e libera intervalo | Estados finais não são editáveis pela API. |
| Histórico | Mantém tutor e profissional da realização, descrição contratada, valor e duração | Transferência ou renomeação posterior não reescreve a identidade registrada. |
| Busca e edição | Mantém seleção enquanto visível; encerra quando filtro oculta | Se houver mudança não salva, o descarte pode ser recusado. |
| Proteção | Escritas transacionais e backup pela API SQLite | Conflito verificado dentro da transação evita duas reservas simultâneas do mesmo profissional. |

## Regras que resolvem os cinco pontos da revisão

1. **Reagendar para concluir:** novos registros exigem futuro. Um agendado pode ser corrigido para o horário em que aconteceu, inclusive passado/agora. A conclusão compara o início com o relógio local e recusa futuro. O botão Reagendar para agora evita digitação quando o serviço começou agora.
2. **Tutor histórico:** enquanto agendado, a consulta mostra o tutor atual do animal. A conclusão guarda o nome do tutor vinculado naquele momento. Depois de transferir o animal, o atendimento antigo mantém esse nome e uma nova realização usa o novo tutor. O nome do profissional na conclusão também é preservado. A descrição do serviço é a contratada no agendamento, mantida em reagendamentos do mesmo serviço.
3. **Seleção consistente:** foi reproduzida a falha anterior: ao filtrar Carlos após selecionar Maria, o destaque desaparecia, mas `self.sel` ainda apontava para Maria. Agora a tabela atualiza as linhas existentes e preserva destaque e texto em edição; se o filtro ocultar o registro, encerra a edição. Com mudanças não salvas, há confirmação de descarte e possibilidade de restaurar o filtro anterior. Não foi comprovado dano real a dados; foi comprovada inconsistência de estado.
4. **Centavos:** entradas aceitam ponto ou vírgula, sem separador de milhar. Frações de centavo novas são recusadas; 0,10 + 0,20 soma exatamente 30 centavos. Preços, atendimento e totais usam inteiros. A exibição é brasileira, com duas casas.
5. **Agenda do profissional:** cada reserva tem profissional. Uma reserva 10h–11h impede outro atendimento do mesmo profissional às 10h30, mas permite começar às 11h. Outro profissional pode atender outro animal em paralelo. Concluir às 10h20 não libera o restante da reserva; cancelar libera. A duração contratada, e não a duração atual do catálogo, define o intervalo.

## Dados de demonstração

A carga fictícia traz Ana Souza e Bruno Lima (Banho e tosa) e Carla Santos (Atendimento veterinário), quatro atendimentos concluídos e três reservas paralelas, uma por profissional. A aba Profissionais permite adicionar somente a equipe a uma base de ensaio existente, sem duplicar nomes, criar usuários ou alterar reservas antigas. Função é descritiva: não há validação de especialidade por serviço.

## Migração e limites

IDs e vínculos são preservados. Atendimentos anteriores não permitem descobrir automaticamente um tutor antigo já substituído: a migração conserva o nome disponível, marca a origem e não afirma ter recuperado a identidade original. Profissional desconhecido permanece sem atribuição, exigindo escolha antes da conclusão de agendado legado.

Valores anteriores com fração de centavo usam arredondamento decimal por metade para cima, com registro do valor anterior em `ajuste_monetario_migracao`. Valores que não produzam centavos positivos interrompem essa etapa para revisão. Os campos monetários anteriores são espelhos de compatibilidade; triggers exigem correspondência com os centavos inteiros.

Não há expediente, pausas, férias, especialidades obrigatórias, pagamentos ou perfis administrativos. Todos os acessos internos possuem as mesmas funções. Recuperação mantém as proteções anteriores, usa Resend simulada nos testes e não revoga automaticamente janelas já autenticadas. A entrega real de e-mail continua pendente de configuração. Não há necessidade de trocar a stack para cumprir esta revisão.

## Evidência acadêmica

A [matriz de requisitos](REQUISITOS_E_ACEITACAO.md) liga necessidade, regra, tela e teste. A [evolução por iterações](EVOLUCAO_POR_ITERACOES.md) registra somente a linha de base, o retorno desta conversa e a revisão verificável. O [roteiro de validação de uso](VALIDACAO_DE_USO.md) está pronto, mas o estudo com uma pessoa segue pendente. Testes funcionais e capturas não comprovam usabilidade humana.
