import struct
import protocol

# --- Funções Auxiliares de Comunicação ---
def send_message(sock, operation, payload=b''):
    """
    Encapsula a lógica de criar um cabeçalho, empacotá-lo e enviar
    a mensagem completa (cabeçalho + payload) através do socket.
    """
    header = struct.pack(protocol.HEADER_FORMAT, operation, len(payload))
    sock.sendall(header + payload)

def receive_message(sock):
    """
    Encapsula a lógica de receber e desempacotar uma mensagem completa.
    Primeiro lê o cabeçalho de tamanho fixo para descobrir o tamanho do payload 
    e depois lê o payload por completo.
    Retorna a operação e o payload, ou (None, None) se a conexão for fechada.
    """
    
    header_data = sock.recv(protocol.HEADER_SIZE)
    if not header_data: return None, None

    operation, payload_size = struct.unpack(protocol.HEADER_FORMAT, header_data)

    # Realiza a leitura do payload em pedaços para não sobrecarregar a memória
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