
import sys
import logging

import create
import start
import list
import delete
import stop
import createoneserver
import info
import configure
import enlarge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

   
# Pedir al usuario que meta un argumento para que se ejecute una acción
if len(sys.argv) == 1:
    logger.info(" Debe introducir un argumento. Para visualizar las distintas opciones introduce 'info' como argumento.")

elif sys.argv[1] == "create":
    create.crearEscenario()

elif sys.argv[1] == "start":
    start.arrancar()

elif sys.argv[1] == "list":
    list.listar()

elif sys.argv[1] == "delete":
    delete.borrar()

elif sys.argv[1] == "configure": # Incluye parte opcional1 práctica 2
    configure.configurar()

# Parte opcional (práctica 1):
elif sys.argv[1] == "stop":
    stop.parar()
    
elif sys.argv[1] == "createoneserver":
    createoneserver.crearUnServidor()
    
elif sys.argv[1] == "info":
    info.informacion()

# Parte opcional2 práctica 2
elif sys.argv[1] == "enlarge":
    enlarge.enlarge()

    
