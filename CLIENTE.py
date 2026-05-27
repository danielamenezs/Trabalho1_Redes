# importa o modulo socket para permitir a comunicacao pela rede
import socket

# importa threading para permitir receber mensagens em segundo plano (sem travar a tela)
import threading

# configuracoes de rede
HOST = "127.0.0.1"
PORTA = 5000
TAMANHO_BUFFER = 4096

# variavel global para avisar quando o cliente deve encerrar e fechar as threads
cliente_rodando = True


def mostrar_menu():
    """Desenha um menu organizado e limpo na tela do usuario"""
    print("\n" + "="*40)
    print("          MURAL ACADEMICO           ")
    print("="*40)
    print(" [1] Lista de materias")
    print(" [2] Avisos de uma materia")
    print(" [3] Publicar novo aviso")
    print(" [4] Apagar um aviso")
    print(" [5] Limpar mural de uma materia")
    print(" [6] Inscrever-se em uma materia")
    print(" [7] Remover inscricao de uma materia")
    print(" [8] Ver minhas inscricoes")
    print(" [9] Ver comandos do servidor")
    print(" [0] Sair do programa")
    print("="*40)


def receber_mensagens(cliente):
    """Fica escutando o servidor o tempo todo para capturar respostas e notificacoes"""
    global cliente_rodando
    
    # buffer de texto pra ir juntando os pedacos de dados que chegam pelo tcp
    buffer_texto = ""

    while cliente_rodando:
        try:
            dados = cliente.recv(TAMANHO_BUFFER)

            # se o servidor fechar a conexao, o recv retorna vazio
            if not dados:
                print("\n[!] Conexao encerrada pelo servidor.")
                cliente_rodando = False
                break

            # converte os bytes recebidos para texto normal e junta no buffer
            texto_recebido = dados.decode("utf-8")
            buffer_texto += texto_recebido

            # processa as mensagens completas (que terminam com quebra de linha)
            while "\n" in buffer_texto:
                # separa a primeira mensagem completa do resto do buffer
                mensagem, buffer_texto = buffer_texto.split("\n", 1)
                mensagem = mensagem.strip()

                if mensagem == "":
                    continue

                # se for um alerta passivo (push) do servidor, mostra uma caixinha bonita
                if mensagem.startswith("NOTIFY|"):
                    partes = mensagem.split("|")
                    
                    if len(partes) >= 5:
                        materia, autor, aviso, horario = partes[1], partes[2], partes[3], partes[4]
                        print("\n" + "-"*40)
                        print(" 🔔 NOVA NOTIFICACAO!")
                        print(f" Materia: {materia}")
                        print(f" Autor:   {autor}")
                        print(f" Horario: {horario}")
                        print(f" Aviso:   {aviso}")
                        print("-"*40 + "\n")
                    else:
                        # se vier num formato estranho, imprime do jeito que chegou
                        print(f"\n[NOTIFICACAO] {mensagem}\n")

                # se for uma resposta normal do servidor (como listar materias), so imprime
                else:
                    print(f"\n{mensagem}")

        except OSError:
            # se der erro de sistema operacional (ex: fechamos o programa abruptamente)
            cliente_rodando = False
            break


def enviar_comando(cliente, comando):
    """Prepara a string com o /n no final e envia os bytes para o servidor"""
    comando_formatado = comando + "\n"
    cliente.sendall(comando_formatado.encode("utf-8"))


def iniciar_cliente():
    """Funcao principal que conecta e gerencia os inputs do usuario"""
    global cliente_rodando

    # cria o socket tcp (ipv4 e stream)
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # tenta plugar no servidor
        cliente.connect((HOST, PORTA))
        print("\n[+] Conectado ao servidor do mural com sucesso!")

        # liga a escuta assincrona jogando a funcao pra rodar numa thread paralela
        thread_recebimento = threading.Thread(target=receber_mensagens, args=(cliente,))
        thread_recebimento.daemon = True
        thread_recebimento.start()

        # laco principal do menu interativo
        while cliente_rodando:
            mostrar_menu()
            opcao = input(">>> Escolha uma opcao (0-9): ").strip()
            
            comando = ""

            # formata a string de acordo com o protocolo que inventamos
            if opcao == "1":
                comando = "MATERIAS"

            elif opcao == "2":
                numero = input(" -> Digite o numero da materia: ")
                comando = f"LIST|{numero}"

            elif opcao == "3":
                numero = input(" -> Digite o numero da materia: ")
                autor = input(" -> Qual o seu nome? ")
                mensagem = input(" -> Digite o recado: ")
                comando = f"POST|{numero}|{autor}|{mensagem}"

            elif opcao == "4":
                numero_mat = input(" -> Digite o numero da materia: ")
                numero_aviso = input(" -> Digite o numero do aviso a ser apagado: ")
                comando = f"DELETE|{numero_mat}|{numero_aviso}"

            elif opcao == "5":
                numero = input(" -> Digite o numero da materia para limpar: ")
                comando = f"CLEAR|{numero}"

            elif opcao == "6":
                numero = input(" -> Digite o numero da materia para se inscrever: ")
                comando = f"SUBSCRIBE|{numero}"

            elif opcao == "7":
                numero = input(" -> Digite o numero da materia para remover inscricao: ")
                comando = f"UNSUBSCRIBE|{numero}"

            elif opcao == "8":
                comando = "INSCRICOES"

            elif opcao == "9":
                comando = "HELP"

            elif opcao == "0":
                comando = "QUIT"
                enviar_comando(cliente, comando)
                cliente_rodando = False
                break

            else:
                print("\n[x] Opcao invalida. Tente novamente.")
                continue

            # se chegou ate aqui, despacha o comando pro servidor processar
            enviar_comando(cliente, comando)

    except ConnectionRefusedError:
        print("\nErro: Nao foi possivel conectar. O servidor esta rodando?")
    except Exception as erro:
        print(f"\nOcorreu um erro inesperado: {erro}")
    finally:
        # garante que a conexao vai ser fechada de um jeito limpo
        cliente_rodando = False
        cliente.close()
        print("\nPrograma encerrado.")


# ponto de entrada do script
if __name__ == "__main__":
    iniciar_cliente()
