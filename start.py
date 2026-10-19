import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def arrancarContenedor(contenedor):
    logger.info("Arrancando el contenedor "+ contenedor)
    subprocess.run(["lxc", "start", contenedor ])


def arrancarServidores():
    for i in range (5):
        nombre_servidor = "s" + str (i+1)
        
        infoS = subprocess.run(["lxc", "info", nombre_servidor], capture_output=True)
        if infoS.returncode != 0: # Si es true, el servidor no existe, entonces queremos "saltar" dicho nombre (lo hacemos por si hay huecos creados con borrarUnServidor de delete.py)
            continue
        
        arrancarContenedor(nombre_servidor)
        # Mostrar consola de los servidores
        mostrarConsola(nombre_servidor)


def mostrarConsola(contenedor):
    orden = "lxc exec " + contenedor + " bash"
    subprocess.Popen(["xterm", "-fa", "monaco", "-fs", "13", "-bg", "black", "-fg", "green", "-e", orden])


def arrancarEscenario():
    arrancarServidores()
    
    arrancarContenedor("cl")
    mostrarConsola("cl")
    
    arrancarContenedor("lb")
    mostrarConsola("lb")

    arrancarContenedor("db")
    mostrarConsola("db")


def arrancar():
    if len(sys.argv) == 3:
        contenedor_arrancar = sys.argv[2]
        arrancarContenedor(contenedor_arrancar)
        mostrarConsola(contenedor_arrancar)
    else:
        arrancarEscenario()
        
        
