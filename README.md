# Aplicação Cliente/Servidor de Transferência de Arquivos

Este projeto implementa um sistema simples de transferência de arquivos usando sockets TCP em Python. O servidor é capaz de lidar com múltiplos clientes de forma concorrente, e o cliente fornece uma interface de linha de comando para interagir com o servidor.

## Estrutura dos Arquivos

O projeto utiliza a seguinte estrutura de diretórios para organizar os arquivos do cliente, do servidor e os logs de execução.

```
├── ClientFiles/          # Diretório para armazenar os arquivos a serem enviados pelo cliente
│   └── arquivo200MB.bin
├── LogFiles/             # Diretório criado pelo cliente para salvar os logs de conexão
│   └── log_cliente_...
├── ServerFiles/          # Diretório criado pelo servidor para armazenar arquivos recebidos
│   └── arquivo200MB.bin
├── client.py            # Script do cliente
└── server.py           # Script do servidor concorrente
```

## Pré-requisitos

* **Python 3.x**

Não são necessárias bibliotecas externas para a execução do projeto.

## Como Executar a Aplicação

Siga estes passos para configurar o ambiente e executar o sistema.

### Passo 1: Preparação do Ambiente

1.  **Crie um arquivo de teste dentro de `ClientFiles`:**
    * **No Windows (Prompt de Comando):**
        ```cmd
        cd ClientFiles
        fsutil file createnew arquivo200MB.bin 200000000
        ```
    * **No Linux ou macOS:**
        ```bash
        dd if=/dev/urandom of=ClientFiles/arquivo200MB.bin bs=1M count=191
        ```

### Passo 2: Iniciar o Servidor

1.  Abra um terminal no diretório src do projeto.
2.  Execute o seguinte comando para iniciar o servidor:
    ```bash
    python server.py
    ```
3.  O servidor ficará ativo e aguardando conexões na porta configurada:
    ```
    [ESCUTANDO] | Servidor | 0.0.0.0:23456
    ```

### Passo 3: Iniciar e Usar o Cliente

1.  Abra um **novo terminal** no diretório src do projeto.
2.  Execute `cliente.py` informando o IP e a porta do servidor. Para uma conexão local, use `127.0.0.1`.
    ```bash
    python client.py 127.0.0.1 23456
    ```
3.  O cliente se conectará e exibirá um prompt para receber comandos:
    ```
    Conectando ao servidor em 127.0.0.1:23456...
    Conectado!
    cliente>
    ```

---

## Comandos Disponíveis no Cliente

### `list`

Lista todos os arquivos armazenados no diretório `ServerFiles` do servidor.

* **Uso:**
    ```
    cliente> list
    ```

### `put <caminho_do_arquivo>`

Envia um arquivo do cliente para o servidor. **Lembre-se de incluir o diretório `ClientFiles` no caminho do arquivo.**

* **Uso:**
    ```
    cliente> put ClientFiles/arquivo200MB.bin
    ```

### `quit`

Encerra a conexão com o servidor e gera um arquivo de log da sessão no diretório `LogFiles`.

* **Uso:**
    ```
    cliente> quit
    ```

## Geração de Logs

Ao encerrar uma sessão com o comando `quit`, um arquivo de log é criado automaticamente na pasta `LogFiles`. Este arquivo registra as estatísticas da conexão, como duração, bytes transferidos e taxa de transmissão.

## Testando Concorrência

Para testar o atendimento concorrente do servidor, execute o arquivo `clientes_concorrentes.bat`.