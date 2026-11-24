"""Gera apresentação editável, com diagramas nativos e notas de fala.
Requer python-pptx (apenas para gerar os slides, não para executar o app).
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

BASE = Path(__file__).resolve().parent.parent
r = Presentation()
r.slide_width, r.slide_height = Inches(13.333), Inches(7.5)
C = {'bg':'F7F4EA','ink':'18302F','green':'1F7A6E','muted':'627471','orange':'F08A4B','yellow':'E8BE57','white':'FFFFFF','light':'E8EDE7','red':'B3402F'}
FONT = 'DejaVu Sans'


def rgb(c): return RGBColor.from_string(C.get(c,c))


def shape(s,x,y,w,h,fill,kind=MSO_SHAPE.ROUNDED_RECTANGLE):
    z=s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    z.fill.solid();z.fill.fore_color.rgb=rgb(fill);z.line.fill.background()
    if kind==MSO_SHAPE.ROUNDED_RECTANGLE:
        z.adjustments[0]=.12
    return z


def text(s,x,y,w,h,txt,size=20,color='ink',bold=False):
    z=s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h));tf=z.text_frame
    tf.word_wrap=True
    tf.margin_left=tf.margin_right=Inches(.02)
    tf.margin_top=tf.margin_bottom=0
    for i,line in enumerate(txt.split('\n')):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text=line;p.font.name=FONT;p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=rgb(color)
        p.space_after=Pt(8)
    return z


def slide(title,sub='',note=''):
    s=r.slides.add_slide(r.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=rgb('bg')
    n=len(r.slides)
    text(s,.55,.28,11.7,.3,'PET SHOP  /  DESENVOLVIMENTO RÁPIDO EM PYTHON',10,'green',True)
    text(s,.55,.85,12.2,.85,title,32,'ink',True)
    if sub: text(s,.58,1.75,12,.6,sub,17,'muted')
    shape(s,.55,7.03,12.2,.015,'green',MSO_SHAPE.RECTANGLE)
    text(s,.57,7.15,11,.2,'Estácio  •  Eduardo Leal e João Sérgio Araújo  •  20/11/2026',9,'muted')
    text(s,12.2,7.12,.6,.25,f'{n:02}',11,'green',True)
    s.notes_slide.notes_text_frame.text=note
    return s


def card(s,x,y,w,h,number,title,body,color='green'):
    shape(s,x,y,w,h,'white')
    shape(s,x+.2,y+.22,.6,.48,color)
    text(s,x+.28,y+.28,.45,.3,number,13,'white',True)
    text(s,x+.22,y+.95,w-.44,.7,title,23,'ink',True)
    text(s,x+.22,y+1.85,w-.44,h-2.02,body,18,'muted')


def arrow(s,x,y,w=.5):
    shape(s,x,y,w,.23,'orange',MSO_SHAPE.CHEVRON)


s=slide('Sistema para Pet Shop','Cadastro consistente, agenda e recuperação de acesso',
'''Abertura (30 s). Apresentar o problema de uma recepção de pet shop. O foco é um MVP desktop para uma disciplina de desenvolvimento rápido, com persistência local e regras verificáveis. Não apresentar como ERP completo nem como sistema multiunidade. A apresentação substitui a versão anterior da Etapa 4 e descreve as regras atuais.''')
shape(s,.6,2.65,7.5,3.65,'ink')
text(s,.92,3.02,6.8,1.5,'Uma rotina completa.\nUm banco local.',34,'white',True)
text(s,.95,5.08,6.6,.7,'Python  +  CustomTkinter  +  SQLite',20,'yellow')
text(s,8.55,2.8,4.2,.7,'Centro Universitário\nEstácio de Sá',20,'green',True)
text(s,8.55,3.9,4.15,2.35,'Professor Hericlys Borges\n\nEduardo Guther Pontes Leal\n202402343289\nJoão Sérgio Cavalcante Marques Araújo\n202503329771',15)

s=slide('O que o MVP resolve','Escopo fechado para um balcão de atendimento local.',
'''Explicar o antes/depois: cadastros soltos e agenda sem vínculo dão lugar a registros relacionados e regras explícitas. O histórico mostra serviços concluídos; não comprova recebimento financeiro. A escolha por bibliotecas pequenas reduz preparação e facilita demonstração na faculdade.''')
card(s,.6,2.65,3.9,3.85,'01','Organizar','Tutores, animais, serviços e profissionais no mesmo aplicativo.')
card(s,4.72,2.65,3.9,3.85,'02','Agendar','Organizar reservas por animal e profissional, sem sobreposição.')
card(s,8.84,2.65,3.9,3.85,'03','Preservar','Histórico, cadastros e acesso sem apagar o banco.')

s=slide('Fluxo principal do atendimento','A sequência acompanha a dependência real dos dados.',
'''Demonstrar a ordem de preparação: entrar, cadastrar tutor, cadastrar animal, cadastrar serviços e agendar. Serviços são preparados uma vez e reutilizados. Os cinco blocos são a jornada operacional depois do login. Conclusão envia o serviço para a consulta do histórico; cancelamento preserva o registro na lista de atendimentos.''')
for i,(a,b) in enumerate([('Cliente','Identificar o tutor'),('Animal','Vincular ao tutor'),('Preparação','Serviço e profissional'),('Agendar','Escolher data/hora'),('Histórico','Consultar concluídos')]):
    x=.65+i*2.56
    shape(s,x,3,2.2,1.65,'ink' if i==3 else 'green')
    text(s,x+.12,3.3,1.96,.5,a,19,'white',True)
    text(s,x+.12,4.02,1.96,.5,b,12,'white')
    if i<4:arrow(s,x+2.27,3.66,.24)
text(s,.75,5.35,11.8,.8,'Login → cadastros e profissionais → agenda → conclusão → histórico e backup',21,'green',True)

s=slide('Modelo de dados enxuto','IDs mantêm os vínculos; documentos identificam o cliente.',
'''Cliente 1:N animal; animal, serviço e profissional têm relação 1:N com atendimento. Usuário de acesso, tutor e profissional são entidades distintas. Recuperação pertence ao usuário. O atendimento guarda preço/duração contratados e nomes históricos. Legados são indicados; profissional desconhecido não é inventado.''')
for x,y,w,h,title,body in [( .7,2.7,3.2,1.3,'CLIENTE','ID · CPF · e-mail'),(.7,4.65,3.2,1.3,'ANIMAL','ID · tutor · espécie'),(5.05,4.65,3.2,1.3,'ATENDIMENTO','Animal · serviço · profissional'),(9.4,4.65,3.2,1.3,'SERVIÇO','Centavos · duração · ativo'),(5.05,2.7,3.2,1.3,'PROFISSIONAL','Nome · função · ativo'),(9.4,2.7,3.2,1.3,'ACESSO','Usuário e recuperação')]:
    shape(s,x,y,w,h,'white');text(s,x+.17,y+.15,w-.34,.4,title,18,'green',True);text(s,x+.17,y+.77,w-.34,.38,body,13)
text(s,1.5,4.12,2,.4,'1 ↓ N',15,'orange',True)
text(s,4,5.05,.95,.45,'1 → N',14,'orange',True)
text(s,8.38,5.05,.95,.45,'N ← 1',14,'orange',True)
text(s,6.1,4.12,2,.4,'1 ↓ N',15,'orange',True)

s=slide('CPF e e-mail: unicidade independente','Nome, telefone e endereço podem ser iguais, inclusive todos juntos.',
'''RN13 atual substitui a antiga comparação do conjunto inteiro. CPF obrigatório em novos cadastros, validado pelo algoritmo e guardado como texto sem máscara. E-mail opcional e único quando informado, normalizado em minúsculas. UNIQUE(cpf,email) não resolveria: são duas restrições independentes. A validação de CPF não prova titularidade nem situação cadastral.''')
card(s,.65,2.65,3.85,3.85,'CPF','Bloquear repetição','Mesmo CPF, outro nome ou outro e-mail: cadastro recusado.','red')
card(s,4.75,2.65,3.85,3.85,'@','Bloquear repetição','Outro CPF, mesmo e-mail informado: cadastro recusado.','red')
card(s,8.85,2.65,3.85,3.85,'✓','Permitir repetição','Demais dados iguais, CPFs e e-mails distintos: permitido.','green')

s=slide('Avisar, bloquear e migrar são ações diferentes','O formulário preserva os dados quando uma gravação é recusada.',
'''RN14 é consultiva. Nome aproximado, telefone ou endereço igual podem ser situações legítimas. CPF/e-mail iguais são conflitos. A migração preserva IDs e vínculos; clientes antigos sem documento ficam pendentes até regularização. Conflitos preexistentes geram IDs para revisão manual, nunca exclusão automática. A migração ocorre em etapas transacionais.''')
card(s,.65,2.65,3.85,3.85,'!','Aviso amarelo','Nome, telefone ou endereço semelhantes: conferir e permitir.','orange')
card(s,4.75,2.65,3.85,3.85,'×','Conflito vermelho','CPF ou e-mail de outra conta de cliente: impedir a gravação.','red')
card(s,8.85,2.65,3.85,3.85,'↻','Banco existente','Preservar clientes, animais e IDs; regularizar CPF pendente.')

s=slide('Agenda com estados e valores preservados','Mudar o catálogo não reescreve o atendimento já combinado.',
'''Valor e duração são copiados na criação. Ao reagendar com o mesmo serviço, ambos são preservados. Ao trocar serviço, o app copia os valores do novo catálogo. A duração antiga nunca armazenada é preenchida com a duração atual durante a migração. Só agendados podem ser alterados, concluídos ou cancelados. A revisão permite corrigir um agendado para o horário passado/agora, com confirmação, e recusa concluir futuro. Mesmo concluído antes do fim, o intervalo previsto permanece reservado. O tutor e o profissional são congelados na conclusão; a descrição contratada é preservada.''')
shape(s,.8,2.9,3.2,1.1,'green');text(s,1.04,3.21,2.7,.5,'AGENDADO',25,'white',True)
arrow(s,4.4,3.32,.65)
shape(s,5.4,2.9,3.2,1.1,'ink');text(s,5.63,3.21,2.75,.5,'CONCLUÍDO',25,'white',True)
shape(s,9.1,2.9,3.35,1.1,'red');text(s,9.31,3.21,2.9,.5,'CANCELADO',25,'white',True)
text(s,8.6,4.17,3.8,.45,'Cancelamento exige motivo',15,'red')
text(s,.9,5.05,11.5,1.3,'Reserva por animal e profissional até o fim previsto\nReagendar para o horário realizado; concluir após o início',22,'green',True)
text(s,1,4.23,6.5,.45,'Agendado → cancelado também é permitido',15,'muted')

s=slide('Arquitetura simples, responsabilidades claras','A interface orienta; a camada de dados revalida antes de gravar.',
'''Não é necessário framework web, microsserviço ou ORM para este escopo. Separar arquivos por responsabilidade já ajuda. App e login controlam widgets; validacoes normaliza campos; database aplica as operações; recuperacao integra o provedor. O envio HTTP usa biblioteca padrão, não requer SDK adicional. A chave só fica na configuração local do operador.''')
for i,(a,b) in enumerate([('INTERFACE','app.py · login.py'),('REGRAS','validacoes.py'),('DADOS','database.py · SQLite')]):
    x=.8+i*4.15;shape(s,x,2.9,3.65,1.8,'white');text(s,x+.18,3.18,3.3,.5,a,23,'green',True);text(s,x+.18,3.95,3.3,.45,b,16)
    if i<2:arrow(s,x+3.75,3.68,.3)
text(s,1,5.35,11.4,.8,'recuperacao.py  →  API HTTPS da Resend  →  e-mail cadastrado',23,'green',True)

s=slide('Recuperar acesso sem perder os cadastros','Esqueci minha senha → código por e-mail → nova senha → login.',
'''Recuperação pertence ao usuário, não ao cliente. Login e e-mail devem corresponder. Mensagem genérica evita confirmar publicamente se o usuário existe. Código de oito dígitos gerado com secrets, hash com sal no banco, expiração de 10 min, cinco tentativas e 60 s entre envios. Consumo e troca de hash da senha na mesma transação. Uma segunda tentativa com o mesmo código é recusada, inclusive em concorrência.''')
for i,(a,b) in enumerate([('Identificar','Usuário + e-mail'),('Receber','Código de 8 dígitos'),('Redefinir','Nova senha + confirmação')]):
    card(s,.7+i*4.15,2.65,3.8,3.4,str(i+1),a,b)
text(s,.85,6.35,11.8,.45,'10 min de validade  •  5 tentativas  •  uso único  •  reenvio após 60 s',19,'green',True)

s=slide('Cada profissional tem sua agenda','O intervalo é reservado pela duração contratada do serviço.',
'''A captura é do aplicativo real com dados fictícios, gerada pelo teste gráfico da revisão. Uma reserva de 10h a 11h impede outro atendimento do mesmo profissional às 10h30; o próximo pode iniciar às 11h. Outro profissional pode atender outro animal em paralelo. Concluir cedo mantém a reserva; cancelar libera. Ana Souza, Bruno Lima e Carla Santos são exemplos; função é descritiva e não valida especialidade. A integração Resend continua implementada e testada com provedor simulado, sem envio real.''')
s.shapes.add_picture(str(BASE/'evidencias'/'agenda_profissionais.png'), Inches(.65), Inches(2.35), width=Inches(7.45))
text(s,8.55,2.65,4.1,.8,'PROFISSIONAL + INTERVALO',20,'green',True)
text(s,8.55,3.6,4.05,2.85,'Mesma pessoa: sem sobreposição.\nPessoas diferentes: paralelo permitido.\nFim previsto visível.\nFiltro por profissional.',19,'muted')

s=slide('Transações, integridade e backup','Proteções concretas para os dados do MVP.',
'''Atomicidade: commit ou rollback. Consistência: UNIQUE, vínculos e regras na camada de dados. Isolamento: escritas serializadas com BEGIN IMMEDIATE. Durabilidade: WAL e synchronous FULL, sem alegar teste físico de queda de energia. O backup usa Connection.backup, não copia só o .db com WAL ativo. SQL externo não garante todas as regras de negócio, como data futura e sobreposição.''')
for i,(a,b) in enumerate([('Atomicidade','Commit completo ou rollback'),('Consistência','Restrições e validação'),('Isolamento','Escritas serializadas'),('Durabilidade','WAL + synchronous FULL')]):
    x=.7+(i%2)*6.35;y=2.6+(i//2)*1.65
    shape(s,x,y,5.95,1.35,'white');text(s,x+.2,y+.15,5.5,.45,a,23,'green',True);text(s,x+.2,y+.8,5.5,.4,b,17)
text(s,.9,6.3,11.6,.5,'Backup pela API SQLite, inclusive com o aplicativo aberto.',21,'green',True)

s=slide('O que foi verificado','Testes temporários: nenhum e-mail real enviado e nenhum banco real migrado.',
'''Evidência nesta execução: Na revisão de 20/11/2026: 78 testes automatizados passaram; 59 verificações gráficas passaram (31 anteriores e 28 novas). A linha de base tinha 52 testes, também executados antes das mudanças. As contagens desta tela são da revisão atual. Capturas são reais com dados fictícios; não representam observação de uma pessoa usando o sistema. O envio real depende de API key e destinatário autorizado, e ainda não foi validado. Não alegar resultado no Windows ou no computador de apresentação.''')
card(s,.7,2.7,3.8,3.8,'78','Automatizados','Incluem tutor histórico, centavos, conclusão e reservas concorrentes.')
card(s,4.85,2.7,3.8,3.8,'59','Fluxos gráficos','31 de regressão + 28 da revisão, nos widgets reais do app.')
card(s,9,2.7,3.65,3.8,'API','Provedor simulado','Contrato HTTP e falhas testados; entrega na caixa de entrada pendente.','orange')

s=slide('Roteiro para a demonstração ao vivo','Preparar os serviços antes de iniciar a jornada do cliente.',
'''Tempo sugerido 3 a 4 minutos. Usar dados de demonstração e banco separado. Criar um cliente com CPF válido de exemplo; não usar dados reais de terceiros. Repetir CPF com outro e-mail e repetir e-mail com outro CPF para mostrar independência. Escolher profissional, tentar conflito e reagendar para agora antes de concluir. Mostrar o histórico com o tutor original após uma transferência e um novo atendimento com o novo tutor. Para recuperar senha de verdade, configurar Resend antes e garantir que o destinatário é o e-mail da conta Resend. Sem chave, mostrar a tela e explicar a limitação sem fingir entrega.''')
for i,(a,b) in enumerate([('Entrar','Mostrar login e Minha conta'),('Preparar','Tutor → animal → serviço → profissional'),('Validar','CPF e e-mail repetidos recusados'),('Agendar','Demonstrar conflito do profissional'),('Realizar','Reagendar para agora → concluir → histórico'),('Proteger','Backup e recuperação de acesso')]):
    x=.75+(i%2)*6.35;y=2.6+(i//2)*1.28
    shape(s,x,y,.5,.5,'green');text(s,x+.13,y+.08,.3,.3,str(i+1),15,'white',True)
    text(s,x+.7,y,5.2,.42,a,21,'green',True);text(s,x+.7,y+.55,5.2,.4,b,16)

s=slide('O tutor da realização permanece no histórico','Transferir o animal não reescreve o atendimento concluído.',
'''Captura real do app com dados fictícios. Thor teve atendimento com Maria e depois foi transferido para Carlos. O antigo continua com Maria; uma nova realização usa Carlos. O nome do tutor é congelado ao concluir. A descrição e o valor do serviço são os contratados; nome do profissional da realização também é preservado. Dados antigos sem snapshot são identificados como migrados, com os nomes disponíveis naquele momento. Não se afirma recuperar o passado que não foi armazenado.''')
s.shapes.add_picture(str(BASE/'evidencias'/'historico_tutores.png'), Inches(.65), Inches(2.35), width=Inches(7.45))
text(s,8.55,2.65,4.05,.8,'CADA REALIZAÇÃO TEM SEU TUTOR',20,'green',True)
text(s,8.55,3.9,4.05,2.5,'Atendimento antigo: Maria.\nAnimal transferido para Carlos.\nNova realização: Carlos.\nTotal soma centavos inteiros.',19,'muted')

s=slide('Evolução comprovável por iterações','Linha de base, retorno recebido, mudança e verificação.',
'''Não há histórico Git nem evidência de entrevistas ou sprints antigos. A entrega de 07/11 é uma linha de base documentada e está preservada no ZIP original. Em 20/11 foram executados seus 52 testes. O solicitante pediu as cinco correções desta revisão. A mudança foi implementada e verificada com 78 testes e 59 checagens gráficas. O solicitante confirmou que nunca houve uso observado por uma pessoa e pediu execução do aplicativo e prints; esses prints são evidência funcional, não estudo humano.''')
for i,(a,b) in enumerate([('Linha de base','ZIP original preservado; 52 testes executados antes das mudanças.'),('Retorno recebido','Reagendamento, tutor histórico, seleção, centavos e agenda por profissional.'),('Revisão validada','78 testes + 59 checagens gráficas; capturas reais com dados fictícios.')]):
    y=2.65+i*1.25;shape(s,.8,y,2.8,.8,'green' if i<2 else 'ink');text(s,.98,y+.2,2.45,.4,a,19,'white',True);text(s,4,y+.08,8.2,.9,b,20)
text(s,.85,6.5,11.6,.3,'Registro detalhado: EVOLUCAO_POR_ITERACOES.md',16,'green',True)

s=slide('Necessidade → regra → tela → teste','A matriz conecta o pedido à evidência de aceitação.',
'''A matriz completa contém 15 requisitos com critérios observáveis, telas e nomes dos testes. Exemplos deste slide são RF10, RF12, RF08 e RF05. A numeração é da revisão e não inventa uma especificação antiga. O documento se chama REQUISITOS_E_ACEITACAO.md.''')
for i,(a,b) in enumerate([('Conclusão válida','Futuro recusado; reagendar agora permitido → Atendimentos → testes de conclusão.'),('Tutor preservado','Transferência não reescreve a realização → Histórico → teste com dois tutores.'),('Agenda da equipe','Intervalo completo sem conflito → Agenda → teste concorrente com dois animais.'),('Valores em centavos','0,10 + 0,20 = 0,30 → Serviços/Histórico → teste de soma inteira.')]):
    y=2.55+i*1.05;shape(s,.75,y,3.5,.75,'green');text(s,.93,y+.18,3.15,.4,a,19,'white',True);text(s,4.5,y+.04,7.9,.8,b,18)
text(s,.85,6.8,11.6,.25,'Matriz completa: REQUISITOS_E_ACEITACAO.md',14,'green',True)

s=slide('Demonstração funcional e próxima validação','O app foi executado; observação com uma pessoa ainda não foi realizada.',
'''O solicitante confirmou que o sistema não teve esse uso observado e autorizou execução e prints. As verificações gráficas exercitam o aplicativo real, com banco temporário e confirmações simuladas. Não são avaliação humana de entendimento, satisfação ou dificuldade. O roteiro de VALIDACAO_DE_USO.md propõe oito tarefas, ficha por participante e registro de problemas/melhorias; todos os campos da sessão permanecem pendentes. Não inventar resultados.''')
card(s,.7,2.65,5.9,3.85,'✓','Executado','Cadastros, agenda, cancelamento, conclusão, histórico e prints do aplicativo.')
card(s,6.85,2.65,5.8,3.85,'→','Roteiro disponível','Observar uma pessoa; registrar tarefas, dificuldades e retorno para outra iteração.','orange')

r.core_properties.title='Sistema para Pet Shop — revisão DRAP 20/11/2026'
r.core_properties.subject='Desenvolvimento Rápido de Aplicações em Python'
r.core_properties.author='Eduardo Guther Pontes Leal e João Sérgio Cavalcante Marques Araújo'
r.core_properties.keywords='Python, CustomTkinter, SQLite, CPF, Resend, recuperação de senha'
BASE.mkdir(exist_ok=True, parents=True)
r.save(BASE/'Etapa4_PetShop.pptx')
print(f'{len(r.slides)} slides salvos em {BASE / "Etapa4_PetShop.pptx"}')
