@echo off

cd src

ECHO Iniciando 4 clientes de teste...

START "Cliente 1" cmd /k "(echo put ClientFiles/arquivo200MB.bin & echo quit) | python client.py 127.0.0.1 23456"
START "Cliente 2" cmd /k "(echo put ClientFiles/arquivo200MB.bin & echo quit) | python client.py 127.0.0.1 23456"
START "Cliente 3" cmd /k "(echo put ClientFiles/arquivo200MB.bin & echo quit) | python client.py 127.0.0.1 23456"
START "Cliente 4" cmd /k "(echo put ClientFiles/arquivo200MB.bin & echo quit) | python client.py 127.0.0.1 23456"

ECHO Clientes iniciados. Eles irao fechar ao concluir a transferencia.