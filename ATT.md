# Observações durante a análise

Enquanto fazia o cenário 4 (latencia variavel), encontrei com um problema de concorrencia: por conta da demora no envio de informações, aconteceu de os 4 clientes terem escritos seus arquivos no servidor. Possivelmete isso ocorreu:

1. Os 4 clientes se conectam, mas cada mensagem (incluindo o PUT inicial) está agora sujeita a atrasos ou retransmissões.

2. O servidor cria uma thread para cada cliente.

3. Devido à lentidão da rede, o agendador de threads do sistema operacional tem tempo de dar a todas as 4 threads a chance de executar o início do seu código.

4. O resultado é que todas as 4 threads conseguem executar a verificação ```if os.path.exists(file_path):``` ANTES que qualquer uma delas tenha tido tempo de efetivamente criar o arquivo com o comando ```with open(file_path, 'wb') as f:```.

5. Como o arquivo ainda não foi criado por ninguém, a verificação retorna False para todas as 4 threads.

6. Com isso, todas as 4 threads recebem "sinal verde" para iniciar a transferência do arquivo.

7. Apesar disso, apenas há um arquivo dentro de ```ServerFiles```. Isso acontece pois cada cliente foi sobreescrevendo o arquivo do outro.

O engraçado é que isso não aconteceu com o cenário 4 (perda de pacotes). 