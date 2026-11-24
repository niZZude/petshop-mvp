"""Login local e recuperação de acesso por e-mail."""
import queue
import threading
import time
import customtkinter as ctk
import database as db
import validacoes as v
import recuperacao

COR_PRIMARIA='#1F7A6E'
COR_DESTAQUE='#F08A4B'
COR_ERRO='#B3402F'
MAX_TENTATIVAS=5
BLOQUEIO_SEGUNDOS=30


def cancelar_agendamentos(janela):
    try:
        for id_ in janela.tk.splitlist(janela.tk.call('after','info')):
            janela.tk.call('after','cancel',id_)
    except Exception:
        pass


def executar_em_segundo_plano(janela,tarefa,concluir):
    resultados=queue.Queue()
    def trabalhar():
        try: resultados.put((tarefa(),None))
        except v.ErroValidacao as erro: resultados.put((None,str(erro)))
        except Exception: resultados.put((None,'Não foi possível concluir agora. Tente novamente.'))
    def verificar():
        try: resultado,erro=resultados.get_nowait()
        except queue.Empty: janela.after(100,verificar)
        else: concluir(resultado,erro)
    threading.Thread(target=trabalhar,daemon=True).start()
    janela.after(100,verificar)


class TelaLogin(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode('light')
        self.title('Pet Shop — Acesso')
        self.usuario=None;self.falhas=0;self.bloqueado_ate=0.;self.relogio=time.monotonic
        self.primeiro_acesso=db.contar_usuarios()==0
        self.geometry(f'440x{min(740 if self.primeiro_acesso else 530,self.winfo_screenheight()-80)}')
        ctk.CTkLabel(self,text='Pet Shop',font=('Arial',28,'bold'),text_color=COR_PRIMARIA).pack(pady=20)
        corpo=ctk.CTkScrollableFrame(self,fg_color='transparent');corpo.pack(fill='both',expand=True,padx=28,pady=8)
        ctk.CTkLabel(corpo,text='Primeiro acesso' if self.primeiro_acesso else 'Entrar no sistema',font=('Arial',21,'bold')).pack(anchor='w')
        if self.primeiro_acesso: self.e_nome=self._campo(corpo,'Seu nome *','Seu nome')
        self.e_login=self._campo(corpo,'Usuário *','3 a 20 caracteres')
        self.e_senha=self._campo(corpo,'Senha *','Letras e números, mínimo 6',True)
        if self.primeiro_acesso:
            self.e_confirma=self._campo(corpo,'Confirmar senha *','Repita a senha',True)
            self.e_email=self._campo(corpo,'E-mail de recuperação *','seu@email.com')
            self.e_email.insert(0,'nixxude@gmail.com')
        self.mostrar=ctk.CTkCheckBox(corpo,text='Mostrar senha',command=self._alternar_senha)
        self.mostrar.pack(anchor='w',pady=8)
        self.mensagem=ctk.CTkLabel(corpo,text='',text_color=COR_ERRO,wraplength=340,justify='left');self.mensagem.pack(fill='x',pady=6)
        acao=self.criar_primeiro_acesso if self.primeiro_acesso else self.entrar
        self.botao=ctk.CTkButton(corpo,text='Criar acesso e entrar' if self.primeiro_acesso else 'Entrar',command=acao,fg_color=COR_DESTAQUE)
        self.botao.pack(fill='x',pady=8)
        if not self.primeiro_acesso:
            ctk.CTkButton(corpo,text='Esqueci minha senha',command=self.abrir_recuperacao,fg_color=COR_PRIMARIA).pack(fill='x',pady=6)
        for e in self._entradas(): e.bind('<Return>',lambda _,a=acao:a())

    def _campo(self,pai,rotulo,dica,senha=False):
        ctk.CTkLabel(pai,text=rotulo).pack(anchor='w',pady=(8,0))
        e=ctk.CTkEntry(pai,placeholder_text=dica,show='•' if senha else '',height=34)
        e.pack(fill='x',pady=(0,4));return e

    def _entradas(self):
        return [getattr(self,n) for n in ('e_nome','e_login','e_senha','e_confirma','e_email') if hasattr(self,n)]

    def _alternar_senha(self):
        for n in ('e_senha','e_confirma'):
            if hasattr(self,n): getattr(self,n).configure(show='' if self.mostrar.get() else '•')

    def entrar(self):
        restante=self.bloqueado_ate-self.relogio()
        if restante>0: return self.mensagem.configure(text=f'Muitas tentativas incorretas. Aguarde {int(restante)+1} s.')
        try: v.obrigatorios(Usuário=self.e_login.get(),Senha=self.e_senha.get())
        except v.ErroValidacao as e: return self.mensagem.configure(text=str(e))
        u=db.autenticar(self.e_login.get(),self.e_senha.get())
        if u is None:
            self.falhas+=1;aviso='Usuário ou senha incorretos.'
            if self.falhas>=MAX_TENTATIVAS:
                self.falhas=0;self.bloqueado_ate=self.relogio()+BLOQUEIO_SEGUNDOS
                aviso=f'Muitas tentativas incorretas. Aguarde {BLOQUEIO_SEGUNDOS} s.'
            self.e_senha.delete(0,'end');return self.mensagem.configure(text=aviso)
        self.usuario=u;self.destroy()

    def criar_primeiro_acesso(self):
        try:
            v.obrigatorios(Nome=self.e_nome.get(),Usuário=self.e_login.get(),Senha=self.e_senha.get(),**{'E-mail':self.e_email.get()})
            db.criar_usuario(self.e_nome.get(),self.e_login.get(),self.e_senha.get(),self.e_confirma.get(),self.e_email.get())
        except v.ErroValidacao as e: return self.mensagem.configure(text=str(e))
        self.usuario=db.autenticar(self.e_login.get(),self.e_senha.get());self.destroy()

    def abrir_recuperacao(self):
        existente=getattr(self,'_recuperacao',None)
        if existente and existente.winfo_exists(): existente.focus();return
        janela=ctk.CTkToplevel(self);self._recuperacao=janela
        janela.title('Recuperar senha');janela.geometry('460x680');janela.transient(self);janela.grab_set()
        corpo=ctk.CTkScrollableFrame(janela,fg_color='transparent');corpo.pack(fill='both',expand=True,padx=20,pady=15)
        ctk.CTkLabel(corpo,text='Recuperar acesso',font=('Arial',21,'bold')).pack(anchor='w')
        ctk.CTkLabel(corpo,text='Use o usuário e o e-mail cadastrado na sua conta. Depois, copie o código recebido e escolha uma nova senha.',wraplength=365,justify='left').pack(pady=8)
        usuario=self._campo(corpo,'Usuário','Seu usuário');usuario.insert(0,self.e_login.get())
        email=self._campo(corpo,'E-mail cadastrado','seu@email.com')
        enviar=ctk.CTkButton(corpo,text='Enviar código',fg_color=COR_PRIMARIA);enviar.pack(fill='x',pady=10)
        codigo=self._campo(corpo,'Código de 8 dígitos (válido por 10 minutos)','Código recebido')
        senha=self._campo(corpo,'Nova senha','Mínimo 6, letras e números',True)
        confirma=self._campo(corpo,'Confirmar nova senha','Repita a senha',True)
        mensagem=ctk.CTkLabel(corpo,text='',wraplength=365,justify='left');mensagem.pack(fill='x',pady=8)
        salvar=ctk.CTkButton(corpo,text='Redefinir senha',fg_color=COR_DESTAQUE);salvar.pack(fill='x',pady=4)
        ocupada=[False]
        def concluir(resultado,erro):
            ocupada[0]=False;enviar.configure(state='normal');salvar.configure(state='normal')
            if erro: mensagem.configure(text=erro,text_color=COR_ERRO)
            elif resultado is None:
                mensagem.configure(text='Senha redefinida. Feche esta janela e entre com a nova senha.',text_color=COR_PRIMARIA)
                for e in (codigo,senha,confirma): e.delete(0,'end')
            else: mensagem.configure(text=resultado,text_color=COR_PRIMARIA)
        def iniciar(tarefa):
            if ocupada[0]: return
            ocupada[0]=True;enviar.configure(state='disabled');salvar.configure(state='disabled')
            mensagem.configure(text='Aguarde…',text_color='#627471')
            executar_em_segundo_plano(janela,tarefa,concluir)
        def pedir():
            valores=usuario.get(),email.get();iniciar(lambda:recuperacao.solicitar(*valores))
        def redefinir():
            valores=usuario.get(),email.get(),codigo.get(),senha.get(),confirma.get();iniciar(lambda:recuperacao.redefinir(*valores))
        enviar.configure(command=pedir);salvar.configure(command=redefinir)
        self._campos_recuperacao=usuario,email,codigo,senha,confirma,pedir,redefinir,mensagem

    def destroy(self):
        cancelar_agendamentos(self)
        super().destroy()


def executar():
    tela=TelaLogin();tela.mainloop();return tela.usuario
