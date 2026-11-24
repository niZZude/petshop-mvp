# Sistema para Pet Shop

MVP desktop de Desenvolvimento Rápido de Aplicações em Python. Usa Python, CustomTkinter e SQLite para gerenciar clientes, animais, serviços, profissionais, agenda e histórico.

**Revisão DRAP de 20/11/2026:** conclusão após o início, reagendamento para o horário realizado, tutor histórico, agenda por profissional e valores em centavos. Veja [requisitos e aceitação](../REQUISITOS_E_ACEITACAO.md), [evolução comprovável](../EVOLUCAO_POR_ITERACOES.md) e [roteiro de validação com usuário](../VALIDACAO_DE_USO.md).

**Entrega reconstruída em 07/11/2026:** a pasta original foi excluída durante o desenvolvimento. O código foi reconstruído com as funções e regras revisadas e testado novamente. O banco antigo e os documentos binários excluídos não foram recuperados. O primeiro uso cria um banco novo, sem usuários ou dados reais.

## Instalar e executar

Requer Python 3.10+ com Tkinter.

```bash
cd petshop
python -m venv .venv
source .venv/bin/activate
# No Windows PowerShell, use: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

O banco `petshop.db` fica ao lado de `database.py`. O primeiro acesso cria usuário, senha e e-mail de recuperação. O e-mail sugerido é `nixxude@gmail.com`; revise antes de salvar. Não há senha padrão. A senha exige pelo menos seis caracteres, letras e números e é guardada com PBKDF2-SHA256 e sal. Cinco falhas de login bloqueiam a tela por 30 segundos.

Os dados fictícios podem ser oferecidos pelo app ou carregados com `python popular_demo.py` em um banco vazio. Essa carga não cria usuários nem envia e-mails. Na aba **Profissionais**, o botão **Adicionar equipe fictícia** inclui Ana Souza, Bruno Lima e Carla Santos, inclusive em um banco que já tenha cadastros. É seguro repetir: nomes existentes são preservados. As funções são descritivas; não há restrição de especialidade por serviço.

## Jornada do aplicativo

1. **Clientes:** nome, telefone com DDD e CPF são obrigatórios para novos clientes. E-mail e endereço são opcionais. Clique na linha para editar. A busca aceita nome, telefone, CPF com máscara e e-mail.
2. **Animais:** informe tutor, nome e espécie. Raça e observações são opcionais.
3. **Serviços:** prepare nome, preço e duração. Preços aceitam vírgula ou ponto decimal, sem separador de milhar, com até duas casas (ex.: `50,05`). Frações de centavo são recusadas. Use inativação em vez de exclusão.
4. **Profissionais:** cadastre nome e função ou adicione a equipe fictícia. Inativar impede novas reservas e mantém os registros existentes. Profissional é quem executa o serviço; usuário é quem entra no sistema.
5. **Atendimentos:** selecione animal, serviço e profissional ativos e data futura em `dd/mm/aaaa hh:mm`. Só agendados podem ser editados, cancelados ou concluídos. Na edição, é permitido corrigir o horário para o passado ou usar **Reagendar para agora**, com confirmação. Conclusão exige que o início tenha chegado. Cancelamento exige motivo.
6. **Histórico:** conserva o nome do tutor na conclusão, a descrição contratada e o profissional da realização. Mostra o total de serviços concluídos; não controla pagamentos.
7. **Backup:** no cabeçalho, escolha um arquivo novo para obter uma cópia consistente do SQLite, inclusive com WAL e o app aberto.

Alterações mostram antes/depois e pedem confirmação. Exclusões e mudanças de estado também pedem confirmação. Cliente com animais e animal com atendimentos não podem ser excluídos. Validações recusadas preservam os dados do formulário. O rótulo **Editando #ID** identifica o registro. Atualizar uma lista preserva seleção e edição enquanto o registro continuar visível. Se um filtro o ocultar, a edição é encerrada; havendo alterações não salvas, o descarte exige confirmação e pode ser recusado.

## CPF e e-mail únicos

CPF e e-mail informado têm restrições únicas **separadas** no banco. Nome, telefone e endereço podem repetir, inclusive todos juntos. Vários clientes podem não informar e-mail; ausência é `NULL`.

CPF é guardado como texto sem máscara e validado pelo algoritmo dos dígitos verificadores. Isso não verifica titularidade ou situação cadastral. E-mail é normalizado sem espaços nas bordas e em minúsculas; não há confirmação de titularidade no cadastro.

Avisos amarelos de nome, telefone ou endereço semelhantes permitem salvar. CPF/e-mail de outro cliente recebem borda vermelha e bloqueiam a gravação. A própria pessoa é ignorada durante a edição. O alerta é consultivo; a restrição do banco decide o resultado final.

Se um banco compatível de versão anterior for recuperado de backup, a migração preserva IDs e vínculos. Clientes legados sem CPF ficam pendentes até regularização. Duplicados preexistentes geram os IDs para revisão, sem exclusão automática. A instalação da proteção de identidade é atômica; as outras migrações ocorrem em etapas transacionais separadas.

## Recuperação de senha com Resend

### Configurar o modo de teste

1. Use uma conta Resend cujo endereço seja `nixxude@gmail.com`.
2. Crie uma chave com permissão de envio na [Resend](https://resend.com/api-keys).
3. Copie `resend.ini.example` para **`resend.ini`**, na mesma pasta de `app.py`.
4. Preencha `api_key` nesse arquivo local. Mantenha `from = Pet Shop <onboarding@resend.dev>`.
5. Abra o app. Na primeira utilização, cadastre `nixxude@gmail.com` no usuário. Para um usuário já existente, entre e use **Minha conta**, confirmando a senha atual.
6. Saia, clique em **Esqueci minha senha**, informe usuário e e-mail, peça o código e use-o para definir a nova senha.

Também é possível definir `RESEND_API_KEY` e `RESEND_FROM` como variáveis de ambiente; elas têm prioridade sobre o arquivo. O arquivo preenchido está excluído pelo `.gitignore`. Não coloque a chave no código, nos slides ou no relatório.

No modo de teste, o remetente `onboarding@resend.dev` só envia para o e-mail da própria conta Resend. `nixxude@gmail.com` é **destinatário**, não remetente Gmail da API. Para recuperar contas com outros e-mails, use um domínio verificado e um remetente desse domínio. Referência: [restrição do remetente de teste](https://resend.com/docs/knowledge-base/403-error-resend-dev-domain).

### Funcionamento

- Cada usuário tem seu e-mail de recuperação; o e-mail do cliente/tutor não é usado.
- A resposta da solicitação é genérica quando usuário/e-mail não correspondem a uma conta.
- Código aleatório de oito dígitos, validade de 10 minutos, cinco tentativas e intervalo de 60 segundos entre envios.
- O banco guarda hash e sal do código, sem o código em texto puro.
- Novo código substitui o anterior. Alterar o e-mail do usuário invalida códigos pendentes.
- Uso do código e troca da senha ocorrem na mesma transação. Duas redefinições simultâneas não reutilizam o código.
- Falha ou envio incerto invalida o código reservado e mantém a senha anterior.
- HTTP em segundo plano, timeout de 15 segundos e chave de idempotência. Nenhuma transação fica aberta durante o envio.

A entrega real não foi executada: não há chave configurada. Os testes usam um provedor simulado. Aceitação pela API não comprova chegada na caixa de entrada. Fonte: [API de envio](https://resend.com/docs/api-reference/emails/send-email).

Uma janela já autenticada não é encerrada automaticamente após redefinir a senha. Este MVP não possui serviço central de sessões. A chave no desktop é adequada à demonstração local controlada; não distribua uma chave de envio junto com o programa. Para distribuição, use um backend para envio e limites globais.

## Agenda, transações e limites

Preço e duração são copiados para cada atendimento. Reagendar com o mesmo serviço preserva ambos; trocar o serviço copia os valores novos. Em um banco legado, a duração é preenchida a partir do serviço atual porque o histórico desse campo nunca foi armazenado.

Escritas usam `BEGIN IMMEDIATE`, commit e rollback. Conexões ativam `foreign_keys`, `synchronous=FULL` e WAL. A sobreposição é conferida dentro da transação. SQL externo protege CPF/e-mail únicos, vínculos quando `foreign_keys` está ativo, duração positiva inteira, status, indicador ativo e cancelamento com motivo; o algoritmo completo de CPF, datas e sobreposição são aplicados pela API Python.

A agenda verifica o intervalo completo `[início, início + duração)`, tanto do animal quanto do profissional, dentro da mesma transação. Animais diferentes podem ser atendidos ao mesmo tempo por profissionais diferentes. O próximo atendimento pode começar exatamente no fim do anterior. Concluir antes do fim estimado mantém a reserva até esse fim; cancelar libera o intervalo. O filtro de profissionais inclui inativos para consulta e a tabela mostra o fim previsto. Não há jornada de trabalho, pausa, férias, controle de especialidade, pagamentos ou perfis de administrador/atendente.

Os campos `preco_centavos` e `valor_centavos` são inteiros e são a fonte dos cálculos e totais. `preco` e `valor` permanecem como espelhos por compatibilidade com o banco anterior, com triggers que exigem correspondência. A interface usa `R$ 50,05`. Valores novos com frações de centavo são recusados.

Na migração de bancos anteriores, valores com frações de centavo são arredondados por `ROUND_HALF_UP` e os valores anteriores são registrados em `ajuste_monetario_migracao`. Valores que não gerem centavos positivos interrompem essa etapa com o ID para revisão. Os nomes disponíveis na migração são conservados e exibidos como **Legado: dados migrados**; não se pode recuperar automaticamente quem era o tutor em uma data anterior. Profissionais antigos desconhecidos ficam sem atribuição: é necessário escolher um profissional antes de concluir um agendado legado. Nenhum vínculo fictício é atribuído automaticamente. A revisão de moeda, profissionais e histórico é uma etapa transacional; as migrações anteriores continuam em etapas separadas.

O tutor é atualizado enquanto o atendimento está agendado e congelado na conclusão, junto do nome do profissional. Assim, transferir o animal depois não altera o atendimento realizado; uma nova realização usa o novo tutor. A descrição e o valor do serviço são os contratados no agendamento; reagendar com o mesmo serviço os conserva. A análise detalhada está em `../ANALISE_DO_FLUXO.md`.

## Verificação

```bash
python -W error::ResourceWarning -m unittest discover -s tests -v
python tests/smoke_interface.py
python tests/smoke_revisao.py
```

A revisão tem 78 testes automatizados e 59 verificações gráficas (31 de regressão e 28 novas). Inclui migração, histórico por tutor, centavos, conclusão, reagendamento e conflito de profissionais em concorrência. Os testes gráficos requerem ambiente gráfico. Usam bancos temporários e Resend simulada; não usam o banco do aplicativo nem enviam e-mails reais. Capturas reais com dados fictícios estão em `../evidencias/`. Elas documentam a interface; a observação de uma pessoa usando o sistema segue pendente até aplicação do roteiro.

## Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Interface, fluxos e confirmações |
| `login.py` | Primeiro acesso, login e recuperação gráfica |
| `database.py` | Persistência, transações, regras e backup |
| `validacoes.py` | Campos, CPF, números e credenciais |
| `duplicidade_clientes.py` | Migração e unicidade de identidade |
| `similaridade_clientes.py` | Avisos consultivos |
| `recuperacao.py` | Código temporário e integração HTTPS com Resend |
| `resend.ini.example` | Modelo de configuração local, sem chave |
| `popular_demo.py` | Carga de dados fictícios |
| `tests/` | Regressão automatizada e gráfica |
