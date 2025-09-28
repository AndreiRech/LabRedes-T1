import socket
import sys
import os
import struct
import time
import random
import protocol
import network

# --- Configurações do Cliente ---
DIR = 'LogFiles'

# --- Funções do Cliente ---
def handle_put(sock, filepath):
    """
    Gerencia a lógica completa do comando PUT.
    Retorna (sucesso, bytes_enviados, bytes_recebidos).
    """
    bytes_sent = 0
    bytes_received = 0

    if not os.path.exists(filepath):
        print(f"ERRO: Arquivo '{filepath}' nao encontrado localmente.")
        return False, 0, 0

    filename = os.path.basename(filepath)
    
    # Passo 1: Envia o comando PUT com o nome do arquivo
    network.send_message(sock, protocol.OP_PUT, filename.encode('utf-8'))
    bytes_sent += protocol.HEADER_SIZE + len(filename.encode('utf-8'))
    
    # Passo 2: Aguarda a confirmação do servidor
    op, payload = network.receive_message(sock)
    bytes_received += protocol.HEADER_SIZE + len(payload)

    if op == protocol.OP_ERROR:
        print(f"Servidor recusou o PUT: {payload.decode('utf-8')}")
        return False, bytes_sent, bytes_received

    if op != protocol.OP_SUCCESS:
        print("Erro: Resposta inesperada do servidor.")
        return False, bytes_sent, bytes_received

    # Passo 3: Envia o conteúdo do arquivo
    file_size = os.path.getsize(filepath)
    print(f"Enviando '{filename}' ({file_size} bytes)...")
    
    # Envia o cabeçalho especial com o tamanho do arquivo
    file_header = struct.pack(protocol.HEADER_FORMAT, 0, file_size)
    sock.sendall(file_header)
    bytes_sent += len(file_header)

    with open(filepath, 'rb') as f:
        while chunk := f.read(4096):
            sock.sendall(chunk)
            bytes_sent += len(chunk)

    # Passo 4: Recebe a confirmação final
    op_final, payload_final = network.receive_message(sock)
    bytes_received += protocol.HEADER_SIZE + len(payload_final)
    
    if op_final == protocol.OP_SUCCESS:
        print(payload_final.decode('utf-8'))
        return True, bytes_sent, bytes_received
    else:
        print("Ocorreu um erro no servidor ao receber o arquivo.")
        return False, bytes_sent, bytes_received

def create_log(server_ip, server_port, bytes_sent, bytes_received, start_time, end_time):
    """
    Cria um arquivo de log com os detalhes da conexão.
    """
    if not os.path.exists(DIR):
        os.makedirs(DIR)
        
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    random_suffix = random.randint(10000, 99999) # Tive que coloca um sufixo random pq tava dando conflito de nomes e sobrescrevendo logs no automatico
    log_filename = f"{DIR}/log_cliente_{timestamp}_{random_suffix}.txt"
    
    duration = end_time - start_time
    rate_bps = (bytes_sent + bytes_received) / duration if duration > 0 else 0
    
    log_content = (
        f"--- Relatorio de Conexao ---\n"
        f"Servidor: {server_ip}:{server_port}\n"
        f"Inicio da Conexao: {time.ctime(start_time)}\n"
        f"Fim da Conexao:    {time.ctime(end_time)}\n"
        f"Duracao (s): {duration:.4f}\n"
        f"Bytes Enviados:  {bytes_sent}\n"
        f"Bytes Recebidos: {bytes_received}\n"
        f"Taxa de Transmissao (Bytes/s): {rate_bps:.2f}\n"
    )
    
    with open(log_filename, 'w') as f:
        f.write(log_content)
        
    print(f"\nLog da conexao salvo em: {log_filename}")

def start_manual(host, port):
    """
    Inicia uma conexão manual com o servidor e permite o envio de arquivos, listagem e desconexão.
    """
    total_bytes_sent = 0
    total_bytes_received = 0
    start_time = 0.0

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print(f"Conectando ao servidor em {host}:{port}...")
        
        client_socket.connect((host, port))
        start_time = time.time()
        
        print("Conectado! Digite 'list', 'put <arquivo>' ou 'quit'.")

        while True:
            # Deixa a linha de comando maravilhosa!!!!!!!! (orgulhoso)
            command_line = input("cliente> ").strip()
            if not command_line: continue

            parts = command_line.split()
            command = parts[0].lower()

            # --- Lógica dos Comandos ---
            if command == 'list':
                network.send_message(client_socket, protocol.OP_LIST)
                total_bytes_sent += protocol.HEADER_SIZE
                
                op, payload = network.receive_message(client_socket)
                total_bytes_received += protocol.HEADER_SIZE + len(payload)
                
                if op == protocol.OP_SUCCESS:
                    print("--- Arquivos no Servidor ---\n" + payload.decode('utf-8'))
                else:
                    print(f"Erro do servidor: {payload.decode('utf-8')}")

            elif command == 'put':
                if len(parts) != 2:
                    print("Uso: put <caminho_do_arquivo>")
                    continue
                
                filepath = parts[1]
                _, sent, received = handle_put(client_socket, filepath)
                
                total_bytes_sent += sent
                total_bytes_received += received

            elif command == 'quit':
                network.send_message(client_socket, protocol.OP_QUIT)
                total_bytes_sent += protocol.HEADER_SIZE
                break

            else:
                print(f"Comando desconhecido: '{command}'")

    except ConnectionRefusedError:
        print("Erro: A conexão foi recusada. O servidor está no ar?")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        end_time = time.time()
        client_socket.close()
        
        print("Conexao com o servidor encerrada.")
        
        if start_time > 0:
            create_log(host, port, total_bytes_sent, total_bytes_received, start_time, end_time)

def start_automatic(server_host, server_port, filepath):
    """
    Inicia uma conexão automática com o servidor e envia um arquivo.
    """
    start_time = 0.0
    total_bytes_sent = 0
    total_bytes_received = 0

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((server_host, server_port))
        start_time = time.time()

        # --- Lógica do PUT ---
        _, sent, received = handle_put(client_socket, filepath)
        total_bytes_sent += sent
        total_bytes_received += received

        # --- Lógica do QUIT ---
        network.send_message(client_socket, protocol.OP_QUIT)
        total_bytes_sent += protocol.HEADER_SIZE

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        end_time = time.time()
        client_socket.close()
        
        print("Conexao com o servidor encerrada.")
        
        if start_time > 0:
            create_log(server_host, server_port, total_bytes_sent, total_bytes_received, start_time, end_time)

if __name__ == '__main__':
    """
    Chama a função apropriada com base nos argumentos da linha de comando
    """
    
    # Caso seja interativo: python client.py <host> <porta>
    if len(sys.argv) == 3:
        server_host = sys.argv[1]
        server_port = int(sys.argv[2])
        
        start_manual(server_host, server_port)

    # Caso seja automatico: python client.py <host> <porta> put <arquivo>
    elif len(sys.argv) == 5 and sys.argv[3].lower() == 'put':
        server_host = sys.argv[1]
        server_port = int(sys.argv[2])
        filepath = sys.argv[4]

        start_automatic(server_host, server_port, filepath)
       
    # Caso de uso incorreto
    else:
        print(f"Uso interativo: python {sys.argv[0]} <host> <porta>")
        print(f"Uso automatico: python {sys.argv[0]} <host> <porta> put <arquivo>")
        sys.exit(1)