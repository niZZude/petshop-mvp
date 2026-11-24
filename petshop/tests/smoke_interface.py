"""Regressão gráfica com banco temporário. Provedor de e-mail simulado."""
from pathlib import Path
import os
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import database as db
import popular_demo
import app as m
import login
import recuperacao as r


def digitar(e,t): e.delete(0,'end');e.insert(0,t)


def esperar(tela,condicao):
    fim=time.monotonic()+8
    while not condicao() and time.monotonic()<fim: tela.update();time.sleep(.02)
    assert condicao(),'Tempo esgotado'


checks=[]
def check(nome,cond):
    assert cond,nome
    checks.append(nome);print('OK',nome)


with tempfile.TemporaryDirectory() as pasta,patch.dict(os.environ,{'RESEND_API_KEY':'re_simulado'}),patch.object(m.messagebox,'askyesno',return_value=True),patch.object(m.messagebox,'showinfo'),patch.object(m.messagebox,'showerror') as erro:
    db.DB_PATH=str(Path(pasta)/'gui.db');db.criar_tabelas()
    t=login.TelaLogin();t.update()
    check('primeiro acesso e e-mail sugerido',t.primeiro_acesso and t.e_email.get()=='nixxude@gmail.com')
    t.criar_primeiro_acesso();check('primeiro acesso rejeita campos vazios',db.contar_usuarios()==0)
    for e,texto in [(t.e_nome,'Eduardo'),(t.e_login,'eduardo'),(t.e_senha,'Senha123'),(t.e_confirma,'Senha123')]:digitar(e,texto)
    t.criar_primeiro_acesso();check('primeiro acesso autentica',bool(t.usuario))
    t=login.TelaLogin();t.update();agora=[1000.];t.relogio=lambda:agora[0]
    for _ in range(5):digitar(t.e_login,'eduardo');digitar(t.e_senha,'errada');t.entrar()
    check('bloqueio após cinco falhas','Aguarde' in t.mensagem.cget('text'))
    digitar(t.e_senha,'Senha123');t.entrar();check('bloqueio impede senha correta',t.usuario is None)
    agora[0]+=31;t.entrar();check('acesso após fim do bloqueio',bool(t.usuario))
    popular_demo.popular()
    a=m.App(t.usuario);a.geometry('1260x760+25+25');a.update()
    check('abas e dados da demonstração',len(a.tables['cliente'].get_children())==3 and len(db.listar_atendimentos())==7)
    a.tables['cliente'].selection_set('1');a.carregar('cliente');check('seleção carrega CPF formatado',a.forms['cliente']['cpf'].get()=='529.982.247-25')
    digitar(a.forms['cliente']['nome'],'Maria alterada');a.salvar_cliente();check('edição confirmada',db.buscar_cliente(1)['nome']=='Maria alterada')
    for k,valor in {'nome':'Pessoa','telefone':'86999990000','cpf':'52998224725','email':'outra@example.com'}.items():digitar(a.forms['cliente'][k],valor)
    a.salvar_cliente();check('CPF repetido bloqueado sem limpar','CPF já' in erro.call_args.args[1] and a.forms['cliente']['nome'].get()=='Pessoa')
    digitar(a.forms['cliente']['cpf'],'98765432100');digitar(a.forms['cliente']['email'],'MARIA@EXEMPLO.COM');a.salvar_cliente()
    check('e-mail repetido com outro CPF bloqueado','E-mail já' in erro.call_args.args[1])
    a.atualizar_alertas();check('borda vermelha no e-mail',a.forms['cliente']['email'].cget('border_color')==m.COR_PERIGO)
    digitar(a.forms['cliente']['email'],'pessoa@example.com');a.salvar_cliente();check('cliente novo permitido',len(db.listar_clientes())==4)
    pessoa=next(c for c in db.listar_clientes() if c['nome']=='Pessoa')['id_cliente']
    a.tables['cliente'].selection_set(str(pessoa));a.carregar('cliente');a.excluir('cliente');check('excluir cliente livre',db.buscar_cliente(pessoa) is None)
    a.tables['cliente'].selection_set('1');a.carregar('cliente');a.excluir('cliente');check('cliente vinculado protegido',db.buscar_cliente(1) is not None)
    a.limpar_form('cliente');check('limpar remove cores e seleção',not a.alerta.cget('text') and a.sel['cliente'] is None)
    a.tables['servico'].selection_set('1');a.carregar('servico');a.alternar_servico();check('inativação remove opção de agendar',not db.buscar_servico(1)['ativo'] and not any(x.startswith('1 - ') for x in a.forms['atendimento']['id_servico'].cget('values')))
    a.tables['servico'].selection_set('1');a.carregar('servico');a.alternar_servico();check('reativação',bool(db.buscar_servico(1)['ativo']))
    from datetime import datetime,timedelta
    data=(datetime.now()+timedelta(days=20)).replace(second=0,microsecond=0)
    a.forms['atendimento']['id_animal'].set('1 - Thor');a.forms['atendimento']['id_servico'].set('1 - Banho');digitar(a.forms['atendimento']['data_hora'],data.strftime('%d/%m/%Y %H:%M'));a.salvar_atendimento()
    novo=max(x['id_atendimento'] for x in db.listar_atendimentos());check('agendamento pela interface',novo==8)
    a.tables['atendimento'].selection_set(str(novo));a.carregar('atendimento')
    with patch.object(m.simpledialog,'askstring',return_value='Tutor viajou'):a.cancelar_atendimento()
    check('cancelamento com motivo',db.buscar_atendimento(novo)['motivo_cancelamento']=='Tutor viajou')
    a.tables['atendimento'].selection_set(str(novo));a.carregar('atendimento');check('finalizado abre só consulta',a.save_buttons['atendimento'].cget('state')=='disabled')
    a.atualizar_historico();check('histórico de concluídos',len(a.t_hist.get_children())==4)
    destino=str(Path(pasta)/'backup.db')
    with patch.object(m.filedialog,'asksaveasfilename',return_value=destino):a.salvar_backup()
    check('backup pela interface',Path(destino).exists())
    a.minha_conta();a.update();janela,email,senha,salvar,msg=a._dialogo_conta
    check('Minha conta carrega e-mail do usuário',email.get()=='nixxude@gmail.com')
    digitar(email,'outro@example.com');digitar(senha,'errada');salvar();check('alterar e-mail exige senha atual','incorreta' in msg.cget('text'))
    digitar(senha,'Senha123');salvar();check('alterar e-mail autenticado',db.email_do_usuario(1)=='outro@example.com')
    a.novo_usuario();a.update();janela,entradas,salvar,msg=a._dialogo_usuario
    for e,valor in zip(entradas,['Bia','bia','Senha123','Senha123','bia@example.com']):digitar(e,valor)
    salvar();check('novo usuário com e-mail',db.autenticar('bia','Senha123') is not None)
    a.sair();check('Sair encerra sessão',a.sair_solicitado)
    t=login.TelaLogin();t.update();t.abrir_recuperacao();t.update()
    usuario,email,codigo,senha,confirma,pedir,redefinir,msg=t._campos_recuperacao
    digitar(usuario,'eduardo');digitar(email,'outro@example.com');entregas=[]
    with patch.object(r,'enviar_codigo',side_effect=lambda *args:entregas.append(args)):
        pedir();esperar(t,lambda:'Se o usuário' in msg.cget('text'))
    check('envio em segundo plano',len(entregas)==1)
    digitar(codigo,entregas[0][1]);digitar(senha,'NovaSenha123');digitar(confirma,'NovaSenha123');redefinir()
    esperar(t,lambda:'Senha redefinida' in msg.cget('text'))
    check('redefinir limpa os campos sensíveis',not codigo.get() and not senha.get())
    t._recuperacao.destroy();digitar(t.e_login,'eduardo');digitar(t.e_senha,'NovaSenha123');t.entrar()
    check('login com a nova senha',bool(t.usuario))
print(f'{len(checks)}/{len(checks)} verificações gráficas aprovadas. Nenhum e-mail real enviado.')
