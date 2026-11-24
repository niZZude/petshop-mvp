"""Interface desktop do MVP Pet Shop. Execute python app.py."""
from datetime import datetime
from tkinter import ttk,messagebox,simpledialog,filedialog
import customtkinter as ctk
import database as db
import login
import popular_demo
import similaridade_clientes as sim
import validacoes as v

COR_PRIMARIA='#1F7A6E'
COR_DESTAQUE='#F08A4B'
COR_PERIGO='#B3402F'
COR_AVISO='#A66B16'


def preencher(e,valor):
    e.delete(0,'end');e.insert(0,valor or '')


class Tabela(ttk.Treeview):
    def __init__(self,pai,colunas):
        super().__init__(pai,columns=[c[0] for c in colunas],show='headings',selectmode='browse',height=12)
        for chave,titulo,largura in colunas:
            self.heading(chave,text=titulo);self.column(chave,width=largura,anchor='w')
    def preencher(self,linhas):
        ids={str(linha[0]) for linha in linhas}
        for id_ in self.get_children():
            if id_ not in ids: self.delete(id_)
        for posicao,linha in enumerate(linhas):
            id_=str(linha[0])
            if self.exists(id_): self.item(id_,values=linha)
            else: self.insert('','end',iid=id_,values=linha)
            self.move(id_,'',posicao)
    def selecionado(self):
        sel=self.selection();return int(sel[0]) if sel else None


class App(ctk.CTk):
    def __init__(self,usuario=None):
        super().__init__();ctk.set_appearance_mode('light')
        self.usuario=usuario;self.sair_solicitado=False;self._alerta_job=None
        self.title('Sistema para Pet Shop');self.geometry('1260x760');self.minsize(1000,650)
        self.sel={k:None for k in ('cliente','animal','servico','profissional','atendimento')}
        self._originais_form={};self._filtros_aplicados={}
        topo=ctk.CTkFrame(self,fg_color='#18302F');topo.pack(fill='x')
        ctk.CTkLabel(topo,text='Pet Shop — Gestão de Atendimentos',font=('Arial',23,'bold'),text_color='white').pack(side='left',padx=18,pady=14)
        ctk.CTkButton(topo,text='Como usar',command=self.mostrar_ajuda,fg_color=COR_DESTAQUE).pack(side='right',padx=12)
        acoes=ctk.CTkFrame(self);acoes.pack(fill='x')
        if usuario:
            ctk.CTkLabel(acoes,text=f"Olá, {usuario['nome']}").pack(side='left',padx=16)
            for titulo,comando in [('Sair',self.sair),('Novo usuário',self.novo_usuario),('Minha conta',self.minha_conta)]:
                ctk.CTkButton(acoes,text=titulo,width=115,command=comando,fg_color=COR_PRIMARIA).pack(side='right',padx=5,pady=6)
        ctk.CTkButton(acoes,text='Backup',width=100,command=self.salvar_backup,fg_color=COR_PRIMARIA).pack(side='right',padx=5,pady=6)
        self.abas=ctk.CTkTabview(self);self.abas.pack(fill='both',expand=True,padx=12,pady=10)
        for n in ('Clientes','Animais','Serviços','Profissionais','Atendimentos','Histórico'): self.abas.add(n)
        self.forms={};self.tables={};self.buscas={};self.save_buttons={};self.action_buttons={};self.modos={}
        self._montar_clientes();self._montar_animais();self._montar_servicos();self._montar_profissionais();self._montar_atendimentos();self._montar_historico()
        self.atualizar_tudo()
        self.after(400,self.oferecer_demo)

    def _aba(self,nome,chave,instrucao,campos,colunas,salvar):
        aba=self.abas.tab(nome)
        ctk.CTkLabel(aba,text=instrucao,wraplength=1100,justify='left',anchor='w').pack(fill='x',padx=10,pady=8)
        corpo=ctk.CTkFrame(aba);corpo.pack(fill='both',expand=True)
        form=ctk.CTkScrollableFrame(corpo,width=250);form.pack(side='left',fill='y',padx=6,pady=6)
        modo=ctk.CTkLabel(form,text='Novo cadastro',text_color=COR_PRIMARIA)
        modo.pack(anchor='w',padx=5);self.modos[chave]=modo
        entradas={}
        for key,titulo,opcoes in campos:
            ctk.CTkLabel(form,text=titulo).pack(anchor='w',padx=5,pady=(7,0))
            e=ctk.CTkOptionMenu(form,values=opcoes,fg_color=COR_PRIMARIA) if opcoes else ctk.CTkEntry(form)
            e.pack(fill='x',padx=5,pady=(0,4));entradas[key]=e
            if not opcoes: e.bind('<Return>',lambda _,a=salvar:a())
        botao=ctk.CTkButton(form,text='Salvar',command=salvar,fg_color=COR_DESTAQUE);botao.pack(fill='x',padx=5,pady=9)
        ctk.CTkButton(form,text='Novo / limpar',command=lambda:self.limpar_form(chave),fg_color='#627471').pack(fill='x',padx=5,pady=4)
        lista=ctk.CTkFrame(corpo);lista.pack(side='left',fill='both',expand=True,padx=6,pady=6)
        busca=ctk.CTkEntry(lista,placeholder_text='Pesquisar');busca.pack(fill='x',padx=8,pady=8)
        grade=ctk.CTkFrame(lista);grade.pack(fill='both',expand=True,padx=8,pady=6)
        tabela=Tabela(grade,colunas);tabela.pack(side='left',fill='both',expand=True)
        vertical=ttk.Scrollbar(grade,orient='vertical',command=tabela.yview);vertical.pack(side='right',fill='y')
        tabela.configure(yscrollcommand=vertical.set)
        barra=ttk.Scrollbar(lista,orient='horizontal',command=tabela.xview);barra.pack(fill='x',padx=8)
        tabela.configure(xscrollcommand=barra.set)
        self.forms[chave]=entradas;self.tables[chave]=tabela;self.buscas[chave]=busca;self.save_buttons[chave]=botao
        busca.bind('<KeyRelease>',lambda _:self.atualizar_lista(chave))
        tabela.bind('<<TreeviewSelect>>',lambda _:self.carregar(chave))
        return form,lista

    def _acao(self,pai,chave,texto,comando):
        b=ctk.CTkButton(pai,text=texto,command=comando,state='disabled',fg_color=COR_PRIMARIA)
        b.pack(fill='x',padx=5,pady=5);self.action_buttons.setdefault(chave,[]).append(b);return b

    def _montar_clientes(self):
        form,lista=self._aba('Clientes','cliente','1. Cadastre o tutor. CPF obrigatório em novos clientes; e-mail único quando informado. Demais dados podem repetir.',
            [('nome','Nome *',None),('telefone','Telefone com DDD *',None),('cpf','CPF * (legados: regularizar)',None),('email','E-mail',None),('endereco','Endereço',None)],
            [('id','ID',45),('nome','Nome',165),('cpf','CPF',135),('tel','Telefone',140),('email','E-mail',180),('end','Endereço',190)],self.salvar_cliente)
        self._acao(form,'cliente','Excluir selecionado',lambda:self.excluir('cliente'))
        self.alerta=ctk.CTkLabel(lista,text='',wraplength=800,justify='left');self.alerta.pack(fill='x',padx=8,pady=6)
        self.tables['cliente'].tag_configure('similar',background='#FFF2CD')
        for e in self.forms['cliente'].values():
            for evento in ('<KeyRelease>','<<Paste>>','<<Cut>>','<FocusOut>'): e.bind(evento,self.agendar_alerta,add='+')
        self._bordas={k:e.cget('border_color') for k,e in self.forms['cliente'].items()}

    def _montar_animais(self):
        form,_=self._aba('Animais','animal','2. Escolha o tutor e cadastre o animal. Animais com histórico não podem ser excluídos.',
            [('id_cliente','Tutor *',['—']),('nome','Nome *',None),('especie','Espécie *',None),('raca','Raça',None),('observacoes','Observações',None)],
            [('id','ID',45),('nome','Animal',180),('especie','Espécie',150),('tutor','Tutor',220)],self.salvar_animal)
        self._acao(form,'animal','Excluir selecionado',lambda:self.excluir('animal'))

    def _montar_servicos(self):
        form,_=self._aba('Serviços','servico','3. Prepare os serviços com preço e duração. Use inativação para preservar o histórico.',
            [('nome','Nome *',None),('descricao','Descrição',None),('preco','Preço (R$) *',None),('duracao_min','Duração em minutos *',None)],
            [('id','ID',45),('nome','Serviço',220),('preco','Preço',120),('dur','Minutos',100),('ativo','Situação',150)],self.salvar_servico)
        self._acao(form,'servico','Ativar / inativar',self.alternar_servico)

    def _montar_atendimentos(self):
        form,lista=self._aba('Atendimentos','atendimento','5. Escolha profissional, animal e serviço. Novos agendamentos exigem futuro; na edição, é possível corrigir o horário realizado. Só conclua após o início.',
            [('id_animal','Animal *',['—']),('id_servico','Serviço ativo *',['—']),('id_profissional','Profissional ativo *',['—']),('data_hora','Data/hora * (dd/mm/aaaa hh:mm)',None)],
            [('id','ID',45),('data','Início',145),('fim','Fim previsto',145),('prof','Profissional',160),('animal','Animal',130),('tutor','Tutor',160),('servico','Serviço',160),('status','Status',100),('valor','Valor',110)],self.salvar_atendimento)
        self._acao(form,'atendimento','Reagendar para agora',self.reagendar_agora)
        self._acao(form,'atendimento','Concluir selecionado',self.concluir_atendimento)
        self._acao(form,'atendimento','Cancelar selecionado',self.cancelar_atendimento)
        self.status_filtro=ctk.CTkOptionMenu(lista,values=['Todos','agendado','concluido','cancelado'],command=lambda _:self.atualizar_lista('atendimento'))
        self.status_filtro.pack(fill='x',padx=8,pady=6)
        self.profissional_filtro=ctk.CTkOptionMenu(lista,values=['Todos os profissionais'],command=lambda _:self.atualizar_lista('atendimento'))
        self.profissional_filtro.pack(fill='x',padx=8,pady=6)

    def _montar_profissionais(self):
        form,_=self._aba('Profissionais','profissional','4. Cadastre quem executa os serviços. Cada profissional tem uma agenda; a função é descritiva. Inativar impede novas reservas e preserva as existentes.',
            [('nome','Nome *',None),('funcao','Função *',None)],
            [('id','ID',45),('nome','Profissional',240),('funcao','Função',240),('ativo','Situação',120)],self.salvar_profissional)
        self._acao(form,'profissional','Ativar / inativar',self.alternar_profissional)
        ctk.CTkButton(form,text='Adicionar equipe fictícia',command=self.adicionar_equipe_demo,fg_color=COR_PRIMARIA).pack(fill='x',padx=5,pady=10)

    def _montar_historico(self):
        aba=self.abas.tab('Histórico')
        ctk.CTkLabel(aba,text='Serviços concluídos. O total representa valores dos serviços, sem controle de pagamento.').pack(pady=8)
        self.h_busca=ctk.CTkEntry(aba,placeholder_text='Pesquisar animal, tutor, serviço ou profissional');self.h_busca.pack(fill='x',padx=10,pady=8)
        self.h_busca.bind('<KeyRelease>',lambda _:self.atualizar_historico())
        grade=ctk.CTkFrame(aba);grade.pack(fill='both',expand=True,padx=10,pady=6)
        self.t_hist=Tabela(grade,[('id','ID',45),('data','Data',150),('animal','Animal',130),('tutor','Tutor na realização',180),('servico','Serviço',170),('prof','Profissional',160),('valor','Valor',110),('origem','Registro',150)])
        self.t_hist.pack(side='left',fill='both',expand=True)
        vertical=ttk.Scrollbar(grade,orient='vertical',command=self.t_hist.yview);vertical.pack(side='right',fill='y');self.t_hist.configure(yscrollcommand=vertical.set)
        horizontal=ttk.Scrollbar(aba,orient='horizontal',command=self.t_hist.xview);horizontal.pack(fill='x',padx=10);self.t_hist.configure(xscrollcommand=horizontal.set)
        self.total=ctk.CTkLabel(aba,text='',font=('Arial',19,'bold'));self.total.pack(pady=8)

    def _dados(self,chave): return {k:e.get().strip() for k,e in self.forms[chave].items()}
    def _id(self,texto):
        try: return int(texto.split(' - ',1)[0])
        except ValueError: raise v.ErroValidacao('Selecione uma opção válida.') from None
    def erro(self,erro): messagebox.showerror('Erro',str(erro),parent=self)
    def confirmar(self,texto): return messagebox.askyesno('Confirmação',texto,parent=self)

    def _confirmar_edicao(self,chave,dados):
        id_=self.sel[chave]
        if id_ is None: return True
        atual=getattr(db,'buscar_'+chave)(id_)
        if atual is None: raise v.ErroValidacao('Registro removido. Atualize a lista antes de editar.')
        mudancas=[]
        for k,novo in dados.items():
            antigo=atual[k]
            if chave=='servico' and k=='preco':
                if atual['preco_centavos']==v.preco_centavos(novo): continue
            if str(antigo or '')!=str(novo or ''): mudancas.append(f'{k}: {antigo or "(vazio)"} → {novo or "(vazio)"}')
        if not mudancas:
            messagebox.showinfo('Sem alterações','Nenhum campo foi alterado.',parent=self);return False
        return self.confirmar(f'Salvar alterações no registro #{id_}?\n\n'+'\n'.join(mudancas))

    def salvar_cliente(self):
        try:
            d=self._dados('cliente');id_=self.sel['cliente'];legado=id_ and db.buscar_cliente(id_)['cpf'] is None
            d['cpf']=None if legado and not d['cpf'] else v.cpf(d['cpf'])
            d['telefone']=v.telefone(d['telefone']);d['email']=v.email_opcional(d['email']) or None
            if not self._confirmar_edicao('cliente',d): return
            if id_: db.atualizar_cliente(id_,**d)
            else: db.inserir_cliente(**d)
        except Exception as e: return self.erro(e)
        self._sucesso('cliente')

    def salvar_animal(self):
        try:
            d=self._dados('animal');d['id_cliente']=self._id(d['id_cliente']);id_=self.sel['animal']
            v.obrigatorios(Nome=d['nome'],Espécie=d['especie'])
            if db.animal_ja_cadastrado(d['id_cliente'],d['nome'],id_) and not self.confirmar('Este tutor já possui um animal com este nome. Cadastrar assim mesmo?'): return
            if not self._confirmar_edicao('animal',d): return
            if id_: db.atualizar_animal(id_,**d)
            else: db.inserir_animal(**d)
        except Exception as e: return self.erro(e)
        self._sucesso('animal')

    def salvar_servico(self):
        try:
            d=self._dados('servico');d['preco']=v.preco(d['preco']);d['duracao_min']=v.inteiro_positivo(d['duracao_min'],'Duração');id_=self.sel['servico']
            if not self._confirmar_edicao('servico',d): return
            if id_: db.atualizar_servico(id_,**d)
            else: db.inserir_servico(**d)
        except Exception as e: return self.erro(e)
        self._sucesso('servico')

    def salvar_atendimento(self):
        try:
            d=self._dados('atendimento');id_=self.sel['atendimento']
            for campo in ('id_animal','id_servico','id_profissional'): d[campo]=self._id(d[campo])
            dt=v.data_hora(d['data_hora']) if id_ else v.data_hora_futura(d['data_hora'])
            if id_ and dt<=datetime.now() and not self.confirmar('Registrar este atendimento no horário informado, que já chegou ou passou? Confirme o horário real antes de concluir.'): return
            if not self._confirmar_edicao('atendimento',{**d,'data_hora':dt.isoformat(timespec='minutes')}): return
            if id_: db.atualizar_atendimento(id_,d['id_animal'],d['id_servico'],dt,d['id_profissional'])
            else: db.inserir_atendimento(d['id_animal'],d['id_servico'],dt,d['id_profissional'])
        except Exception as e: return self.erro(e)
        self._sucesso('atendimento')

    def reagendar_agora(self):
        if self.sel['atendimento'] is None: return
        preencher(self.forms['atendimento']['data_hora'],datetime.now().strftime('%d/%m/%Y %H:%M'))
        self.salvar_atendimento()

    def salvar_profissional(self):
        try:
            d=self._dados('profissional');id_=self.sel['profissional']
            if not self._confirmar_edicao('profissional',d): return
            if id_: db.atualizar_profissional(id_,**d)
            else: db.inserir_profissional(**d)
        except Exception as e: return self.erro(e)
        self._sucesso('profissional')

    def alternar_profissional(self):
        id_=self.sel['profissional']
        if not id_: return
        try:
            atual=db.buscar_profissional(id_)
            if not self.confirmar(('Inativar' if atual['ativo'] else 'Reativar')+' este profissional? Os atendimentos existentes serão preservados.'): return
            db.definir_profissional_ativo(id_,not atual['ativo'])
        except Exception as e: return self.erro(e)
        self.limpar_form('profissional');self.atualizar_tudo()

    def adicionar_equipe_demo(self):
        if not self.confirmar('Adicionar Ana Souza, Bruno Lima e Carla Santos como profissionais fictícios? Não serão criados usuários de login.'): return
        try: popular_demo.popular_profissionais()
        except Exception as e: return self.erro(e)
        self.atualizar_tudo()

    def _sucesso(self,chave):
        self.limpar_form(chave);self.atualizar_tudo();messagebox.showinfo('Sucesso','Registro salvo.',parent=self)

    def limpar_form(self,chave):
        self.sel[chave]=None
        self._originais_form.pop(chave,None)
        self.modos[chave].configure(text='Novo cadastro')
        for e in self.forms[chave].values():
            e.configure(state='normal')
            if isinstance(e,ctk.CTkOptionMenu): e.set(e.cget('values')[0])
            else: e.delete(0,'end')
        self.tables[chave].selection_remove(*self.tables[chave].selection())
        self.save_buttons[chave].configure(state='normal')
        for b in self.action_buttons.get(chave,[]): b.configure(state='disabled')
        if chave=='cliente': self.atualizar_alertas()

    def carregar(self,chave):
        id_=self.tables[chave].selecionado()
        if id_ is None: return
        if self.sel[chave]==id_: return
        linha=getattr(db,'buscar_'+chave)(id_)
        if linha is None: return
        self.sel[chave]=id_
        for k,e in self.forms[chave].items():
            e.configure(state='normal');valor=linha[k]
            if k.startswith('id_'):
                opcoes=e.cget('values');e.set(next((x for x in opcoes if x.startswith(str(valor)+' - ')),'—' if valor is None else str(valor)+' - inativo'))
            else:
                if k=='cpf': valor=v.formatar_cpf(valor)
                elif k=='telefone': valor=v.formatar_telefone(valor)
                elif k=='data_hora': valor=datetime.fromisoformat(valor).strftime('%d/%m/%Y %H:%M')
                elif k=='preco': valor=v.valor_para_campo(linha['preco_centavos'])
                preencher(e,str(valor) if valor is not None else '')
        permitido=chave!='atendimento' or linha['status']=='agendado'
        self._originais_form[chave]=self._dados(chave)
        self.modos[chave].configure(text=f'{"Editando" if permitido else "Consulta"} #{id_}')
        self.save_buttons[chave].configure(state='normal' if permitido else 'disabled')
        for b in self.action_buttons.get(chave,[]): b.configure(state='normal' if permitido else 'disabled')
        if not permitido:
            for e in self.forms[chave].values(): e.configure(state='disabled')
        if chave=='cliente': self.atualizar_alertas()

    def excluir(self,chave):
        id_=self.sel[chave]
        if id_ is None: return
        try:
            qtd=db.contar_animais_do_cliente(id_) if chave=='cliente' else db.contar_atendimentos_do_animal(id_)
            if qtd: raise v.ErroValidacao('Não é possível excluir: existem registros vinculados.')
            if not self.confirmar('Excluir o registro selecionado? Esta ação não pode ser desfeita.'): return
            getattr(db,'excluir_'+chave)(id_)
        except Exception as e: return self.erro(e)
        self.limpar_form(chave);self.atualizar_tudo()

    def alternar_servico(self):
        id_=self.sel['servico']
        if not id_: return
        try:
            atual=db.buscar_servico(id_)
            if not self.confirmar(('Inativar' if atual['ativo'] else 'Reativar')+' o serviço selecionado?'): return
            db.definir_servico_ativo(id_,not atual['ativo'])
        except Exception as e: return self.erro(e)
        self.limpar_form('servico');self.atualizar_tudo()

    def concluir_atendimento(self):
        id_=self.sel['atendimento']
        if not id_: return
        try:
            if not self.confirmar('Concluir o atendimento selecionado?'): return
            db.concluir_atendimento(id_)
        except Exception as e: return self.erro(e)
        self.limpar_form('atendimento');self.atualizar_tudo()

    def cancelar_atendimento(self):
        id_=self.sel['atendimento']
        if not id_: return
        try:
            if not self.confirmar('Cancelar o atendimento? Ele permanecerá registrado.'): return
            motivo=simpledialog.askstring('Cancelar atendimento','Motivo do cancelamento:',parent=self)
            if motivo is None: return
            db.cancelar_atendimento(id_,motivo)
        except Exception as e: return self.erro(e)
        self.limpar_form('atendimento');self.atualizar_tudo()

    def atualizar_lista(self,chave):
        busca=self.buscas[chave].get()
        filtro=(busca,)
        if chave=='cliente':
            linhas=[(c['id_cliente'],c['nome'],v.formatar_cpf(c['cpf']) or 'Pendente',v.formatar_telefone(c['telefone']),c['email'] or '',c['endereco'] or '') for c in db.listar_clientes(busca)]
        elif chave=='animal': linhas=[(a['id_animal'],a['nome'],a['especie'],a['tutor']) for a in db.listar_animais(busca)]
        elif chave=='servico': linhas=[(s['id_servico'],s['nome'],v.formatar_centavos(s['preco_centavos']),s['duracao_min'],'Ativo' if s['ativo'] else 'Inativo') for s in db.listar_servicos() if busca.lower() in s['nome'].lower()]
        elif chave=='profissional': linhas=[(p['id_profissional'],p['nome'],p['funcao'],'Ativo' if p['ativo'] else 'Inativo') for p in db.listar_profissionais() if busca.lower() in (p['nome']+' '+p['funcao']).lower()]
        else:
            status=self.status_filtro.get();status=None if status=='Todos' else status
            profissional=self.profissional_filtro.get()
            id_profissional=None if profissional=='Todos os profissionais' else self._id(profissional)
            filtro=(busca,self.status_filtro.get(),profissional)
            linhas=[(a['id_atendimento'],datetime.fromisoformat(a['data_hora']).strftime('%d/%m/%Y %H:%M'),datetime.fromisoformat(a['fim_estimado']).strftime('%d/%m/%Y %H:%M'),a['profissional'],a['animal'],a['tutor'],a['servico'],a['status'],v.formatar_centavos(a['valor_centavos'])) for a in db.listar_atendimentos(busca,status,id_profissional=id_profissional)]
        if self.sel[chave] is not None and self.sel[chave] not in {linha[0] for linha in linhas}:
            alterado=self._originais_form.get(chave)!=self._dados(chave)
            if alterado and not self.confirmar('O filtro ocultará o registro em edição. Descartar as alterações não salvas e encerrar a edição?'):
                anterior=self._filtros_aplicados.get(chave,('', 'Todos','Todos os profissionais'))
                preencher(self.buscas[chave],anterior[0])
                if chave=='atendimento':
                    self.status_filtro.set(anterior[1]);self.profissional_filtro.set(anterior[2])
                return
            self.limpar_form(chave)
        self.tables[chave].preencher(linhas)
        self._filtros_aplicados[chave]=filtro
        if chave=='cliente': self.atualizar_alertas()

    def atualizar_historico(self):
        linhas=db.listar_atendimentos(self.h_busca.get(),'concluido',True)
        self.t_hist.preencher([(a['id_atendimento'],datetime.fromisoformat(a['data_hora']).strftime('%d/%m/%Y %H:%M'),a['animal'],a['tutor'],a['servico'],a['profissional'],v.formatar_centavos(a['valor_centavos']),'Legado: dados migrados' if a['origem_historico']=='migracao' else 'Identidade preservada') for a in linhas])
        self.total.configure(text='Total de serviços concluídos: '+v.formatar_centavos(sum(a['valor_centavos'] for a in linhas)))

    def atualizar_tudo(self):
        opcoes=[('animal','id_cliente',db.listar_clientes(),'id_cliente','nome'),('atendimento','id_animal',db.listar_animais(),'id_animal','nome'),('atendimento','id_servico',db.listar_servicos(True),'id_servico','nome'),('atendimento','id_profissional',db.listar_profissionais(True),'id_profissional','nome')]
        for aba,campo,linhas,id_,nome in opcoes:
            e=self.forms[aba][campo];valores=[f'{r[id_]} - {r[nome]}' for r in linhas] or ['—'];atual=e.get()
            e.configure(values=valores)
            if atual not in valores:
                id_atual=atual.split(' - ',1)[0]
                mesmo=next((valor for valor in valores if valor.split(' - ',1)[0]==id_atual),None)
                if mesmo: e.set(mesmo)
                elif self.sel[aba] is None: e.set(valores[0])
        profissionais=['Todos os profissionais']+[f"{p['id_profissional']} - {p['nome']}" for p in db.listar_profissionais()]
        atual=self.profissional_filtro.get();self.profissional_filtro.configure(values=profissionais)
        if atual not in profissionais:
            id_atual=atual.split(' - ',1)[0]
            self.profissional_filtro.set(next((p for p in profissionais if p.split(' - ',1)[0]==id_atual),profissionais[0]))
        for chave in self.tables: self.atualizar_lista(chave)
        self.atualizar_historico()

    def agendar_alerta(self,*_):
        if self._alerta_job: self.after_cancel(self._alerta_job)
        self._alerta_job=self.after(250,self.atualizar_alertas)

    def atualizar_alertas(self):
        if self._alerta_job: self.after_cancel(self._alerta_job);self._alerta_job=None
        try: achados=sim.comparar(self._dados('cliente'),db.listar_clientes(),self.sel['cliente'])
        except Exception: self.alerta.configure(text='Não foi possível verificar semelhanças agora.');return
        campos={k for a in achados for k in a['campos']}
        for k,e in self.forms['cliente'].items(): e.configure(border_color=(COR_PERIGO if k in ('cpf','email') else COR_AVISO) if k in campos else self._bordas[k])
        ids={a['id_cliente'] for a in achados}
        for i in self.tables['cliente'].get_children(): self.tables['cliente'].item(i,tags=('similar',) if int(i) in ids else ())
        detalhes=[f"#{a['id_cliente']} {a['nome']}: "+', '.join(sim.ROTULOS[k] for k in a['campos']) for a in achados[:3]]
        aviso='\n'.join(detalhes)+('\nNome, telefone e endereço podem repetir; CPF e e-mail repetidos impedem salvar.' if achados else '')
        self.alerta.configure(text=aviso,text_color=COR_PERIGO if campos & {'cpf','email'} else COR_AVISO)

    def salvar_backup(self):
        destino=filedialog.asksaveasfilename(parent=self,title='Salvar cópia do banco',initialfile=f'petshop_backup_{datetime.now():%Y%m%d_%H%M%S}.db',defaultextension='.db',filetypes=[('SQLite','*.db')])
        if not destino: return
        try: db.fazer_backup(destino)
        except Exception as e: return self.erro(e)
        messagebox.showinfo('Backup concluído','Cópia salva com sucesso.',parent=self)

    def minha_conta(self):
        janela=ctk.CTkToplevel(self);janela.title('Minha conta');janela.geometry('420x340');janela.transient(self)
        ctk.CTkLabel(janela,text='E-mail para recuperar sua senha',font=('Arial',18,'bold')).pack(pady=15)
        email=ctk.CTkEntry(janela,width=350);email.pack(pady=8);email.insert(0,db.email_do_usuario(self.usuario['id_usuario']) or '')
        ctk.CTkLabel(janela,text='Confirme sua senha atual').pack()
        senha=ctk.CTkEntry(janela,width=350,show='•');senha.pack(pady=8)
        mensagem=ctk.CTkLabel(janela,text='',text_color=COR_PERIGO,wraplength=350);mensagem.pack(pady=8)
        def salvar():
            try: db.atualizar_email_usuario(self.usuario['id_usuario'],senha.get(),email.get())
            except v.ErroValidacao as erro: return mensagem.configure(text=str(erro))
            messagebox.showinfo('Minha conta','E-mail de recuperação atualizado.');janela.destroy()
        ctk.CTkButton(janela,text='Salvar e-mail',command=salvar).pack(pady=8)
        self._dialogo_conta=janela,email,senha,salvar,mensagem

    def novo_usuario(self):
        janela=ctk.CTkToplevel(self);janela.title('Novo usuário');janela.geometry('400x600');janela.transient(self)
        corpo=ctk.CTkScrollableFrame(janela);corpo.pack(fill='both',expand=True,padx=16,pady=12)
        entradas=[]
        for rotulo,mascara in [('Nome *',False),('Usuário *',False),('Senha *',True),('Confirmar senha *',True),('E-mail de recuperação *',False)]:
            ctk.CTkLabel(corpo,text=rotulo).pack(anchor='w',pady=(7,0))
            e=ctk.CTkEntry(corpo,show='•' if mascara else '');e.pack(fill='x',pady=4);entradas.append(e)
        msg=ctk.CTkLabel(corpo,text='',text_color=COR_PERIGO,wraplength=340);msg.pack(fill='x',pady=6)
        def salvar():
            try:
                valores=[e.get() for e in entradas];v.obrigatorios(Nome=valores[0],Usuário=valores[1],**{'E-mail':valores[4]})
                db.criar_usuario(*valores)
            except v.ErroValidacao as erro: return msg.configure(text=str(erro))
            messagebox.showinfo('Sucesso','Usuário cadastrado.');janela.destroy()
        ctk.CTkButton(corpo,text='Cadastrar usuário',command=salvar).pack(fill='x',pady=10)
        self._dialogo_usuario=janela,entradas,salvar,msg

    def mostrar_ajuda(self):
        messagebox.showinfo('Como usar','1. Cadastre o cliente e seu animal.\n2. Prepare serviços com preço de até duas casas decimais.\n3. Cadastre profissionais ou use Adicionar equipe fictícia.\n4. Agende animal, serviço, profissional e horário futuro.\n5. Para corrigir a realização, selecione e use Reagendar para agora ou edite data/hora.\n6. Conclua após o início ou cancele com motivo.\n\nO profissional e o animal ficam reservados até o fim previsto, mesmo após conclusão antecipada. Cancelamento libera o intervalo.\nO histórico conserva o tutor da realização. Registros antigos são identificados como migrados.\nO rótulo Editando #ID identifica o registro; filtros encerram a edição quando o ocultam e confirmam o descarte de mudanças.\nBackup salva uma cópia consistente do banco.',parent=self)

    def oferecer_demo(self):
        if db.listar_clientes() or db.listar_animais() or db.listar_servicos(): return
        if messagebox.askyesno('Dados fictícios','Deseja carregar dados fictícios para conhecer o sistema?',parent=self):
            popular_demo.popular();self.atualizar_tudo()

    def sair(self):
        if self.confirmar('Encerrar a sessão e voltar para o login?'): self.sair_solicitado=True;self.destroy()

    def destroy(self):
        login.cancelar_agendamentos(self);super().destroy()


if __name__=='__main__':
    try: db.criar_tabelas()
    except (db.DuplicadosExistentes,v.ErroValidacao) as erro:
        janela=ctk.CTk();janela.withdraw();messagebox.showerror('Revisão do banco necessária',str(erro));janela.destroy();raise SystemExit(1)
    while True:
        usuario=login.executar()
        if usuario is None: break
        app=App(usuario);app.mainloop()
        if not app.sair_solicitado: break
