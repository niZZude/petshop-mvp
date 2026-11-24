# Verificação da revisão DRAP — 20/11/2026

A linha de base de 07/11/2026 foi inspecionada antes das alterações. Os 52 testes automatizados dessa base passaram nesta sessão. O resultado histórico de 108 testes mencionado na documentação antiga corresponde a arquivos excluídos anteriormente e não é usado como evidência da entrega atual.

## Resultados executados nesta revisão

| Verificação | Resultado |
|---|---|
| Suíte automatizada atual | 78 testes aprovados: 52 da suíte anterior (adaptada ao profissional obrigatório) e 26 novos |
| Regressão gráfica original | 31/31 verificações aprovadas |
| Regressão gráfica da revisão | 28/28 verificações aprovadas |
| Reprodução da seleção na versão anterior | Confirmada: busca removia destaque sem encerrar edição do ID antigo |
| Capturas | Seis imagens reais do app, com banco temporário e dados fictícios |
| Apresentação | 17 slides editáveis com notas; PDF renderizado e conferido, com prints reais |
| E-mail real | Não enviado; Resend simulada |
| Observação com pessoa usuária | Pendente; roteiro e ficha em `VALIDACAO_DE_USO.md` |

Ambiente: Linux, Python 3.14.9 e CustomTkinter 6.0.0. Dependências de verificação foram instaladas em diretório temporário; não foram incluídas no pacote. Os testes gráficos acessaram a sessão gráfica do ambiente. Não houve ensaio no Windows, migração de banco real ou teste físico de queda de energia.

## Cobertura acrescida

- Conclusão futura recusada sem alterar estado; reagendamento para horário passado/agora e conclusão; estados finais protegidos.
- Tutor da realização preservado após transferência/renomeação; novo atendimento usa novo tutor; nomes do serviço e profissional preservados.
- Entradas monetárias, frações de centavo, formato brasileiro, soma exata, armazenamento inteiro e proteção contra espelhos monetários inconsistentes.
- Profissional obrigatório/ativo, equipe fictícia repetível sem logins, conflito do mesmo profissional com animais diferentes, paralelismo entre profissionais, proteção do mesmo animal, limite exato, meia-noite e normalização dos segundos.
- Cancelamento libera intervalo; conclusão antecipada mantém reserva; reagendamento não conflita consigo e faz rollback quando outro profissional está ocupado; nova duração é revalidada.
- Duas reservas simultâneas do mesmo profissional têm um único vencedor.
- Migração repetível de IDs, duração, moeda e nomes disponíveis, indicação de origem legada, profissional desconhecido e registro dos ajustes monetários.
- Widgets: seleção preservada, filtro com descarte aceito/recusado, preço correto, atribuição/filtro de profissional, conclusão/reagendamento, histórico de dois tutores, total em centavos e inativação/reativação.

## Como repetir

Na pasta `petshop/`, com requisitos instalados:

```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python tests/smoke_interface.py
python tests/smoke_revisao.py
```

Para gerar as capturas, instalar Pillow no ambiente de testes e executar, em sessão gráfica:

```bash
python tests/smoke_revisao.py --capturas ../evidencias
```

Os logs de execução estão em `evidencias/testes_automatizados.txt`, `evidencias/testes_interface.txt` e `evidencias/testes_revisao_interface.txt`. As capturas foram conferidas visualmente. Nenhum teste usa o banco do aplicativo ou dados reais; nenhum e-mail foi enviado. Validação funcional automatizada não equivale a observação de uma pessoa usando o sistema.
