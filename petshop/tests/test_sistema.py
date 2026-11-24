"""Regressão da reconstrução. Bancos temporários, sem e-mail real."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta
from io import BytesIO
from pathlib import Path
import json
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError,URLError
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import database as db
import validacoes as v
import recuperacao as r
import similaridade_clientes as sim
import popular_demo


class Sistema(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.original=db.DB_PATH;db.DB_PATH=str(Path(self.tmp.name)/'teste.db')
        db.criar_tabelas()
        db.inserir_cliente('Ana','86999990000','ana@example.com','Rua A','52998224725')
        db.inserir_animal(1,'Mel','Gato','','');db.inserir_servico('Banho','',50,60)
        db.inserir_profissional('Ana Souza','Banho e tosa')
        self.futuro=(datetime.now()+timedelta(days=2)).replace(second=0,microsecond=0)
    def tearDown(self):
        db.DB_PATH=self.original;self.tmp.cleanup()
    def agendar(self): return db.inserir_atendimento(1,1,self.futuro,1)

    def test_normalizacao(self):
        db.atualizar_cliente(1,' Ana ','(86) 99999-0000',' ANA@EXAMPLE.COM ','Rua A','529.982.247-25')
        c=db.buscar_cliente(1);self.assertEqual((c['nome'],c['cpf'],c['email'],c['telefone']),('Ana','52998224725','ana@example.com','86999990000'))
    def test_cpf_repetido_email_diferente(self):
        with self.assertRaisesRegex(v.ErroValidacao,'CPF já'): db.inserir_cliente('Outra','86999990000','outra@example.com','','52998224725')
    def test_email_repetido_cpf_diferente(self):
        with self.assertRaisesRegex(v.ErroValidacao,'E-mail já'): db.inserir_cliente('Outra','86999990000',' ANA@EXAMPLE.COM ','','11144477735')
    def test_demais_dados_iguais(self):
        db.inserir_cliente('Ana','86999990000','outra@example.com','Rua A','11144477735');self.assertEqual(len(db.listar_clientes()),2)
    def test_email_opcional_varios_nulos(self):
        db.inserir_cliente('Ana','86999990000','','Rua A','11144477735');db.inserir_cliente('Ana','86999990000',None,'Rua A','12345678909')
        self.assertIsNone(db.buscar_cliente(2)['email']);self.assertIsNone(db.buscar_cliente(3)['email'])
    def test_cpf_invalido(self):
        for cpf in ['','00000000000','11111111111','52998224724','abc52998224725','5299822472']:
            with self.subTest(cpf=cpf),self.assertRaises(v.ErroValidacao): db.inserir_cliente('Outra','86999990000','','',cpf)
    def test_editar_proprio_registro(self):
        db.atualizar_cliente(1,'Ana editada','86999990000','ana@example.com','Rua A','52998224725');self.assertEqual(db.buscar_cliente(1)['nome'],'Ana editada')
    def test_rollback_edicao_conflitante(self):
        db.inserir_cliente('Bia','86999990000','bia@example.com','','11144477735')
        with self.assertRaises(v.ErroValidacao): db.atualizar_cliente(2,'Outro nome','86999990000','ana@example.com','','11144477735')
        self.assertEqual(db.buscar_cliente(2)['nome'],'Bia')
    def test_nao_remove_cpf(self):
        with self.assertRaises(v.ErroValidacao): db.atualizar_cliente(1,'Ana','86999990000','','','')
    def test_busca_cpf_email_telefone(self):
        for busca in ['529.982.247-25','ana@example.com','(86) 99999','Ana']:
            with self.subTest(busca=busca): self.assertEqual(len(db.listar_clientes(busca)),1)
    def test_validacoes_api(self):
        for nome,tel,email in [('','86999990000',''),('Ana','123',''),('Ana','86999990000','xx')]:
            with self.subTest(nome=nome,tel=tel,email=email),self.assertRaises(v.ErroValidacao): db.inserir_cliente(nome,tel,email,'','11144477735')
    def test_cliente_vinculado_nao_exclui(self):
        with self.assertRaises(v.ErroValidacao): db.excluir_cliente(1)
    def test_excluir_livres(self):
        db.excluir_animal(1);db.excluir_cliente(1);self.assertEqual(db.listar_clientes(),[])
    def test_fk_invalida(self):
        with self.assertRaises(sqlite3.IntegrityError): db.inserir_animal(999,'Rex','Cachorro','','')
    def test_animal_com_historico_nao_exclui(self):
        self.agendar()
        with self.assertRaises(v.ErroValidacao): db.excluir_animal(1)
    def test_servico_nome_unico(self):
        with self.assertRaises(v.ErroValidacao): db.inserir_servico(' BANHO ','',20,30)
    def test_precos_e_duracoes(self):
        for preco in ['nan','inf','-inf',0,-5,'abc']:
            with self.subTest(preco=preco),self.assertRaises(v.ErroValidacao): db.inserir_servico('Outro','',preco,30)
        for duracao in [0,-2,1.5,True,'abc']:
            with self.subTest(duracao=duracao),self.assertRaises(v.ErroValidacao): db.inserir_servico('Outro','',20,duracao)
    def test_agendamento_copia_preco_duracao(self):
        self.agendar();a=db.buscar_atendimento(1);self.assertEqual((a['valor'],a['duracao_min'],a['status']),(50,60,'agendado'))
    def test_sobreposicao_e_limite_exato(self):
        self.agendar()
        with self.assertRaises(v.ErroValidacao): db.inserir_atendimento(1,1,self.futuro+timedelta(minutes=30),1)
        db.inserir_atendimento(1,1,self.futuro+timedelta(minutes=60),1);self.assertEqual(len(db.listar_atendimentos()),2)
    def test_reagendar_preserva_snapshot(self):
        self.agendar();db.atualizar_servico(1,'Banho','',80,10)
        self.assertTrue(db.existe_sobreposicao(1,self.futuro+timedelta(minutes=30),10))
        db.atualizar_atendimento(1,1,1,self.futuro+timedelta(days=1),1);a=db.buscar_atendimento(1)
        self.assertEqual((a['valor'],a['duracao_min']),(50,60))
    def test_troca_servico_copia_novos_valores(self):
        self.agendar();db.inserir_servico('Tosa','',80,90);db.atualizar_atendimento(1,1,2,self.futuro,1)
        a=db.buscar_atendimento(1);self.assertEqual((a['valor'],a['duracao_min']),(80,90))
    def test_data_passada_e_servico_inativo(self):
        with self.assertRaises(v.ErroValidacao): db.inserir_atendimento(1,1,datetime.now()-timedelta(days=1),1)
        db.definir_servico_ativo(1,False)
        with self.assertRaises(v.ErroValidacao): self.agendar()
        self.assertEqual(db.listar_servicos(True),[])
    def test_cancelar_exige_motivo(self):
        self.agendar()
        with self.assertRaises(v.ErroValidacao): db.cancelar_atendimento(1,'  ')
        db.cancelar_atendimento(1,'Tutor viajou');self.assertEqual(db.buscar_atendimento(1)['motivo_cancelamento'],'Tutor viajou')
        self.assertFalse(db.existe_sobreposicao(1,self.futuro,60))
    def test_status_final_bloqueia_mutacoes(self):
        self.agendar();db.atualizar_atendimento(1,1,1,datetime.now()-timedelta(minutes=1),1);db.concluir_atendimento(1)
        for acao in [lambda:db.cancelar_atendimento(1,'x'),lambda:db.concluir_atendimento(1),lambda:db.atualizar_atendimento(1,1,1,self.futuro,1)]:
            with self.assertRaises(v.ErroValidacao): acao()
        self.assertEqual(len(db.listar_atendimentos('Mel','concluido')),1)
    def test_sql_externo_restricoes(self):
        self.agendar()
        for sql in ['UPDATE servico SET duracao_min=0','UPDATE servico SET ativo=2',"UPDATE atendimento SET status='outro'",'UPDATE atendimento SET duracao_min=-1',"UPDATE atendimento SET status='cancelado',motivo_cancelamento=''", "INSERT INTO cliente(nome,telefone,cpf) VALUES('x','123','abc')"]:
            with self.subTest(sql=sql),closing(sqlite3.connect(db.DB_PATH)) as con,self.assertRaises(sqlite3.IntegrityError): con.execute(sql)
    def test_rollback_multiplas_escritas(self):
        with self.assertRaises(RuntimeError):
            with db.conectar(True) as con:
                con.execute("UPDATE cliente SET nome='Mudou'");con.execute("UPDATE servico SET preco=99,preco_centavos=9900");raise RuntimeError('falha')
        self.assertEqual(db.buscar_cliente(1)['nome'],'Ana');self.assertEqual(db.buscar_servico(1)['preco'],50)
    def test_isolamento_e_wal(self):
        with db.conectar(True) as con:
            con.execute("UPDATE cliente SET nome='Mudou'");self.assertEqual(db.buscar_cliente(1)['nome'],'Ana')
            self.assertEqual(con.execute('PRAGMA journal_mode').fetchone()[0],'wal');self.assertEqual(con.execute('PRAGMA synchronous').fetchone()[0],2)
        self.assertEqual(db.buscar_cliente(1)['nome'],'Mudou')
    def test_concorrencia_email(self):
        def salvar(cpf):
            try: db.inserir_cliente('Outra','86999990000','nova@example.com','',cpf);return True
            except v.ErroValidacao: return False
        with ThreadPoolExecutor(max_workers=2) as pool: self.assertCountEqual(list(pool.map(salvar,['11144477735','12345678909'])),[True,False])
    def test_concorrencia_agenda(self):
        def salvar(_):
            try: self.agendar();return True
            except v.ErroValidacao: return False
        with ThreadPoolExecutor(max_workers=2) as pool: self.assertCountEqual(list(pool.map(salvar,range(2))),[True,False])
    def test_backup(self):
        destino=str(Path(self.tmp.name)/'copia.db');db.fazer_backup(destino)
        with closing(sqlite3.connect(destino)) as con:
            self.assertEqual(con.execute('SELECT cpf FROM cliente').fetchone()[0],'52998224725');self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        with self.assertRaises(FileExistsError): db.fazer_backup(destino)
        with self.assertRaises(v.ErroValidacao): db.fazer_backup(db.DB_PATH)
    def test_alertas_nao_gravam(self):
        achados=sim.comparar({'nome':'Ana','cpf':'529.982.247-25','email':'ANA@example.com'},db.listar_clientes())
        self.assertCountEqual(achados[0]['campos'],['cpf','email']);self.assertEqual(sim.comparar({'cpf':'52998224725'},db.listar_clientes(),1),[])
        self.assertEqual(len(db.listar_clientes()),1)
    def test_demo_repetivel(self):
        db.DB_PATH=str(Path(self.tmp.name)/'demo.db');popular_demo.popular();popular_demo.popular()
        self.assertEqual(len(db.listar_clientes()),3);self.assertEqual(len(db.listar_atendimentos()),7)
    def test_usuario_hash_login_normalizado(self):
        db.criar_usuario('Eduardo',' EDUARDO ','Senha123',email='user@example.com')
        self.assertIsNotNone(db.autenticar('eduardo','Senha123'));self.assertIsNone(db.autenticar('eduardo','errada'))
        with db.conectar() as con: self.assertNotIn('Senha123',str(tuple(con.execute('SELECT senha_hash,salt FROM usuario').fetchone())))
    def test_usuario_email_unico(self):
        db.criar_usuario('A','usera','Senha123',email='user@example.com')
        with self.assertRaises(v.ErroValidacao): db.criar_usuario('B','userb','Senha123',email='USER@example.com')
    def test_migracao_legada(self):
        db.DB_PATH=str(Path(self.tmp.name)/'legado.db')
        with closing(sqlite3.connect(db.DB_PATH)) as con:
            con.executescript("CREATE TABLE cliente(id_cliente INTEGER PRIMARY KEY,nome TEXT,telefone TEXT,email TEXT,endereco TEXT); INSERT INTO cliente VALUES(7,'Legado','86999990000',NULL,'');")
        db.criar_tabelas();db.criar_tabelas();self.assertIsNone(db.buscar_cliente(7)['cpf'])
        db.atualizar_cliente(7,'Legado editado','86999990000','','',None)
        db.atualizar_cliente(7,'Legado editado','86999990000','','','11144477735');self.assertEqual(db.buscar_cliente(7)['cpf'],'11144477735')
    def test_migracao_conflito_nao_exclui(self):
        db.DB_PATH=str(Path(self.tmp.name)/'duplicado.db')
        with closing(sqlite3.connect(db.DB_PATH)) as con:
            con.executescript("CREATE TABLE cliente(id_cliente INTEGER PRIMARY KEY,nome TEXT,telefone TEXT,email TEXT,endereco TEXT); INSERT INTO cliente VALUES(1,'A','86999990000','a@example.com',''); INSERT INTO cliente VALUES(2,'B','86999990000',' A@EXAMPLE.COM ','');")
        with self.assertRaises(db.DuplicadosExistentes): db.criar_tabelas()
        with closing(sqlite3.connect(db.DB_PATH)) as con:
            self.assertEqual(con.execute('SELECT count(*) FROM cliente').fetchone()[0],2);self.assertNotIn('cpf',[x[1] for x in con.execute('PRAGMA table_info(cliente)')])


class Recuperacao(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.original=db.DB_PATH;db.DB_PATH=str(Path(self.tmp.name)/'teste.db');db.criar_tabelas()
        db.criar_usuario('Eduardo','eduardo','Senha123',email='nixxude@gmail.com')
        self.amb=patch.dict(os.environ,{'RESEND_API_KEY':'re_teste','RESEND_FROM':'Pet Shop <onboarding@resend.dev>'});self.amb.start()
        self.entregas=[];self.envio=patch.object(r,'enviar_codigo',side_effect=lambda *a:self.entregas.append(a));self.envio.start()
    def tearDown(self):
        self.envio.stop();self.amb.stop();db.DB_PATH=self.original;self.tmp.cleanup()
    def pedir(self): r.solicitar('eduardo','nixxude@gmail.com');return self.entregas[-1][1]
    def trocar(self,codigo): r.redefinir('eduardo','nixxude@gmail.com',codigo,'NovaSenha123','NovaSenha123')
    def test_fluxo_uso_unico(self):
        codigo=self.pedir();self.trocar(codigo);self.assertIsNone(db.autenticar('eduardo','Senha123'));self.assertIsNotNone(db.autenticar('eduardo','NovaSenha123'))
        with self.assertRaises(v.ErroValidacao): self.trocar(codigo)
    def test_codigo_hash(self):
        codigo=self.pedir()
        with db.conectar() as con: self.assertNotIn(codigo,str(dict(con.execute('SELECT * FROM recuperacao_senha').fetchone())))
    def test_resposta_generica(self):
        self.assertEqual(r.solicitar('ninguem','nixxude@gmail.com'),r.MENSAGEM_ENVIO);self.assertEqual(r.solicitar('eduardo','outra@example.com'),r.MENSAGEM_ENVIO);self.assertEqual(self.entregas,[])
    def test_intervalo_persistente(self):
        codigo=self.pedir();db.criar_tabelas();r.solicitar('eduardo','nixxude@gmail.com');self.assertEqual(len(self.entregas),1);self.trocar(codigo)
    def test_reenvio_invalida_anterior(self):
        anterior=self.pedir()
        with db.conectar(True) as con: con.execute('UPDATE recuperacao_senha SET solicitado_em=solicitado_em-61')
        novo=self.pedir()
        with self.assertRaises(v.ErroValidacao): self.trocar(anterior)
        self.trocar(novo)
    def test_expiracao(self):
        codigo=self.pedir()
        with db.conectar(True) as con: con.execute('UPDATE recuperacao_senha SET expira_em=0')
        with self.assertRaises(v.ErroValidacao): self.trocar(codigo)
    def test_limite_falhas(self):
        codigo=self.pedir()
        for _ in range(5):
            with self.assertRaises(v.ErroValidacao): self.trocar('invalido')
        with self.assertRaises(v.ErroValidacao): self.trocar(codigo)
    def test_confirmacao_senha(self):
        codigo=self.pedir()
        with self.assertRaises(v.ErroValidacao): r.redefinir('eduardo','nixxude@gmail.com',codigo,'NovaSenha123','outra')
        self.trocar(codigo)
    def test_falha_envio(self):
        def falhar(*a): self.entregas.append(a);raise v.ErroValidacao('Sem conexão')
        with patch.object(r,'enviar_codigo',side_effect=falhar),self.assertRaises(v.ErroValidacao): self.pedir()
        with self.assertRaises(v.ErroValidacao): self.trocar(self.entregas[-1][1])
        self.assertIsNotNone(db.autenticar('eduardo','Senha123'))
    def test_concorrencia_reset(self):
        codigo=self.pedir()
        def executar(_):
            try: self.trocar(codigo);return True
            except v.ErroValidacao: return False
        with ThreadPoolExecutor(max_workers=2) as pool: self.assertCountEqual(list(pool.map(executar,range(2))),[True,False])
    def test_concorrencia_solicitacao(self):
        with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(lambda _:r.solicitar('eduardo','nixxude@gmail.com'),range(2)))
        self.assertEqual(len(self.entregas),1)
    def test_sem_chave(self):
        with patch.dict(os.environ,{'RESEND_API_KEY':''}),self.assertRaisesRegex(v.ErroValidacao,'RESEND_API_KEY'): self.pedir()
    def test_atualizar_email_exige_senha(self):
        codigo=self.pedir()
        with self.assertRaises(v.ErroValidacao): db.atualizar_email_usuario(1,'errada','outro@example.com')
        db.atualizar_email_usuario(1,'Senha123','outro@example.com')
        with self.assertRaises(v.ErroValidacao): self.trocar(codigo)
    def test_usuario_sem_email_nao_usa_fallback(self):
        db.criar_usuario('Legado','legado','Senha123');r.solicitar('legado','nixxude@gmail.com');self.assertEqual(self.entregas,[])
    def test_http_contrato(self):
        self.envio.stop()
        with patch.object(r.request,'urlopen',return_value=BytesIO(b'{"id":"teste"}')) as http: r.enviar_codigo('nixxude@gmail.com','12345678','id-teste')
        req=http.call_args.args[0];dados=json.loads(req.data)
        self.assertEqual(req.full_url,'https://api.resend.com/emails');self.assertEqual(dados['to'],['nixxude@gmail.com']);self.assertEqual(http.call_args.kwargs['timeout'],15)
        self.assertEqual(req.get_header('Idempotency-key'),'recuperacao/id-teste')
    def test_http_erros_sem_segredos(self):
        self.envio.stop()
        for erro in [HTTPError('url',403,'forbidden',{},None),URLError('sem rede')]:
            with patch.object(r.request,'urlopen',side_effect=erro),self.assertRaises(v.ErroValidacao) as contexto: r.enviar_codigo('nixxude@gmail.com','12345678','id')
            self.assertNotIn('re_teste',str(contexto.exception))
