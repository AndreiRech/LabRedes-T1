import socket
import sys
import os
import struct
import time
import datetime
import random

# --- Configurações do Cliente ---
DIR = 'LogFiles'

# --- Definições do Protocolo de Aplicação ---
OP_LIST = 0
OP_PUT = 1
OP_QUIT = 2
OP_SUCCESS = 3
OP_ERROR = 4

# --- Estrutura do Cabeçalho ---
HEADER_FORMAT = '!BI'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# --- Funções Auxiliares de Comunicação ---
def send_message(sock, operation, payload=b''):
    header = struct.pack(HEADER_FORMAT, operation, len(payload))
    sock.sendall(header + payload)

def receive_message(sock):
    header_data = sock.recv(HEADER_SIZE)
    if not header_data:
        return None, None
    operation, payload_size = struct.unpack(HEADER_FORMAT, header_data)
    payload = b''
    if payload_size > 0:
        chunks = []
        bytes_received = 0
        while bytes_received < payload_size:
            chunk = sock.recv(min(payload_size - bytes_received, 4096))
            if not chunk:
                raise ConnectionError("Conexão perdida ao receber o payload.")
            chunks.append(chunk)
            bytes_received += len(chunk)
        payload = b"".join(chunks)
    return operation, payload

# --- Funções do Cliente ---
def handle_put_command(sock, filepath):
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
    send_message(sock, OP_PUT, filename.encode('utf-8'))
    bytes_sent += HEADER_SIZE + len(filename.encode('utf-8'))
    
    # Passo 2: Aguarda a confirmação do servidor
    op, payload = receive_message(sock)
    bytes_received += HEADER_SIZE + len(payload)

    if op == OP_ERROR:
        print(f"Servidor recusou o PUT: {payload.decode('utf-8')}")
        return False, bytes_sent, bytes_received

    if op != OP_SUCCESS:
        print("Erro: Resposta inesperada do servidor.")
        return False, bytes_sent, bytes_received

    # Passo 3: Envia o conteúdo do arquivo
    file_size = os.path.getsize(filepath)
    print(f"Enviando '{filename}' ({file_size} bytes)...")
    
    # Envia o cabeçalho especial com o tamanho do arquivo
    file_header = struct.pack(HEADER_FORMAT, 0, file_size)
    sock.sendall(file_header)
    bytes_sent += len(file_header)

    with open(filepath, 'rb') as f:
        while chunk := f.read(4096):
            sock.sendall(chunk)
            bytes_sent += len(chunk)

    # Passo 4: Recebe a confirmação final
    op_final, payload_final = receive_message(sock)
    bytes_received += HEADER_SIZE + len(payload_final)
    
    if op_final == OP_SUCCESS:
        print(payload_final.decode('utf-8'))
        return True, bytes_sent, bytes_received
    else:
        print("Ocorreu um erro no servidor ao receber o arquivo.")
        return False, bytes_sent, bytes_received

def create_log(server_ip, server_port, bytes_sent, bytes_received, start_time, end_time):
    if not os.path.exists(DIR):
        os.makedirs(DIR)
        
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    random_suffix = random.randint(10000, 99999)
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

def main(host, port):
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
            command_line = input("cliente> ").strip()
            if not command_line:
                continue

            parts = command_line.split()
            command = parts[0].lower()

            if command == 'list':
                send_message(client_socket, OP_LIST)
                total_bytes_sent += HEADER_SIZE
                op, payload = receive_message(client_socket)
                total_bytes_received += HEADER_SIZE + len(payload)
                if op == OP_SUCCESS:
                    print("--- Arquivos no Servidor ---\n" + payload.decode('utf-8'))
                else:
                    print(f"Erro do servidor: {payload.decode('utf-8')}")

            elif command == 'put':
                if len(parts) < 2:
                    print("Uso: put <caminho_do_arquivo>")
                    continue
                
                filepath = parts[1]
                _, sent, received = handle_put_command(client_socket, filepath)
                total_bytes_sent += sent
                total_bytes_received += received

            elif command == 'quit':
                send_message(client_socket, OP_QUIT)
                total_bytes_sent += HEADER_SIZE
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

if __name__ == '__main__':
    if len(sys.argv) == 3:
        server_host = sys.argv[1]
        server_port = int(sys.argv[2])
        main(server_host, server_port)

    elif len(sys.argv) == 5 and sys.argv[3].lower() == 'put':
        server_host = sys.argv[1]
        server_port = int(sys.argv[2])
        filepath = sys.argv[4]

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        start_time = 0.0
        total_bytes_sent = 0
        total_bytes_received = 0

        try:
            client_socket.connect((server_host, server_port))
            start_time = time.time()

            # --- Lógica do PUT agora usa a função modular ---
            _, sent, received = handle_put_command(client_socket, filepath)
            total_bytes_sent += sent
            total_bytes_received += received

            # --- Lógica do QUIT ---
            send_message(client_socket, OP_QUIT)
            total_bytes_sent += HEADER_SIZE

        except Exception as e:
            print(f"Ocorreu um erro: {e}")
        finally:
            end_time = time.time()
            client_socket.close()
            if start_time > 0:
                create_log(server_host, server_port, total_bytes_sent, total_bytes_received, start_time, end_time)
                print("Log criado. Conexao encerrada.")
    else:
        print(f"Uso interativo: python {sys.argv[0]} <host> <porta>")
        print(f"Uso automatico: python {sys.argv[0]} <host> <porta> put <arquivo>")
        sys.exit(1)