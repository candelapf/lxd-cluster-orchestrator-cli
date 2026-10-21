import subprocess
import sys
import logging
import time

import direccionesIP

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Imagen a importar
path_imagen = "/mnt/vnx/repo/arso/ubuntu2004.tar.gz" 


def comprobarNumeroS():
    if len(sys.argv) == 3:
        numero_servidores = int(sys.argv[2])

        # Lanzar excepción si el número de servidores no entra en el rango 1-5
        if  not (1 <= numero_servidores <= 5):
            logger.info("Error: El número de servidores debe estar entre 1 y 5")
            sys.exit() # Salir de la función


def crear(elemento, nombreI): #Sirve tanto para crear (y configurar) los bridges como los contenedores.
    if elemento in ["lxdbr0", "lxdbr1"]:
        if elemento == "lxdbr0":
            orden = "set"
            dir_subred = direccionesIP.dir_bridge0
        else: #si no es lxdbr0, por descarte es lxdbr1
            orden = "create"
            dir_subred = direccionesIP.dir_bridge1
        subprocess.run(["lxc", "network", orden, elemento,"ipv6.address=none", "ipv6.nat=false", "ipv4.address=" +dir_subred, "ipv4.nat=true", "dns.domain=lxd", "dns.mode=none"])
    else:
        subprocess.run(["lxc", "init", nombreI, elemento])

        
def crearServidores(nombreI):
    numero_servidores = 2 # Si el usuario no pasa un parámetro por defecto son 2
    logger.info("Los argumentos introducidos son: " + str(len(sys.argv)))
    if len(sys.argv) == 3: # Si el usuario pasa parámetro (longitud 3: pfinal1 create.py 5)
        numero_servidores = int(sys.argv[2])
    
    for i in range(numero_servidores):
        nombre_servidor = "s" + str(i+1)
        crear(nombre_servidor, nombreI)

    # Guardar el número de servidores creados en un fichero para que 'start' o 'delete' sepan cuántos hay
    with open("num_servidores.txt", "w") as f:
        f.write(str(numero_servidores))

    return numero_servidores


def attachToBridge(bridge,contenedor,eth):
    subprocess.run(["lxc", "network", "attach", bridge, contenedor, eth])

def configurarIp(contenedor,eth,ip):
    subprocess.run(["lxc", "config", "device", "set", contenedor, eth, "ipv4.address", ip])


def configurar(contenedor): # Lo usamos para configurar el cliente, el balanceador, y la bd.
    logger.info("Configurando las conexiones del contenedor "+ contenedor)
    
    if contenedor == "cl":
        attachToBridge("lxdbr1", contenedor, "eth0")
    elif contenedor == "lb":
        attachToBridge("lxdbr0", contenedor, "eth0")
        configurarIp(contenedor, "eth0", direccionesIP.dir_lb_0)
        attachToBridge("lxdbr1", contenedor, "eth1")
        configurarIp(contenedor, "eth1", direccionesIP.dir_lb_1)
    elif contenedor == "db":
        attachToBridge("lxdbr0", contenedor, "eth0")
        configurarIp(contenedor, "eth0", direccionesIP.dir_db)
    

def configurarServidores(num_servidores):
    for i in range(num_servidores):
        nombreS = "s" + str(i+1)  # Empiece a escribir en 1 (s1)
        logger.info("Configurando las conexiones del servidor "+ nombreS)
        
        ipS = direccionesIP.dir_ip_subred0 + str(i+11)

        attachToBridge("lxdbr0", nombreS, "eth0")
        configurarIp(nombreS, "eth0", ipS)


def configurarBalanceador():
    configurar("lb")

    # Modificar el fichero en el SO del LB 
    subprocess.run(["lxc", "start", "lb" ]) # Debe de estar activo para editar el fichero
    eth1_in = False
    while not eth1_in:
        time.sleep(3)
        subprocess.run(["lxc", "file", "push", "50-cloud-init.yaml", "lb/etc/netplan/50-cloud-init.yaml"])
        time.sleep(2)
        respuesta = subprocess.run(["lxc", "exec", "lb", "--", "cat", "/etc/netplan/50-cloud-init.yaml"], stdout=subprocess.PIPE)
        eth1_in = "eth1" in respuesta.stdout.decode("utf-8")
    
    subprocess.run(["lxc", "stop", "lb", "--force" ]) # lo volvemos a parar para que lo arranque el módulo start


def crearImagen(nombre_imagen, path):
        subprocess.run(["lxc", "image", "import", path, "--alias", nombre_imagen ])
        return nombre_imagen

def crearEscenario():
    # Comprobar primero si el número introducido es válido
    comprobarNumeroS()
    
    # Creamos la imagen. 
    nombreI = crearImagen("ubuntu2004", path_imagen) 
    
    # Crear elementos
    crear("lxdbr0", nombreI)
    crear("lxdbr1", nombreI)   
    crear("cl", nombreI)
    crear("lb", nombreI)
    crear("db", nombreI)   
    # Crear los N servidores
    num_servidores = crearServidores(nombreI)

    # Configurar servidores
    configurarServidores(num_servidores)
    # Configurar resto de contenedores
    configurar("cl")
    configurar("db")
    # Configurar balanceador
    configurarBalanceador()
    

    # Logs para mostrar conexiones a los bridges
    configuracionBridge0 = subprocess.run(["lxc", "network", "show", "lxdbr0"], stdout=subprocess.PIPE)
    logger.debug("Las caracteristicas del bridge 0 son: " + configuracionBridge0.stdout.decode("utf-8")) # Al usar stdout debemos poner el metodo decode.

    configuracionBridge1 = subprocess.run(["lxc", "network", "show", "lxdbr1"], stdout=subprocess.PIPE)
    logger.debug("Las caracteristicas del bridge 1 son: " + configuracionBridge1.stdout.decode("utf-8"))

    




