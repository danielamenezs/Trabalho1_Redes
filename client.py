# importa o modulo socket para permitir a comunicacao pela rede
import socket

# define o ip do servidor (127.0.0.1 significa que é o seu proprio computador)
HOST = "127.0.0.1"

# define a porta de comunicacao (tem que ser a mesma do servidor)
PORTA = 5000

# define a quantidade maxima de dados que o cliente pode receber de uma vez
TAMANHO_BUFFER = 4096

# cria uma funcao que vai apenas imprimir as opcoes na tela pro usuario
def mostrar_menu():
    # pula uma linha e imprime 30 sinais de igual para fazer uma linha de separacao
    print("\n" + "="*30)
    
    # imprime o titulo do menu
    print("MURAL ACADEMICO - MENU")
    
    # imprime outra linha de separacao
    print("="*30)
    
    # mostra a opcao 1 para ver as materias
    print("1 - Ver lista de materias")
    
    # mostra a opcao 2 para listar os avisos
    print("2 - Ver avisos de uma materia")
    
    # mostra a opcao 3 para criar um aviso novo
    print("3 - Postar novo aviso")
    
    # mostra a opcao 4 para deletar um aviso
    print("4 - Apagar um aviso")
    
    # mostra a opcao 5 para limpar tudo de uma materia
    print("5 - Limpar mural de uma materia")
    
    # mostra a opcao 0 para sair do programa
    print("0 - Sair")
    
    # imprime a ultima linha de separacao
    print("="*30)


# cria a funcao principal que vai fazer o cliente funcionar
def iniciar_cliente():
    # cria o socket tcp usando ipv4 (af_inet) e stream (sock_stream) [cite: 327]
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # tenta executar o codigo abaixo, se der erro de conexao ele pula pro except
    try:
        # tenta se conectar ao servidor usando o ip e a porta definidos [cite: 344]
        cliente.connect((HOST, PORTA))
        
        # mostra na tela que conseguiu conectar com sucesso
        print("conectado ao servidor do mural com sucesso!")

        # cria um loop infinito para o menu ficar aparecendo ate a pessoa querer sair
        while True:
            # chama a funcao que desenha o menu na tela
            mostrar_menu()
            
            # pede pro usuario digitar uma opcao e guarda na variavel opcao
            opcao = input("escolha uma opcao (0-5): ")
            
            # cria uma variavel vazia que vai guardar o comando no formato do servidor
            comando = ""

            # verifica se o usuario digitou a opcao 1
            if opcao == "1":
                # define o comando como materias, que o servidor ja entende
                comando = "MATERIAS"
                
            # verifica se o usuario digitou a opcao 2
            elif opcao == "2":
                # pede pro usuario digitar qual o numero da materia
                numero = input("digite o numero da materia: ")
                
                # monta o comando list juntando com o numero da materia
                comando = f"LIST|{numero}"
                
            # verifica se o usuario digitou a opcao 3
            elif opcao == "3":
                # pede o numero da materia
                numero = input("digite o numero da materia: ")
                
                # pede o nome do autor do recado
                autor = input("qual o seu nome? ")
                
                # pede o texto do aviso
                mensagem = input("digite o recado: ")
                
                # junta tudo no formato que a sua amiga criou no servidor
                comando = f"POST|{numero}|{autor}|{mensagem}"
                
            # verifica se o usuario digitou a opcao 4
            elif opcao == "4":
                # pede o numero da materia
                numero_mat = input("digite o numero da materia: ")
                
                # pede o numero do aviso que vai ser apagado
                numero_aviso = input("digite o numero do aviso a ser apagado: ")
                
                # monta o comando delete com a materia e o aviso
                comando = f"DELETE|{numero_mat}|{numero_aviso}"
                
            # verifica se o usuario digitou a opcao 5
            elif opcao == "5":
                # pede o numero da materia para apagar tudo
                numero = input("digite o numero da materia para limpar o mural: ")
                
                # monta o comando clear com o numero
                comando = f"CLEAR|{numero}"
                
            # verifica se o usuario escolheu sair
            elif opcao == "0":
                # define o comando quit para encerrar
                comando = "QUIT"
                
            # trata qualquer outra coisa que o usuario digitar errado
            else:
                # avisa que a opcao nao existe
                print("\nopcao invalida. tente novamente.")
                
                # ignora o resto do codigo abaixo e volta pro inicio do loop (pro menu)
                continue

            # converte o texto do comando para bytes (utf-8) e envia pro servidor [cite: 347]
            cliente.sendall(comando.encode("utf-8"))

            # recebe a resposta do servidor (em bytes) e converte de volta para texto [cite: 348]
            resposta = cliente.recv(TAMANHO_BUFFER).decode("utf-8")
            
            # pula uma linha e avisa que a mensagem abaixo veio do servidor
            print("\n>>> resposta do servidor:")
            
            # imprime a resposta que o servidor mandou
            print(resposta)

            # verifica de novo se a opcao era 0 (sair)
            if opcao == "0":
                # quebra o loop infinito para o programa poder terminar
                break

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
        # fecha a conexao com o servidor [cite: 350]
        cliente.close()
        
        # avisa na tela que o programa terminou
        print("programa encerrado.")


# verifica se o arquivo esta sendo executado direto (e nao importado)
if __name__ == "__main__":
    # chama a funcao principal para o programa comecar a rodar
    iniciar_cliente()
