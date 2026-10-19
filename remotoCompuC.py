# las 2 líneas de comienzo de configuración: NECESARIO HACERLO ANTES DE QUERER CONFIGURAR EL REMOTO
import subprocess

import direccionesIP

orden = ["lxc", "config", "set"]

subprocess.run(orden +["core.https_address", direccionesIP.IP_C+":8443"])
subprocess.run(orden +["core.trust_password", "mypass"])

