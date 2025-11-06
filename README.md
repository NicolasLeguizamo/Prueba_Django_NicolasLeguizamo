# Prueba técnica

Proyecto Django que implementa una funcion de flujo de caja:

- Función `calcular_cronograma` en `PruebaTecnica/calculos.py` que calcula el cronograma de crédito y aportes usando los datos del JSON oficial.
- Vista `cronograma_view` (ruta `/`) permite ingresar parámetros, consumir un JSON público y mostrar los resultados en una tabla por periodo.
- Los movimientos, parámetros del crédito, desembolsos y aportes se guardan en base de datos para cada ejecución.

## Analisis en Excel
El archivo `EjemploGerpro.xlsx` contiene un análisis detallado del flujo de caja constructor basado en los datos del JSON oficial. Este análisis incluye:
- Desglose de ingresos y costos por periodo.
- Cálculo de los desembolsos del crédito y aportes propios.

Además, se pudo determinar posibles errores en el ejemplo puesto en el PDF, con lo que se corrigio para que cumpla con la premisa 'El
saldo a pagar se realiza en los últimos 2 periodos de la línea de ingresos'.


## Requisitos

- Python 3.12+
- Dependencias listadas en `requirements.txt` (Django y requests).

## Configuración rápida

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Visita `http://localhost:8000/` y completa el formulario con la URL del JSON y los parámetros del crédito.

## Modelos principales

- `Proyecto` → agrupa cada escenario calculado.
- `Subetapa` → guarda las torres con periodos de ventas y construcción detectados.
- `MovimientoFinanciero` → ingresos/costos por periodo y subetapa.
- `CreditoConstructor`, `DesembolsoCredito` y `AporteCapital` → parámetros, cronograma del crédito y aportes propios resultantes.

Los datos calculados se actualizan cada vez que se procesa un nuevo JSON para el mismo proyecto.

## Pruebas rápidas

```bash
python PruebaTecnica/test.py
```

El script muestra un ejemplo de uso de `calcular_cronograma` con los datos base.
