import subprocess
import logging
import sys
import time
from pathlib import Path

import direccionesIP
import delete
import create
import stop
import start

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nombreImgCreada = "ubuntu2004"


# FUNCIONES ESPECÍFICAS

# Instalación y configuración de la BD:
def instalarDB(tipo_despliegue):
    if tipo_despliegue == "local":
        orden = "db"
    elif tipo_despliegue == "remoto":
        orden = "remoto:db"
    
    logger.info("Instalando MongoDB en la base de datos.")
    subprocess.run(["lxc", "exec", orden, "--", "apt", "update"])
    subprocess.run(["lxc", "exec", orden, "--", "apt", "install", "-y", "mongodb"])


def configurarDB(tipo_despliegue): #NOTA: puedo comprobar que ha escrito la dir_BD en el fichero haciendo "lxc exec db -- nano /etc/mongodb.conf" 
    if tipo_despliegue == "local":
        orden = "db"   
    elif tipo_despliegue == "remoto":
        orden = "remoto:db"

    dir_BD = direccionesIP.dir_db 
    logger.info("Configurando MongoDB en la base de datos.")
    subprocess.run(["lxc", "file", "pull", orden+"/etc/mongodb.conf", "mongodb.conf"])

    with open("mongodb.conf", "r") as f: # Añade la dirección del contenedor db en el fichero mongodb.conf
        texto = f.read()
    with open("mongodb.conf", "w") as f:
        texto = texto.replace("bind_ip = 127.0.0.1", "bind_ip = 127.0.0.1,"+dir_BD)
        f.write(texto)

    subprocess.run(["lxc", "file", "push", "mongodb.conf", orden+"/etc/mongodb.conf"])
    subprocess.run(["lxc", "restart", orden])
    time.sleep(5)


# Instalación y configuración de los SERVIDORES:
def hallarPrimerSerE(): # Hallamos el primer servidor existente, al que instalaremos y configuraremos los ficheros.
    for i in range (5):
        servidor = "s" + str (i+1)
        
        infoS = subprocess.run(["lxc", "info", servidor], capture_output=True)
        if infoS.returncode != 0: # Si es true, el servidor no existe, entonces queremos "saltar" dicho nombre (lo hacemos por si hay huecos creados con borrarUnServidor de delete.py)
            continue
        break
    return servidor


def configurarServidorInicial(dir_BD): # Dirección de la BD como parámetro: local meter dir_db y en remoto IP_B
    # Vamos a configurar solo el PRIMERO EXISTENTE
    servidor = hallarPrimerSerE()

    logger.info("Instalando la aplicación del Gestor Hospitalario en el servidor "+ servidor)
    subprocess.run(["lxc", "file", "push", "install.sh", servidor+"/root/install.sh"])
    subprocess.run(["lxc", "exec", servidor, "--", "chmod", "+x", "install.sh"])
    subprocess.run(["lxc", "file", "push", "-r", "app.tar.gz", servidor+"/root/"])
    subprocess.run(["lxc", "exec", servidor, "--", "tar", "-oxvf", "app.tar.gz"])

    # Cambiamos la IP de MongoDB en: 'rest_server.js' de la aplicación para que sea la de nuestra BD: 134.3.0.20 o IP_B:
    logger.info("La dirección donde está nuestra base de datos es: "+ dir_BD)
    subprocess.run(["lxc", "file", "pull", servidor+"/root/app/rest_server.js", "rest_server.js"])
    with open("rest_server.js", "r") as f:
        texto = f.read()
    with open("rest_server.js", "w") as f:
        texto = texto.replace("10.0.0.20",dir_BD+":27017") 
        f.write(texto)
    subprocess.run(["lxc", "file", "push", "rest_server.js", servidor+"/root/app/rest_server.js"])

    #Cambiamos la IP de MongoDB en: 'md-seed-config.js' de la aplicación para que sea la de nuestra BD: 134.3.0.20 o IP_B:
    subprocess.run(["lxc", "file", "pull", servidor+"/root/app/md-seed-config.js", "md-seed-config.js"])
    with open("md-seed-config.js", "r") as f:
        texto = f.read()
    with open("md-seed-config.js", "w") as f:
        texto = texto.replace("10.0.0.20:27017",dir_BD+":27017")
        f.write(texto)
    subprocess.run(["lxc", "file", "push", "md-seed-config.js", servidor+"/root/app/md-seed-config.js"])

    subprocess.run(["lxc", "exec", servidor, "--", "./install.sh"]) # Instala NodeJS y Puebla la BD (ejecutar el install.sh)
    subprocess.run(["lxc", "restart", servidor])
    time.sleep(10)
    
    # Creamos una imagen a partir de este servidor configurado: la llamaremos imagenSC
    stop.pararContenedor(servidor)
    logger.info("Creando una imagen a partir del servidor "+ servidor)
    subprocess.run(["lxc", "publish", servidor, "--alias", "imagenSC"])
    start.arrancarContenedor(servidor)
    subprocess.run(["lxc", "exec", servidor, "--", "forever", "start", "app/rest_server.js"])

    return servidor


def configurarConImagen(nombre_servidor): 
    i = int(nombre_servidor[1]) # conseguir qué numero de servidor estoy creando 
    
    create.crear(nombre_servidor, "imagenSC")
    create.attachToBridge("lxdbr0", nombre_servidor, "eth0")
    ipS = direccionesIP.dir_ip_subred0 + str(i+10)
    create.configurarIp(nombre_servidor, "eth0", ipS)
    start.arrancarContenedor(nombre_servidor) 
    subprocess.run(["lxc", "exec", nombre_servidor, "--", "forever", "start", "app/rest_server.js"])
   

def configurarServidores(servidorConfigurado): # Crear a partir de imagenSC el resto de servidores existentes.
    iSC = int(servidorConfigurado[1])
    for i in range (iSC, 5):
        nombre_servidor = "s" + str (i+1)
        # Mira si el servidor existe
        infoS = subprocess.run(["lxc", "info", nombre_servidor], capture_output=True)
        if infoS.returncode != 0: # Si es true, el servidor no existe, entonces queremos "saltar" dicho nombre (lo hacemos por si hay huecos creados con borrarUnServidor de delete.py)
            continue
        # Si existe, lo borramos para crearlo a partir de imagenSC (servidor ya configurado)
        delete.borrarContenedor(nombre_servidor) # como lo borramos con esta función que no edita num_servidores.txt, no tenemos que preocuparnos de volver a sumar uno al fichero al crearlo de nuevo. 
        configurarConImagen(nombre_servidor)


# Instalación y configuración del LB:
def instalarLB():
    logger.info("Instalando Haproxy en el balanceador.")
    subprocess.run(["lxc", "exec", "lb", "--", "apt", "update"])
    subprocess.run(["lxc", "exec", "lb", "--", "apt", "install", "haproxy"])


# Creamos un archivo txt para escribir las líneas a incluir en el 'contenidoampliar_haproxy.cfg' de forma dinámica según los webservers existentes
def escribirtxtIPS(): 
    with open("webserversHaproxycfg.txt", "w") as f:
        for i in range (5):
            nombre_servidor = "s" + str (i+1)

            infoS = subprocess.run(["lxc", "info", nombre_servidor], capture_output=True)
            if infoS.returncode != 0: # Si es true, el servidor no existe, entonces queremos "saltar" dicho nombre (lo hacemos por si hay huecos creados con borrarUnServidor de delete.py)
                continue
        
            # Escribimos la línea de configuración para el servidor:
            ipS = direccionesIP.dir_ip_subred0 + str(i+11) 
            linea = "    server webserver"+str(i+1)+" "+ipS+":8001 \n"
            f.write(linea)


# Creamos un archivo txt con los bloques frontend y backend a añadir al final del haproxy.cf del contenedor lb
def modificarHaproxycfg():
    with open("contenidoampliar_haproxycfg.txt", "r") as f:
        texto = f.read()
    with open("webserversHaproxycfg.txt", "r") as f2:
        textoAñadir = f2.read()
    with open("contenidoampliar_haproxycfg.txt", "w") as f:
        texto = texto.replace("$cambiame$",textoAñadir)
        f.write(texto)


def configurarLB():
    escribirtxtIPS()
    modificarHaproxycfg()

    logger.info("Configurando Haproxy en el balanceador.")
    subprocess.run(["lxc", "file", "pull", "lb/etc/haproxy/haproxy.cfg", "haproxy.cfg"])

    with open("contenidoampliar_haproxycfg.txt", "r") as f:
        texto = f.read()
    with open("haproxy.cfg", "a") as f:
        f.write(texto)

    subprocess.run(["lxc", "file", "push", "haproxy.cfg", "lb/etc/haproxy/haproxy.cfg"])
    subprocess.run(["lxc", "restart", "lb"])
    logger.info("Comprobando que el fichero de configuración es válido.")
    subprocess.run(["lxc", "exec", "lb", "--","haproxy", "-f", "/etc/haproxy/haproxy.cfg", "-c"])



# PARA LA CONFIGURACIÓN REMOTA:

def configRemoto(remoto,IP_Compu):
    logger.info("Procesando acceso remoto.")
    subprocess.run(["lxc", "config", "set", "core.https_address", direccionesIP.IP_A+":8443"])
    subprocess.run(["lxc", "remote", "add", remoto, IP_Compu+":8443", "--password", "mypass", "--accept-certificate"])
    
    logger.info("Configurando bridge0 remoto.")
    ordenR = ["lxc", "network", "set", remoto+":lxdbr0"]
    subprocess.run(ordenR + ["ipv4.address", direccionesIP.dir_bridge0])
    subprocess.run(ordenR + ["ipv4.nat", "true"])


def configurarBDRemota():
    configRemoto("remoto",direccionesIP.IP_B)    

    # Crear la bd remota e instalar MongoDB 
    crearBDremota()

    # Crear proxy para acceder a la bd remota
    subprocess.run(["lxc", "config", "device", "add", "remoto:db", "miproxy", "proxy", "listen=tcp:"+direccionesIP.IP_B+":27017", "connect=tcp:"+direccionesIP.dir_db+":27017"])


def crearBDremota(): # Instala la BD en compuB y la configura.
    logger.info("Creando el contenedor db en el equipo remoto.")
    subprocess.run(["lxc", "init", nombreImgCreada, "remoto:db"])

    logger.info("Configurando la dirección IP del contenedor db.")
    subprocess.run(["lxc", "config", "device", "override", "remoto:db", "eth0", "ipv4.address="+direccionesIP.dir_db])

    subprocess.run(["lxc", "start", "remoto:db"])
    time.sleep(5)

    instalarDB("remoto")
    configurarDB("remoto")


# COMPROBACIONES por si el usuario quiere hacer "local" antes de "remote" o al revés:

# 1. Mirar si la base de datos existe:
def compExistDB(tipo_despliegue): # Devuelve un boolean.
    if tipo_despliegue == "local":
        orden = "db"
    elif tipo_despliegue == "remoto":
        orden = "remoto:db"

    infoBD = subprocess.run(["lxc", "info", orden], capture_output=True)
    if infoBD.returncode != 0: 
        return False # la db no existe 
    else:
        return True

# 2. Mirar si el lb se ha configurado: miramos que exista haproxy.cfg en la carpeta local
def compExistHcfg(): # Devuelve un boolean.
    archivo = Path("haproxy.cfg")
    if archivo.is_file():
        return True
    else:
        return False


# FUNCIÓN "GRANDE" a la que llama pfinal2.py:

def configurar():
    if len(sys.argv) == 2:
        logger.info("Para configurar el escenario web, introduce un segundo argumento, 'local' o 'remote'.")
        sys.exit() # Salir de la función

    elif sys.argv[2] == "local":
        # Primero comprueba si existe la base de datos remota y si existe la para.
        existedb = compExistDB("remoto")
        if existedb:
            stop.pararContenedor("remoto:db") 

        start.arrancarContenedor("db")
        time.sleep(5) # Para que le de tiempo a configurar las redes antes de instalar Mongo en db

        instalarDB("local")
        configurarDB("local")

        servidorConfigurado = configurarServidorInicial(direccionesIP.dir_db)
        configurarServidores(servidorConfigurado)
        
    elif sys.argv[2] == "remote":
        # Primero comprueba si existe la base de datos en local, y si existe la para.
        existedb = compExistDB("local")
        if existedb:
            stop.pararContenedor("db")  
        
        configurarBDRemota()

        servidorConfigurado = configurarServidorInicial(direccionesIP.IP_B)
        configurarServidores(servidorConfigurado)

    # Comprueba si ya he configurado previamente LB.
    existeHcfg = compExistHcfg()
    if not existeHcfg:
        instalarLB()
        configurarLB()
    