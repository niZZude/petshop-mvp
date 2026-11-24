"""Normalização e validações de entrada para o MVP."""
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime


class ErroValidacao(Exception):
    pass


def obrigatorios(**campos):
    vazios=[n for n,v in campos.items() if v is None or not str(v).strip()]
    if vazios: raise ErroValidacao('Preencha os campos obrigatórios: '+', '.join(vazios))


def telefone(valor):
    d=re.sub(r'\D','',valor or '')
    if len(d) not in (10,11): raise ErroValidacao('Telefone inválido. Use DDD + número.')
    return d


def email_opcional(valor):
    valor=(valor or '').strip().lower()
    if valor and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',valor): raise ErroValidacao('E-mail inválido.')
    return valor


def preco(valor):
    try:
        texto=str(valor).strip()
        if not re.fullmatch(r'[0-9]+(?:[.,][0-9]+)?',texto): raise InvalidOperation
        p=Decimal(texto.replace(',','.'))
        if not p.is_finite() or p<=0: raise InvalidOperation
        if p != p.quantize(Decimal('0.01')):
            raise ErroValidacao('Preço deve ter no máximo duas casas decimais.')
        if p > Decimal('999999999.99'):
            raise ErroValidacao('Preço deve ser no máximo R$ 999.999.999,99.')
    except (InvalidOperation,ValueError,TypeError):
        raise ErroValidacao('Preço deve ser um número maior que zero, com até duas casas decimais.') from None
    return p


def preco_centavos(valor):
    return int(preco(valor)*100)


def valor_para_campo(centavos):
    inteiro,fracao=divmod(centavos,100)
    return f'{inteiro},{fracao:02d}'


def formatar_centavos(centavos):
    inteiro,fracao=divmod(centavos,100)
    return f"R$ {inteiro:,}".replace(',','.')+f',{fracao:02d}'


def inteiro_positivo(valor,campo):
    try:
        if isinstance(valor,bool) or (isinstance(valor,float) and not valor.is_integer()): raise ValueError
        n=int(valor)
    except (ValueError,TypeError,OverflowError): raise ErroValidacao(f'{campo} deve ser um inteiro.') from None
    if n<=0: raise ErroValidacao(f'{campo} deve ser maior que zero.')
    return n


def data_hora(texto):
    try: dt=datetime.strptime(texto.strip(),'%d/%m/%Y %H:%M')
    except ValueError: raise ErroValidacao('Data/hora inválida. Use dd/mm/aaaa hh:mm.') from None
    return dt


def data_hora_futura(texto):
    dt=data_hora(texto)
    if dt<=datetime.now(): raise ErroValidacao('Não é possível agendar em data ou hora passada.')
    return dt


def cpf(valor):
    texto=(valor or '').strip()
    if not re.fullmatch(r'(?:[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})',texto):
        raise ErroValidacao('CPF inválido. Informe 11 dígitos ou use 000.000.000-00.')
    d=re.sub(r'[^0-9]','',texto)
    if len(set(d))==1: raise ErroValidacao('CPF inválido.')
    for t in (9,10):
        soma=sum(int(n)*peso for n,peso in zip(d[:t],range(t+1,1,-1)))
        if (soma*10%11)%10!=int(d[t]): raise ErroValidacao('CPF inválido. Confira os dígitos.')
    return d


def formatar_cpf(d):
    d=d or ''
    return f'{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}' if len(d)==11 else d


def formatar_telefone(valor):
    d=re.sub(r'\D','',valor or '')
    if len(d)==11: return f'({d[:2]}) {d[2:7]}-{d[7:]}'
    if len(d)==10: return f'({d[:2]}) {d[2:6]}-{d[6:]}'
    return valor or ''


def usuario_login(valor):
    login=valor.strip().lower()
    if not re.fullmatch(r'[a-z0-9._-]{3,20}',login): raise ErroValidacao('Usuário inválido. Use 3 a 20 letras, números, ponto, hífen ou sublinhado.')
    return login


def senha_valida(senha,confirmacao=None):
    if len(senha)<6 or not re.search(r'[A-Za-z]',senha) or not re.search(r'\d',senha):
        raise ErroValidacao('A senha deve ter pelo menos 6 caracteres, com letras e números.')
    if confirmacao is not None and senha!=confirmacao: raise ErroValidacao('As senhas não conferem.')
    return senha
