import socket
import threading
import os
import struct

# --- Configurações do Servidor ---
HOST = '0.0.0.0'
PORT = 23456
DIR = 'ServerFiles'

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
    """
    Encapsula a lógica de criar um cabeçalho, empacotá-lo e enviar
    a mensagem completa (cabeçalho + payload) através do socket.
    """
    header = struct.pack(HEADER_FORMAT, operation, len(payload))
    sock.sendall(header + payload)

def receive_message(sock):
    """
    Encapsula a lógica de receber e desempacotar uma mensagem completa.
    Primeiro lê o cabeçalho de tamanho fixo para descobrir o tamanho do payload 
    e depois lê o payload por completo.
    Retorna a operação e o payload, ou (None, None) se a conexão for fechada.
    """
    
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

# --- Lógica Principal do Servidor ---
def handle_client(conn, addr):
    """
    Gerencia a conexão com um único cliente usando as funções auxiliares.
    O loop principal agora é muito mais legível.
    """
    print(f"[NOVA CONEXAO] | {addr} conectado.")

    try:
        while True:
            operation, payload = receive_message(conn)

            if operation is None: # Cliente desconectou
                break

            if operation == OP_LIST:
                print(f"[OP: LIST] | Recebido de {addr}")
                try:
                    files = os.listdir(DIR)
                    file_list_str = "\n".join(files) if files else "Nenhum arquivo no servidor."
                    send_message(conn, OP_SUCCESS, file_list_str.encode('utf-8'))
                except Exception as e:
                    error_msg = f"Erro ao listar arquivos: {e}".encode('utf-8')
                    send_message(conn, OP_ERROR, error_msg)

            elif operation == OP_PUT:
                filename = payload.decode('utf-8')
                print(f"[OP: PUT] | Pedido para o arquivo '{filename}' de {addr}")
                file_path = os.path.join(DIR, os.path.basename(filename))

                if os.path.exists(file_path):
                    error_msg = f"ERRO: Arquivo '{filename}' ja existe.".encode('utf-8')
                    send_message(conn, OP_ERROR, error_msg)
                    continue

                send_message(conn, OP_SUCCESS) # Confirma que pode receber

                header_data = conn.recv(HEADER_SIZE)
                if not header_data: break
                
                # Desempacota o cabeçalho para obter o tamanho do arquivo.
                # O código de operação (primeiro byte) é ignorado aqui.
                _, file_size = struct.unpack(HEADER_FORMAT, header_data)
                
                # Recebe o conteúdo do arquivo
                with open(file_path, 'wb') as f:
                    bytes_received = 0
                    while bytes_received < file_size:
                        chunk = conn.recv(4096)
                        if not chunk: break
                        f.write(chunk)
                        bytes_received += len(chunk)

                print(f"Arquivo '{filename}' ({file_size} bytes) recebido de {addr}.")
                send_message(conn, OP_SUCCESS, "Arquivo recebido com sucesso!".encode('utf-8'))

            elif operation == OP_QUIT:
                print(f"[OP: QUIT] | Recebido de {addr}. Encerrando conexao.")
                break

    except ConnectionError as e:
        print(f"[AVISO] | {e} | Cliente: {addr}")
    except Exception as e:
        print(f"[ERRO] | Erro com o cliente {addr}: {e}")
    finally:
        conn.close()
        print(f"[CONEXAO FECHADA] | {addr}")

def start():
    """
    Inicia o servidor, escuta por conexoes e cria threads para os clientes.
    """
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[ESCUTANDO] | Servidor | {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
    finally:
        server_socket.close()

if __name__ == '__main__':
    start()