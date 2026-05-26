# importa o modulo socket para criar a comunicação em rede
import socket

# importa threading para permitir que mais de um cliente use o servidor ao mesmo tempo
import threading

# importa datetime para registrar a data e a hora de cada aviso
from datetime import datetime


# define o ip em que o servidor vai escutar conexões
HOST = "0.0.0.0"

# define a porta usada pelo servidor
PORTA = 5000

# define o tamanho maximo de bytes recebidos por mensagem
TAMANHO_BUFFER = 4096

# cria uma lista com as materias disponiveis no mural
MATERIAS = [
    "Circuitos Eletricos I",
    "Redes de Computadores I",
    "Calculo III",
    "Sistemas Operacionais"
]

# cria o dicionario que vai guardar os avisos de cada materia
murais = {
    "Circuitos Eletricos I": [],
    "Redes de Computadores I": [],
    "Calculo III": [],
    "Sistemas Operacionais": []
}

# cria uma trava para evitar que dois clientes alterem o mural ao mesmo tempo
trava_mural = threading.Lock()

# cria uma lista para guardar os clientes que estão conectados ao servidor
clientes_conectados = []

# cria uma trava para evitar conflito ao acessar a lista de clientes conectados
trava_clientes = threading.Lock()


# cria uma função para enviar texto para um cliente
def enviar_mensagem(conexao, mensagem):
    # adiciona uma quebra de linha no final da mensagem para marcar o fim dela
    mensagem = mensagem + "\n"

    # envia a mensagem convertida para bytes
    conexao.sendall(mensagem.encode("utf-8"))


# cria uma função para montar a lista de materias em texto
def listar_materias():
    # cria uma lista vazia para guardar as linhas de resposta
    linhas = []

    # percorre as materias usando indice e nome
    for indice, materia in enumerate(MATERIAS, start=1):
        # adiciona uma linha com numero e nome da materia
        linhas.append(f"{indice} - {materia}")

    # junta todas as linhas em uma unica string separada por quebra de linha
    return "\n".join(linhas)


# cria uma função para converter o numero da materia em nome da materia
def obter_materia_por_numero(numero_texto):
    # tenta converter o texto recebido para numero inteiro
    try:
        # converte o texto para inteiro
        numero = int(numero_texto)

    # trata o caso em que o texto nao é um numero valido
    except ValueError:
        # retorna none quando nao for possivel converter
        return None

    # verifica se o numero esta dentro do intervalo das materias
    if numero < 1 or numero > len(MATERIAS):
        # retorna none quando o numero nao corresponde a nenhuma materia
        return None

    # retorna a materia correspondente ao numero escolhido
    return MATERIAS[numero - 1]


# cria uma função para adicionar um cliente na lista de conectados
def registrar_cliente(conexao, endereco):
    # cria um dicionario com os dados do cliente
    cliente = {
        "conexao": conexao,
        "endereco": endereco,
        "inscricoes": set()
    }

    # usa a trava para alterar a lista de clientes com segurança
    with trava_clientes:
        # adiciona o cliente na lista global
        clientes_conectados.append(cliente)

    # retorna o dicionario do cliente para ser usado pela thread dele
    return cliente


# cria uma função para remover um cliente da lista de conectados
def remover_cliente(cliente):
    # usa a trava para alterar a lista de clientes com segurança
    with trava_clientes:
        # verifica se o cliente ainda esta na lista
        if cliente in clientes_conectados:
            # remove o cliente da lista
            clientes_conectados.remove(cliente)


# cria uma função para inscrever um cliente em uma materia
def inscrever_cliente(cliente, numero_materia):
    # busca o nome da materia a partir do numero recebido
    materia = obter_materia_por_numero(numero_materia)

    # verifica se a materia existe
    if materia is None:
        # retorna erro se a materia for invalida
        return "ERRO materia invalida"

    # adiciona a materia ao conjunto de inscricoes do cliente
    cliente["inscricoes"].add(materia)

    # retorna confirmação para o cliente
    return f"OK inscrito em {materia}"


# cria uma função para remover a inscrição de um cliente em uma materia
def desinscrever_cliente(cliente, numero_materia):
    # busca o nome da materia a partir do numero recebido
    materia = obter_materia_por_numero(numero_materia)

    # verifica se a materia existe
    if materia is None:
        # retorna erro se a materia for invalida
        return "ERRO materia invalida"

    # verifica se o cliente estava inscrito nessa materia
    if materia in cliente["inscricoes"]:
        # remove a materia do conjunto de inscricoes
        cliente["inscricoes"].remove(materia)

        # retorna confirmação para o cliente
        return f"OK inscricao removida de {materia}"

    # retorna aviso caso o cliente nao estivesse inscrito
    return f"OK voce nao estava inscrito em {materia}"


# cria uma função para listar as materias em que o cliente esta inscrito
def listar_inscricoes(cliente):
    # verifica se o cliente nao possui inscricoes
    if len(cliente["inscricoes"]) == 0:
        # retorna mensagem informando que nao ha inscricoes
        return "voce ainda nao esta inscrito em nenhuma materia"

    # cria uma lista com as inscricoes do cliente
    linhas = ["suas inscricoes:"]

    # percorre as materias inscritas em ordem alfabetica
    for materia in sorted(cliente["inscricoes"]):
        # adiciona a materia na lista de resposta
        linhas.append(f"- {materia}")

    # junta as linhas em uma unica string
    return "\n".join(linhas)


# cria uma função para notificar os clientes inscritos em uma materia
def notificar_inscritos(materia, autor, mensagem, horario, cliente_autor):
    # cria o texto da notificação
    notificacao = f"NOTIFY|{materia}|{autor}|{mensagem}|{horario}"

    # cria um contador de notificações enviadas
    total_enviado = 0

    # cria uma lista para guardar clientes que deram erro no envio
    clientes_com_erro = []

    # usa a trava para percorrer a lista de clientes com segurança
    with trava_clientes:
        # percorre todos os clientes conectados
        for cliente in clientes_conectados:
            # verifica se é o mesmo cliente que postou o aviso
            if cliente is cliente_autor:
                # pula o autor para nao notificar quem acabou de postar
                continue

            # verifica se o cliente esta inscrito na materia do aviso
            if materia in cliente["inscricoes"]:
                # tenta enviar a notificação para esse cliente
                try:
                    # envia a notificação pelo socket do cliente
                    enviar_mensagem(cliente["conexao"], notificacao)

                    # aumenta o contador de notificações enviadas
                    total_enviado += 1

                # trata erro caso o cliente tenha desconectado
                except OSError:
                    # guarda o cliente para remover depois
                    clientes_com_erro.append(cliente)

        # remove da lista os clientes que deram erro
        for cliente in clientes_com_erro:
            # verifica se o cliente ainda esta na lista
            if cliente in clientes_conectados:
                # remove o cliente da lista
                clientes_conectados.remove(cliente)

    # mostra no terminal do servidor quantas notificações foram enviadas
    print(f"notificacao de {materia} enviada para {total_enviado} cliente(s)")

    # retorna o total de notificações enviadas
    return total_enviado


# cria uma função para adicionar um aviso no mural
def adicionar_aviso(numero_materia, autor, mensagem, cliente_autor):
    # busca o nome da materia a partir do numero recebido
    materia = obter_materia_por_numero(numero_materia)

    # verifica se a materia existe
    if materia is None:
        # retorna uma mensagem de erro se a materia for invalida
        return "ERRO materia invalida"

    # remove espacos extras do nome do autor
    autor = autor.strip()

    # remove espacos extras da mensagem
    mensagem = mensagem.strip()

    # verifica se o autor foi preenchido
    if autor == "":
        # retorna erro se o nome estiver vazio
        return "ERRO nome do autor vazio"

    # verifica se a mensagem foi preenchida
    if mensagem == "":
        # retorna erro se a mensagem estiver vazia
        return "ERRO mensagem vazia"

    # pega a data e a hora atuais em formato legivel
    horario = datetime.now().strftime("%d/%m/%Y %H:%M")

    # monta o aviso em formato de dicionario
    aviso = {
        "autor": autor,
        "mensagem": mensagem,
        "horario": horario
    }

    # usa a trava para alterar o mural com segurança
    with trava_mural:
        # adiciona o aviso na lista da materia escolhida
        murais[materia].append(aviso)

    # chama a função que notifica os clientes inscritos nessa materia
    total_notificados = notificar_inscritos(materia, autor, mensagem, horario, cliente_autor)

    # retorna confirmação para o cliente que postou
    return f"OK aviso adicionado em {materia}\nnotificacoes enviadas: {total_notificados}"


# cria uma função para listar os avisos de uma materia
def listar_avisos(numero_materia):
    # busca o nome da materia a partir do numero recebido
    materia = obter_materia_por_numero(numero_materia)

    # verifica se a materia existe
    if materia is None:
        # retorna erro se o numero da materia for invalido
        return "ERRO materia invalida"

    # usa a trava para ler o mural com segurança
    with trava_mural:
        # cria uma copia da lista de avisos da materia
        avisos = list(murais[materia])

    # verifica se a lista esta vazia
    if len(avisos) == 0:
        # retorna uma mensagem dizendo que ainda nao ha avisos
        return f"MURAL {materia}\nnenhum aviso cadastrado ainda"

    # cria a primeira linha da resposta com o nome da materia
    linhas = [f"MURAL {materia}"]

    # percorre os avisos usando indice e conteudo
    for indice, aviso in enumerate(avisos, start=1):
        # monta uma linha formatada com numero, horario, autor e mensagem
        linha = f"{indice} - [{aviso['horario']}] {aviso['autor']}: {aviso['mensagem']}"

        # adiciona a linha na lista de resposta
        linhas.append(linha)

    # junta todas as linhas em uma unica resposta
    return "\n".join(linhas)


# cria uma função para limpar os avisos de uma materia
def limpar_mural(numero_materia):
    # busca o nome da materia a partir do numero recebido
    materia = obter_materia_por_numero(numero_materia)

    # verifica se a materia existe
    if materia is None:
        # retorna erro se a materia for invalida
        return "ERRO materia invalida"

    # usa a trava para limpar o mural com segurança
    with trava_mural:
        # limpa todos os avisos da materia escolhida
        murais[materia].clear()

    # retorna confirmação para o cliente
    return f"OK mural de {materia} limpo"


# cria uma função para apagar um aviso especifico
def apagar_aviso(numero_materia, numero_aviso_texto):
    # busca o nome da materia a partir do numero recebido
    materia = obter_materia_por_numero(numero_materia)

    # verifica se a materia existe
    if materia is None:
        # retorna erro se a materia for invalida
        return "ERRO materia invalida"

    # tenta converter o numero do aviso para inteiro
    try:
        # converte o numero do aviso
        numero_aviso = int(numero_aviso_texto)

    # trata o caso em que o numero do aviso nao é valido
    except ValueError:
        # retorna erro se nao for numero
        return "ERRO numero de aviso invalido"

    # usa a trava para alterar o mural com segurança
    with trava_mural:
        # verifica se o numero do aviso existe na lista
        if numero_aviso < 1 or numero_aviso > len(murais[materia]):
            # retorna erro se o aviso nao existir
            return "ERRO aviso inexistente"

        # remove o aviso usando o indice correspondente
        murais[materia].pop(numero_aviso - 1)

    # retorna confirmação para o cliente
    return f"OK aviso {numero_aviso} removido de {materia}"


# cria uma função para interpretar uma mensagem recebida do cliente
def processar_comando(comando, cliente):
    # remove espacos e quebras de linha no inicio e no fim
    comando = comando.strip()

    # verifica se o comando esta vazio
    if comando == "":
        # retorna erro se nao houver comando
        return "ERRO comando vazio"

    # divide o comando usando o simbolo | como separador
    partes = comando.split("|")

    # pega o primeiro campo como nome do comando
    tipo = partes[0].upper()

    # verifica se o cliente pediu ajuda
    if tipo == "HELP":
        # retorna a lista de comandos aceitos pelo servidor
        return (
            "comandos disponiveis:\n"
            "MATERIAS\n"
            "SUBSCRIBE|numero_materia\n"
            "UNSUBSCRIBE|numero_materia\n"
            "INSCRICOES\n"
            "POST|numero_materia|autor|mensagem\n"
            "LIST|numero_materia\n"
            "CLEAR|numero_materia\n"
            "DELETE|numero_materia|numero_aviso\n"
            "QUIT"
        )

    # verifica se o cliente pediu a lista de materias
    if tipo == "MATERIAS":
        # retorna a lista de materias
        return listar_materias()

    # verifica se o cliente pediu para se inscrever em uma materia
    if tipo == "SUBSCRIBE":
        # verifica se o comando tem exatamente duas partes
        if len(partes) != 2:
            # retorna erro se o formato estiver errado
            return "ERRO formato correto: SUBSCRIBE|numero_materia"

        # chama a função que inscreve o cliente
        return inscrever_cliente(cliente, partes[1])

    # verifica se o cliente pediu para remover uma inscrição
    if tipo == "UNSUBSCRIBE":
        # verifica se o comando tem exatamente duas partes
        if len(partes) != 2:
            # retorna erro se o formato estiver errado
            return "ERRO formato correto: UNSUBSCRIBE|numero_materia"

        # chama a função que remove a inscrição
        return desinscrever_cliente(cliente, partes[1])

    # verifica se o cliente pediu para listar suas inscrições
    if tipo == "INSCRICOES":
        # retorna a lista de inscrições do cliente
        return listar_inscricoes(cliente)

    # verifica se o cliente pediu para postar um aviso
    if tipo == "POST":
        # verifica se o comando tem pelo menos quatro partes
        if len(partes) < 4:
            # retorna erro se faltarem campos
            return "ERRO formato correto: POST|numero_materia|autor|mensagem"

        # pega o numero da materia
        numero_materia = partes[1]

        # pega o nome do autor
        autor = partes[2]

        # junta o restante como mensagem para permitir o uso de | no texto
        mensagem = "|".join(partes[3:])

        # chama a função que adiciona o aviso
        return adicionar_aviso(numero_materia, autor, mensagem, cliente)

    # verifica se o cliente pediu a listagem dos avisos
    if tipo == "LIST":
        # verifica se o comando tem exatamente duas partes
        if len(partes) != 2:
            # retorna erro se o formato estiver errado
            return "ERRO formato correto: LIST|numero_materia"

        # chama a função que lista os avisos
        return listar_avisos(partes[1])

    # verifica se o cliente pediu para limpar um mural
    if tipo == "CLEAR":
        # verifica se o comando tem exatamente duas partes
        if len(partes) != 2:
            # retorna erro se o formato estiver errado
            return "ERRO formato correto: CLEAR|numero_materia"

        # chama a função que limpa o mural
        return limpar_mural(partes[1])

    # verifica se o cliente pediu para apagar um aviso especifico
    if tipo == "DELETE":
        # verifica se o comando tem exatamente tres partes
        if len(partes) != 3:
            # retorna erro se o formato estiver errado
            return "ERRO formato correto: DELETE|numero_materia|numero_aviso"

        # chama a função que apaga um aviso
        return apagar_aviso(partes[1], partes[2])

    # verifica se o cliente pediu para sair
    if tipo == "QUIT":
        # retorna confirmação de encerramento
        return "OK conexao encerrada"

    # retorna erro se o comando nao for conhecido
    return "ERRO comando desconhecido"


# cria uma função para atender um cliente conectado
def atender_cliente(conexao, endereco):
    # mostra no terminal do servidor qual cliente se conectou
    print(f"cliente conectado: {endereco[0]}:{endereco[1]}")

    # registra o cliente na lista de conectados
    cliente = registrar_cliente(conexao, endereco)

    # cria uma string para guardar dados recebidos que ainda nao formaram um comando completo
    buffer_texto = ""

    # tenta enviar uma mensagem inicial para o cliente
    try:
        # envia uma mensagem de boas-vindas
        enviar_mensagem(conexao, "OK conectado ao mural academico")

        # envia uma dica inicial para o cliente
        enviar_mensagem(conexao, "digite HELP para ver os comandos disponiveis")

    # trata erro caso a conexão falhe logo no começo
    except OSError:
        # remove o cliente da lista de conectados
        remover_cliente(cliente)

        # fecha a conexão
        conexao.close()

        # encerra a função
        return

    # usa try para evitar que um erro derrube o servidor inteiro
    try:
        # mantém o atendimento enquanto o cliente estiver conectado
        while True:
            # recebe dados enviados pelo cliente
            dados = conexao.recv(TAMANHO_BUFFER)

            # verifica se o cliente fechou a conexão
            if not dados:
                # interrompe o loop se nao houver dados
                break

            # converte os bytes recebidos para texto
            texto_recebido = dados.decode("utf-8")

            # adiciona o texto recebido ao buffer
            buffer_texto += texto_recebido

            # processa todos os comandos completos que terminam com quebra de linha
            while "\n" in buffer_texto:
                # separa um comando completo do restante do buffer
                comando, buffer_texto = buffer_texto.split("\n", 1)

                # remove espaços extras do comando
                comando = comando.strip()

                # ignora linhas vazias
                if comando == "":
                    # continua para o proximo comando
                    continue

                # mostra no terminal o comando recebido
                print(f"recebido de {endereco[0]}:{endereco[1]} -> {comando}")

                # processa o comando recebido
                resposta = processar_comando(comando, cliente)

                # envia a resposta de volta para o cliente
                enviar_mensagem(conexao, resposta)

                # verifica se o comando era para sair
                if comando.upper() == "QUIT":
                    # encerra o atendimento desse cliente
                    return

    # captura erro quando o cliente fecha a conexão de forma inesperada
    except ConnectionResetError:
        # mostra que o cliente fechou a conexão de forma inesperada
        print(f"cliente desconectado inesperadamente: {endereco[0]}:{endereco[1]}")

    # captura outros erros de comunicação
    except OSError:
        # mostra que ocorreu erro com esse cliente
        print(f"erro de comunicação com cliente: {endereco[0]}:{endereco[1]}")

    # executa no final, com erro ou sem erro
    finally:
        # remove o cliente da lista de conectados
        remover_cliente(cliente)

        # fecha o socket da conexão com esse cliente
        conexao.close()

        # mostra no terminal que a conexão foi fechada
        print(f"conexao fechada: {endereco[0]}:{endereco[1]}")


# cria a função principal do servidor
def iniciar_servidor():
    # cria o socket tcp usando ipv4
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # permite reutilizar a porta logo apos fechar o servidor
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # associa o socket ao ip e a porta definidos
    servidor.bind((HOST, PORTA))

    # coloca o servidor em modo de escuta
    servidor.listen(5)

    # mostra no terminal que o servidor iniciou
    print("servidor do mural academico iniciado")

    # mostra o ip usado pelo servidor
    print(f"ip de escuta: {HOST}")

    # mostra a porta usada pelo servidor
    print(f"porta: {PORTA}")

    # mostra o protocolo de transporte usado
    print("protocolo: tcp")

    # mostra uma observação sobre as notificações
    print("notificacoes em tempo real ativadas via socket tcp")

    # mantém o servidor rodando continuamente
    while True:
        # espera um cliente se conectar
        conexao, endereco = servidor.accept()

        # cria uma thread para atender esse cliente
        thread_cliente = threading.Thread(target=atender_cliente, args=(conexao, endereco))

        # define a thread como daemon para fechar junto com o programa principal
        thread_cliente.daemon = True

        # inicia a thread do cliente
        thread_cliente.start()


# verifica se este arquivo esta sendo executado diretamente
if __name__ == "__main__":
    # chama a função que inicia o servidor
    iniciar_servidor()
