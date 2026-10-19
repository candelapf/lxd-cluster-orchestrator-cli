# En este subprograma definimos como variables generales las IPs utilizadas en nuestro entorno, para poder verlas y modificarlas más facilmente.


dir_ip_subred0 = "134.3.0."   
dir_ip_subred1 = "134.3.1."

# Dirección de las subredes que usamos al configurar los bridges:
dir_bridge0 = dir_ip_subred0 + "1/24"
dir_bridge1 = dir_ip_subred1 + "1/24"

# Direcciones del balanceador:
dir_lb_0 = dir_ip_subred0+"10"
dir_lb_1 = dir_ip_subred1+"10"
# Dirección de la base de datos:
dir_db = dir_ip_subred0+"20" 

# PARA LA PARTE REMOTA: direcciones de nuestros ordenadores:
IP_A = "138.4.31.114"
IP_B = "138.4.31.113"
IP_C = "138.4.31.112"













