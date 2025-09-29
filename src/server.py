import socket
import threading
import os
import struct
import protocol
import network

# --- Configurações do Servidor ---
HOST = '0.0.0.0'
PORT = 23456
DIR = 'ServerFiles'

# --- Semaforo ---
file_system_semaphore = threading.Semaphore(1)

# --- Lógica Principal do Servidor ---
def handle_put(addr, conn, payload):
    """
    Gerencia o recebimento de arquivos enviados pelos clientes.
    """
    with file_system_semaphore:
        filename = payload.decode('utf-8')
        print(f"[OP: PUT] | Pedido para o arquivo '{filename}' de {addr}")
                    
        file_path = os.path.join(DIR, os.path.basename(filename))
        if os.path.exists(file_path):
            error_msg = f"ERRO: Arquivo '{filename}' ja existe.".encode('utf-8')
            network.send_message(conn, protocol.OP_ERROR, error_msg)
            return

        # Envia confirmação para o cliente iniciar o envio do arquivo
        network.send_message(conn, protocol.OP_SUCCESS)
    
    # Recebe o cabeçalho especial com o tamanho do arquivo
    header_data = conn.recv(protocol.HEADER_SIZE)
    if not header_data: return "BREAK"
                
    # Desempacota o cabeçalho para obter o tamanho do arquivo, ignorando a operação
    _, file_size = struct.unpack(protocol.HEADER_FORMAT, header_data)
                
    # Recebe o conteúdo do arquivo
    with open(file_path, 'wb') as f:
        bytes_received = 0
                    
        while bytes_received < file_size:
            chunk = conn.recv(4096)
            if not chunk: return "BREAK"
            f.write(chunk)
            bytes_received += len(chunk)
            
    with file_system_semaphore:
        print(f"Arquivo '{filename}' ({file_size} bytes) recebido de {addr}.")
        network.send_message(conn, protocol.OP_SUCCESS, "Arquivo recebido com sucesso!".encode('utf-8'))

def handle_list(addr, conn):
    """
    Gerencia o comando LIST, enviando a lista de arquivos no diretório do servidor.
    """
    print(f"[OP: LIST] | Recebido de {addr}")
                
    with file_system_semaphore:
        try:
            files = os.listdir(DIR)
            file_list_str = "\n".join(files) if files else "Nenhum arquivo no servidor."
            network.send_message(conn, protocol.OP_SUCCESS, file_list_str.encode('utf-8'))
        except Exception as e:
            error_msg = f"Erro ao listar arquivos: {e}".encode('utf-8')
            network.send_message(conn, protocol.OP_ERROR, error_msg)
    
def handle_client(conn, addr):
    """
    Gerencia a conexão com um único cliente usando as funções auxiliares.
    """
    print(f"[NOVA CONEXAO] | {addr} conectado.")

    try:
        while True:
            operation, payload = network.receive_message(conn)

            # Cliente desconectou
            if operation is None: break

            if operation == protocol.OP_LIST:
                handle_list(addr, conn)

            elif operation == protocol.OP_PUT:
                status = handle_put(addr, conn, payload)
                if status == "BREAK": break

            elif operation == protocol.OP_QUIT:
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