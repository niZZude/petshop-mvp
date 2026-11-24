"""Alertas consultivos: não gravam nem bloqueiam cadastros."""
import re
import unicodedata
from difflib import SequenceMatcher
ROTULOS={'nome':'nome','telefone':'telefone','email':'e-mail','endereco':'endereço','cpf':'CPF'}


def texto(valor): return ' '.join((valor or '').lower().split())


def sem_acentos(valor):
    return ''.join(c for c in unicodedata.normalize('NFD',texto(valor)) if unicodedata.category(c)!='Mn')


def comparar(dados,existentes,ignorar_id=None):
    resultado=[]
    for c in existentes:
        if c['id_cliente']==ignorar_id: continue
        campos=[]
        for campo in ROTULOS:
            a,b=dados.get(campo,''),c[campo] if campo in c.keys() else ''
            if campo in ('telefone','cpf'):
                a,b=re.sub(r'\D','',a or ''),re.sub(r'\D','',b or '')
                parecido=a==b and len(a) in ((11,) if campo=='cpf' else (10,11))
            elif campo=='email':
                a,b=texto(a),texto(b);parecido='@' in a and a==b
            else:
                a,b=sem_acentos(a),sem_acentos(b)
                parecido=min(len(a),len(b))>=4 and SequenceMatcher(None,a,b,autojunk=False).ratio()>=.85
            if parecido: campos.append(campo)
        if campos: resultado.append({'id_cliente':c['id_cliente'],'nome':c['nome'],'campos':campos})
    return resultado
