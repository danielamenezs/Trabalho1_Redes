import socket
import threading
from datetime import datetime

# configuracoes de rede do servidor
HOST = "0.0.0.0"
PORTA = 5000
TAMANHO_BUFFER = 4096

# lista fixa com as materias do mural
MATERIAS = [
    "Circuitos Eletricos I",
    "Redes de Computadores I",
    "Calculo III",
    "Sistemas Operacionais"
]

# banco de dados em memoria (dicionario de listas)
murais = {
    "Circuitos Eletricos I": [],
    "Redes de Computadores I": [],
    "Calculo III": [],
    "Sistemas Operacionais": []
}

# travas de concorrencia (evitar condicao de corrida)
trava_mural = threading.Lock()
trava_clientes = threading.Lock()

# armazena sessoes ativas para mandar os pushs (notificacoes)
clientes_conectados = []

def enviar_mensagem(conexao, mensagem):
    # sempre finaliza a mensagem com \n para o split do cliente funcionar
    mensagem = mensagem + "\n"
    conexao.sendall(mensagem.encode("utf-8"))

def listar_materias():
    # cria uma lista legivel de todas as materias para o cliente escolher
    linhas = []
    for indice, materia in enumerate(MATERIAS, start=1):
        linhas.append(f"{indice} - {materia}")
    return "\n".join(linhas)

def obter_materia_por_numero(numero_texto):
    # converte o input do usuario para a materia real validando se ela existe
    try:
        numero = int(numero_texto)
    except ValueError:
        return None

    if numero < 1 or numero > len(MATERIAS):
        return None

    return MATERIAS[numero - 1]

def registrar_cliente(conexao, endereco):
    # guarda as informacoes do novo aluno conectado
    cliente = {
        "conexao": conexao,
        "endereco": endereco,
        "inscricoes": set()
    }
    with trava_clientes:
        clientes_conectados.append(cliente)
    return cliente

def remover_cliente(cliente):
    # limpa a sessao do aluno quando ele desliga
    with trava_clientes:
        if cliente in clientes_conectados:
            clientes_conectados.remove(cliente)

def inscrever_cliente(cliente, numero_materia):
    # bota o aluno na "mailing list" da materia para receber alertas
    materia = obter_materia_por_numero(numero_materia)
    if materia is None:
        return "ERRO: materia invalida."

    cliente["inscricoes"].add(materia)
    return f"OK. Inscrito em {materia} com sucesso."

def desinscrever_cliente(cliente, numero_materia):
    materia = obter_materia_por_numero(numero_materia)
    if materia is None:
        return "ERRO: materia invalida."

    if materia in cliente["inscricoes"]:
        cliente["inscricoes"].remove(materia)
        return f"OK. Inscricao removida de {materia}."

    return f"Aviso: voce ja nao estava inscrito em {materia}."

def listar_inscricoes(cliente):
    if len(cliente["inscricoes"]) == 0:
        return "Voce ainda nao esta inscrito em nenhuma materia."

    linhas = ["Suas inscricoes atuais:"]
    for materia in sorted(cliente["inscricoes"]):
        linhas.append(f"- {materia}")
    return "\n".join(linhas)

def notificar_inscritos(materia, autor, mensagem, horario, cliente_autor):
    # essa eh a funcao passiva que despacha o aviso para todos sem eles pedirem
    notificacao = f"NOTIFY|{materia}|{autor}|{mensagem}|{horario}"
    total_enviado = 0
    clientes_com_erro = []

    with trava_clientes:
        for cliente in clientes_conectados:
            # nao notifica o cara que acabou de postar
            if cliente is cliente_autor:
                continue

            # se ele segue a materia, atira a mensagem no socket dele
            if materia in cliente["inscricoes"]:
                try:
                    enviar_mensagem(cliente["conexao"], notificacao)
                    total_enviado += 1
                except OSError:
                    clientes_com_erro.append(cliente)

        # limpa os sockets q morreram no meio do caminho
        for cliente in clientes_com_erro:
            if cliente in clientes_conectados:
                clientes_conectados.remove(cliente)

    print(f"[info] notificacao enviada para {total_enviado} cliente(s) inscrito(s).")
    return total_enviado

def adicionar_aviso(numero_materia, autor, mensagem, cliente_autor):
    materia = obter_materia_por_numero(numero_materia)
    if materia is None:
        return "ERRO: materia invalida."

    autor = autor.strip()
    mensagem = mensagem.strip()

    if not autor or not mensagem:
        return "ERRO: Autor e mensagem nao podem ser vazios."

    horario = datetime.now().strftime("%d/%m/%Y %H:%M")
    aviso = {"autor": autor, "mensagem": mensagem, "horario": horario}

    # lock fundamental aqui pra nao corromper a memoria se tiver 2 POST simultaneos
    with trava_mural:
        murais[materia].append(aviso)

    # dispara push pra galera dessa materia
    total_notificados = notificar_inscritos(materia, autor, mensagem, horario, cliente_autor)

    return f"OK. Aviso publicado em {materia}. Alunos notificados em tempo real: {total_notificados}."

def listar_avisos(numero_materia):
    materia = obter_materia_por_numero(numero_materia)
    if materia is None:
        return "ERRO: materia invalida."

    with trava_mural:
        avisos = list(murais[materia])

    if len(avisos) == 0:
        return f"MURAL DE {materia.upper()}\nNenhum aviso cadastrado ate o momento."

    linhas = [f"--- MURAL DE {materia.upper()} ---"]
    for indice, aviso in enumerate(avisos, start=1):
        linhas.append(f"[{indice}] {aviso['horario']} | {aviso['autor']}: {aviso['mensagem']}")
    linhas.append("-" * 30)
    
    return "\n".join(linhas)

def limpar_mural(numero_materia):
    materia = obter_materia_por_numero(numero_materia)
    if materia is None:
        return "ERRO: materia invalida."

    with trava_mural:
        murais[materia].clear()

    return f"OK. Mural de {materia} foi totalmente apagado."

def apagar_aviso(numero_materia, numero_aviso_texto):
    materia = obter_materia_por_numero(numero_materia)
    if materia is None:
        return "ERRO: materia invalida."

    try:
        numero_aviso = int(numero_aviso_texto)
    except ValueError:
        return "ERRO: O indice do aviso tem que ser um numero."

    with trava_mural:
        if numero_aviso < 1 or numero_aviso > len(murais[materia]):
            return "ERRO: Nao existe aviso com esse numero."

        murais[materia].pop(numero_aviso - 1)

    return f"OK. Aviso apagado com sucesso."

def processar_comando(comando, cliente):
    # coracao do roteamento das operacoes da rede
    comando = comando.strip()
    if not comando:
        return "ERRO: comando vazio"

    partes = comando.split("|")
    tipo = partes[0].upper()

    if tipo == "MATERIAS":
        return listar_materias()

    if tipo == "SUB":
        if len(partes) != 2: return "ERRO de Sintaxe."
        return inscrever_cliente(cliente, partes[1])

    if tipo == "UNSUB":
        if len(partes) != 2: return "ERRO de Sintaxe."
        return desinscrever_cliente(cliente, partes[1])

    if tipo == "INSCRICOES":
        return listar_inscricoes(cliente)

    if tipo == "POST":
        if len(partes) < 4: return "ERRO de Sintaxe."
        numero_materia = partes[1]
        autor = partes[2]
        # remonta a msg caso o usuario tenha digitado um "|" na reclamacao dele
        mensagem = "|".join(partes[3:])
        return adicionar_aviso(numero_materia, autor, mensagem, cliente)

    if tipo == "LIST":
        if len(partes) != 2: return "ERRO de Sintaxe."
        return listar_avisos(partes[1])

    if tipo == "CLEAR":
        if len(partes) != 2: return "ERRO de Sintaxe."
        return limpar_mural(partes[1])

    if tipo == "DELETE":
        if len(partes) != 3: return "ERRO de Sintaxe."
        return apagar_aviso(partes[1], partes[2])

    if tipo == "QUIT":
        return "OK conexao encerrada"

    return "ERRO: comando invalido ou nao mapeado no protocolo."

def atender_cliente(conexao, endereco):
    print(f"[+] cliente conectado: {endereco[0]}:{endereco[1]}")
    cliente = registrar_cliente(conexao, endereco)
    buffer_texto = ""

    # (Nota: as antigas msgs de Boas-Vindas e HELP foram removidas daqui)

    try:
        while True:
            dados = conexao.recv(TAMANHO_BUFFER)
            if not dados:
                break

            buffer_texto += dados.decode("utf-8")

            # processamento pra evitar colar msgs TCP caso cheguem rapido demais
            while "\n" in buffer_texto:
                comando, buffer_texto = buffer_texto.split("\n", 1)
                comando = comando.strip()

                if not comando:
                    continue

                print(f"[{endereco[1]}] Requisição: {comando}")
                resposta = processar_comando(comando, cliente)
                enviar_mensagem(conexao, resposta)

                if comando.upper() == "QUIT":
                    return

    except ConnectionResetError:
        print(f"[-] conexao interrompida pelo cliente: {endereco[1]}")
    except OSError:
        print(f"[-] erro de comunicacao com o cliente: {endereco[1]}")
    finally:
        remover_cliente(cliente)
        conexao.close()
        print(f"[-] sessao encerrada: {endereco[0]}:{endereco[1]}")

def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORTA))
    servidor.listen(5)

        
    print()
    print("╔════════════════════════════════════════════╗")
    print("║        SERVIDOR DO MURAL ACADEMICO         ║")
    print("╚════════════════════════════════════════════╝")
    print(f"IP de escuta : {HOST}")
    print(f"Porta TCP    : {PORTA}")
    print("Protocolo    : TCP/IP")
    print("Status       : ativo e aguardando conexoes")
    print("Modo         : atendimento concorrente")
    print()
    

    while True:
        conexao, endereco = servidor.accept()
        thread_cliente = threading.Thread(target=atender_cliente, args=(conexao, endereco))
        thread_cliente.daemon = True
        thread_cliente.start()

if __name__ == "__main__":
    iniciar_servidor()