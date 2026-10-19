import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def pararServidores ():
    for i in range (5):
        nombre_servidor = "s" + str (i+1)
        
        infoS = subprocess.run(["lxc", "info", nombre_servidor], capture_output=True)
        if infoS.returncode != 0: # Si es true, el servidor no existe, entonces queremos "saltar" dicho nombre (lo hacemos por si hay huecos creados con borrarUnServidor de delete.py)
            continue
        
        pararContenedor(nombre_servidor)
    

def pararContenedor(contenedor):
    logger.info("Parando el contenedor "+ contenedor)
    subprocess.run(["lxc", "stop", contenedor, "--force"])


def pararEscenario():
    pararServidores()
    pararContenedor("cl")
    pararContenedor("lb")
    pararContenedor("db")


def parar():
    if len(sys.argv) == 3:
        contenedor_parar = sys.argv[2]
        pararContenedor(contenedor_parar)
    else:
        pararEscenario()
