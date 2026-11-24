"""Código de recuperação com uso único e entrega HTTPS pela Resend."""
import configparser
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from urllib import request,error
import database as db
import validacoes as v

VALIDADE_SEGUNDOS=600
INTERVALO_SEGUNDOS=60
MAX_TENTATIVAS=5
MENSAGEM_ENVIO=('Se o usuário e o e-mail corresponderem a uma conta, um código será enviado. '
                'Confira a caixa de entrada e o spam. Aguarde 60 segundos antes de reenviar.')


def _configuracao():
    config=configparser.ConfigParser(interpolation=None)
    try: config.read(Path(__file__).with_name('resend.ini'),encoding='utf-8')
    except (configparser.Error,OSError): raise v.ErroValidacao('Configuração resend.ini inválida.') from None
    chave=os.environ.get('RESEND_API_KEY',config.get('resend','api_key',fallback='')).strip()
    remetente=os.environ.get('RESEND_FROM',config.get('resend','from',fallback='Pet Shop <onboarding@resend.dev>')).strip()
    if not chave: raise v.ErroValidacao('Recuperação indisponível: configure RESEND_API_KEY ou resend.ini neste computador.')
    if '\n' in remetente or '\r' in remetente: raise v.ErroValidacao('Remetente inválido.')
    return chave,remetente


def enviar_codigo(destinatario,codigo,identificador):
    chave,remetente=_configuracao()
    corpo=json.dumps({'from':remetente,'to':[destinatario],'subject':'Pet Shop — código para redefinir sua senha',
        'text':f'Seu código de recuperação do Pet Shop é: {codigo}\n\nEle vale por 10 minutos e só pode ser utilizado uma vez. '
               'Se você não pediu a recuperação, ignore esta mensagem. Sua senha atual permanece válida até a redefinição.'}).encode()
    req=request.Request('https://api.resend.com/emails',data=corpo,method='POST',headers={
        'Authorization':f'Bearer {chave}','Content-Type':'application/json','User-Agent':'PetShopAcademico/1.0',
        'Idempotency-Key':f'recuperacao/{identificador}'})
    try:
        with request.urlopen(req,timeout=15) as resposta:
            if not json.load(resposta).get('id'): raise v.ErroValidacao('O provedor não confirmou o envio.')
    except error.HTTPError as erro:
        mensagens={401:'A chave da Resend não foi aceita.',403:'Envio não autorizado. No modo de teste, o destinatário deve ser o e-mail da conta Resend.',429:'Limite de envio atingido. Aguarde e tente novamente.'}
        aviso=mensagens.get(erro.code,'O provedor de e-mail está indisponível. Tente mais tarde.')
        erro.close()
        raise v.ErroValidacao(aviso) from None
    except (error.URLError,TimeoutError,OSError,ValueError):
        raise v.ErroValidacao('Não foi possível enviar o e-mail. Confira sua conexão e tente mais tarde.') from None


def _hash_codigo(codigo,sal):
    return hashlib.pbkdf2_hmac('sha256',codigo.encode(),bytes.fromhex(sal),db.ITERACOES_HASH).hex()


def solicitar(login,email):
    _configuracao()
    login=v.usuario_login(login);email=v.email_opcional(email);v.obrigatorios(**{'E-mail':email})
    agora=time.time();codigo=f'{secrets.randbelow(100_000_000):08d}'
    sal=secrets.token_hex(16);identificador=secrets.token_hex(16);digest=_hash_codigo(codigo,sal)
    with db.conectar(True) as con:
        usuario=con.execute('SELECT id_usuario,email FROM usuario WHERE login=? AND lower(trim(email))=?',(login,email)).fetchone()
        if usuario is None: return MENSAGEM_ENVIO
        id_usuario=usuario['id_usuario']
        anterior=con.execute('SELECT solicitado_em FROM recuperacao_senha WHERE id_usuario=?',(id_usuario,)).fetchone()
        if anterior and agora-anterior['solicitado_em']<INTERVALO_SEGUNDOS: return MENSAGEM_ENVIO
        con.execute('''INSERT INTO recuperacao_senha(id_usuario,identificador,codigo_hash,sal,solicitado_em,expira_em,tentativas,enviado)
            VALUES(?,?,?,?,?,?,0,0) ON CONFLICT(id_usuario) DO UPDATE SET identificador=excluded.identificador,
            codigo_hash=excluded.codigo_hash,sal=excluded.sal,solicitado_em=excluded.solicitado_em,
            expira_em=excluded.expira_em,tentativas=0,enviado=0''',(id_usuario,identificador,digest,sal,agora,agora+VALIDADE_SEGUNDOS))
    try: enviar_codigo(usuario['email'],codigo,identificador)
    except Exception:
        with db.conectar(True) as con: con.execute('UPDATE recuperacao_senha SET expira_em=0 WHERE identificador=?',(identificador,))
        raise
    with db.conectar(True) as con: con.execute('UPDATE recuperacao_senha SET enviado=1 WHERE identificador=?',(identificador,))
    return MENSAGEM_ENVIO


def redefinir(login,email,codigo,senha,confirmacao):
    login=v.usuario_login(login);email=v.email_opcional(email);v.senha_valida(senha,confirmacao);codigo=codigo.strip()
    sucesso=False
    with db.conectar(True) as con:
        linha=con.execute('''SELECT r.* FROM recuperacao_senha r JOIN usuario u USING(id_usuario)
            WHERE u.login=? AND lower(trim(u.email))=?''',(login,email)).fetchone()
        if linha and linha['enviado'] and linha['expira_em']>time.time() and linha['tentativas']<MAX_TENTATIVAS:
            con.execute('UPDATE recuperacao_senha SET tentativas=tentativas+1 WHERE id_usuario=?',(linha['id_usuario'],))
            if len(codigo)==8 and codigo.isascii() and codigo.isdigit() and hmac.compare_digest(_hash_codigo(codigo,linha['sal']),linha['codigo_hash']):
                sal=os.urandom(16)
                con.execute('UPDATE usuario SET senha_hash=?,salt=? WHERE id_usuario=?',(db._hash_senha(senha,sal),sal.hex(),linha['id_usuario']))
                con.execute('DELETE FROM recuperacao_senha WHERE id_usuario=?',(linha['id_usuario'],));sucesso=True
    if not sucesso: raise v.ErroValidacao('Código inválido, expirado ou sem tentativas disponíveis. Solicite outro código.')
