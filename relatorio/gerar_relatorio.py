"""Gera o relatório acadêmico em DOCX a partir das evidências locais.

Dependências de geração: python-docx e matplotlib. Não são dependências do app.
O PDF é obtido abrindo/exportando o DOCX no LibreOffice ou no Word.
"""
from pathlib import Path
import os
import sys

BASE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
OUT.mkdir(exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', '/tmp/petshop-relatorio-matplotlib')
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

GREEN = '1F655C'
INK = '18302F'
d = Document()
s = d.sections[0]
s.page_width, s.page_height = Cm(21), Cm(29.7)
s.top_margin, s.bottom_margin = Cm(2.2), Cm(2)
s.left_margin, s.right_margin = Cm(2.5), Cm(2)
s.header_distance, s.footer_distance = Cm(0.9), Cm(0.9)
s.different_first_page_header_footer = True
normal = d.styles['Normal']
normal.font.name = 'Liberation Serif'
normal.font.size = Pt(11)
normal.font.color.rgb = RGBColor.from_string(INK)
normal.paragraph_format.line_spacing = 1.15
normal.paragraph_format.space_after = Pt(7)
normal.paragraph_format.widow_control = True
for name, size in [('Title', 26), ('Heading 1', 18), ('Heading 2', 13), ('Heading 3', 11)]:
    st = d.styles[name]
    st.font.name = 'Liberation Sans'
    st.font.size = Pt(size)
    st.font.color.rgb = RGBColor.from_string(GREEN)
    st.font.bold = True
    st.paragraph_format.space_before = Pt(10)
    st.paragraph_format.space_after = Pt(8)
for name in ['Caption', 'Header', 'Footer']:
    d.styles[name].font.name = 'Liberation Sans'
    d.styles[name].font.size = Pt(9)
d.styles['Caption'].font.color.rgb = RGBColor.from_string('526661')
d.styles['Caption'].paragraph_format.space_after = Pt(9)
header = s.header.paragraphs[0]
header.text = 'ESTÁCIO DE SÁ  |  SISTEMA PARA PET SHOP  |  RELATÓRIO RAD'
header.runs[0].font.color.rgb = RGBColor.from_string(GREEN)
footer = s.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('Pet Shop • ')
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)
d.core_properties.title = 'Sistema para Pet Shop — Relatório de Desenvolvimento Rápido de Aplicações em Python'
d.core_properties.author = 'Eduardo Guther Pontes Leal; João Sérgio Cavalcante Marques Araújo'
d.core_properties.subject = 'Relatório organizado conforme a seção 7 das orientações do trabalho prático'
d.core_properties.keywords = 'Python, RAD, Pet Shop, CustomTkinter, SQLite, Etapa 4'


def p(text='', style=None):
    z = d.add_paragraph(text, style)
    if style is None:
        z.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return z


def h(text, level=1):
    return d.add_heading(text, level)


def page(title, level=1):
    heading = h(title, level)
    heading.paragraph_format.page_break_before = True
    return heading


def table(headers, rows, widths=None, size=9):
    t = d.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = 'Table Grid'
    t.autofit = False
    for i, name in enumerate(headers):
        t.rows[0].cells[i].text = name
    for row in rows:
        for cell, value in zip(t.add_row().cells, row):
            cell.text = str(value)
    for ri, row in enumerate(t.rows):
        trpr = row._tr.get_or_add_trPr()
        cant = OxmlElement('w:cantSplit')
        trpr.append(cant)
        for ci, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if widths:
                cell.width = Cm(widths[ci])
            tcpr = cell._tc.get_or_add_tcPr()
            margins = OxmlElement('w:tcMar')
            for side in ['top', 'left', 'bottom', 'right']:
                e = OxmlElement('w:' + side)
                e.set(qn('w:w'), '85')
                e.set(qn('w:type'), 'dxa')
                margins.append(e)
            tcpr.append(margins)
            for par in cell.paragraphs:
                par.paragraph_format.space_after = Pt(3)
                par.paragraph_format.space_before = Pt(1)
                par.paragraph_format.line_spacing = 1.05
                for r in par.runs:
                    r.font.name = 'Liberation Sans'
                    r.font.size = Pt(size)
                    if ri == 0:
                        r.font.bold = True
                        r.font.color.rgb = RGBColor(255, 255, 255)
            if ri == 0:
                shade = OxmlElement('w:shd')
                shade.set(qn('w:fill'), GREEN)
                tcpr.append(shade)
            elif ri % 2 == 0:
                shade = OxmlElement('w:shd')
                shade.set(qn('w:fill'), 'F1F5F3')
                tcpr.append(shade)
    repeat = OxmlElement('w:tblHeader')
    t.rows[0]._tr.get_or_add_trPr().append(repeat)
    if widths:
        for col, width in zip(t.columns, widths):
            col.width = Cm(width)
    p()
    return t


def code(text):
    z = p()
    z.alignment = WD_ALIGN_PARAGRAPH.LEFT
    z.paragraph_format.line_spacing = 1.05
    z.paragraph_format.space_after = Pt(8)
    r = z.add_run(text)
    r.font.name = 'Liberation Mono'
    r.font.size = Pt(9)
    return z


def pic(filename, caption, width=16.4):
    z = d.add_paragraph()
    z.alignment = WD_ALIGN_PARAGRAPH.CENTER
    z.paragraph_format.keep_with_next = True
    z.add_run().add_picture(str(BASE / 'evidencias' / filename), width=Cm(width))
    p(caption, 'Caption')


# Diagrama construído a partir do esquema efetivamente criado por database.py.
fig, ax = plt.subplots(figsize=(11, 6.7))
fig.patch.set_facecolor('white')
ax.set(xlim=(0, 11), ylim=(0, 6.7))
ax.axis('off')


def box(x, y, w, title, body):
    rect = FancyBboxPatch((x, y), w, 1.45, boxstyle='round,pad=0.06',
                          facecolor='#F1F5F3', edgecolor='#1F655C', linewidth=1.3)
    ax.add_patch(rect)
    ax.text(x+.15, y+1.13, title, fontsize=11, weight='bold', color='#1F655C')
    ax.text(x+.15, y+.83, body, fontsize=9, va='top', linespacing=1.5, color='#18302F')


box(.15, 4.8, 2.8, 'CLIENTE', 'PK id_cliente\nCPF e e-mail únicos')
box(.15, 2.5, 2.8, 'ANIMAL', 'PK id_animal\nFK id_cliente')
box(4.0, 2.5, 2.95, 'ATENDIMENTO', 'PK id_atendimento\nFK animal, serviço, profissional')
box(4.0, 4.8, 2.95, 'PROFISSIONAL', 'PK id_profissional\nNome, função, ativo')
box(8.05, 2.5, 2.8, 'SERVIÇO', 'PK id_servico\nCentavos, duração, ativo')
box(.15, .15, 2.8, 'USUÁRIO', 'PK id_usuario\nLogin, hash, e-mail')
box(4.0, .15, 2.95, 'RECUPERAÇÃO_SENHA', 'PK/FK id_usuario\nHash do código e validade')
box(8.05, .15, 2.8, 'AJUSTE MONETÁRIO', 'PK tabela + id_registro\nValor anterior e centavos')


def arrow(a, b, label, label_xy):
    ax.annotate('', xy=b, xytext=a, arrowprops=dict(arrowstyle='->', color='#627471', lw=1.4))
    ax.text(*label_xy, label, fontsize=10, color='#1F655C', ha='center', va='center',
            bbox=dict(facecolor='white', edgecolor='none', pad=2))


arrow((1.55, 4.74), (1.55, 4.03), '1 : N', (1.55, 4.4))
arrow((3.02, 3.22), (3.94, 3.22), '1 : N', (3.48, 3.52))
arrow((5.48, 4.74), (5.48, 4.03), '1 : N', (5.48, 4.4))
arrow((7.99, 3.22), (7.01, 3.22), '1 : N', (7.5, 3.52))
arrow((3.02, .88), (3.94, .88), '1 : 0..1', (3.48, 1.18))
fig.tight_layout(pad=.5)
diagram = OUT / 'diagrama_banco.png'
fig.savefig(diagram, dpi=200, bbox_inches='tight')
plt.close(fig)

# 1. Capa
z = p('CENTRO UNIVERSITÁRIO ESTÁCIO DE SÁ')
z.alignment = WD_ALIGN_PARAGRAPH.CENTER
z.runs[0].bold = True
z.runs[0].font.name = 'Liberation Sans'
z.runs[0].font.size = Pt(14)
z = p('Desenvolvimento Rápido de Aplicações em Python')
z.alignment = WD_ALIGN_PARAGRAPH.CENTER
p('\n')
for text in ['Eduardo Guther Pontes Leal', 'Matrícula: 202402343289',
             'João Sérgio Cavalcante Marques Araújo', 'Matrícula: 202503329771']:
    z = p(text)
    z.alignment = WD_ALIGN_PARAGRAPH.CENTER
p('\n\n')
z = p('SISTEMA PARA PET SHOP', 'Title')
z.alignment = WD_ALIGN_PARAGRAPH.CENTER
z = p('Relatório do Trabalho Prático')
z.alignment = WD_ALIGN_PARAGRAPH.CENTER
z.runs[0].font.size = Pt(16)
z = p('Cadastros, agenda por profissional e histórico de atendimentos')
z.alignment = WD_ALIGN_PARAGRAPH.CENTER
p('\n')
z = p('Relatório apresentado à disciplina de Desenvolvimento Rápido de Aplicações em Python, sob orientação do professor Hericlys Borges. Documento baseado na implementação e nas evidências da revisão de 20/11/2026, organizada até a Etapa 4.')
z.paragraph_format.left_indent = Cm(5)
p('\n')
z = p('21 de novembro de 2026')
z.alignment = WD_ALIGN_PARAGRAPH.CENTER

page('Sumário')
p('A organização acompanha as 13 seções indicadas no documento Trabalho Prático de Desenvolvimento Rápido de Aplicações em Python. A capa corresponde à seção 1.')
toc = [
    ('1', 'Capa'), ('2', 'Introdução e objetivo'), ('3', 'Requisitos e regras de negócio'),
    ('4', 'Tecnologias utilizadas'), ('5', 'Banco de dados'), ('6', 'Interface e funcionalidades'),
    ('7', 'Aplicação da metodologia RAD'), ('8', 'Registro de feedbacks e melhorias'),
    ('9', 'Testes e resultados'), ('10', 'Participação dos integrantes'), ('11', 'Conclusão'),
    ('12', 'Referências'), ('13', 'Instruções de execução'),
]
toc_pages = [1, 3, 4, 7, 8, 11, 17, 18, 19, 21, 22, 23, 24]
for (number, title), page_number in zip(toc, toc_pages):
    z = p(f'{number}. {title}\t{page_number}')
    z.alignment = WD_ALIGN_PARAGRAPH.LEFT
    z.paragraph_format.tab_stops.add_tab_stop(Cm(16.2), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
    z.paragraph_format.space_after = Pt(11)
h('Base documental', 2)
p('Foram utilizados o código-fonte, a apresentação Etapa4_PetShop, a matriz de requisitos, os registros de evolução e validação e as evidências da aplicação. As capturas representam o aplicativo real com dados fictícios. A descrição das limitações acompanha os resultados disponíveis, sem atribuir feedbacks ou atividades individuais que não estejam documentados.')

page('2. Introdução e objetivo')
h('2.1 Problema abordado', 2)
p('A rotina de um pet shop exige relacionar os dados dos tutores aos animais, organizar os serviços oferecidos e distribuir atendimentos entre profissionais. Quando essas informações ficam dispersas em anotações, torna-se difícil localizar cadastros, evitar reservas sobrepostas e consultar o histórico sem perder a identificação do responsável por cada realização.')
p('O projeto Sistema para Pet Shop reúne essas operações em uma aplicação desktop local. A solução prioriza a rotina do balcão: identificar o tutor, vincular o animal, preparar serviços e profissionais, agendar, registrar a conclusão ou o cancelamento e consultar o histórico.')
h('2.2 Público-alvo', 2)
p('O público-alvo previsto é formado por atendentes e responsáveis pela organização de pequenos pet shops que necessitam de um sistema local de cadastro e agenda. Esse perfil descreve o usuário pretendido; não houve pesquisa de campo ou observação de uso com participantes nos registros disponíveis.')
h('2.3 Objetivo geral', 2)
p('Desenvolver uma aplicação em Python com interface gráfica e banco de dados relacional para gerenciar tutores, animais, serviços, profissionais e atendimentos, aplicando desenvolvimento incremental, validações, operações CRUD e persistência de dados.')
h('2.4 Objetivos específicos', 2)
for txt in [
    'Centralizar os cadastros e permitir consulta, busca, edição e exclusão ou inativação conforme os vínculos existentes.',
    'Evitar conflitos no intervalo completo de atendimento de um mesmo animal ou profissional.',
    'Preservar valores contratados e a identificação do tutor e do profissional na realização de um atendimento.',
    'Proteger as operações com validação, confirmação, transações, autenticação e cópia de segurança.',
    'Registrar a evolução da versão e verificar os resultados com testes automatizados e fluxos gráficos.',
]:
    p(txt, 'List Bullet')
h('2.5 Escopo da versão relatada', 2)
p('O documento descreve a revisão de 20/11/2026, apresentada como segunda iteração/Etapa 4. A organização segue o modelo de relatório final, mas não implica homologação da Etapa 5. O escopo implementado não inclui vendas, estoque, pagamentos, prontuário clínico, múltiplas unidades ou gestão de jornada de trabalho. Não foi localizado registro separado de aprovação formal do escopo pelo professor.')

page('3. Requisitos e regras de negócio')
h('3.1 Requisitos funcionais — acesso e cadastros', 2)
p('Os identificadores RF01 a RF15 seguem a matriz REQUISITOS_E_ACEITACAO.md da revisão. As operações de cadastro, listagem, pesquisa e alteração são oferecidas nos módulos principais. A retirada de registros respeita o histórico e os relacionamentos.')
table(['ID', 'Requisito implementado', 'Critério de aceitação'], [
    ('RF01', 'Criar acesso e autenticar o operador.', 'Primeiro acesso sem senha padrão; credencial válida permite entrar. Cinco erros bloqueiam a tela por 30 segundos.'),
    ('RF02', 'Recuperar acesso por código de e-mail.', 'Código válido permite uma troca de senha. Expiração, limite de tentativas e uso único são verificados.'),
    ('RF03', 'Identificar os tutores.', 'Novo cliente exige nome, telefone com DDD e CPF válido. CPF e e-mail informado são únicos independentemente.'),
    ('RF04', 'Vincular animais a tutores.', 'O tutor deve existir. Tutor com animais e animal com atendimentos não podem ser excluídos.'),
    ('RF05', 'Cadastrar serviços com preço e duração.', 'Valores positivos são tratados em centavos; frações de centavo são recusadas. Duração inteira e positiva.'),
    ('RF06', 'Manter profissionais.', 'Nome e função obrigatórios; nome único. Inativação impede novas reservas e conserva registros existentes.'),
    ('RF07', 'Agendar atendimentos.', 'Novo agendamento exige data futura, animal existente, serviço ativo e profissional ativo. Copia condições contratadas.'),
], [1.2, 5.2, 10.1], 10)
h('3.2 Retirada de registros', 2)
p('Clientes e animais podem ser excluídos quando não possuem os vínculos impeditivos. Serviços e profissionais são inativados, podendo ser reativados. Atendimentos são cancelados com motivo, mantendo o registro para consulta. Essas escolhas evitam eliminar referências necessárias ao histórico.')
h('3.3 Busca e atualização da interface', 2)
p('A pesquisa de clientes aceita nome, telefone, CPF com máscara e e-mail. Animais podem ser encontrados pelo nome ou tutor. A agenda e o histórico permitem consultas por dados do atendimento. Após salvar ou mudar o estado, as listas e opções relacionadas são atualizadas. Uma validação recusada mantém os dados preenchidos para correção.')

page('3. Requisitos e regras de negócio — continuação')
h('3.4 Requisitos funcionais — agenda e preservação', 2)
table(['ID', 'Requisito implementado', 'Critério de aceitação'], [
    ('RF08', 'Reservar o profissional pelo intervalo.', 'O mesmo profissional não atende animais diferentes em intervalos sobrepostos. Um novo início no fim exato do anterior é permitido.'),
    ('RF09', 'Permitir trabalho em paralelo.', 'Animais diferentes com profissionais diferentes podem ocupar o mesmo horário. O mesmo animal permanece protegido contra sobreposição.'),
    ('RF10', 'Reagendar e concluir.', 'Agendado pode ser corrigido para passado/agora com confirmação. Futuro não conclui; conclusão após o início conserva a reserva até o fim previsto.'),
    ('RF11', 'Cancelar sem apagar.', 'Motivo obrigatório. Cancelamento libera o intervalo. Concluídos e cancelados não podem ser editados pelo fluxo de atendimento.'),
    ('RF12', 'Preservar a realização.', 'Conclusão conserva os nomes do tutor e profissional. Transferência posterior do animal não reescreve a realização anterior.'),
    ('RF13', 'Editar sem seleção oculta.', 'Pesquisa preserva seleção visível; se ocultar o registro, encerra a edição. Alterações não salvas exigem confirmação de descarte.'),
    ('RF14', 'Proteger reservas simultâneas.', 'Duas gravações concorrentes para o mesmo intervalo/profissional têm apenas um resultado aceito.'),
    ('RF15', 'Migrar e copiar dados.', 'Migrações preservam IDs e vínculos, indicam origem legada e registram ajustes monetários. Backup gera cópia consistente em arquivo novo.'),
], [1.2, 5.2, 10.1], 9.5)
h('3.5 Requisitos de qualidade', 2)
p('A aplicação deve persistir os dados em arquivo SQLite, separar interface, validação e persistência, usar consultas parametrizadas para os dados informados e tratar falhas com mensagens compreensíveis. As gravações usam transações com commit ou rollback. A autenticação armazena hash e sal da senha; o código de recuperação também não é armazenado em texto puro.')
p('A instalação local e as instruções de execução favorecem a demonstração acadêmica. A existência de testes automatizados fornece verificação repetível das regras. Portabilidade para outros sistemas operacionais e usabilidade com usuários continuam sujeitas a validação específica.')

page('3. Requisitos e regras de negócio — regras detalhadas')
h('3.6 Identificação e integridade dos cadastros', 2)
p('O CPF é normalizado para texto com 11 dígitos e validado pelos dígitos verificadores. Essa verificação não comprova titularidade nem situação cadastral. O e-mail informado é normalizado em minúsculas e sem espaços nas bordas. CPF e e-mail possuem índices únicos separados; vários clientes podem não informar e-mail, armazenado como NULL. Nome, telefone e endereço podem repetir, inclusive em conjunto.')
p('Semelhanças em nome, telefone ou endereço geram aviso consultivo amarelo. CPF ou e-mail já pertencente a outro cliente bloqueia a gravação e recebe sinalização vermelha. Na edição, o próprio registro é desconsiderado na identificação de duplicidade.')
h('3.7 Agenda, estados e duração', 2)
p('O intervalo reservado é [início, início + duração). Assim, uma reserva das 10h às 11h impede sobreposição às 10h30, mas permite outro atendimento às 11h. A verificação é feita tanto para o animal quanto para o profissional, dentro da transação de escrita. Agendados e concluídos ocupam o intervalo contratado; cancelados não o ocupam.')
p('O fluxo de estados admite agendado → concluído ou agendado → cancelado. A criação exige horário futuro. A edição permite corrigir o horário realizado para o passado ou para o minuto atual, com confirmação. Concluir exige que o início já tenha chegado; não exige aguardar toda a duração prevista e, nesse caso, o restante do intervalo continua reservado.')
h('3.8 Condições contratadas e histórico', 2)
p('Cada atendimento copia o preço em centavos, a duração e o nome do serviço. Reagendar mantendo o serviço conserva essas condições, mesmo após mudanças no catálogo. Trocar o serviço copia as novas condições e revalida o conflito. O tutor da realização é o tutor vinculado ao animal no momento da conclusão; seu nome é então congelado, juntamente com o nome do profissional. O campo animal não é uma cópia histórica de seu nome.')
p('A representação monetária principal usa inteiros: R$ 50,05 equivale a 5005 centavos. A soma dos serviços concluídos usa centavos e não representa pagamentos recebidos. Entradas novas com frações de centavo são recusadas. Na migração legada, arredondamentos por ROUND_HALF_UP mantêm o valor anterior em tabela de auditoria.')
h('3.9 Restrições do escopo', 2)
p('Usuário de acesso, tutor e profissional são entidades distintas. A função do profissional é descritiva; a aplicação não restringe especialidade, expediente, pausas ou férias. Migrações não inventam quem era o tutor ou profissional de fatos antigos: usam a informação disponível, indicam legado e deixam profissionais desconhecidos pendentes de atribuição.')

page('4. Tecnologias utilizadas')
table(['Tecnologia / recurso', 'Aplicação e justificativa'], [
    ('Python 3.10+', 'Linguagem principal. Permite organizar as operações em funções, módulos e classes e dispõe de bibliotecas para SQLite, validação, testes e comunicação HTTP.'),
    ('CustomTkinter', 'Biblioteca de interface desktop baseada em Tkinter, com campos, botões, abas e janelas. Adequada à construção rápida da interface local. Faixa no requirements.txt: >=5.2,<7.'),
    ('Tkinter / ttk', 'Base gráfica e tabelas da aplicação; diálogos de confirmação, mensagens e seleção do destino do backup.'),
    ('SQLite / sqlite3', 'Banco relacional em arquivo local, sem processo servidor separado. Permite relacionamentos, índices, triggers, transações e backup pela API.'),
    ('Decimal e inteiros', 'Decimal interpreta entradas monetárias; inteiros em centavos sustentam armazenamento principal e totais exatos.'),
    ('hashlib, hmac, os e secrets', 'Derivação e comparação de hashes, sal aleatório e código temporário de recuperação. Senhas usam PBKDF2-SHA256 com 200.000 iterações.'),
    ('urllib, JSON e Resend', 'Integração HTTPS para recuperação de acesso. O código usa a biblioteca padrão; não depende do SDK da Resend.'),
    ('unittest e unittest.mock', 'Regressão de regras e simulação do provedor de e-mail. Bancos temporários isolam as verificações dos dados do app.'),
], [4.2, 12.3], 9.5)
h('4.1 Organização do código', 2)
p('app.py concentra telas, eventos e confirmações; login.py cuida do primeiro acesso e da autenticação gráfica. database.py implementa persistência, transações, agenda, migrações e backup. validacoes.py normaliza e valida campos. duplicidade_clientes.py instala a proteção de identidade e similaridade_clientes.py fornece alertas consultivos. recuperacao.py implementa os códigos temporários e o envio HTTPS. popular_demo.py prepara a demonstração fictícia.')
h('4.2 Ambiente e justificativa da arquitetura', 2)
p('O registro da revisão informa Linux, Python 3.14.9 e CustomTkinter 6.0.0. A versão mínima declarada no README é Python 3.10 com Tkinter. Não foi localizado registro do editor/IDE utilizado nem ensaio no Windows. A aplicação desktop com banco local reduz a configuração necessária para a entrega; não há servidor web, serviço central de sessões ou infraestrutura de múltiplas unidades.')
p('As referências técnicas de Python, CustomTkinter e Resend consultadas estão na seção 12. A geração dos documentos e slides possui ferramentas próprias e não altera as dependências necessárias para executar o aplicativo.')

page('5. Banco de dados')
h('5.1 Modelo e relacionamentos', 2)
p('O banco petshop.db é criado ao lado de database.py. O modelo usa identificadores inteiros como chaves primárias e chaves estrangeiras para manter os vínculos. A estrutura a seguir foi conferida em um banco temporário criado pela versão atual do código.')
z = d.add_paragraph()
z.alignment = WD_ALIGN_PARAGRAPH.CENTER
z.paragraph_format.keep_with_next = True
z.add_run().add_picture(str(diagram), width=Cm(16.4))
p('Figura 1 — Esquema relacional da versão revisada. Fonte: elaboração a partir de database.py, 21/11/2026. PK: chave primária; FK: chave estrangeira.', 'Caption')
table(['Relacionamento', 'Cardinalidade e significado'], [
    ('cliente → animal', '1:N. Um tutor pode possuir vários animais; cada animal referencia um tutor.'),
    ('animal → atendimento', '1:N. Um animal pode ter vários atendimentos; cada atendimento pertence a um animal.'),
    ('servico → atendimento', '1:N. Um serviço pode constar em vários atendimentos; cada atendimento contrata um serviço.'),
    ('profissional → atendimento', '1:N. Cada novo atendimento exige um profissional. O vínculo pode estar ausente em registros legados.'),
    ('usuario → recuperacao_senha', '1:0..1. Um usuário pode não ter código pendente ou ter apenas um. Novo código substitui o anterior.'),
], [5.6, 10.9], 9.5)
p('ajuste_monetario_migracao é uma tabela técnica com referência lógica à tabela e ao ID ajustado; não possui chave estrangeira polimórfica para as tabelas de origem. Usuários não são vinculados automaticamente a tutores ou profissionais.')

page('5. Banco de dados — dicionário')
h('5.2 Tabelas, campos e tipos', 2)
p('INTEGER representa inteiro; TEXT representa texto; REAL é usado em campos legados e instantes numéricos. As regras do sistema complementam as restrições do esquema, especialmente nas migrações de versões anteriores.')
table(['Tabela / identificador', 'Campos e tipos'], [
    ('cliente\nPK: id_cliente INTEGER', 'nome TEXT; telefone TEXT; email TEXT; endereco TEXT; cpf TEXT. Nome e telefone obrigatórios; CPF obrigatório nos novos cadastros pela API/triggers. CPF e e-mail normalizados têm unicidade independente.'),
    ('animal\nPK: id_animal INTEGER', 'id_cliente INTEGER (FK); nome TEXT; especie TEXT; raca TEXT; observacoes TEXT. Tutor, nome e espécie obrigatórios.'),
    ('servico\nPK: id_servico INTEGER', 'nome TEXT; descricao TEXT; preco REAL; duracao_min INTEGER; ativo INTEGER; preco_centavos INTEGER. Nome único normalizado; preço/centavos positivos; duração inteira positiva; ativo 0 ou 1.'),
    ('profissional\nPK: id_profissional INTEGER', 'nome TEXT; funcao TEXT; ativo INTEGER. Nome único normalizado; nome e função exigidos pela API; ativo 0 ou 1.'),
    ('atendimento\nPK: id_atendimento INTEGER', 'id_animal INTEGER (FK); id_servico INTEGER (FK); data_hora TEXT; valor REAL; status TEXT; motivo_cancelamento TEXT; duracao_min INTEGER; valor_centavos INTEGER; id_profissional INTEGER (FK); tutor_nome TEXT; servico_nome TEXT; profissional_nome TEXT; origem_historico TEXT; concluido_em TEXT.'),
    ('usuario\nPK: id_usuario INTEGER', 'nome TEXT; login TEXT único; senha_hash TEXT; salt TEXT; criado_em TEXT; email TEXT com índice único quando informado. Credenciais independentes dos clientes e profissionais.'),
    ('recuperacao_senha\nPK/FK: id_usuario INTEGER', 'identificador TEXT único; codigo_hash TEXT; sal TEXT; solicitado_em REAL; expira_em REAL; tentativas INTEGER; enviado INTEGER. A FK usa ON DELETE CASCADE.'),
    ('ajuste_monetario_migracao\nPK composta: tabela + id_registro', 'tabela TEXT; id_registro INTEGER; valor_anterior TEXT; centavos INTEGER. Mantém o valor anterior quando a conversão legada exige arredondamento.'),
], [5.1, 11.4], 9)
h('5.3 Campos calculados e registros históricos', 2)
p('data_hora armazena data/hora local em texto ISO com precisão de minutos. O fim estimado é calculado somando duracao_min, sem coluna persistida própria. concluido_em registra o instante da conclusão. A origem do histórico diferencia registros da versão atual de dados migrados. preco e valor permanecem como espelhos compatíveis com versões antigas; os cálculos usam preco_centavos e valor_centavos.')

page('5. Banco de dados — integridade e persistência')
h('5.4 Transações e validação', 2)
p('As conexões ativam foreign_keys=ON, synchronous=FULL e read_uncommitted=OFF. A inicialização exige journal_mode=WAL. Escritas começam com BEGIN IMMEDIATE; o conjunto é confirmado por commit ou revertido por rollback, e a conexão é fechada ao final. A verificação de sobreposição ocorre dentro da transação que grava a reserva, evitando que duas solicitações aceitem o mesmo intervalo simultaneamente.')
p('Índices únicos protegem CPF e e-mail do cliente, nomes de serviço/profissional e e-mail de usuário quando informado. Triggers verificam formato de CPF, duração, estados, inativação, motivo de cancelamento e correspondência entre campos monetários. O algoritmo completo do CPF, a validade das datas e o conflito da agenda são regras da API Python; não se presume que toda gravação SQL externa receba essas validações.')
h('5.5 Tratamento de exceções', 2)
p('A aplicação converte conflitos conhecidos de unicidade em mensagens de negócio e informa que a alteração não foi salva. Erros de integridade e operações recusadas provocam rollback. Quando o SQLite está ocupado ou bloqueado, o operador recebe orientação para aguardar e tentar novamente. Os formulários mantêm os valores recusados para que a correção não exija novo preenchimento.')
h('5.6 Migrações', 2)
p('A inicialização instala as proteções e acrescenta campos conforme a versão encontrada. A migração de identidade é atômica; outras migrações são etapas transacionais separadas. Duplicidades legadas interrompem a etapa correspondente com identificação dos IDs, sem exclusão automática. Clientes antigos sem CPF permanecem pendentes de regularização.')
p('A revisão converte os valores monetários para centavos, preserva IDs e vínculos e registra ajustes quando há arredondamento. Nomes disponíveis no momento da migração são mantidos com indicação de legado. Um atendimento antigo sem profissional não recebe um nome fictício: exige atribuição antes da conclusão. A duração antiga deriva do catálogo disponível, pois a versão anterior não armazenava esse histórico.')
h('5.7 Backup', 2)
p('O botão Backup utiliza a API de cópia do SQLite para produzir um arquivo consistente mesmo com a aplicação aberta e WAL ativo. O destino deve ser um arquivo novo. A cópia é um recurso de proteção, mas o projeto não registra teste físico de queda de energia nem uma política automatizada de retenção e restauração. O banco antigo perdido durante o desenvolvimento não foi recuperado; a entrega inicia uma base nova quando não existe petshop.db.')

page('6. Interface e funcionalidades')
h('6.1 Acesso, navegação e clientes', 2)
p('No primeiro uso, o operador cria nome, login, senha e e-mail de recuperação. Depois da autenticação, a janela principal organiza a navegação nas abas Clientes, Animais, Serviços, Profissionais, Atendimentos e Histórico. O cabeçalho disponibiliza recursos como Backup e orientações de uso.')
pic('cadastro_cliente.png', 'Figura 2 — Cadastro de cliente/tutor e identificação do registro em edição. Fonte: evidências do projeto, 20/11/2026; dados fictícios.')
p('Para cadastrar um tutor, preencha nome, telefone com DDD e CPF; e-mail e endereço são opcionais. Use Salvar. Para editar, selecione uma linha, revise o formulário identificado por “Editando #ID”, modifique os campos e confirme o antes/depois. A pesquisa aceita nome, telefone, CPF e e-mail. A exclusão exige confirmação e é recusada quando há animais vinculados.')
h('6.2 Animais e continuidade da edição', 2)
p('Na aba Animais, escolha um tutor existente e informe nome e espécie. Raça e observações são opcionais. A listagem permite pesquisar e selecionar o animal para edição; a exclusão é bloqueada se existir qualquer atendimento vinculado. A transferência para outro tutor afeta as próximas realizações, preservando o tutor de atendimentos já concluídos.')
p('A busca mantém a seleção enquanto o registro estiver visível. Se o filtro ocultar a linha em edição, o formulário encerra a edição; havendo alterações não salvas, a confirmação permite recusar o descarte e restaurar o filtro anterior. Essa proteção evita um formulário continuar associado a um ID sem destaque na tabela.')

page('6. Interface e funcionalidades — serviços')
h('6.3 Catálogo e valores em centavos', 2)
pic('servicos_centavos.png', 'Figura 3 — Cadastro e edição de serviço com preço de R$ 19,95. Fonte: evidências do projeto, 20/11/2026; dados fictícios.')
p('Na aba Serviços, informe nome, descrição opcional, preço e duração em minutos. O preço deve ser positivo e representar centavos inteiros; pode ser digitado com vírgula ou ponto decimal, como 19,95 ou 19.95, sem separador de milhar. Uma entrada como 0,005 é recusada. A duração deve ser um inteiro maior que zero.')
p('Selecione uma linha para carregar e editar o serviço. Ao salvar, confirme as mudanças. Use a ação de inativação quando o serviço não deva aparecer em novos agendamentos; a reativação permite oferecê-lo novamente. Os atendimentos já contratados preservam suas condições.')
h('Exemplo de preservação do contrato', 2)
p('Um banho contratado por R$ 50,05 e 60 minutos continua com esse valor e duração se o catálogo passar a R$ 60,00 e 45 minutos. Reagendar mantendo o serviço não altera as condições. Ao trocar o serviço do atendimento, o sistema copia preço, nome e duração do novo item e verifica novamente a disponibilidade do intervalo.')

page('6. Interface e funcionalidades — profissionais')
h('6.4 Equipe e disponibilidade para reservas', 2)
pic('profissionais.png', 'Figura 4 — Cadastro da equipe e ação para carregar profissionais fictícios. Fonte: evidências do projeto, 20/11/2026.')
p('Na aba Profissionais, cadastre nome e função. Nomes não podem se repetir segundo a normalização adotada. Selecione uma linha para editar e confirme as alterações. O botão Adicionar equipe fictícia inclui Ana Souza, Bruno Lima e Carla Santos sem duplicar nomes existentes e sem criar contas de login.')
p('Inativar um profissional impede que ele seja selecionado para novas reservas e mantém seus atendimentos anteriores. Reativar devolve a opção à agenda. O filtro de consulta permite incluir profissionais inativos para examinar registros existentes. Não há regra de especialidade por tipo de serviço; a função cadastrada descreve a atividade.')
h('Profissional, tutor e usuário', 2)
p('O profissional é quem executa o serviço. O tutor é o cliente responsável pelo animal. O usuário é a credencial utilizada para entrar no programa. Esses papéis permanecem separados no banco e na interface. Adicionar um profissional fictício não dá a ele uma senha nem representa a participação de um integrante da equipe acadêmica.')

page('6. Interface e funcionalidades — agenda')
h('6.5 Agendar, pesquisar e reagendar', 2)
pic('agenda_profissionais.png', 'Figura 5 — Agenda com profissional, início e fim estimado. Fonte: evidências do projeto, 20/11/2026; dados fictícios.')
p('Antes de agendar, cadastre tutor e animal e prepare um serviço e um profissional ativos. Na aba Atendimentos, selecione essas referências e informe data/hora futura no formato dd/mm/aaaa hh:mm. Ao salvar, a aplicação valida os relacionamentos e a disponibilidade de todo o intervalo.')
p('Use a pesquisa e os filtros de situação/profissional para localizar reservas. Para reagendar, selecione um atendimento agendado, altere os dados e confirme. O botão Reagendar para agora permite registrar o horário em que a execução começou, respeitando as validações e eventuais conflitos.')
p('Uma tentativa de concluir um atendimento futuro é recusada. Após o início, Concluir registra a realização e fixa os nomes históricos. A operação é confirmada pelo operador e não constitui comprovação externa de prestação do serviço. Mesmo quando a conclusão ocorre antes do fim previsto, a reserva ocupa o intervalo originalmente contratado.')

page('6. Interface e funcionalidades — cancelamento')
h('6.6 Cancelar preservando o registro', 2)
pic('cancelamento.png', 'Figura 6 — Atendimento cancelado preservado na listagem e aberto para consulta. Fonte: evidências do projeto, 20/11/2026; dados fictícios.')
p('Selecione um atendimento ainda agendado, utilize Cancelar, informe o motivo e confirme. A ausência do motivo impede a operação. O atendimento permanece registrado com situação cancelado e deixa de reservar o intervalo do animal e do profissional.')
p('Atendimentos concluídos e cancelados ficam disponíveis para consulta, com edição bloqueada no fluxo. A preservação substitui a exclusão definitiva para não apagar a trajetória de um atendimento e seus vínculos. Essa decisão atende à orientação de justificar cancelamento quando é necessário conservar o histórico.')
h('Exemplo de liberação de horário', 2)
p('Se Ana Souza estava reservada das 10h às 11h e o atendimento foi cancelado, outro animal pode ocupar esse intervalo com Ana, desde que as demais regras sejam satisfeitas. Se o atendimento tivesse sido concluído às 10h20, o intervalo até 11h continuaria reservado.')

page('6. Interface e funcionalidades — histórico e apoio')
h('6.7 Consultar o histórico', 2)
pic('historico_tutores.png', 'Figura 7 — Histórico de Thor antes e depois da troca de tutor e total de R$ 432,65 na base demonstrativa. Fonte: evidências do projeto, 20/11/2026; dados fictícios.')
p('A aba Histórico exibe serviços concluídos e permite busca por animal, tutor, serviço ou profissional. O tutor exibido corresponde ao nome conservado na conclusão. Na demonstração, um atendimento de Thor permanece associado a Maria Oliveira e a realização posterior aparece com Carlos Pereira. O total soma os valores dos serviços concluídos em centavos; não é controle de caixa ou de pagamento.')
h('6.8 Backup e recuperação de acesso', 2)
p('Para copiar o banco, clique em Backup e escolha um arquivo de destino novo. Para recuperar a senha, saia da sessão e utilize Esqueci minha senha: informe usuário e e-mail, solicite o código e defina a nova senha com confirmação. A recuperação depende de configuração da Resend e conectividade; a validação registrada utiliza um provedor simulado, sem envio real.')
p('O código tem oito dígitos, validade de dez minutos, limite de cinco tentativas e intervalo de sessenta segundos entre solicitações. A resposta de solicitação é genérica para não confirmar a existência de uma conta. Minha conta permite atualizar o e-mail de recuperação mediante a senha atual.')

page('7. Aplicação da metodologia RAD')
p('A metodologia RAD é aplicada à construção de uma solução de escopo limitado, com interface executável, evolução incremental e verificação das mudanças. A rastreabilidade liga necessidade, regra, tela e teste. O histórico disponível sustenta a linha de base e a revisão; não permite reconstruir todas as entregas acadêmicas anteriores ou afirmar que cada ciclo recebeu aprovação docente.')
table(['Etapa das orientações', 'Aplicação no projeto / evidência disponível'], [
    ('1 — Planejamento', 'O problema, o público previsto, os relacionamentos e o catálogo atual de requisitos estão documentados. Não foi localizado o documento original de planejamento nem registro da aprovação inicial. A orientação acadêmica indica 13/10, sem comprovação local da entrega nessa data.'),
    ('2 — Prototipação', 'A interface foi construída em abas com formulários, listas e fluxo entre cadastros e agenda. Há apresentação e capturas da versão executável. Não foi localizado um protótipo inicial independente nem registro de avaliação docente dessa etapa.'),
    ('3 — MVP funcional', 'A linha de base reconstruída de 07/11/2026 já reúne cadastros, agenda, persistência, autenticação, recuperação e backup. O ZIP original conserva essa versão. A data da entrega acadêmica específica da Etapa 3 não está comprovada.'),
    ('4 — Segunda iteração', 'Em 20/11/2026, a revisão técnica reproduziu problemas, incorporou o retorno do solicitante e alterou regras, interface e testes. A entrega atual documenta 78 testes e 59 verificações gráficas.'),
    ('5 — Produto final', 'Este relatório organiza a versão atual no formato final solicitado. A conclusão da disciplina, a apresentação final e a validação docente não estão comprovadas pelos arquivos. A observação de uso com uma pessoa permanece planejada.'),
], [4.4, 12.1], 9.5)
h('7.1 Ciclo de revisão comprovável', 2)
p('A base preservada no ZIP de 07/11 foi inspecionada em 20/11, quando 52 testes passaram antes das alterações. A revisão reproduziu conclusão futura indevida, mudança de tutor no histórico, problema de seleção e aceitação de frações de centavo, além de identificar a falta de agenda por profissional. O retorno do solicitante definiu as correções. Após a implementação, foram executados novos testes, fluxos gráficos e capturas da interface.')
h('7.2 Participação do professor', 2)
p('O professor identificado é Hericlys Borges. O PDF da disciplina prevê avaliação e feedback a cada entrega, porém os arquivos não contêm comentários específicos do professor, datas de devolutiva ou aprovações. Por isso, os retornos técnicos descritos neste relatório são atribuídos à revisão documentada e ao solicitante, sem apresentá-los como feedback docente.')

page('8. Registro de feedbacks e melhorias')
p('As observações abaixo correspondem à análise crítica e ao retorno do solicitante registrados em EVOLUCAO_POR_ITERACOES.md. Cada melhoria está associada a uma evidência verificável.')
table(['Observação / problema', 'Mudança implementada', 'Resultado registrado'], [
    ('Conclusão de atendimento futuro.', 'Conclusão exige início já ocorrido. Edição permite corrigir a data e oferece Reagendar para agora.', 'Testes de recusa sem mudança de estado e conclusão após correção; verificação nos widgets.'),
    ('Transferência do animal alterava a interpretação do tutor de realizações antigas.', 'Conclusão conserva o nome do tutor e do profissional. Nova realização usa o tutor então vinculado.', 'Teste com dois tutores e renomeações posteriores; captura historico_tutores.png.'),
    ('Filtro removia destaque visual e mantinha o ID antigo em edição.', 'Seleção visível é preservada; ocultação encerra edição e alterações não salvas exigem confirmação.', 'Reprodução da falha anterior e testes gráficos com descarte aceito e recusado.'),
    ('Valores aceitavam fração de centavo.', 'Entradas validadas com Decimal; armazenamento principal inteiro e exibição brasileira com duas casas.', '0,005 recusado; soma 0,10 + 0,20 = 0,30; migração e espelhos monetários verificados.'),
    ('Agenda sem vínculo com o executor.', 'Cadastro de profissionais, filtro de agenda e conflitos pelo intervalo completo. Equipe fictícia repetível.', 'Mesmo profissional bloqueado; profissionais distintos em paralelo; concorrência com um vencedor.'),
    ('Evidências insuficientes para apresentar a evolução.', 'Matriz de requisitos, registros de revisão, roteiro de validação, logs, capturas e slides atualizados.', '17 slides; seis capturas; 78 testes automatizados e 59 verificações gráficas documentados.'),
], [4.5, 6.3, 5.7], 9)
h('8.1 Pendências e justificativas', 2)
p('A avaliação com uma pessoa usuária não foi realizada; existe roteiro com oito tarefas e ficha de observação em VALIDACAO_DE_USO.md. Não há chave configurada nem evidência de entrega real de e-mail, de modo que a integração foi testada por simulação. O histórico Git, o banco antigo e documentos binários perdidos não foram recuperados. A contribuição individual e as devolutivas docentes não podem ser reconstituídas apenas pelo código disponível.')
p('Essas pendências limitam as conclusões possíveis: testes funcionais demonstram comportamento nas condições verificadas, mas não medem compreensão, satisfação ou dificuldade de uso. Uma próxima iteração deverá registrar observações reais antes de propor melhorias de usabilidade baseadas em participantes.')

page('9. Testes e resultados')
h('9.1 Método e resultados gerais', 2)
p('A verificação utiliza unittest para regras de negócio, migrações e persistência, além de scripts que acionam os widgets reais com confirmações simuladas. Os testes usam bancos temporários e provedor de e-mail simulado. Não alteram o banco de operação nem enviam mensagens reais.')
table(['Conjunto', 'Resultado', 'Origem da evidência'], [
    ('Suíte automatizada da revisão', '78 testes aprovados: 52 anteriores adaptados e 26 novos.', 'Log evidencias/testes_automatizados.txt e VALIDACAO_ETAPA4.md, 20/11/2026.'),
    ('Regressão gráfica original', '31/31 verificações aprovadas.', 'evidencias/testes_interface.txt, 20/11/2026.'),
    ('Regressão gráfica da revisão', '28/28 verificações aprovadas.', 'evidencias/testes_revisao_interface.txt, 20/11/2026.'),
    ('Conferência para este relatório', '78 testes automatizados aprovados novamente, sem falhas, em 2,535 s.', 'Execução em 21/11/2026: python3 -W error::ResourceWarning -m unittest discover -s tests -v.'),
], [4.9, 5.8, 5.8], 9.5)
h('9.2 Cenários de cadastro e integridade', 2)
table(['Cenário', 'Resultado esperado', 'Resultado obtido'], [
    ('CPF repetido com outro e-mail.', 'Recusar e não gravar alterações.', 'Aprovado; unicidade independente preservada.'),
    ('E-mail repetido com outro CPF.', 'Recusar após normalização.', 'Aprovado; conflito tratado e formulário preservado no fluxo gráfico.'),
    ('Nome, telefone e endereço iguais com identificadores diferentes.', 'Permitir; semelhança é consultiva.', 'Aprovado; novo cliente inserido.'),
    ('CPF inválido, campos vazios ou telefone curto.', 'Recusar e orientar a correção.', 'Aprovado; entradas inválidas rejeitadas.'),
    ('Excluir tutor com animal ou animal com atendimento.', 'Bloquear para manter os vínculos.', 'Aprovado; registros mantidos.'),
    ('Preço 50,05 e fração 0,005.', 'Guardar 5005 centavos; recusar fração.', 'Aprovado; soma e exibição com duas casas conferidas.'),
], [5.2, 5.5, 5.8], 9)

page('9. Testes e resultados — agenda e segurança')
h('9.3 Cenários do fluxo principal', 2)
table(['Cenário', 'Resultado esperado', 'Resultado obtido'], [
    ('Mesmo profissional e intervalos sobrepostos para animais diferentes.', 'Bloquear o segundo atendimento.', 'Aprovado; conflito reconhecido.'),
    ('Profissionais e animais diferentes no mesmo horário.', 'Permitir reservas paralelas.', 'Aprovado; dois atendimentos aceitos.'),
    ('Mesmo animal com profissionais diferentes e sobreposição.', 'Bloquear a segunda reserva.', 'Aprovado; proteção do animal mantida.'),
    ('Início no fim exato de outro atendimento; intervalo cruza meia-noite.', 'Permitir no limite; calcular intervalo corretamente.', 'Aprovado em ambos os cenários.'),
    ('Concluir futuro e depois reagendar para agora.', 'Recusar futuro; permitir após correção válida.', 'Aprovado; nenhuma mudança de estado na recusa.'),
    ('Cancelar com/sem motivo.', 'Recusar sem motivo; preservar registro e liberar intervalo com motivo.', 'Aprovado na suíte e na interface.'),
    ('Concluir antes do fim previsto.', 'Manter a reserva até o fim contratado.', 'Aprovado; sobreposição ainda recusada.'),
    ('Transferir animal após conclusão.', 'Preservar tutor antigo; nova realização usa o novo.', 'Aprovado; histórico com os dois tutores.'),
    ('Reservas concorrentes para o mesmo profissional.', 'Apenas uma gravação aceita.', 'Aprovado; transação protege o intervalo.'),
], [5.7, 5.5, 5.3], 9)
h('9.4 Recuperação, persistência e interface', 2)
p('A suíte verifica uso único e expiração do código, cinco tentativas, substituição por novo código, resposta genérica, erros HTTP, falha de envio, troca de e-mail autenticada e redefinição concorrente. Também inclui backup, migração de estruturas legadas, rollback de operações conflitantes, preservação de IDs e proteção contra inconsistências monetárias. Os fluxos gráficos verificam seleção, pesquisa, confirmação, inativação, reagendamento, conclusão e exibição de totais.')
h('9.5 Limites dos resultados', 2)
p('Os 59 resultados gráficos são evidências da execução de 20/11; não foram repetidos para a redação deste relatório. Os arquivos não registram ensaio no Windows, uso observado por uma pessoa, envio real de e-mail, migração de banco real ou teste físico de falha de energia. O resultado antigo de 108 testes refere-se a arquivos excluídos e não é contabilizado como evidência da versão atual.')

page('10. Participação dos integrantes')
p('A identificação da equipe foi recuperada da capa de Etapa4_PetShop.pdf e do gerador da apresentação. A equipe identificada contém dois integrantes:')
table(['Integrante', 'Matrícula', 'Participação documentada'], [
    ('Eduardo Guther Pontes Leal', '202402343289', 'Integrante identificado na apresentação do Sistema para Pet Shop. A distribuição individual de atividades não está registrada nos arquivos disponíveis.'),
    ('João Sérgio Cavalcante Marques Araújo', '202503329771', 'Integrante identificado na apresentação do Sistema para Pet Shop. A distribuição individual de atividades não está registrada nos arquivos disponíveis.'),
], [6, 3.2, 7.3], 10)
h('10.1 Atividades registradas no projeto', 2)
p('O material permite identificar levantamento e organização de requisitos, construção da interface, modelagem e implementação do banco, regras de cadastro e agenda, autenticação, recuperação de senha, testes, documentação e preparação da apresentação. Essas atividades estão comprovadas como componentes da entrega; não há registros que permitam atribuir uma delas exclusivamente a um dos integrantes.')
p('EVOLUCAO_POR_ITERACOES.md declara a ausência de histórico Git e de registros suficientes para reconstruir a participação individual. Assim, este relatório registra os integrantes e a limitação documental, sem apresentar uma divisão estimada como fato. A seção poderá ser complementada pelos autores com o relato efetivo das atividades de cada membro.')
h('10.2 Compreensão do conjunto', 2)
p('Conforme as orientações acadêmicas, ambos devem compreender o funcionamento geral e estar preparados para explicar os módulos e as regras durante a apresentação. O fluxo a demonstrar é: autenticar, cadastrar tutor e animal, preparar serviço e profissional, agendar sem conflito, reagendar ou cancelar, concluir e consultar o histórico. A apresentação disponível contém notas de fala e um roteiro de demonstração.')

page('11. Conclusão')
p('O Sistema para Pet Shop reúne em uma aplicação desktop os cadastros de tutores, animais, serviços e profissionais, o agendamento de atendimentos, o cancelamento justificado e a consulta dos serviços concluídos. A versão atual relaciona os dados em SQLite, atualiza a interface após as operações e aplica validações e transações para evitar gravações inconsistentes.')
p('A revisão de 20/11/2026 fortaleceu o fluxo principal ao vincular reservas ao profissional, preservar o tutor de cada realização, corrigir o estado de seleção durante pesquisas, recusar conclusão futura e tratar dinheiro em centavos. Os registros apresentam 78 testes automatizados e 59 verificações gráficas aprovadas; para este relatório, os 78 testes automatizados passaram novamente em 21/11/2026.')
h('11.1 Dificuldades encontradas', 2)
p('As principais dificuldades técnicas documentadas envolveram conservar o passado quando o cadastro atual muda, impedir sobreposição concorrente, evitar estados diferentes entre tabela e formulário e converter preços legados sem perder a informação anterior. A perda da pasta original e do banco antigo exigiu reconstruir uma linha de base, sem recuperar dados que já não estavam disponíveis. A ausência de histórico Git limita a reconstrução cronológica e a atribuição das contribuições individuais.')
h('11.2 Limitações', 2)
p('A solução permanece voltada à operação local. Não contempla pagamentos, estoque, jornadas, pausas, férias, restrições de especialidade, múltiplas unidades ou perfis distintos de administrador/atendente. A recuperação depende de configuração externa e foi testada com simulação. Uma janela já autenticada não é encerrada automaticamente após a redefinição da senha. Em dados legados, nomes históricos indisponíveis não podem ser reconstruídos com certeza.')
p('As evidências não substituem avaliação com usuário ou feedback docente. O roteiro de uso existe, mas ainda não foi aplicado. O projeto, portanto, oferece uma base funcional verificada para a Etapa 4 e para revisão acadêmica, sem afirmar homologação ou encerramento das etapas não documentadas.')
h('11.3 Possibilidades de melhoria', 2)
p('A próxima avaliação pode aplicar o roteiro com uma pessoa e registrar dificuldades reais, resultados e mudanças decorrentes. Outras evoluções possíveis são controle de jornada e especialidades, perfis de acesso, política de backup/restauração, relatórios operacionais e backend para o envio de e-mail em uma distribuição mais ampla. A equipe também deve completar os registros individuais e incorporar as devolutivas do professor quando ocorrerem.')

page('12. Referências')
p('TRABALHO PRÁTICO DE DESENVOLVIMENTO RÁPIDO DE APLICAÇÕES EM PYTHON: orientações. Documento acadêmico fornecido em PDF, sem autoria ou data editorial explicitadas. Arquivo: Trabalho_Pratico_RAD_Orientacoes.pdf. Utilizado para a estrutura de 13 seções e os critérios das etapas.')
p('LEAL, Eduardo Guther Pontes; ARAÚJO, João Sérgio Cavalcante Marques. Sistema para Pet Shop: apresentação da Etapa 4. 20 nov. 2026. Arquivos: Etapa4_PetShop.pdf e Etapa4_PetShop.pptx. Identificação dos autores conforme a capa.')
p('SISTEMA PARA PET SHOP. Código-fonte e documentação da revisão de 20/11/2026. Arquivos: petshop/README.md; REQUISITOS_E_ACEITACAO.md; ANALISE_DO_FLUXO.md; EVOLUCAO_POR_ITERACOES.md; VALIDACAO_ETAPA4.md; VALIDACAO_DE_USO.md; evidencias/README.md; logs e capturas em evidencias/. Fontes locais consultadas em 21 nov. 2026.')
p('PYTHON SOFTWARE FOUNDATION. sqlite3 — DB-API 2.0 interface for SQLite databases. Documentação oficial. Disponível em: https://docs.python.org/3/library/sqlite3.html. Acesso em: 21 nov. 2026. Referência para persistência local e API do SQLite.')
p('PYTHON SOFTWARE FOUNDATION. tkinter — Python interface to Tcl/Tk. Documentação oficial. Disponível em: https://docs.python.org/3/library/tkinter.html. Acesso em: 21 nov. 2026. Referência para a base gráfica e verificação da instalação.')
p('SCHIMANSKY, Tom. CustomTkinter: official documentation and tutorial. Disponível em: https://customtkinter.tomschimansky.com/. Acesso em: 21 nov. 2026. Referência para a biblioteca de interface baseada em Tkinter.')
p('RESEND. Send Email: API reference. Disponível em: https://resend.com/docs/api-reference/emails/send-email. Acesso em: 21 nov. 2026. Referência da integração HTTPS de recuperação de acesso; a entrega real de e-mail não foi validada.')
p('OPENAI. ChatGPT / Codex. Ferramentas de inteligência artificial utilizadas com supervisão do solicitante para apoio à revisão técnica documentada e à organização deste relatório, incluindo inspeção dos arquivos, conferência automatizada e geração dos documentos. Os dados de identificação, as funcionalidades e os resultados relatados derivam das fontes locais; lacunas documentais são explicitadas. Redação e geração deste relatório em 21 nov. 2026.')

page('13. Instruções de execução')
h('13.1 Dependências e preparação', 2)
p('É necessário Python 3.10 ou superior com Tkinter e permissão de escrita na pasta do aplicativo. A dependência declarada é customtkinter>=5.2,<7. O SQLite é acessado pelo módulo sqlite3. Conexão à internet é necessária para instalar a dependência e, opcionalmente, para a recuperação de senha por e-mail.')
p('A partir da pasta petshop_mvp, abra o terminal e acesse petshop. Crie um ambiente virtual e instale as dependências:')
code('cd petshop\npython -m venv .venv')
p('Ativação no Linux/macOS:')
code('source .venv/bin/activate')
p('Ativação no Windows PowerShell:')
code('.venv\\Scripts\\Activate.ps1')
p('Com o ambiente ativo, execute:')
code('python -m pip install -r requirements.txt\npython app.py')
h('13.2 Inicialização do banco e primeiro acesso', 2)
p('O programa inicializa petshop.db automaticamente na pasta de database.py, cria as tabelas e aplica as migrações compatíveis. Não é necessário importar um arquivo SQL. O primeiro acesso pede a criação do usuário; não há senha padrão. Use login com 3 a 20 caracteres permitidos e senha com pelo menos seis caracteres, incluindo letras e números. Revise o e-mail sugerido antes de salvar.')
p('Para demonstrar com dados fictícios, aceite a carga oferecida pelo app no primeiro uso ou execute o comando a seguir em uma base de demonstração. O script não cria usuários e não envia e-mails. Se a base já possui cadastros, ele apenas confere/adiciona a equipe fictícia, preservando os registros existentes.')
code('python popular_demo.py')
p('A aba Profissionais também oferece Adicionar equipe fictícia. Prepare tutor, animal, serviço e profissional antes do agendamento. Para um ensaio sem dados reais, mantenha o banco de demonstração separado do banco em uso; não apague um banco existente para reiniciar a apresentação.')

page('13. Instruções de execução — testes e recuperação')
h('13.3 Executar os testes', 2)
p('Na pasta petshop, com o ambiente virtual ativo:')
code('python -W error::ResourceWarning -m unittest discover -s tests -v\npython tests/smoke_interface.py\npython tests/smoke_revisao.py')
p('Resultado de referência: 78 testes automatizados, 31 verificações gráficas originais e 28 da revisão. Os dois scripts gráficos exigem sessão gráfica e Tkinter funcional. As verificações usam bancos temporários e Resend simulada; não precisam de uma chave real de envio.')
p('Para gerar novas capturas, instale Pillow no ambiente de testes e utilize:')
code('python -m pip install Pillow\npython tests/smoke_revisao.py --capturas ../evidencias')
p('Esse comando grava capturas na pasta indicada; use outro destino se desejar conservar as evidências originais. Os testes não substituem a observação com participante proposta em VALIDACAO_DE_USO.md.')
h('13.4 Configurar a recuperação de acesso', 2)
p('A recuperação é opcional para a demonstração local dos cadastros e da agenda. Para habilitá-la, copie resend.ini.example para resend.ini, na mesma pasta de app.py, e preencha a configuração local. Alternativamente, defina RESEND_API_KEY e RESEND_FROM como variáveis de ambiente; elas têm prioridade sobre o arquivo. Siga petshop/README.md para a configuração de destinatário no modo de teste do provedor.')
p('Não inclua a chave preenchida no relatório ou no pacote. O arquivo de configuração de exemplo não contém credencial válida. Em uma distribuição para vários computadores, a evolução prevista é usar um backend para envio e limites globais. A integração atual guarda códigos com hash e sal, faz a solicitação HTTP em segundo plano e invalida o código se houver falha ou incerteza no envio.')
h('13.5 Organização da entrega', 2)
p('Os documentos Relatorio_PetShop_RAD.docx e Relatorio_PetShop_RAD.pdf ficam em petshop_mvp/relatorio/. A pasta petshop contém o código, as dependências e os testes; evidencias contém imagens, logs e o patch da revisão. A apresentação da Etapa 4 e os registros de requisitos/evolução permanecem na raiz de petshop_mvp. Não há banco de operação ou chave de API incluídos nos arquivos gerados para este relatório.')

path = OUT / 'Relatorio_PetShop_RAD.docx'
d.save(path)
print(path)
print('Parágrafos:', len(d.paragraphs), '| Tabelas:', len(d.tables), '| Figuras:', len(d.inline_shapes))
