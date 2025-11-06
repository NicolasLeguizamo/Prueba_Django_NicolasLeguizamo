import json
from PruebaTecnica.calculos import calcular_cronograma

with open("../datos_gerpro_prueba.json") as fh:
    datos = json.load(fh)

#   Datos de ejemplo para probar la función
#     movimientos=datos,
#     cupo_credito=7000,
#     porcentaje_maximo_mensual=8,   
#     periodo_inicial_credito=7,    
#     periodo_final_credito=30,      
#     tasa_interes_anual=12,        

print(calcular_cronograma(datos,7000,8,7,30,12))