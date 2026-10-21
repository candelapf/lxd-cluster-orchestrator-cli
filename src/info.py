import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def informacion():
    if len(sys.argv) == 2:
        logger.info(" Puedes introducir como argumento: create, start, list, delete, configure, stop, createoneserver, enlarge. "
        "Si deseas obtener más información sobre la funcionalidad de cada argumento escribe: 'info' + <argumento>")
    
    elif sys.argv[2] == "create":
        logger.info(" 'create' crea y despliega el escenario: 2 bridges, un cliente, un balanceador, una base de datos y de 1 a 5 servidores. "
        "El número de servidores a crear puedes introducirlo como argumento tras el 'create'. En caso de no introducir un número, se crearán 2 servidores.")
    
    elif sys.argv[2] == "start":
        logger.info(" 'start' arranca el escenario previamente desplegado. " 
        "Si desea arrancar únicamente un contenedor, escribe el nombre del contenedor a arrancar como argumento tras el 'start'.")
        
    elif sys.argv[2] == "list":
        logger.info(" 'list' lista la información de los contenedores existentes. " 
        "Si desea consultar la información de un solo contenedor, escribe el nombre del contenedor como argumento tras el 'list'.")
        
    elif sys.argv[2] == "delete":
        logger.info(" 'delete' destruye el escenario. Si desea borrar solo uno de los servidores, introduce el nombre del servidor a borrar como argumento tras el 'delete'.")
        
    elif sys.argv[2] == "stop":
        logger.info(" 'stop' para los contenedores. Si desea parar solo uno de los contenedores, introduce el nombre del contenedor a parar como argumento tras el 'stop'.")
        
    elif sys.argv[2] == "createoneserver":
        logger.info(" 'createoneserver' crea servidores individualmente. Recuerda que se pueden crear un máximo de 5 servidores.")

    elif sys.argv[2] == "configure":
        logger.info(" 'configure' desarrolla el escenario proporcionando servidores web que tienen acceso a la aplicación de Gestión Hospitalaria. "
        "Instala y configura los contenedores del escenario previamente desplegado. "
        "Puede elegir si desea configurar la bd localmente o remotamente, introduciendo además los argumentos 'local' o 'remote'")
    
    elif sys.argv[2] == "enlarge":
        logger.info(" 'enlarge' crea servidores web individualmente, y los configura debidamente para que se conecten con la bd. Recuerda que se pueden crear un máximo de 5 servidores.")