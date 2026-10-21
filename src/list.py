import subprocess
import logging
import sys 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def listarInfoServidores ():
    for i in range (5):
        nombre_servidor = "s" + str (i+1)
        
        infoS = subprocess.run(["lxc", "info", nombre_servidor], capture_output=True)
        if infoS.returncode != 0: # Si es true, el servidor no existe, entonces queremos "saltar" dicho nombre (lo hacemos por si hay huecos creados con borrarUnServidor de delete.py)
            continue
        
        listarContenedor(nombre_servidor)


def listarContenedor(contenedor):
    logger.info("La información del contenedor " + contenedor + " es: ")
    subprocess.run(["lxc", "info", contenedor ])


def listarContenedores():
    listarInfoServidores()
    listarContenedor("cl")
    listarContenedor("lb")
    listarContenedor("db")


def listar():
    if len(sys.argv) == 3: # Si hay argumento listar la info solo de ese contenedor
        contenedor_listar = sys.argv[2]
        listarContenedor(contenedor_listar)
    else:
        listarContenedores()
    
