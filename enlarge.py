import subprocess
import logging
import sys

import direccionesIP
import configure
import createoneserver
import start

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Añadir una línea en 'haproxy.cfg' con la info del webserver a crear
def modiHaproxycfg(tipo_despliegue, num_ipS):
    logger.info("Añadiendo el nuevo servidor web al fichero haproxy.cfg del balanceador.")
    subprocess.run(["lxc", "file", "pull", "lb/etc/haproxy/haproxy.cfg", "haproxy.cfg"])
    with open("haproxy.cfg", "r") as f:
        lineasTexto = f.readlines() 
    for i, linea in enumerate(lineasTexto): # enumerate nos devuelve cada elemento de la lista líneas, y su posición 
        if "server webserver" in linea:
            i_insertar = i + 1

    # Definimos la línea que queremos añadir
    if tipo_despliegue == "local":
        ipS = direccionesIP.dir_ip_subred0 + str(num_ipS+11)
        texto = ipS+":8001"
    elif tipo_despliegue == "remoto":
        ipS = direccionesIP.IP_C
        texto = ipS+":80"
    
    nueva_linea = "    server webserver"+str(num_ipS+1)+" "+texto+" \n"
    # Insertamos dicha línea a continuación del último webserver 
    lineasTexto.insert(i_insertar, nueva_linea)

    # Sobrescribimos haproxy.cfg
    with open("haproxy.cfg", "w") as f: 
        f.writelines(lineasTexto)
    subprocess.run(["lxc", "file", "push", "haproxy.cfg", "lb/etc/haproxy/haproxy.cfg"])
    subprocess.run(["lxc", "restart", "lb"])
    logger.info("Comprobando que el fichero de configuración del lb es válido.")
    subprocess.run(["lxc", "exec", "lb", "--","haproxy", "-f", "/etc/haproxy/haproxy.cfg", "-c"])


def enlarge(): 
    if len(sys.argv) == 2:
        logger.info("Para crear un nuevo servidor web, introduce un segundo argumento para elegir dónde quieres crearlo, 'local' o 'remote'.")
        sys.exit() # Salir de la función

    elif sys.argv[2] == "local":
        # Verificar que no haya ya 5 servidores creados, y ver cuál corresponde crear
        num_servidores = createoneserver.comprobarNumeroScreados() 
        [nombre_S_, num_ipS] = createoneserver.hallarServidorCrear() # num_ipS toma valores 0 1 2 ... 
        
        # Configurar, a partir de la imagen s1, el nuevo servidor para que sea servidor web
        configure.configurarConImagen(nombre_S_) 

        # Volvemos a configurar LB para añadir la ip del webserver nuevo a haproxy.cfg
        modiHaproxycfg("local", num_ipS)

        # Actualizar el fichero num_servidores.txt 
        createoneserver.actualizNumServidores(num_servidores)

    elif sys.argv[2] == "remote": # Podemos crear uno remoto solo una vez y el último.
        # Verificar que no haya ya 5 servidores creados, y ver cuál corresponde crear
        num_servidores = createoneserver.comprobarNumeroScreados() 
        [nombre_S_, num_ipS] = createoneserver.hallarServidorCrear() # num_ipS toma valores 0 1 2 ... 

        # Configurar la conexión remota con el CompuC donde queremos crear el servidor nuevo
        configure.configRemoto("remotoC",direccionesIP.IP_C)

        # Crear y configurar, a partir de la imagen de s1, el nuevo servidor
        logger.info("Creando el servidor " + nombre_S_ + " en el equipo remoto.")
        subprocess.run(["lxc", "init", "imagenSC", "remotoC:"+nombre_S_])
        
        logger.info("Configurando la dirección IP del servidor.")
        ipS = direccionesIP.dir_ip_subred0 + str(num_ipS+11)
        subprocess.run(["lxc", "config", "device", "override", "remotoC:"+nombre_S_, "eth0", "ipv4.address="+ipS])
        start.arrancarContenedor("remotoC:"+nombre_S_)
        subprocess.run(["lxc", "exec", "remotoC:"+nombre_S_, "--", "forever", "start", "app/rest_server.js"])

        # Crear proxy para arreder al servidor remoto
        subprocess.run(["lxc", "config", "device", "add", "remotoC:"+nombre_S_, "miproxy", "proxy", "listen=tcp:0.0.0.0:80", "connect=tcp:"+ipS+":8001"])

        # Volvemos a configurar LB para añadir la ip del webserver nuevo a haproxy.cfg
        modiHaproxycfg("remoto", num_ipS)

        # Actualizar el fichero num_servidores.txt 
        createoneserver.actualizNumServidores(num_servidores)