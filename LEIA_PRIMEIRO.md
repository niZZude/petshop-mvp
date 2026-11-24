# Entrega Pet Shop — revisão DRAP de 20/11/2026

Aplicativo desktop local com tutores, animais, serviços, profissionais, agenda e histórico. A revisão implementa o retorno sobre os cinco pontos da análise crítica e inclui documentação de evidências.

- **Executar:** siga [petshop/README.md](petshop/README.md).
- **Experimentar a equipe:** aceite os dados fictícios no primeiro uso ou abra **Profissionais → Adicionar equipe fictícia**. Ana Souza, Bruno Lima e Carla Santos são exemplos, sem usuário de login associado.
- **Reagendar e concluir:** selecione um agendado; corrija data/hora ou use **Reagendar para agora**. Confirme e depois conclua. Futuro não pode ser concluído.
- **Agenda:** mesmo profissional e mesmo animal não podem ter intervalos sobrepostos. A conclusão antecipada mantém a reserva até o fim previsto; cancelamento libera.
- **Valores:** use `50,05` ou `50.05`. Frações de centavo são recusadas; tabelas e totais mostram duas casas.
- **Apresentar:** `Etapa4_PetShop.pptx` e `Etapa4_PetShop.pdf`, atualizados para a revisão, com 17 slides e notas de fala. Capturas reais com dados fictícios estão em `evidencias/`.
- **Evidências:** [requisitos](REQUISITOS_E_ACEITACAO.md), [iterações comprováveis](EVOLUCAO_POR_ITERACOES.md), [validação de uso](VALIDACAO_DE_USO.md) e [resultados técnicos](VALIDACAO_ETAPA4.md).
- **Resend:** configuração local conforme README; testes não enviam e-mail real. Nunca incluir chave no pacote.

A linha de base reconstruída de 07/11/2026 está preservada no ZIP original da pasta superior. A revisão tem um novo pacote, `petshop_entrega_revisada_drap.zip`. O banco original e o antigo relatório DOCX excluídos antes desta revisão não foram recuperados. Não há dados reais, credenciais padrão ou chave de API na entrega.

O histórico passa a preservar o tutor da realização. Registros anteriores à revisão conservam os nomes disponíveis na migração e são identificados como legados; o sistema não inventa o tutor ou profissional de um passado que não foi armazenado. CPF e e-mail informado continuam únicos separadamente. Usuário de acesso, tutor e profissional são entidades distintas.
