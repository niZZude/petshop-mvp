"""Critérios de aceitação da revisão DRAP; somente bancos temporários."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import database as db
import validacoes as v
import popular_demo


class Revisao(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.original=db.DB_PATH
        db.DB_PATH=str(Path(self.tmp.name)/'revisao.db')
        db.criar_tabelas()
        self.c1=db.inserir_cliente('Tutor original','85999990000','','','52998224725')
        self.c2=db.inserir_cliente('Novo tutor','85999990001','','','11144477735')
        self.a1=db.inserir_animal(self.c1,'Mel','Gato','','')
        self.a2=db.inserir_animal(self.c2,'Bob','Cachorro','','')
        self.s=db.inserir_servico('Banho','', '50,05',60)
        self.p1=db.inserir_profissional('Ana Souza','Banho e tosa')
        self.p2=db.inserir_profissional('Bruno Lima','Banho e tosa')
        self.futuro=(datetime.now()+timedelta(days=2)).replace(hour=10,minute=0,second=0,microsecond=0)

    def tearDown(self):
        db.DB_PATH=self.original
        self.tmp.cleanup()

    def agendar(self,animal=None,profissional=None,inicio=None):
        return db.inserir_atendimento(animal or self.a1,self.s,inicio or self.futuro,profissional or self.p1)

    def realizar(self,inicio=None):
        id_=self.agendar()
        db.atualizar_atendimento(id_,self.a1,self.s,inicio or datetime.now()-timedelta(minutes=5),self.p1)
        db.concluir_atendimento(id_)
        return id_

    def test_conclusao_futura_recusada_sem_mudar_estado(self):
        id_=self.agendar()
        with self.assertRaisesRegex(v.ErroValidacao,'futuro'): db.concluir_atendimento(id_)
        self.assertEqual(db.buscar_atendimento(id_)['status'],'agendado')
        self.assertEqual(db.listar_atendimentos(status='concluido'),[])

    def test_reagendar_passado_e_concluir(self):
        id_=self.realizar()
        a=db.buscar_atendimento(id_)
        self.assertEqual(a['status'],'concluido')
        self.assertIsNotNone(a['concluido_em'])

    def test_reagendar_minuto_atual_e_concluir(self):
        id_=self.realizar(datetime.now().replace(second=0,microsecond=0))
        self.assertEqual(db.buscar_atendimento(id_)['status'],'concluido')

    def test_reagendar_futuro_continua_sem_poder_concluir(self):
        id_=self.agendar()
        db.atualizar_atendimento(id_,self.a1,self.s,self.futuro+timedelta(days=1),self.p1)
        with self.assertRaises(v.ErroValidacao): db.concluir_atendimento(id_)

    def test_tutor_historico_e_novo_atendimento(self):
        antigo=self.realizar(datetime.now()-timedelta(days=1))
        db.atualizar_animal(self.a1,self.c2,'Mel','Gato','','')
        novo=self.agendar()
        db.atualizar_atendimento(novo,self.a1,self.s,datetime.now()-timedelta(minutes=2),self.p1)
        db.concluir_atendimento(novo)
        db.atualizar_cliente(self.c1,'Tutor renomeado','85999990000','','','52998224725')
        db.atualizar_cliente(self.c2,'Novo tutor renomeado','85999990001','','','11144477735')
        linhas={a['id_atendimento']:a for a in db.listar_atendimentos(status='concluido')}
        self.assertEqual(linhas[antigo]['tutor'],'Tutor original')
        self.assertEqual(linhas[novo]['tutor'],'Novo tutor')
        self.assertEqual(db.listar_atendimentos('Tutor original','concluido')[0]['id_atendimento'],antigo)

    def test_tutor_da_realizacao_e_nao_so_do_agendamento(self):
        id_=self.agendar()
        db.atualizar_atendimento(id_,self.a1,self.s,datetime.now()-timedelta(minutes=2),self.p1)
        db.atualizar_animal(self.a1,self.c2,'Mel','Gato','','')
        db.concluir_atendimento(id_)
        self.assertEqual(db.listar_atendimentos(status='concluido')[0]['tutor'],'Novo tutor')

    def test_servico_e_profissional_historicos_preservados(self):
        self.realizar()
        db.atualizar_servico(self.s,'Banho premium','','80,75',90)
        db.atualizar_profissional(self.p1,'Ana renomeada','Supervisão')
        a=db.listar_atendimentos(status='concluido')[0]
        self.assertEqual((a['servico'],a['profissional'],a['valor_centavos'],a['duracao_min']),('Banho','Ana Souza',5005,60))

    def test_centavos_entrada_exibicao_e_soma(self):
        self.assertEqual(v.preco_centavos('0,10')+v.preco_centavos('0.20'),30)
        self.assertEqual(v.formatar_centavos(30),'R$ 0,30')
        self.assertEqual(v.formatar_centavos(123456),'R$ 1.234,56')
        self.assertEqual(v.valor_para_campo(5005),'50,05')
        for entrada,esperado in [('50',5000),('50,5',5050),('50.05',5005),('0,01',1)]:
            with self.subTest(entrada=entrada): self.assertEqual(v.preco_centavos(entrada),esperado)
        with db.conectar() as con:
            r=con.execute('SELECT preco_centavos,typeof(preco_centavos) tipo FROM servico').fetchone()
        self.assertEqual((r['preco_centavos'],r['tipo']),(5005,'integer'))

    def test_fracao_de_centavo_e_formato_ambiguo_recusados(self):
        for preco in ['0.005','10,999','1.234,56','nan','inf','-1','1e2',True,'1000000000']:
            with self.subTest(preco=preco),self.assertRaises(v.ErroValidacao): db.inserir_servico('Outro','',preco,30)

    def test_centavos_soma_historico(self):
        db.atualizar_servico(self.s,'Banho','','0,10',60)
        self.realizar(datetime.now()-timedelta(days=2))
        db.atualizar_servico(self.s,'Banho','','0,20',60)
        self.realizar(datetime.now()-timedelta(days=1))
        self.assertEqual(sum(a['valor_centavos'] for a in db.listar_atendimentos(status='concluido')),30)

    def test_profissional_obrigatorio_ativo_e_unico(self):
        with self.assertRaises(v.ErroValidacao): db.inserir_atendimento(self.a1,self.s,self.futuro)
        with self.assertRaises(v.ErroValidacao): db.inserir_profissional(' ANA SOUZA ','Outro')
        db.definir_profissional_ativo(self.p1,False)
        with self.assertRaises(v.ErroValidacao): self.agendar()
        self.assertEqual(len(db.listar_profissionais(True)),1)

    def test_mesmo_profissional_outro_animal_bloqueia_intervalo(self):
        self.agendar()
        for minutos in [0,1,30,59,-1,-30]:
            with self.subTest(minutos=minutos),self.assertRaisesRegex(v.ErroValidacao,'profissional'):
                self.agendar(self.a2,inicio=self.futuro+timedelta(minutes=minutos))

    def test_profissionais_distintos_podem_atender_em_paralelo(self):
        self.agendar()
        self.agendar(self.a2,self.p2)
        self.assertEqual(len(db.listar_atendimentos()),2)
        self.assertEqual(len(db.listar_atendimentos(id_profissional=self.p2)),1)

    def test_mesmo_animal_outro_profissional_continua_bloqueado(self):
        self.agendar()
        with self.assertRaisesRegex(v.ErroValidacao,'animal'): self.agendar(profissional=self.p2)

    def test_inicio_no_fim_exato_permitido(self):
        self.agendar()
        self.agendar(self.a2,inicio=self.futuro+timedelta(minutes=60))
        a=db.listar_atendimentos()[0]
        self.assertEqual(a['fim_estimado'],(self.futuro+timedelta(minutes=60)).isoformat(timespec='minutes'))

    def test_intervalo_atravessa_meia_noite(self):
        inicio=self.futuro.replace(hour=23,minute=30)
        self.agendar(inicio=inicio)
        with self.assertRaises(v.ErroValidacao): self.agendar(self.a2,inicio=inicio+timedelta(minutes=45))

    def test_segundos_nao_burlam_sobreposicao(self):
        self.agendar(inicio=self.futuro+timedelta(seconds=59))
        with self.assertRaises(v.ErroValidacao): self.agendar(self.a2,inicio=self.futuro+timedelta(minutes=59,seconds=59))

    def test_cancelar_libera_profissional(self):
        id_=self.agendar()
        db.cancelar_atendimento(id_,'Tutor viajou')
        self.agendar(self.a2)

    def test_concluir_antes_do_fim_nao_libera_reserva(self):
        inicio=datetime.now()-timedelta(minutes=5)
        self.realizar(inicio)
        with self.assertRaisesRegex(v.ErroValidacao,'profissional'):
            self.agendar(self.a2,inicio=datetime.now()+timedelta(minutes=5))

    def test_reagendar_sem_conflitar_consigo_e_rejeitar_conflito(self):
        id_=self.agendar()
        db.atualizar_atendimento(id_,self.a1,self.s,self.futuro,self.p2)
        outro=self.agendar(self.a2,self.p1)
        with self.assertRaises(v.ErroValidacao): db.atualizar_atendimento(id_,self.a1,self.s,self.futuro,self.p1)
        self.assertEqual(db.buscar_atendimento(id_)['id_profissional'],self.p2)
        self.assertEqual(db.buscar_atendimento(outro)['id_profissional'],self.p1)

    def test_reagendar_preserva_preco_duracao_e_descricao(self):
        id_=self.agendar()
        db.atualizar_servico(self.s,'Banho novo','','90,99',10)
        db.atualizar_atendimento(id_,self.a1,self.s,self.futuro+timedelta(days=1),self.p2)
        a=db.buscar_atendimento(id_)
        self.assertEqual((a['valor_centavos'],a['duracao_min'],a['servico_nome']),(5005,60,'Banho'))

    def test_trocar_servico_revalida_nova_duracao(self):
        id_=self.agendar()
        self.agendar(self.a2,inicio=self.futuro+timedelta(minutes=60))
        s2=db.inserir_servico('Tosa','','70,25',90)
        with self.assertRaises(v.ErroValidacao): db.atualizar_atendimento(id_,self.a1,s2,self.futuro,self.p1)
        self.assertEqual(db.buscar_atendimento(id_)['id_servico'],self.s)

    def test_concorrencia_mesmo_profissional_animais_distintos(self):
        def reservar(animal):
            try: self.agendar(animal);return True
            except v.ErroValidacao: return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(reservar,[self.a1,self.a2])),[True,False])

    def test_equipe_demo_repetivel_e_sem_logins(self):
        popular_demo.popular_profissionais();popular_demo.popular_profissionais()
        self.assertEqual(len(db.listar_profissionais()),3)
        self.assertEqual(db.contar_usuarios(),0)

    def test_sql_recusa_centavos_inconsistentes(self):
        with db.conectar(True) as con:
            with self.assertRaises(sqlite3.IntegrityError): con.execute('UPDATE servico SET preco_centavos=100')
        self.assertEqual(db.buscar_servico(self.s)['preco_centavos'],5005)

    def test_migracao_legada_preserva_ids_e_indica_origem(self):
        db.DB_PATH=str(Path(self.tmp.name)/'legado.db')
        with closing(sqlite3.connect(db.DB_PATH)) as con:
            con.executescript('''CREATE TABLE cliente(id_cliente INTEGER PRIMARY KEY,nome TEXT,telefone TEXT,email TEXT,endereco TEXT);
                INSERT INTO cliente VALUES(7,'Tutor disponível','85999990000',NULL,'');
                CREATE TABLE animal(id_animal INTEGER PRIMARY KEY,id_cliente INTEGER,nome TEXT,especie TEXT,raca TEXT,observacoes TEXT);
                INSERT INTO animal VALUES(8,7,'Mel','Gato','','');
                CREATE TABLE servico(id_servico INTEGER PRIMARY KEY,nome TEXT,descricao TEXT,preco REAL,duracao_min INTEGER,ativo INTEGER);
                INSERT INTO servico VALUES(9,'Banho','',10.005,60,1);
                CREATE TABLE atendimento(id_atendimento INTEGER PRIMARY KEY,id_animal INTEGER,id_servico INTEGER,data_hora TEXT,valor REAL,status TEXT,motivo_cancelamento TEXT);
                INSERT INTO atendimento VALUES(10,8,9,'2026-01-01T10:00',10.005,'concluido',NULL);
                INSERT INTO atendimento VALUES(11,8,9,'2026-01-02T10:00',10.005,'agendado',NULL);''')
        db.criar_tabelas();db.criar_tabelas()
        a=db.listar_atendimentos(status='concluido')[0]
        self.assertEqual((a['id_atendimento'],a['tutor'],a['valor_centavos'],a['origem_historico']),(10,'Tutor disponível',1001,'migracao'))
        self.assertEqual(a['profissional'],'Não informado (legado)')
        with self.assertRaisesRegex(v.ErroValidacao,'profissional'): db.concluir_atendimento(11)
        with db.conectar() as con: self.assertEqual(con.execute('SELECT count(*) FROM ajuste_monetario_migracao').fetchone()[0],3)
        db.atualizar_cliente(7,'Outro nome','85999990000','','',None)
        self.assertEqual(db.listar_atendimentos(status='concluido')[0]['tutor'],'Tutor disponível')


if __name__=='__main__': unittest.main()
