import struct

# --- Definições do Protocolo de Aplicação ---
OP_LIST = 0
OP_PUT = 1
OP_QUIT = 2
OP_SUCCESS = 3
OP_ERROR = 4

# --- Estrutura do Cabeçalho ---
# !BI = 1 byte (operação) + 4 bytes (tamanho do payload)
HEADER_FORMAT = '!BI'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)