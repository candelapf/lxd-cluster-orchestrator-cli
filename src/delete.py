import subprocess
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def borrarServidores ():
    for i in range (5):
        nombre_servidor = "s" + str (i+1)
        
        infoS = subprocess.run(["lxc", "info", nombre_servidor], capture_output=True)
        if infoS.returncode != 0: # Si es true, el servidor no existe, entonces queremos "saltar" dicho nombre 
            continue
        
        borrarContenedor(nombre_servidor)


def borrarContenedor(contenedor):
    logger.info("Borrando el contenedor " + contenedor)
    subprocess.run(["lxc", "delete", contenedor, "--force" ])


def borrarBridges():
    for i in range(2):
        logger.info("Borrando bridge "+ str(i))
        subprocess.run(["lxc", "network", "delete", "lxdbr" + str(i)])


def borrarEscenario():
    borrarServidores()
    borrarContenedor("cl")
    borrarContenedor("lb")
    borrarContenedor("db")
    borrarBridges()


def modiHaproxycfg(servidor): # borrar la linea del webserver correspondiente
    iS = servidor[1]
    logger.info("Borrando el servidor web del fichero haproxy.cfg del balanceador.")
    subprocess.run(["lxc", "file", "pull", "lb/etc/haproxy/haproxy.cfg", "haproxy.cfg"])
    with open("haproxy.cfg", "r") as f:
        lineasTexto = f.readlines() 

    # Sobrescribimos haproxy.cfg
    with open("haproxy.cfg", "w") as f: 
        for linea in lineasTexto:
            # Si la línea no es la del servidor web que queremos borrar, la escribimos
            if "server webserver" + iS not in linea:
                f.write(linea)

    subprocess.run(["lxc", "file", "push", "haproxy.cfg", "lb/etc/haproxy/haproxy.cfg"])
    subprocess.run(["lxc", "restart", "lb"])
    logger.info("Comprobando que el fichero de configuración del lb es válido.")
    subprocess.run(["lxc", "exec", "lb", "--","haproxy", "-f", "/etc/haproxy/haproxy.cfg", "-c"])


def borrarUnServidor(servidor):
    # Leer el número actual de servidores
    try:
        with open ("num_servidores.txt", "r") as fich:
            num_servidores = int(fich.read())
    except FileNotFoundError: # Error si no encuentra el fichero
        num_servidores = 0
        
    # Borrar el servidor
    borrarContenedor(servidor)
    
    # Restar -1 al fichero numero_servidores.txt
    num_actualizado = num_servidores - 1
    with open ("num_servidores.txt", "w") as fich:
        fich.write(str(num_actualizado))

    # borre el webserver de haproxy.cfg
    modiHaproxycfg(servidor)
        
    
def borrar():
    if len(sys.argv) == 3:  
        servidor_borrar = sys.argv[2]
        # Comprobar que el argumento sea un servidor (s + int)
        try: 
            if servidor_borrar[0] == "s" and type(int(servidor_borrar[1])) == int :
                borrarUnServidor(servidor_borrar)
            else:
                logger.info("Solamente puedes borrar de forma individual servidores. La sintaxis es del tipo: s + número.") 
        except ValueError:
            logger.error("Solamente puedes borrar de forma individual servidores. La sintaxis es del tipo: s + número.")
                 
    else:
        borrarEscenario()

