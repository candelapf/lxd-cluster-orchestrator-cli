# 🚀 Distributed System & Container Orchestrator (LXD / Python CLI)

Herramienta de automatización y orquestación de infraestructura como servicio (IaaS) desarrollada en **Python 3** para la asignatura *Arquitectura de Computadores y Sistemas Operativos* (Grado en Ingeniería Biomédica, ETSIT - UPM).

El proyecto automatiza el ciclo de vida completo (creación, configuración de redes, balanceo de carga, replicación y despliegue remoto) de un clúster de contenedores **LXD/LXC** que ejecutan una arquitectura cliente-servidor para la gestión hospitalaria.

---

## 🏛️ Arquitectura del Sistema

El escenario orquestado despliega una red segmentada con balanceador de carga, servidores replicados de aplicaciones y almacenamiento no volátil:

```text
                    [ Red Externa / Cliente ]
                                |
                         (subnet 134.3.1.0/24)
                                |
                             [lxdbr1]
                                |
                 +--------------+--------------+
                 |   134.3.1.10 (eth1)         |
                 |      [ lb ]                 |  Balanceador HAProxy
                 |   134.3.0.10 (eth0)         |  (Round-Robin / IP Hashing)
                 +--------------+--------------+
                                |
                             [lxdbr0]
                         (subnet 134.3.0.0/24)
                                |
        +-----------------------+-----------------------+
        |                       |                       |
     [ s1 ]                  [ s2 ]                  [ s3 ] ... [ sn ] (1 a 5)
  134.3.0.11              134.3.0.12              134.3.0.13
Node.js Express         Node.js Express         Node.js Express
        |                       |                       |
        +-----------------------+-----------------------+
                                |
                   (Conexión local o remota por proxy)
                                |
                             [ db ]
                          134.3.0.20
                       MongoDB Server
                   (Despliegue local / remoto)
```

### Componentes de la Plataforma:
1. **Balanceador de Carga (`lb`):** Contenedor con interfaz dual (`lxdbr1` hacia clientes y `lxdbr0` hacia el backend) configurado con **HAProxy** para redistribuir el tráfico HTTP de forma transparente hacia los servidores de aplicaciones.
2. **Servidores Web Replicados (`s1`, `s2`, ...):** Contenedores conectados a la red interna (`134.3.0.0/24`) que ejecutan un servicio web en **Node.js** con la lógica de negocio de la aplicación clínica.
3. **Servidor de Base de Datos (`db`):** Instancia de **MongoDB** (`134.3.0.20:27017`) con persistencia documental de usuarios y pacientes.
4. **Despliegue Remoto Multihost (LXD Remotes):** Capacidad de aprovisionar y enlazar el contenedor de base de datos en un nodo remoto (`remoto:db`), estableciendo túneles/proxies de red para la comunicación entre diferentes hosts físicos.

---

## 🛠️ Tecnologías y Módulos Utilizados

* **Lenguaje:** Python 3 (uso de módulos nativos `subprocess`, `sys`, `os`, `shutil`, `logging`).
* **Virtualización ligera:** LXD / LXC sobre Ubuntu 20.04 LTS.
* **Redes virtuales:** Linux Bridges (`lxdbr0`, `lxdbr1`), direccionamiento estático y reglas NAT.
* **Servicios de Red:** HAProxy (Reverse Proxy & Load Balancer).
* **Persistencia & Backend:** MongoDB, Node.js.

---

## 📋 Estructura del Código

El desarrollo se encuentra desacoplado en módulos funcionales reutilizables:

```text
.
├── pfinal2.py                      # Punto de entrada principal (CLI)
├── info.py                         # Documentación interactiva de comandos
├── create.py                       # Creación masiva del escenario inicial
├── createoneserver.py              # Creación dinámica de una réplica individual
├── enlarge.py                      # Escalado horizontal del clúster
├── configure.py                    # Aprovisionamiento e instalación de servicios
├── start.py                        # Arranque total o selectivo de nodos
├── stop.py                         # Parada total o selectiva de nodos
├── list.py                         # Inspección de estado e IPs del clúster
├── delete.py                       # Destrucción selectiva o borrado completo
├── direccionesIP.py                # Asignación y comprobación de direccionamiento
├── remotoCompuB.py                 # Orquestación remota del contenedor DB (Host B)
├── remotoCompuC.py                 # Orquestación y proxying en nodo auxiliar
├── install.sh                      # Script de instalación del stack web
├── app.tar.gz                      # Código empaquetado de la aplicación clínica
├── webserversHaproxycfg.txt        # Plantilla de configuración HAProxy
└── 50-cloud-init.yaml              # Configuración de red vía Netplan/cloud-init
```

---

## 💻 Guía de Uso del CLI

El comando principal `pfinal2.py` gestiona todas las operaciones del clúster:

```bash
python3 pfinal2.py <orden> [argumentos...]
```

### 1. Ayuda Interactiva
Muestra la lista de órdenes disponibles, sintaxis y descripción:
```bash
python3 pfinal2.py info
# o alternativamente:
python3 info.py
```

### 2. Creación del Escenario (`create`)
Crea las redes virtuales (`lxdbr0`, `lxdbr1`), el balanceador, la base de datos y el número indicado de servidores (de 1 a 5, por defecto 2):
```bash
python3 pfinal2.py create 3
```

### 3. Aprovisionamiento y Configuración (`configure`)
Instala y configura automáticamente MongoDB, HAProxy y la aplicación Node.js en los contenedores:
```bash
python3 pfinal2.py configure
```

### 4. Arranque de Contenedores (`start`)
* Arrancar todo el escenario (abriendo consolas `xterm` de monitorización):
  ```bash
  python3 pfinal2.py start
  ```
* Arrancar un contenedor específico:
  ```bash
  python3 pfinal2.py start s1
  ```

### 5. Parada de Contenedores (`stop`)
* Detener todo el clúster:
  ```bash
  python3 pfinal2.py stop
  ```
* Detener un contenedor específico:
  ```bash
  python3 pfinal2.py stop s2
  ```

### 6. Monitorización e Inspección (`list`)
* Consultar el estado y direcciones IP de todas las máquinas virtuales y bridges:
  ```bash
  python3 pfinal2.py list
  ```
* Consultar la información de un único nodo:
  ```bash
  python3 pfinal2.py list lb
  ```

### 7. Escalado Horizontal Dinámico (`enlarge` / `createoneserver`)
Añade una nueva réplica de servidor en caliente y actualiza el fichero de configuración de HAProxy sin interrumpir el servicio:
```bash
python3 pfinal2.py enlarge
```

### 8. Destrucción y Limpieza (`delete`)
* Eliminar todo el escenario y restaurar los puentes de red:
  ```bash
  python3 pfinal2.py delete
  ```
* Eliminar un servidor individual por su nombre:
  ```bash
  python3 pfinal2.py delete s3
  ```

---

## 🌐 Configuración Multihost (Despliegue Remoto de Base de Datos)

Para aislar la base de datos en un computador independiente:
1. **Configurar Host Remoto (1B):**
   ```bash
   lxc config set core.https_address IP-B:8443
   lxc config set core.trust_password <contraseña>
   ```
2. **Enlazar desde el Host Local (1A):**
   ```bash
   python3 pfinal2.py remotoCompuB
   ```
   *El script autentica el nodo remoto, configura el puente de red, inicializa el contenedor `remoto:db` e instala el proxy TCP para redirigir el tráfico del puerto `27017`.*

---

## 👥 Autoras
Proyecto realizado por el **Grupo 8** para la asignatura Arquitectura de Computadores y Sistemas Operativos (ETSIT - UPM).