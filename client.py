# importa o modulo socket para permitir a comunicacao pela rede
import socket

# importa threading para permitir receber mensagens enquanto o usuario digita comandos
import threading


# define o ip do servidor
HOST = "127.0.0.1"

# define a porta de comunicacao
PORTA = 5000

# define a quantidade maxima de dados que o cliente pode receber de uma vez
TAMANHO_BUFFER = 4096

# cria uma variavel global para avisar quando o cliente deve encerrar
cliente_rodando = True


# cria uma funcao que vai apenas imprimir as opcoes na tela pro usuario
def mostrar_menu():
    # pula uma linha e imprime uma linha de separacao
    print("\n")

    # imprime o titulo do menu
    print("Mural Academico - MENU")

    # imprime outra linha de separacao
    print("=" * 40)

    # mostra a opcao 1 para ver as materias
    print("1. Lista de Matérias")

    # mostra a opcao 2 para listar os avisos
    print("2. Avisos de uma matéria")

    # mostra a opcao 3 para criar um aviso novo
    print("3. Publicar novo aviso")

    # mostra a opcao 4 para deletar um aviso
    print("4. Apagar um aviso")

    # mostra a opcao 5 para limpar tudo de uma materia
    print("5. Limpar mural de uma materia")

    # mostra a opcao 6 para se inscrever em uma materia
    print("6. Inscrever-se em uma materia")

    # mostra a opcao 7 para remover a inscricao de uma materia
    print("7. Remover inscricao de uma materia")

    # mostra a opcao 8 para ver as inscricoes atuais
    print("8. Ver minhas inscricoes")

    # mostra a opcao 9 para pedir ajuda ao servidor
    print("9. Ver comandos do servidor")

    # mostra a opcao 0 para sair do programa
    print("0. Sair")

# cria uma funcao para receber mensagens do servidor o tempo todo
def receber_mensagens(cliente):
    # usa a variavel global que controla se o cliente continua rodando
    global cliente_rodando

    # cria um buffer de texto pra juntar dados recebidos pelo tcp
    buffer_texto = ""

    # mantem a escuta enquanto o programa estiver rodando
    while cliente_rodando:
        # tenta receber dados do servidor
        try:
            # recebe bytes enviados pelo servidor
            dados = cliente.recv(TAMANHO_BUFFER)

            # se nao vier nenhum dado, significa que a conexao foi fechada
            if not dados:
                # avisa que o servidor encerrou a conexao
                print("\nConexao encerrada pelo servidor.")

                # marca o cliente como encerrado
                cliente_rodando = False

                # encerra o loop
                break

            # converte os bytes recebidos para texto
            texto_recebido = dados.decode("utf-8")

            # adiciona o texto recebido ao buffer
            buffer_texto += texto_recebido

            # processa todas as mensagens completas terminadas com quebra de linha
            while "\n" in buffer_texto:
                # separa uma mensagem completa do restante do buffer
                mensagem, buffer_texto = buffer_texto.split("\n", 1)

                # remove espacos extras da mensagem
                mensagem = mensagem.strip()

                # ignora mensagens vazias
                if mensagem == "":
                    continue

                # verifica se a mensagem recebida é uma notificacao
                if mensagem.startswith("NOTIFY|"):
                    # divide a notificacao em partes
                    partes = mensagem.split("|")

                    # verifica se a notificacao veio no formato esperado
                    if len(partes) >= 5:
                        # pega a materia da notificacao
                        materia = partes[1]

                        # pega o autor da notificacao
                        autor = partes[2]

                        # pega a mensagem do aviso
                        aviso = partes[3]

                        # pega o horario do aviso
                        horario = partes[4]

                        # imprime a notificacao de um jeito mais bonito
                        print("\n\n>>> NOVA NOTIFICACAO")
                        print(f"Materia: {materia}")
                        print(f"Autor: {autor}")
                        print(f"Horario: {horario}")
                        print(f"Aviso: {aviso}")

                    # caso o formato esteja estranho, imprime cru mesmo
                    else:
                        print("\n>>> NOTIFICACAO RECEBIDA:")
                        print(mensagem)

                # se nao for notificacao, imprime como resposta normal do servidor
                else:
                    # pula uma linha e avisa que a mensagem veio do servidor
                    print("\n>>> Resposta do servidor:")

                    # imprime a mensagem recebida
                    print(mensagem)

                # reimprime o convite de comando para nao deixar o terminal confuso
                print("\nPressione enter para continuar ou escolha uma opcao no menu.")

        # captura erro se a conexao for encerrada
        except OSError:
            # marca o cliente como encerrado
            cliente_rodando = False

            # encerra o loop
            break


# cria uma funcao para enviar um comando ao servidor
def enviar_comando(cliente, comando):
    # adiciona quebra de linha no final para o servidor saber onde o comando termina
    comando = comando + "\n"

    # envia o comando convertido para bytes
    cliente.sendall(comando.encode("utf-8"))


# cria a funcao principal que vai fazer o cliente funcionar
def iniciar_cliente():
    # usa a variavel global que controla se o cliente continua rodando
    global cliente_rodando

    # cria o socket tcp usando ipv4 e stream
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # tenta executar o codigo abaixo
    try:
        # tenta se conectar ao servidor usando o ip e a porta definidos
        cliente.connect((HOST, PORTA))

        # mostra na tela que conseguiu conectar com sucesso
        print("conectado ao servidor do mural com sucesso!")

        # cria uma thread para receber mensagens do servidor em segundo plano
        thread_recebimento = threading.Thread(target=receber_mensagens, args=(cliente,))

        # define a thread como daemon para ela fechar junto com o programa principal
        thread_recebimento.daemon = True

        # inicia a thread de recebimento
        thread_recebimento.start()

        # cria um loop para o menu ficar aparecendo ate a pessoa querer sair
        while cliente_rodando:
            # chama a funcao que desenha o menu na tela
            mostrar_menu()

            # pede pro usuario digitar uma opcao
            opcao = input("Escolha uma opcao (0-9): ")

            # cria uma variavel vazia que vai guardar o comando no formato do servidor
            comando = ""

            # verifica se o usuario digitou a opcao 1
            if opcao == "1":
                # define o comando como materias
                comando = "MATERIAS"

            # verifica se o usuario digitou a opcao 2
            elif opcao == "2":
                # pede pro usuario digitar qual o numero da materia
                numero = input("Digite o numero da materia: ")

                # monta o comando list juntando com o numero da materia
                comando = f"LIST|{numero}"

            # verifica se o usuario digitou a opcao 3
            elif opcao == "3":
                # pede o numero da materia
                numero = input("Digite o numero da materia: ")

                # pede o nome do autor do recado
                autor = input("Qual o seu nome? ")

                # pede o texto do aviso
                mensagem = input("Digite o recado: ")

                # monta o comando post no formato entendido pelo servidor
                comando = f"POST|{numero}|{autor}|{mensagem}"

            # verifica se o usuario digitou a opcao 4
            elif opcao == "4":
                # pede o numero da materia
                numero_mat = input("Digite o numero da materia: ")

                # pede o numero do aviso que vai ser apagado
                numero_aviso = input("Digite o numero do aviso a ser apagado: ")

                # monta o comando delete com a materia e o aviso
                comando = f"DELETE|{numero_mat}|{numero_aviso}"

            # verifica se o usuario digitou a opcao 5
            elif opcao == "5":
                # pede o numero da materia para apagar tudo
                numero = input("Digite o numero da materia para limpar o mural: ")

                # monta o comando clear com o numero
                comando = f"CLEAR|{numero}"

            # verifica se o usuario digitou a opcao 6
            elif opcao == "6":
                # pede o numero da materia para inscricao
                numero = input("Digite o numero da materia para se inscrever: ")

                # monta o comando subscribe
                comando = f"SUBSCRIBE|{numero}"

            # verifica se o usuario digitou a opcao 7
            elif opcao == "7":
                # pede o numero da materia para remover inscricao
                numero = input("Digite o numero da materia para remover inscricao: ")

                # monta o comando unsubscribe
                comando = f"UNSUBSCRIBE|{numero}"

            # verifica se o usuario digitou a opcao 8
            elif opcao == "8":
                # monta o comando para listar inscricoes
                comando = "INSCRICOES"

            # verifica se o usuario digitou a opcao 9
            elif opcao == "9":
                # monta o comando help
                comando = "HELP"

            # verifica se o usuario escolheu sair
            elif opcao == "0":
                # define o comando quit para encerrar
                comando = "QUIT"

                # envia o comando quit para o servidor
                enviar_comando(cliente, comando)

                # marca o cliente como encerrado
                cliente_rodando = False

                # encerra o loop
                break

            # trata qualquer outra coisa que o usuario digitar errado
            else:
                # avisa que a opcao nao existe
                print("\nopcao invalida. tente novamente.")

                # volta pro inicio do loop
                continue

            # envia o comando montado para o servidor
            enviar_comando(cliente, comando)

    # captura o erro especifico de quando o servidor esta desligado
    except ConnectionRefusedError:
        # avisa o usuario que nao deu pra conectar
        print("erro: nao foi possivel conectar. o servidor esta rodando?")

    # captura qualquer outro erro que possa acontecer
    except Exception as erro:
        # mostra qual foi o erro inesperado
        print(f"ocorreu um erro inesperado: {erro}")

    # o bloco finally sempre executa no final, dando erro ou nao
    finally:
        # marca o cliente como encerrado
        cliente_rodando = False

        # fecha a conexao com o servidor
        cliente.close()

        # avisa na tela que o programa terminou
        print("programa encerrado.")


# verifica se o arquivo esta sendo executado direto
if __name__ == "__main__":
    # chama a funcao principal para o programa comecar a rodar
    iniciar_cliente()
