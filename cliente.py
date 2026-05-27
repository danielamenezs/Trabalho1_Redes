import socket
import threading

# configuracoes de conexao
HOST = "127.0.0.1"
PORTA = 5000
TAMANHO_BUFFER = 4096

# flag para controlar o loop principal e as threads
cliente_rodando = True

# evento usado apenas para organizar a ordem da saida no terminal
resposta_recebida = threading.Event()

def mostrar_menu():
    # desenha as opcoes na tela
    print("╔════════════════════════════════════════════╗")
    print("║              MURAL ACADEMICO               ║")
    print("╚════════════════════════════════════════════╝")
    print("Selecione uma opcao:")
    print()
    print("1. Lista de materias disponiveis")
    print("2. Ver avisos de uma materia")
    print("3. Publicar novo aviso")
    print("4. Apagar um aviso especifico")
    print("5. Limpar mural de uma materia")
    print("6. Inscrever-se em uma materia")
    print("7. Remover inscricao de uma materia")
    print("8. Ver materias em que estou inscrito")
    print("0. Sair do programa")
    print()

def receber_mensagens(cliente):
    global cliente_rodando
    
    # string para ir juntando os dados recebidos aos poucos
    buffer_texto = ""

    while cliente_rodando:
        try:
            # aguarda receber dados do servidor
            dados = cliente.recv(TAMANHO_BUFFER)

            # se os dados vierem vazios, a conexao caiu
            if not dados:
                print("\nConexao encerrada pelo servidor.")
                cliente_rodando = False
                resposta_recebida.set()
                break

            # converte os bytes pra texto
            texto_recebido = dados.decode("utf-8")
            buffer_texto += texto_recebido

            # controla se alguma resposta normal foi recebida nesse bloco
            recebeu_resposta_normal = False

            # processa as mensagens cortando a cada quebra de linha
            while "\n" in buffer_texto:
                mensagem, buffer_texto = buffer_texto.split("\n", 1)
                mensagem = mensagem.strip()

                if mensagem == "":
                    continue

                # verifica se a mensagem eh um alerta de inscricao (push)
                if mensagem.startswith("NOTIFY|"):
                    partes = mensagem.split("|")
                    
                    if len(partes) >= 5:
                        materia = partes[1]
                        autor = partes[2]
                        aviso = partes[3]
                        horario = partes[4]
                        
                        # imprime os dados da notificacao
                        print()
                        print("Nova notificacao recebida")
                        print(f"Materia : {materia}")
                        print(f"Autor   : {autor}")
                        print(f"Horario : {horario}")
                        print(f"Aviso   : {aviso}")
                        print()
                    else:
                        print(f"\nNotificacao recebida: {mensagem}\n")

                # se for resposta de um comando normal, so imprime
                else:
                    print(f"\n{mensagem}")
                    recebeu_resposta_normal = True

            # libera o menu principal somente depois de imprimir a resposta recebida
            if recebeu_resposta_normal:
                resposta_recebida.set()

        except OSError:
            # trata erro caso o programa seja fechado
            cliente_rodando = False
            resposta_recebida.set()
            break

def enviar_comando(cliente, comando):
    # adiciona o \n no final pro servidor saber que o comando terminou
    comando_formatado = comando + "\n"
    cliente.sendall(comando_formatado.encode("utf-8"))

def iniciar_cliente():
    global cliente_rodando

    # cria o socket tcp
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # tenta conectar com o servidor
        cliente.connect((HOST, PORTA))
        print("\nConectado ao servidor com sucesso.")

        # inicia a thread de escuta pra nao travar o input do usuario
        thread_recebimento = threading.Thread(target=receber_mensagens, args=(cliente,))
        thread_recebimento.daemon = True
        thread_recebimento.start()

        # loop do menu principal
        while cliente_rodando:
            mostrar_menu()
            opcao = input("Escolha uma opcao: ").strip()
            
            comando = ""

            # monta os comandos seguindo o protocolo
            if opcao == "1":
                comando = "MATERIAS"

            elif opcao == "2":
                numero = input("Digite o numero da materia: ")
                comando = f"LIST|{numero}"

            elif opcao == "3":
                numero = input("Digite o numero da materia: ")
                autor = input("Qual o seu nome? ")
                mensagem = input("Digite o recado: ")
                comando = f"POST|{numero}|{autor}|{mensagem}"

            elif opcao == "4":
                numero_mat = input("Digite o numero da materia: ")
                numero_aviso = input("Digite o numero do aviso a ser apagado: ")
                comando = f"DELETE|{numero_mat}|{numero_aviso}"

            elif opcao == "5":
                numero = input("Digite o numero da materia para limpar: ")
                comando = f"CLEAR|{numero}"

            elif opcao == "6":
                resposta_recebida.clear()
                enviar_comando(cliente, "MATERIAS")
                resposta_recebida.wait(timeout=3)
                numero = input("Digite o numero da materia para se inscrever: ")
                comando = f"SUB|{numero}"

            elif opcao == "7":
                numero = input("Digite o numero da materia para remover inscricao: ")
                comando = f"UNSUB|{numero}"

            elif opcao == "8":
                comando = "INSCRICOES"

            elif opcao == "0":
                comando = "QUIT"
                resposta_recebida.clear()
                enviar_comando(cliente, comando)
                resposta_recebida.wait(timeout=3)
                cliente_rodando = False
                break

            else:
                print("\nOpcao invalida.")
                continue

            # envia o comando processado
            resposta_recebida.clear()
            enviar_comando(cliente, comando)
            resposta_recebida.wait(timeout=3)

    except ConnectionRefusedError:
        print("\nErro: Nao foi possivel conectar. O servidor esta ligado?")
    except Exception as erro:
        print(f"\nOcorreu um erro: {erro}")
    finally:
        # garante que as coisas vao fechar certo no final
        cliente_rodando = False
        cliente.close()
        print("\nPrograma encerrado.")

if __name__ == "__main__":
    iniciar_cliente()