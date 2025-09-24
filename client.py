import socket
import sys
import os
import struct
import time

# --- Configurações do Cliente ---
DIR = 'LogFiles' 

# --- Definicões do Protocolo de Aplicacao ---
OP_LIST = 0
OP_PUT = 1
OP_QUIT = 2
OP_SUCCESS = 3
OP_ERROR = 4

HEADER_FORMAT = '!BI'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

def create_log(server_ip, server_port, bytes_sent, bytes_received, duration):
    """
    Cria um registro de log da conexao. 
    """
    
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    log_filename = f"{DIR}/log_cliente_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    rate_bps = (bytes_sent + bytes_received) / duration if duration > 0 else 0
    
    log_content = (
        f"--- Relatorio de Conexao ---\n"
        f"Servidor: {server_ip}:{server_port}\n"
        f"Inicio da Conexao: {time.ctime(start_time)}\n"
        f"Fim da Conexao: {time.ctime(end_time)}\n"
        f"Duracao (s): {duration:.4f}\n"
        f"Bytes Enviados: {bytes_sent}\n"
        f"Bytes Recebidos: {bytes_received}\n"
        f"Taxa de Transmissao (Bytes/s): {rate_bps:.2f}\n"
    )
    
    with open(log_filename, 'w') as f:
        f.write(log_content)
        
    print(f"Log da conexao salvo em: {log_filename}")

def main(host, port):
    """
    Funcao principal do cliente: conecta, processa comandos e interage com o servidor.
    """
    global start_time, end_time
    total_bytes_sent = 0
    total_bytes_received = 0

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Conectando ao servidor em {host}:{port}...")
        client_socket.connect((host, port))
        start_time = time.time()
        print("Conectado!")

        while True:
            command_line = input("cliente> ").strip()
            if not command_line:
                continue

            parts = command_line.split()
            command = parts[0].lower()

            if command == 'list': 
                header = struct.pack(HEADER_FORMAT, OP_LIST, 0)
                client_socket.sendall(header)
                total_bytes_sent += len(header)
                
                # Recebe a resposta
                resp_header_data = client_socket.recv(HEADER_SIZE)
                total_bytes_received += len(resp_header_data)
                op, payload_size = struct.unpack(HEADER_FORMAT, resp_header_data)
                
                resp_payload = client_socket.recv(payload_size)
                total_bytes_received += len(resp_payload)
                
                if op == OP_SUCCESS:
                    print("--- Arquivos no Servidor ---")
                    print(resp_payload.decode('utf-8'))
                else:
                    print(f"Erro do servidor: {resp_payload.decode('utf-8')}")

            elif command == 'put': 
                if len(parts) < 2:
                    print("Uso: put <caminho_do_arquivo>")
                    continue
                
                filepath = parts[1]
                if not os.path.exists(filepath):
                    print(f"ERRO: Arquivo local '{filepath}' nao encontrado.")
                    continue

                filename = os.path.basename(filepath)
                
                # 1. Envia o comando PUT com o nome do arquivo
                payload = filename.encode('utf-8')
                header = struct.pack(HEADER_FORMAT, OP_PUT, len(payload))
                client_socket.sendall(header + payload)
                total_bytes_sent += len(header) + len(payload)
                
                # 2. Aguarda a confirmacao do servidor (se pode enviar)
                resp_header_data = client_socket.recv(HEADER_SIZE)
                total_bytes_received += len(resp_header_data)
                op, _ = struct.unpack(HEADER_FORMAT, resp_header_data)
                
                if op == OP_ERROR:
                    print("Servidor recusou o PUT (arquivo pode ja existir).")
                    continue
                
                # 3. Envia o conteúdo do arquivo
                file_size = os.path.getsize(filepath)
                print(f"Enviando '{filename}' ({file_size} bytes)...")
                
                file_header = struct.pack(HEADER_FORMAT, 0, file_size) # Op é ignorado, só importa o tamanho
                client_socket.sendall(file_header)
                total_bytes_sent += len(file_header)

                with open(filepath, 'rb') as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk: break
                        client_socket.sendall(chunk)
                        total_bytes_sent += len(chunk)
                
                # 4. Recebe a confirmacao final
                final_resp_header = client_socket.recv(HEADER_SIZE)
                total_bytes_received += len(final_resp_header)
                op, payload_size = struct.unpack(HEADER_FORMAT, final_resp_header)
                
                final_payload = client_socket.recv(payload_size)
                total_bytes_received += len(final_payload)
                
                if op == OP_SUCCESS:
                    print(final_payload.decode('utf-8'))
                else:
                    print("Ocorreu um erro no servidor ao receber o arquivo.")

            elif command == 'quit': 
                header = struct.pack(HEADER_FORMAT, OP_QUIT, 0)
                client_socket.sendall(header)
                total_bytes_sent += len(header)
                break
            
            else:
                print(f"Comando desconhecido: '{command}'")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        end_time = time.time()
        client_socket.close()
        print("Conexao com o servidor encerrada.")
        duration = end_time - start_time
        create_log(host, port, total_bytes_sent, total_bytes_received, duration)


if __name__ == '__main__':
    server_host = sys.argv[1] 
    server_port = int(sys.argv[2]) 
    main(server_host, server_port)