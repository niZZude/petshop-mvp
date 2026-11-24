"""Exemplos fictícios e equipe demonstrativa; não cria usuários de login."""
from datetime import datetime,timedelta
import database as db

EQUIPE=[('Ana Souza','Banho e tosa'),('Bruno Lima','Banho e tosa'),('Carla Santos','Atendimento veterinário')]


def popular_profissionais():
    db.criar_tabelas()
    for nome,funcao in EQUIPE:
        with db.conectar(True) as con:
            con.execute('INSERT OR IGNORE INTO profissional(nome,funcao) VALUES(?,?)',(nome,funcao))
    return {p['nome']:p['id_profissional'] for p in db.listar_profissionais()}


def popular():
    db.criar_tabelas()
    equipe=popular_profissionais()
    profissionais=[equipe[nome] for nome,_ in EQUIPE]
    if db.listar_clientes() or db.listar_animais() or db.listar_servicos():
        print('Banco já possui dados; apenas a equipe fictícia foi conferida.');return
    clientes=[]
    for nome,tel,email,end,cpf in [('Maria Oliveira','86991110001','maria@exemplo.com','Rua das Flores, 120','52998224725'),
        ('Carlos Pereira','86991110002','carlos@exemplo.com','Av. Central, 45','11144477735'),
        ('Fernanda Lima','86991110003','','Rua do Sol, 300','12345678909')]:
        clientes.append(db.inserir_cliente(nome,tel,email,end,cpf))
    animais=[]
    for tutor,nome,especie,raca in [(0,'Thor','Cachorro','Golden'),(0,'Mel','Gato','Siamês'),(1,'Bob','Cachorro','Poodle'),(2,'Luna','Gato','SRD')]:
        animais.append(db.inserir_animal(clientes[tutor],nome,especie,raca,''))
    servicos=[]
    for nome,preco,dur in [('Banho','50,50',60),('Tosa','70,90',90),('Consulta veterinária','120,00',30),('Vacinação','90,25',20)]:
        servicos.append(db.inserir_servico(nome,'',preco,dur))
    for animal,servico,dias,prof in [(0,0,14,0),(0,1,7,1),(2,3,10,2),(3,2,3,2)]:
        futuro=(datetime.now()+timedelta(days=30+ dias)).replace(second=0,microsecond=0)
        id_=db.inserir_atendimento(animais[animal],servicos[servico],futuro,profissionais[prof])
        db.atualizar_atendimento(id_,animais[animal],servicos[servico],datetime.now()-timedelta(days=dias),profissionais[prof])
        db.concluir_atendimento(id_)
    # Dois profissionais atendem animais distintos no mesmo intervalo.
    inicio=(datetime.now()+timedelta(days=1)).replace(hour=10,minute=0,second=0,microsecond=0)
    for animal,servico,prof in [(1,0,0),(2,1,1),(0,0,2)]:
        db.inserir_atendimento(animais[animal],servicos[servico],inicio,profissionais[prof])
    print('Dados fictícios inseridos: 3 profissionais, 4 concluídos e 3 reservas simultâneas.')


if __name__=='__main__': popular()
