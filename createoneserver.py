import subprocess
import logging
import sys

import create
import direccionesIP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

nombreImgCreada = "ubuntu2004"


def comprobarNumeroScreados():
    # Leer el número actual de servidores
    try:
        with open ("num_servidores.txt", "r") as fich:
            num_servidores = int(fich.read())
    except FileNotFoundError: # Error si no encuentra el fichero
        num_servidores = 0
    
    # Si hay 5 servidores ya creados, no se pueden crear más
    if num_servidores == 5:
        logger.info("Error: No se pueden crear más de 5 servidores")
        sys.exit()
    
    return num_servidores


def hallarServidorCrear():
    # Buscamos desde s1 hasta s5 el primer servidor que no existe (para rellenar posibles huecos generados por la función borrarUnServidor() de delete.py) 
    nombre_servidor = "" # Se inicializa a un string vacío
    for i in range(5):
        posible_nombre = "s" + str(i+1)
        
        # Ejecutamos 'lxc info' para ver si existe. Si devuelve error (returncode != 0), es que el nombre está libre. 
        infoS = subprocess.run(["lxc", "info", posible_nombre], capture_output=True)
        
        if infoS.returncode != 0: # Esto es true si da un error el lxc info porque no exista el servidor
            nombre_servidor = posible_nombre
            num_ipS = i # Guardamos el índice para la IP (cuánto le sumaremos a la terminación de dir_s1)
            break
    
    datosS =[nombre_servidor, num_ipS] 
    return datosS
    

def actualizNumServidores(num_servidores):
    # Sumar +1 al número que haya en el fichero numero_servidores.txt
    num_actualizado = num_servidores + 1
    with open ("num_servidores.txt", "w") as fich:
        fich.write(str(num_actualizado))
        

def crearUnServidor():
    # Comprobamos que no haya creado ya 5 servidores:
    num_servidores = comprobarNumeroScreados() 

    # Buscamos el primer servidor no existente para crear ese:
    [nombre_servidor, num_ipS] = hallarServidorCrear()  
            
    # Crear el servidor con el nombre correspondiente
    logger.info("Creando el servidor " + nombre_servidor)
    create.crear(nombre_servidor, nombreImgCreada)
    
    # Configurar el servidor
    ipS = direccionesIP.dir_ip_subred0 + str(11+num_ipS)

    create.attachToBridge("lxdbr0", nombre_servidor, "eth0")
    create.configurarIp(nombre_servidor, "eth0", ipS)

    # Actualiza el número de servidores existentes en num_servidores.txt
    actualizNumServidores(num_servidores)
        
   
   
    
    
    
    




