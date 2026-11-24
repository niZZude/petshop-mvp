"""Regressão real dos widgets da revisão; não equivale a estudo com usuário."""
from datetime import datetime,timedelta
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import database as db
import app as m
import popular_demo


def digitar(e,texto):
    e.delete(0,'end');e.insert(0,texto)


checks=[]
def check(nome,condicao):
    assert condicao,nome
    checks.append(nome);print('OK',nome,flush=True)


capturas=None
if '--capturas' in sys.argv:
    capturas=Path(sys.argv[sys.argv.index('--capturas')+1]);capturas.mkdir(parents=True,exist_ok=True)


def capturar(app,nome,aba):
    if capturas is None: return
    from PIL import ImageGrab
    app.abas.set(aba);app.lift();app.attributes('-topmost',True);app.update()
    fim=time.monotonic()+0.4
    while time.monotonic()<fim:
        app.update();time.sleep(0.02)
    x,y=app.winfo_rootx(),app.winfo_rooty()
    ImageGrab.grab(bbox=(x,y,x+app.winfo_width(),y+app.winfo_height())).save(capturas/nome)
    app.attributes('-topmost',False)


with tempfile.TemporaryDirectory() as pasta,patch.object(m.messagebox,'askyesno',return_value=True) as confirmar,patch.object(m.messagebox,'showinfo'),patch.object(m.messagebox,'showerror') as erro:
    db.DB_PATH=str(Path(pasta)/'gui.db');popular_demo.popular()
    a=m.App();a.geometry('1260x760+20+20');a.update()
    try:
        check('aba Profissionais e equipe fictícia',len(a.tables['profissional'].get_children())==3)
        a.adicionar_equipe_demo();a.update()
        check('equipe fictícia não duplica nem cria logins',len(db.listar_profissionais())==3 and db.contar_usuarios()==0)
        t=a.tables['cliente'];t.selection_set('1');a.carregar('cliente');a.update()
        digitar(a.forms['cliente']['nome'],'Maria em edição')
        digitar(a.buscas['cliente'],'Maria');a.atualizar_lista('cliente');a.update()
        check('busca mantém destaque e edição não salva',t.selection()==('1',) and a.sel['cliente']==1 and a.forms['cliente']['nome'].get()=='Maria em edição')
        confirmar.return_value=False
        digitar(a.buscas['cliente'],'Carlos');a.atualizar_lista('cliente');a.update()
        check('recusar descarte preserva formulário e filtro anterior',a.sel['cliente']==1 and t.selection()==('1',) and a.buscas['cliente'].get()=='Maria' and a.forms['cliente']['nome'].get()=='Maria em edição')
        confirmar.return_value=True
        digitar(a.buscas['cliente'],'Carlos');a.atualizar_lista('cliente');a.update()
        check('filtro que oculta registro encerra edição após confirmação',a.sel['cliente'] is None and not t.selection() and a.forms['cliente']['nome'].get()=='' and a.modos['cliente'].cget('text')=='Novo cadastro')
        check('nenhuma alteração de pesquisa foi gravada',db.buscar_cliente(1)['nome']=='Maria Oliveira')
        digitar(a.buscas['cliente'],'');a.atualizar_lista('cliente')

        for k,valor in {'nome':'Serviço centavos','descricao':'Exemplo','preco':'0,005','duracao_min':'30'}.items(): digitar(a.forms['servico'][k],valor)
        a.salvar_servico()
        check('interface rejeita fração de centavo e preserva entrada','duas casas' in erro.call_args.args[1] and a.forms['servico']['preco'].get()=='0,005')
        digitar(a.forms['servico']['preco'],'19,95');a.salvar_servico();a.update()
        s=max(db.listar_servicos(),key=lambda r:r['id_servico'])['id_servico']
        a.tables['servico'].selection_set(str(s));a.carregar('servico');a.update()
        check('preço armazenado em centavos e formulário com vírgula',db.buscar_servico(s)['preco_centavos']==1995 and a.forms['servico']['preco'].get()=='19,95')
        check('tabela exibe reais com dois decimais',a.tables['servico'].item(str(s),'values')[2]=='R$ 19,95')

        digitar(a.forms['profissional']['nome'],'Diego Moraes');digitar(a.forms['profissional']['funcao'],'Banho e tosa')
        a.salvar_profissional();a.update()
        p=max(db.listar_profissionais(),key=lambda r:r['id_profissional'])['id_profissional']
        check('cadastro de profissional pela interface',db.buscar_profissional(p)['nome']=='Diego Moraes' and any(x.startswith(str(p)+' - ') for x in a.forms['atendimento']['id_profissional'].cget('values')))
        a.tables['profissional'].selection_set(str(p));a.carregar('profissional')
        digitar(a.forms['profissional']['funcao'],'Banho e tosa — demonstração');a.salvar_profissional();a.update()
        check('edição de profissional pela interface',db.buscar_profissional(p)['funcao']=='Banho e tosa — demonstração')

        futuro=(datetime.now()+timedelta(days=20)).replace(hour=10,minute=0,second=0,microsecond=0)
        form=a.forms['atendimento']
        form['id_animal'].set('1 - Thor');form['id_servico'].set('1 - Banho');form['id_profissional'].set('1 - Ana Souza')
        digitar(form['data_hora'],futuro.strftime('%d/%m/%Y %H:%M'));a.salvar_atendimento();a.update()
        id_=max(r['id_atendimento'] for r in db.listar_atendimentos())
        check('cadastro com profissional',db.buscar_atendimento(id_)['id_profissional']==1)
        a.tables['atendimento'].selection_set(str(id_));a.carregar('atendimento');a.concluir_atendimento()
        check('botão Concluir recusa atendimento futuro',db.buscar_atendimento(id_)['status']=='agendado' and 'futuro' in erro.call_args.args[1])
        a.limpar_form('atendimento')
        form['id_animal'].set('2 - Mel');form['id_servico'].set('1 - Banho');form['id_profissional'].set('1 - Ana Souza')
        digitar(form['data_hora'],(futuro+timedelta(minutes=30)).strftime('%d/%m/%Y %H:%M'));a.salvar_atendimento()
        check('interface informa conflito do profissional','profissional Ana Souza' in erro.call_args.args[1] and len(db.listar_atendimentos())==8)
        form['id_profissional'].set('2 - Bruno Lima');a.salvar_atendimento();a.update()
        outro=max(r['id_atendimento'] for r in db.listar_atendimentos())
        check('outro profissional aceita horário paralelo',db.buscar_atendimento(outro)['id_profissional']==2)
        a.profissional_filtro.set('1 - Ana Souza');a.atualizar_lista('atendimento');a.update()
        check('filtro de agenda por profissional',str(outro) not in a.tables['atendimento'].get_children() and str(id_) in a.tables['atendimento'].get_children())
        a.profissional_filtro.set('Todos os profissionais');a.atualizar_lista('atendimento')
        a.tables['atendimento'].selection_set(str(id_));a.carregar('atendimento');a.reagendar_agora();a.update()
        check('Reagendar para agora salva horário realizado',datetime.fromisoformat(db.buscar_atendimento(id_)['data_hora'])<=datetime.now())
        a.tables['atendimento'].selection_set(str(id_));a.carregar('atendimento')
        realizado=(datetime.now()-timedelta(days=2)).replace(second=0,microsecond=0)
        digitar(form['data_hora'],realizado.strftime('%d/%m/%Y %H:%M'));a.salvar_atendimento();a.update()
        check('correção de horário passado pela interface',db.buscar_atendimento(id_)['data_hora']==realizado.isoformat(timespec='minutes'))
        a.tables['atendimento'].selection_set(str(id_));a.carregar('atendimento');a.concluir_atendimento();a.update()
        check('conclusão após reagendar aceita',db.buscar_atendimento(id_)['status']=='concluido')

        db.atualizar_animal(1,2,'Thor','Cachorro','Golden','');a.atualizar_tudo();a.update()
        historico={r['id_atendimento']:r for r in db.listar_atendimentos(status='concluido')}
        check('troca de tutor preserva conclusão antiga',historico[id_]['tutor']=='Maria Oliveira')
        novo=db.inserir_atendimento(1,1,futuro+timedelta(days=3),1)
        db.atualizar_atendimento(novo,1,1,datetime.now()-timedelta(days=1),1);db.concluir_atendimento(novo)
        a.atualizar_tudo();a.update()
        historico={r['id_atendimento']:r for r in db.listar_atendimentos(status='concluido')}
        check('novo atendimento usa novo tutor',historico[novo]['tutor']=='Carlos Pereira')
        check('histórico gráfico usa os dois tutores',a.t_hist.item(str(id_),'values')[3]=='Maria Oliveira' and a.t_hist.item(str(novo),'values')[3]=='Carlos Pereira')
        check('total gráfico soma centavos exatamente',a.total.cget('text')=='Total de serviços concluídos: '+m.v.formatar_centavos(sum(r['valor_centavos'] for r in historico.values())))

        a.tables['atendimento'].selection_set('7');a.carregar('atendimento');a.update()
        a.tables['profissional'].selection_set('3');a.carregar('profissional');a.alternar_profissional();a.update()
        check('inativação remove profissional de novas reservas',not any(p.startswith('3 - ') for p in form['id_profissional'].cget('values')))
        check('inativação não troca profissional de edição aberta',form['id_profissional'].get().startswith('3 - ') and a.sel['atendimento']==7)
        a.tables['profissional'].selection_set('3');a.carregar('profissional');a.alternar_profissional();a.update()
        check('reativação devolve profissional à agenda',any(p.startswith('3 - ') for p in form['id_profissional'].cget('values')))
        check('tabela apresenta fim estimado',a.tables['atendimento'].item(str(outro),'values')[2]==(futuro+timedelta(minutes=90)).strftime('%d/%m/%Y %H:%M'))
        a.profissional_filtro.set('Todos os profissionais');a.status_filtro.set('agendado');a.atualizar_lista('atendimento');a.tables['atendimento'].selection_set('5');a.carregar('atendimento');a.update()
        capturar(a,'agenda_profissionais.png','Atendimentos')
        capturar(a,'historico_tutores.png','Histórico')
        capturar(a,'profissionais.png','Profissionais')
        a.tables['cliente'].selection_set('1');a.carregar('cliente');a.update()
        capturar(a,'cadastro_cliente.png','Clientes')
        a.tables['servico'].selection_set(str(s));a.carregar('servico');a.update()
        capturar(a,'servicos_centavos.png','Serviços')
        a.tables['atendimento'].selection_set(str(outro));a.carregar('atendimento')
        with patch.object(m.simpledialog,'askstring',return_value='Cancelamento de demonstração'):
            a.cancelar_atendimento()
        a.status_filtro.set('cancelado');a.atualizar_lista('atendimento');a.tables['atendimento'].selection_set(str(outro));a.carregar('atendimento');a.update()
        check('cancelamento pela interface preserva motivo e registro',db.buscar_atendimento(outro)['motivo_cancelamento']=='Cancelamento de demonstração' and a.save_buttons['atendimento'].cget('state')=='disabled')
        a.tables['atendimento'].xview_moveto(1.0)
        capturar(a,'cancelamento.png','Atendimentos')
    finally:
        a.destroy()

print(f'{len(checks)}/{len(checks)} verificações gráficas da revisão aprovadas. Dados fictícios; sem e-mail real.')
