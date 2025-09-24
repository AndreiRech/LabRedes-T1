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

HEADER_FORMAT = '!BI'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

def handle_client(conn, addr):
    """
    Funcao executada por cada thread para gerenciar um cliente conectado.
    """
    print(f"[NOVA CONEXAO] | {addr} conectado.")

    try:
        while True:
            # 1. Receber o cabeçalho da mensagem
            header_data = conn.recv(HEADER_SIZE)
            if not header_data:
                break

            # 2. Desempacotar o cabeçalho para obter a operação e o tamanho do payload 
            operation, payload_size = struct.unpack(HEADER_FORMAT, header_data)

            # 3. Receber o payload, se houver
            payload = b''
            if payload_size > 0:
                payload = conn.recv(payload_size)

            # 4. Verificar a operação
            if operation == OP_LIST:
                print(f"[OP: LIST] | Recebido de {addr}")
                
                try:
                    files = os.listdir(DIR)
                    file_list_str = "\n".join(files)
                    
                    if not file_list_str:
                        file_list_str = "Nenhum arquivo no servidor."
                    
                    response_payload = file_list_str.encode('utf-8')
                    response_header = struct.pack(HEADER_FORMAT, OP_SUCCESS, len(response_payload))
                    conn.sendall(response_header + response_payload)
                    
                except Exception as e:
                    error_msg = f"Erro ao listar arquivos: {e}".encode('utf-8')
                    error_header = struct.pack(HEADER_FORMAT, OP_ERROR, len(error_msg))
                    conn.sendall(error_header + error_msg)

            elif operation == OP_PUT:
                filename = payload.decode('utf-8')
                print(f"[OP: PUT] | Recebido pedido para o arquivo '{filename}' de {addr}")

                file_path = os.path.join(DIR, os.path.basename(filename))

                # Verifica se o arquivo já existe
                if os.path.exists(file_path):
                    error_msg = f"ERRO: Arquivo '{filename}' ja existe no servidor.".encode('utf-8')
                    error_header = struct.pack(HEADER_FORMAT, OP_ERROR, len(error_msg))
                    conn.sendall(error_header + error_msg)
                    continue

                success_header = struct.pack(HEADER_FORMAT, OP_SUCCESS, 0)
                conn.sendall(success_header)

                file_header_data = conn.recv(HEADER_SIZE)
                if not file_header_data: break
                _, file_size = struct.unpack(HEADER_FORMAT, file_header_data)

                with open(file_path, 'wb') as f:
                    bytes_received = 0
                    while bytes_received < file_size:
                        chunk = conn.recv(4096)
                        if not chunk: break
                        f.write(chunk)
                        bytes_received += len(chunk)
                
                print(f"Arquivo '{filename}' recebido com sucesso de {addr}.")
                
                final_msg = "Arquivo recebido com sucesso!".encode('utf-8')
                final_header = struct.pack(HEADER_FORMAT, OP_SUCCESS, len(final_msg))
                conn.sendall(final_header + final_msg)

            elif operation == OP_QUIT:
                print(f"[OP: QUIT] | Recebido de {addr}. Encerrando conexao.")
                break
                
    except Exception as e:
        print(f"[ERRO] | Erro com o cliente {addr}: {e}")
    finally:
        conn.close()
        print(f"[CONEXAO FECHADA] | {addr}")

def start():
    """
    Inicia o servidor, escuta por conexoes e cria threads para os clientes.
    """
    # Cria o diretório se não existir
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    # Configuração do socket do servidor
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    
    print(f"[ESCUTANDO] | Servidor | {HOST}:{PORT}")

    while True:
        conn, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.daemon = True
        thread.start()

if __name__ == '__main__':
    start()