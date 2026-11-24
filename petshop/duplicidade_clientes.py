"""Instalação atômica de CPF/e-mail únicos, sem exclusão de dados."""
import sqlite3
import validacoes as v


class DuplicadosExistentes(ValueError):
    pass


def instalar_protecao(conexao: sqlite3.Connection):
    if conexao.in_transaction: raise ValueError('Finalize a transação atual antes de instalar a proteção.')
    try:
        conexao.execute('BEGIN IMMEDIATE')
        if 'cpf' not in {r[1] for r in conexao.execute('PRAGMA table_info(cliente)')}:
            conexao.execute('ALTER TABLE cliente ADD COLUMN cpf TEXT')
        cpf_sql="replace(replace(replace(trim(cpf),'.',''),'-',''),' ','')"
        email_sql='lower(trim(email))'
        for campo,expr in [('CPF',cpf_sql),('e-mail',email_sql)]:
            duplicados=conexao.execute(f"SELECT group_concat(id_cliente) FROM cliente WHERE nullif({expr},'') IS NOT NULL GROUP BY {expr} HAVING count(*)>1").fetchall()
            if duplicados: raise DuplicadosExistentes(f'{campo} repetido (IDs: '+ '; '.join(r[0] for r in duplicados)+'). Revise os cadastros e vínculos. Nenhum cliente foi excluído.')
        for evento in ('insert','update'):
            conexao.execute(f'DROP TRIGGER IF EXISTS cliente_duplicado_{evento}_etapa4')
        conexao.execute('DROP INDEX IF EXISTS ux_cliente_dados_etapa4')
        for id_,cpf in conexao.execute('SELECT id_cliente,cpf FROM cliente WHERE cpf IS NOT NULL').fetchall():
            try: documento=v.cpf(cpf)
            except v.ErroValidacao: raise DuplicadosExistentes(f'CPF inválido no cliente ID {id_}. Revise antes de atualizar.') from None
            if documento!=cpf: conexao.execute('UPDATE cliente SET cpf=? WHERE id_cliente=?',(documento,id_))
        conexao.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS ux_cliente_cpf ON cliente({cpf_sql}) WHERE nullif({cpf_sql},'') IS NOT NULL")
        conexao.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS ux_cliente_email ON cliente({email_sql}) WHERE nullif({email_sql},'') IS NOT NULL")
        for evento in ('INSERT','UPDATE'):
            obrigatorio='1' if evento=='INSERT' else '(OLD.cpf IS NOT NULL OR NEW.cpf IS NOT NULL)'
            conexao.execute(f'''CREATE TRIGGER IF NOT EXISTS cliente_formato_{evento.lower()} BEFORE {evento} ON cliente
                BEGIN SELECT CASE WHEN ({obrigatorio}) AND (NEW.cpf IS NULL OR length(NEW.cpf)!=11 OR NEW.cpf GLOB '*[^0-9]*')
                THEN RAISE(ABORT,'CPF deve conter 11 dígitos.') END; END''')
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
