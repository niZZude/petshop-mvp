"""Persistência SQLite do MVP. Escritas transacionais e vínculos preservados."""
import hashlib
import hmac
import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import validacoes as v
from validacoes import ErroValidacao
from duplicidade_clientes import instalar_protecao, DuplicadosExistentes

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'petshop.db')
ITERACOES_HASH = 200_000
STATUS_AGENDADO = 'agendado'
STATUS_CONCLUIDO = 'concluido'
STATUS_CANCELADO = 'cancelado'


@contextmanager
def conectar(escrita=False):
    con = sqlite3.connect(DB_PATH, timeout=5)
    con.row_factory = sqlite3.Row
    try:
        con.execute('PRAGMA foreign_keys=ON')
        con.execute('PRAGMA synchronous=FULL')
        con.execute('PRAGMA read_uncommitted=OFF')
        if escrita:
            con.execute('BEGIN IMMEDIATE')
        yield con
        con.commit()
    except sqlite3.IntegrityError as erro:
        con.rollback()
        mensagem = str(erro)
        for indice, aviso in [('ux_cliente_cpf', 'CPF já cadastrado.'), ('ux_cliente_email', 'E-mail já cadastrado para outro cliente.'),
                               ('ux_servico_nome', 'Já existe um serviço com este nome.'), ('ux_usuario_email', 'E-mail já cadastrado para outro usuário.'),
                               ('ux_profissional_nome', 'Já existe um profissional com este nome.')]:
            if indice in mensagem:
                raise ErroValidacao(aviso + ' Nenhuma alteração foi salva.') from erro
        if 'Dados inválidos' in mensagem or 'CPF deve' in mensagem:
            raise ErroValidacao(mensagem) from erro
        raise
    except sqlite3.OperationalError as erro:
        con.rollback()
        if getattr(erro, 'sqlite_errorcode', 0) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            raise ErroValidacao('Banco em uso. Aguarde e tente novamente.') from erro
        raise
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def criar_tabelas():
    with conectar() as con:
        if con.execute('PRAGMA journal_mode=WAL').fetchone()[0].lower() != 'wal':
            raise ErroValidacao('Não foi possível ativar WAL.')
        con.executescript('''
            CREATE TABLE IF NOT EXISTS cliente(id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, telefone TEXT NOT NULL, email TEXT, endereco TEXT, cpf TEXT);
            CREATE TABLE IF NOT EXISTS animal(id_animal INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente INTEGER NOT NULL REFERENCES cliente(id_cliente), nome TEXT NOT NULL,
                especie TEXT NOT NULL, raca TEXT, observacoes TEXT);
            CREATE TABLE IF NOT EXISTS servico(id_servico INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, descricao TEXT, preco REAL NOT NULL CHECK(preco>0),
                duracao_min INTEGER NOT NULL, ativo INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS atendimento(id_atendimento INTEGER PRIMARY KEY AUTOINCREMENT,
                id_animal INTEGER NOT NULL REFERENCES animal(id_animal),
                id_servico INTEGER NOT NULL REFERENCES servico(id_servico), data_hora TEXT NOT NULL,
                valor REAL NOT NULL, status TEXT NOT NULL DEFAULT 'agendado', motivo_cancelamento TEXT);
            CREATE TABLE IF NOT EXISTS usuario(id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, login TEXT NOT NULL UNIQUE, senha_hash TEXT NOT NULL,
                salt TEXT NOT NULL, criado_em TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS profissional(id_profissional INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL, funcao TEXT NOT NULL, ativo INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN (0,1)));
        ''')
        instalar_protecao(con)
        _migrar_atendimentos(con)
        _migrar_recuperacao(con)
        _migrar_revisao_drap(con)


def _migrar_revisao_drap(con):
    """Preserva IDs; não inventa profissionais nem autoria histórica inexistente."""
    try:
        con.execute('BEGIN IMMEDIATE')
        con.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_profissional_nome ON profissional(lower(trim(nome)))')
        con.execute('''CREATE TABLE IF NOT EXISTS ajuste_monetario_migracao(
            tabela TEXT NOT NULL,id_registro INTEGER NOT NULL,valor_anterior TEXT NOT NULL,
            centavos INTEGER NOT NULL,PRIMARY KEY(tabela,id_registro))''')
        for tabela,campo,id_ in [('servico','preco','id_servico'),('atendimento','valor','id_atendimento')]:
            colunas={r[1] for r in con.execute(f'PRAGMA table_info({tabela})')}
            if campo+'_centavos' not in colunas:
                con.execute(f'ALTER TABLE {tabela} ADD COLUMN {campo}_centavos INTEGER')
            for row in con.execute(f'SELECT {id_},{campo} FROM {tabela} WHERE {campo}_centavos IS NULL').fetchall():
                try:
                    valor=Decimal(str(row[campo]))
                    if not valor.is_finite() or valor<=0: raise InvalidOperation
                    centavos=int((valor*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
                    if not 0<centavos<=99_999_999_999: raise InvalidOperation
                except (InvalidOperation,ValueError,OverflowError):
                    raise ErroValidacao(f'Valor inválido em {tabela} ID {row[id_]}. Revise antes de migrar.') from None
                if valor != Decimal(centavos)/100:
                    con.execute('INSERT INTO ajuste_monetario_migracao VALUES(?,?,?,?)',
                                (tabela,row[id_],str(valor),centavos))
                con.execute(f'UPDATE {tabela} SET {campo}=?,{campo}_centavos=? WHERE {id_}=?',
                            (centavos/100,centavos,row[id_]))
            for evento in ('INSERT','UPDATE'):
                con.execute(f'''CREATE TRIGGER IF NOT EXISTS moeda_{tabela}_{evento.lower()}
                    BEFORE {evento} ON {tabela} WHEN NEW.{campo}_centavos IS NULL
                    OR typeof(NEW.{campo}_centavos)!='integer' OR NEW.{campo}_centavos NOT BETWEEN 1 AND 99999999999
                    OR NEW.{campo} != NEW.{campo}_centavos/100.0
                    BEGIN SELECT RAISE(ABORT,'Dados inválidos: valor deve corresponder aos centavos.'); END''')
        colunas={r[1] for r in con.execute('PRAGMA table_info(atendimento)')}
        for campo,tipo in [('id_profissional','INTEGER REFERENCES profissional(id_profissional)'),
                           ('tutor_nome','TEXT'),('servico_nome','TEXT'),('profissional_nome','TEXT'),
                           ('origem_historico','TEXT'),('concluido_em','TEXT')]:
            if campo not in colunas: con.execute(f'ALTER TABLE atendimento ADD COLUMN {campo} {tipo}')
        con.execute('''UPDATE atendimento SET
            tutor_nome=(SELECT c.nome FROM animal a JOIN cliente c USING(id_cliente) WHERE a.id_animal=atendimento.id_animal),
            servico_nome=(SELECT nome FROM servico s WHERE s.id_servico=atendimento.id_servico),
            origem_historico='migracao' WHERE origem_historico IS NULL''')
        con.execute('CREATE INDEX IF NOT EXISTS ix_agenda_animal ON atendimento(id_animal,status,data_hora)')
        con.execute('CREATE INDEX IF NOT EXISTS ix_agenda_profissional ON atendimento(id_profissional,status,data_hora)')
        # Registros antigos sem profissional ficam pendentes. Novos exigem o vínculo.
        con.execute('''CREATE TRIGGER IF NOT EXISTS atendimento_profissional_insert BEFORE INSERT ON atendimento
            WHEN NEW.id_profissional IS NULL OR trim(coalesce(NEW.tutor_nome,''))=''
            OR trim(coalesce(NEW.servico_nome,''))='' OR trim(coalesce(NEW.profissional_nome,''))=''
            BEGIN SELECT RAISE(ABORT,'Dados inválidos: informe profissional e identificação do atendimento.'); END''')
        con.execute('''CREATE TRIGGER IF NOT EXISTS atendimento_profissional_update BEFORE UPDATE ON atendimento
            WHEN OLD.id_profissional IS NOT NULL AND NEW.id_profissional IS NULL
            BEGIN SELECT RAISE(ABORT,'Dados inválidos: não remova o profissional do atendimento.'); END''')
        con.commit()
    except Exception:
        con.rollback()
        raise


def _migrar_atendimentos(con):
    try:
        con.execute('BEGIN IMMEDIATE')
        if 'duracao_min' not in {r[1] for r in con.execute('PRAGMA table_info(atendimento)')}:
            con.execute('ALTER TABLE atendimento ADD COLUMN duracao_min INTEGER')
            con.execute('UPDATE atendimento SET duracao_min=(SELECT duracao_min FROM servico s WHERE s.id_servico=atendimento.id_servico)')
        regras = {
            'servico': "NEW.duracao_min IS NULL OR typeof(NEW.duracao_min)!='integer' OR NEW.duracao_min<=0 OR NEW.ativo IS NULL OR NEW.ativo NOT IN (0,1)",
            'atendimento': "NEW.status IS NULL OR NEW.status NOT IN ('agendado','concluido','cancelado') OR NEW.duracao_min IS NULL OR typeof(NEW.duracao_min)!='integer' OR NEW.duracao_min<=0 OR NEW.valor IS NULL OR NEW.valor<=0 OR (NEW.status='cancelado' AND trim(coalesce(NEW.motivo_cancelamento,''))='')"
        }
        for tabela, regra in regras.items():
            for evento in ('INSERT', 'UPDATE'):
                con.execute(f"CREATE TRIGGER IF NOT EXISTS validar_{tabela}_{evento.lower()} BEFORE {evento} ON {tabela} WHEN {regra} BEGIN SELECT RAISE(ABORT,'Dados inválidos de {tabela}.'); END")
        repetidos = con.execute('SELECT group_concat(id_servico) FROM servico GROUP BY lower(trim(nome)) HAVING count(*)>1').fetchall()
        if repetidos:
            raise DuplicadosExistentes('Serviços repetidos (IDs: ' + '; '.join(r[0] for r in repetidos) + '). Revise o banco.')
        con.execute('CREATE UNIQUE INDEX IF NOT EXISTS ux_servico_nome ON servico(lower(trim(nome)))')
        con.commit()
    except Exception:
        con.rollback()
        raise


def _dados_cliente(nome, telefone, email, endereco, cpf, legado=False):
    v.obrigatorios(Nome=nome, Telefone=telefone)
    cpf = None if legado and not (cpf or '').strip() else v.cpf(cpf)
    return nome.strip(), v.telefone(telefone), v.email_opcional(email) or None, (endereco or '').strip(), cpf


def inserir_cliente(nome, telefone, email, endereco, cpf):
    dados = _dados_cliente(nome, telefone, email, endereco, cpf)
    with conectar(True) as con:
        return con.execute('INSERT INTO cliente(nome,telefone,email,endereco,cpf) VALUES(?,?,?,?,?)', dados).lastrowid


def atualizar_cliente(id_cliente, nome, telefone, email, endereco, cpf):
    with conectar(True) as con:
        atual = con.execute('SELECT cpf FROM cliente WHERE id_cliente=?', (id_cliente,)).fetchone()
        if atual is None:
            raise ErroValidacao('Cliente não encontrado.')
        dados = _dados_cliente(nome, telefone, email, endereco, cpf, atual['cpf'] is None)
        con.execute('UPDATE cliente SET nome=?,telefone=?,email=?,endereco=?,cpf=? WHERE id_cliente=?', (*dados, id_cliente))


def listar_clientes(busca=''):
    numeros = re.sub(r'\D', '', busca) or busca
    with conectar() as con:
        return con.execute('SELECT * FROM cliente WHERE nome LIKE ? OR telefone LIKE ? OR cpf LIKE ? OR email LIKE ? ORDER BY nome',
            (f'%{busca}%', f'%{numeros}%', f'%{numeros}%', f'%{busca}%')).fetchall()


def _buscar(tabela, id_):
    with conectar() as con:
        return con.execute(f'SELECT * FROM {tabela} WHERE id_{tabela}=?', (id_,)).fetchone()


def buscar_cliente(id_): return _buscar('cliente', id_)
def buscar_animal(id_): return _buscar('animal', id_)
def buscar_servico(id_): return _buscar('servico', id_)
def buscar_profissional(id_): return _buscar('profissional', id_)
def buscar_atendimento(id_): return _buscar('atendimento', id_)


def contar_animais_do_cliente(id_):
    with conectar() as con:
        return con.execute('SELECT count(*) FROM animal WHERE id_cliente=?', (id_,)).fetchone()[0]


def contar_atendimentos_do_animal(id_):
    with conectar() as con:
        return con.execute('SELECT count(*) FROM atendimento WHERE id_animal=?', (id_,)).fetchone()[0]


def excluir_cliente(id_):
    with conectar(True) as con:
        if con.execute('SELECT count(*) FROM animal WHERE id_cliente=?', (id_,)).fetchone()[0]:
            raise ErroValidacao('Não é possível excluir: o cliente possui animais cadastrados.')
        con.execute('DELETE FROM cliente WHERE id_cliente=?', (id_,))


def inserir_animal(id_cliente, nome, especie, raca, observacoes):
    v.obrigatorios(Nome=nome, Espécie=especie)
    with conectar(True) as con:
        return con.execute('INSERT INTO animal(id_cliente,nome,especie,raca,observacoes) VALUES(?,?,?,?,?)',
                           (id_cliente, nome.strip(), especie.strip(), raca, observacoes)).lastrowid


def atualizar_animal(id_animal, id_cliente, nome, especie, raca, observacoes):
    v.obrigatorios(Nome=nome, Espécie=especie)
    with conectar(True) as con:
        con.execute('UPDATE animal SET id_cliente=?,nome=?,especie=?,raca=?,observacoes=? WHERE id_animal=?',
                    (id_cliente, nome.strip(), especie.strip(), raca, observacoes, id_animal))


def listar_animais(busca=''):
    with conectar() as con:
        return con.execute('''SELECT a.*,c.nome AS tutor FROM animal a JOIN cliente c USING(id_cliente)
            WHERE a.nome LIKE ? OR c.nome LIKE ? ORDER BY a.nome''', (f'%{busca}%',f'%{busca}%')).fetchall()


def animal_ja_cadastrado(id_cliente, nome, ignorar_id=None):
    with conectar() as con:
        return bool(con.execute('SELECT 1 FROM animal WHERE id_cliente=? AND lower(nome)=lower(?) AND id_animal!=?',
                                (id_cliente,nome,ignorar_id or 0)).fetchone())


def excluir_animal(id_):
    with conectar(True) as con:
        if con.execute('SELECT count(*) FROM atendimento WHERE id_animal=?', (id_,)).fetchone()[0]:
            raise ErroValidacao('Não é possível excluir: o animal possui atendimentos no histórico.')
        con.execute('DELETE FROM animal WHERE id_animal=?', (id_,))


def inserir_servico(nome, descricao, preco, duracao_min):
    v.obrigatorios(Nome=nome)
    centavos, duracao_min = v.preco_centavos(preco), v.inteiro_positivo(duracao_min,'Duração')
    with conectar(True) as con:
        return con.execute('INSERT INTO servico(nome,descricao,preco,preco_centavos,duracao_min) VALUES(?,?,?,?,?)',
                           (nome.strip(),descricao,centavos/100,centavos,duracao_min)).lastrowid


def atualizar_servico(id_, nome, descricao, preco, duracao_min):
    v.obrigatorios(Nome=nome)
    centavos, duracao_min = v.preco_centavos(preco), v.inteiro_positivo(duracao_min,'Duração')
    with conectar(True) as con:
        con.execute('UPDATE servico SET nome=?,descricao=?,preco=?,preco_centavos=?,duracao_min=? WHERE id_servico=?',
                    (nome.strip(),descricao,centavos/100,centavos,duracao_min,id_))


def listar_servicos(somente_ativos=False):
    with conectar() as con:
        return con.execute('SELECT * FROM servico '+('WHERE ativo=1 ' if somente_ativos else '')+'ORDER BY nome').fetchall()


def definir_servico_ativo(id_, ativo):
    with conectar(True) as con:
        con.execute('UPDATE servico SET ativo=? WHERE id_servico=?', (int(bool(ativo)),id_))


def inserir_profissional(nome,funcao):
    v.obrigatorios(Nome=nome,Função=funcao)
    with conectar(True) as con:
        return con.execute('INSERT INTO profissional(nome,funcao) VALUES(?,?)',(nome.strip(),funcao.strip())).lastrowid


def atualizar_profissional(id_profissional,nome,funcao):
    v.obrigatorios(Nome=nome,Função=funcao)
    with conectar(True) as con:
        con.execute('UPDATE profissional SET nome=?,funcao=? WHERE id_profissional=?',(nome.strip(),funcao.strip(),id_profissional))


def listar_profissionais(somente_ativos=False):
    with conectar() as con:
        return con.execute('SELECT * FROM profissional '+('WHERE ativo=1 ' if somente_ativos else '')+'ORDER BY nome').fetchall()


def definir_profissional_ativo(id_,ativo):
    with conectar(True) as con:
        con.execute('UPDATE profissional SET ativo=? WHERE id_profissional=?',(int(bool(ativo)),id_))


def _existe_sobreposicao(con,id_animal,inicio,duracao_min,ignorar_id=None,*,id_profissional=None):
    campo,identidade=('id_profissional',id_profissional) if id_profissional is not None else ('id_animal',id_animal)
    fim = inicio + timedelta(minutes=duracao_min)
    for a in con.execute(f"SELECT * FROM atendimento WHERE {campo}=? AND status IN ('agendado','concluido')", (identidade,)):
        outro = datetime.fromisoformat(a['data_hora'])
        if a['id_atendimento'] != ignorar_id and inicio < outro+timedelta(minutes=a['duracao_min']) and outro < fim:
            return True
    return False


def existe_sobreposicao(id_animal,inicio,duracao_min,ignorar_id=None):
    with conectar() as con:
        return _existe_sobreposicao(con,id_animal,inicio,duracao_min,ignorar_id)


def _validar_agendamento(con,id_animal,id_servico,data_hora,id_profissional,ignorar_id=None,duracao_min=None):
    if not isinstance(data_hora,datetime) or data_hora.tzinfo is not None:
        raise ErroValidacao('Informe uma data e hora local válida.')
    data_hora=data_hora.replace(second=0,microsecond=0)
    if ignorar_id is None and data_hora <= datetime.now():
        raise ErroValidacao('Não é possível agendar em data ou hora passada.')
    if con.execute('SELECT 1 FROM animal WHERE id_animal=?',(id_animal,)).fetchone() is None:
        raise ErroValidacao('Animal não encontrado.')
    servico = con.execute('SELECT * FROM servico WHERE id_servico=?',(id_servico,)).fetchone()
    if servico is None or not servico['ativo']:
        raise ErroValidacao('Serviço inexistente ou inativo. Selecione um serviço ativo.')
    if _existe_sobreposicao(con,id_animal,data_hora,duracao_min or servico['duracao_min'],ignorar_id):
        raise ErroValidacao('Este animal já possui atendimento sobreposto neste horário.')
    profissional=con.execute('SELECT * FROM profissional WHERE id_profissional=?',(id_profissional,)).fetchone()
    if profissional is None or not profissional['ativo']:
        raise ErroValidacao('Selecione um profissional ativo para o atendimento.')
    if _existe_sobreposicao(con,None,data_hora,duracao_min or servico['duracao_min'],ignorar_id,id_profissional=id_profissional):
        raise ErroValidacao(f"O profissional {profissional['nome']} já está reservado neste intervalo. Escolha outro horário ou profissional.")
    return servico


def _tutor_atual(con,id_animal):
    return con.execute('SELECT c.nome FROM animal a JOIN cliente c USING(id_cliente) WHERE a.id_animal=?',(id_animal,)).fetchone()[0]


def inserir_atendimento(id_animal,id_servico,data_hora,id_profissional=None):
    with conectar(True) as con:
        s=_validar_agendamento(con,id_animal,id_servico,data_hora,id_profissional)
        profissional=con.execute('SELECT nome FROM profissional WHERE id_profissional=?',(id_profissional,)).fetchone()[0]
        return con.execute('''INSERT INTO atendimento(id_animal,id_servico,data_hora,valor,valor_centavos,duracao_min,
            id_profissional,tutor_nome,servico_nome,profissional_nome,origem_historico) VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
            (id_animal,id_servico,data_hora.isoformat(timespec='minutes'),s['preco_centavos']/100,s['preco_centavos'],s['duracao_min'],
             id_profissional,_tutor_atual(con,id_animal),s['nome'],profissional,'registro')).lastrowid


def _exigir_agendado(con,id_):
    a=con.execute('SELECT * FROM atendimento WHERE id_atendimento=?',(id_,)).fetchone()
    if a is None or a['status'] != STATUS_AGENDADO:
        raise ErroValidacao('Só atendimentos agendados podem ser alterados.')
    return a


def atualizar_atendimento(id_,id_animal,id_servico,data_hora,id_profissional=None):
    with conectar(True) as con:
        a=_exigir_agendado(con,id_)
        mesmo=a['id_servico']==id_servico
        s=_validar_agendamento(con,id_animal,id_servico,data_hora,id_profissional,id_,a['duracao_min'] if mesmo else None)
        centavos=a['valor_centavos'] if mesmo else s['preco_centavos']
        profissional=con.execute('SELECT nome FROM profissional WHERE id_profissional=?',(id_profissional,)).fetchone()[0]
        con.execute('''UPDATE atendimento SET id_animal=?,id_servico=?,data_hora=?,valor=?,valor_centavos=?,duracao_min=?,
            id_profissional=?,tutor_nome=?,servico_nome=?,profissional_nome=?,origem_historico='registro' WHERE id_atendimento=?''',
            (id_animal,id_servico,data_hora.isoformat(timespec='minutes'),centavos/100,centavos,a['duracao_min'] if mesmo else s['duracao_min'],
             id_profissional,_tutor_atual(con,id_animal),a['servico_nome'] if mesmo else s['nome'],profissional,id_))


def cancelar_atendimento(id_,motivo):
    v.obrigatorios(Motivo=motivo)
    with conectar(True) as con:
        a=_exigir_agendado(con,id_)
        con.execute("UPDATE atendimento SET status='cancelado',motivo_cancelamento=?,tutor_nome=? WHERE id_atendimento=?",
                    (motivo.strip(),_tutor_atual(con,a['id_animal']),id_))


def concluir_atendimento(id_):
    with conectar(True) as con:
        a=_exigir_agendado(con,id_)
        agora=datetime.now()
        if datetime.fromisoformat(a['data_hora'])>agora:
            raise ErroValidacao('Não é possível concluir um atendimento futuro. Reagende para o horário em que foi realizado.')
        if a['id_profissional'] is None:
            raise ErroValidacao('Atribua um profissional antes de concluir este atendimento legado.')
        profissional=con.execute('SELECT nome FROM profissional WHERE id_profissional=?',(a['id_profissional'],)).fetchone()[0]
        con.execute('''UPDATE atendimento SET status='concluido',tutor_nome=?,profissional_nome=?,
            concluido_em=?,origem_historico='registro' WHERE id_atendimento=?''',
            (_tutor_atual(con,a['id_animal']),profissional,agora.isoformat(timespec='seconds'),id_))


def listar_atendimentos(busca='', status=None, mais_recentes_primeiro=False,id_profissional=None):
    sql='''SELECT * FROM (SELECT at.*,an.nome AS animal,
        CASE WHEN at.status='agendado' THEN c.nome ELSE at.tutor_nome END AS tutor,
        at.servico_nome AS servico,
        CASE WHEN at.status='agendado' THEN coalesce(p.nome,'Pendente de atribuição')
             ELSE coalesce(at.profissional_nome,'Não informado (legado)') END AS profissional
        FROM atendimento at JOIN animal an USING(id_animal) JOIN cliente c USING(id_cliente)
        LEFT JOIN profissional p USING(id_profissional)) at
        WHERE (animal LIKE ? OR tutor LIKE ? OR servico LIKE ? OR profissional LIKE ?)'''
    params=[f'%{busca}%']*4
    if status:
        sql+=' AND at.status=?';params.append(status)
    if id_profissional is not None:
        sql+=' AND at.id_profissional=?';params.append(id_profissional)
    sql+=' ORDER BY at.data_hora '+('DESC' if mais_recentes_primeiro else 'ASC')
    with conectar() as con:
        linhas=[dict(r) for r in con.execute(sql,params)]
    for a in linhas:
        a['fim_estimado']=(datetime.fromisoformat(a['data_hora'])+timedelta(minutes=a['duracao_min'])).isoformat(timespec='minutes')
    return linhas


def _hash_senha(senha,salt):
    return hashlib.pbkdf2_hmac('sha256',senha.encode(),salt,ITERACOES_HASH).hex()


def contar_usuarios():
    with conectar() as con:
        return con.execute('SELECT count(*) FROM usuario').fetchone()[0]


def criar_usuario(nome,login,senha,confirmacao=None,email=None):
    v.obrigatorios(Nome=nome)
    login=v.usuario_login(login)
    v.senha_valida(senha,confirmacao)
    email=v.email_opcional(email) or None
    sal=os.urandom(16)
    try:
        with conectar(True) as con:
            return con.execute('INSERT INTO usuario(nome,login,senha_hash,salt,criado_em,email) VALUES(?,?,?,?,?,?)',
                (nome.strip(),login,_hash_senha(senha,sal),sal.hex(),datetime.now().isoformat(timespec='seconds'),email)).lastrowid
    except sqlite3.IntegrityError:
        raise ErroValidacao('Já existe um usuário com este nome de acesso ou e-mail.') from None


def autenticar(login,senha):
    with conectar() as con:
        u=con.execute('SELECT * FROM usuario WHERE login=?',(login.strip().lower(),)).fetchone()
    calculado=_hash_senha(senha,bytes.fromhex(u['salt']) if u else b'\x00'*16)
    if u and hmac.compare_digest(calculado,u['senha_hash']):
        return {k:u[k] for k in ('id_usuario','nome','login')}


def fazer_backup(destino):
    destino=os.path.abspath(destino)
    if destino==os.path.abspath(DB_PATH):
        raise ErroValidacao('Escolha outro arquivo para o backup.')
    with open(destino,'xb'):
        pass
    try:
        with conectar() as origem:
            copia=sqlite3.connect(destino)
            try: origem.backup(copia)
            finally: copia.close()
    except Exception:
        os.unlink(destino)
        raise


def _migrar_recuperacao(con):
    try:
        con.execute('BEGIN IMMEDIATE')
        if 'email' not in {r[1] for r in con.execute('PRAGMA table_info(usuario)')}:
            con.execute('ALTER TABLE usuario ADD COLUMN email TEXT')
        con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_usuario_email ON usuario(lower(trim(email))) WHERE nullif(trim(email),'') IS NOT NULL")
        con.execute('''CREATE TABLE IF NOT EXISTS recuperacao_senha(
            id_usuario INTEGER PRIMARY KEY REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            identificador TEXT NOT NULL UNIQUE,codigo_hash TEXT NOT NULL,sal TEXT NOT NULL,
            solicitado_em REAL NOT NULL,expira_em REAL NOT NULL,tentativas INTEGER NOT NULL DEFAULT 0,
            enviado INTEGER NOT NULL DEFAULT 0)''')
        con.commit()
    except Exception:
        con.rollback()
        raise


def email_do_usuario(id_):
    with conectar() as con:
        u=con.execute('SELECT email FROM usuario WHERE id_usuario=?',(id_,)).fetchone()
        return u['email'] if u else None


def atualizar_email_usuario(id_,senha_atual,email):
    email=v.email_opcional(email)
    v.obrigatorios(**{'E-mail':email,'Senha atual':senha_atual})
    with conectar(True) as con:
        u=con.execute('SELECT * FROM usuario WHERE id_usuario=?',(id_,)).fetchone()
        if u is None or not hmac.compare_digest(_hash_senha(senha_atual,bytes.fromhex(u['salt'])),u['senha_hash']):
            raise ErroValidacao('Senha atual incorreta.')
        con.execute('UPDATE usuario SET email=? WHERE id_usuario=?',(email,id_))
        con.execute('DELETE FROM recuperacao_senha WHERE id_usuario=?',(id_,))
