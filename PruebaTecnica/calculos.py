from __future__ import annotations

from decimal import Decimal, getcontext
from typing import Dict, Iterable, List, Sequence, Tuple

# TODO : implementar en el flujo de apalancamiento los valores negativos al tener descuento en flujo acumulado
def calcular_cronograma(
        movimientos: Sequence[Dict[str, float]],
        cupo_credito: float,
        porcentaje_maximo_mensual: float,
        periodo_inicial_credito: int,
        periodo_final_credito: int,
        tasa_interes_anual: float,
) -> Dict[str, List[Dict[str, Decimal]]]:
    """Calcula cronogramas de crédito y aportes utilizando Decimal para mayor precisión.

    Retorna un diccionario con dos claves:
        - ``creditos``: detalle por periodo del crédito constructor.
        - ``aportes``: aportes propios requeridos para evitar flujos negativos.
    """

    global flujo_neto2
    if periodo_inicial_credito > periodo_final_credito:
        raise ValueError("El periodo inicial del crédito no puede superar al periodo final.")
    if cupo_credito <= 0:
        raise ValueError("El cupo del crédito debe ser mayor a cero.")
    if porcentaje_maximo_mensual <= 0:
        raise ValueError("El porcentaje máximo mensual debe ser positivo.")
    if tasa_interes_anual < 0:
        raise ValueError("La tasa de interés no puede ser negativa.")

    getcontext().prec = 28  # Precisión alta para cálculos financieros.

    def to_decimal(value: float) -> Decimal:
        return value if isinstance(value, Decimal) else Decimal(str(value))

    cupo_total = to_decimal(cupo_credito)
    porcentaje_mensual = to_decimal(porcentaje_maximo_mensual)
    if porcentaje_mensual > 1:
        porcentaje_mensual = porcentaje_mensual / Decimal("100")
    tasa_anual = to_decimal(tasa_interes_anual)
    if tasa_anual > 1:
        tasa_anual = tasa_anual / Decimal("100")
    tasa_mensual = tasa_anual / Decimal("12")

    movimientos_por_periodo: Dict[int, Dict[str, Decimal]] = {}
    for mov in movimientos:
        periodo = int(mov["periodo"])
        concepto = mov["concepto"]
        valor = to_decimal(mov["valor"])
        periodo_data = movimientos_por_periodo.setdefault(
            periodo, {"ingresos": Decimal("0"), "costos": Decimal("0")}
        )
        if concepto not in ("ingresos", "costos"):
            raise ValueError(f"Concepto desconocido: {concepto}")
        periodo_data[concepto] += valor

    periodos = sorted(movimientos_por_periodo.keys())
    if not periodos:
        return {"creditos": [], "aportes": []}

    periodos_con_ingresos = [p for p in periodos if movimientos_por_periodo[p]["ingresos"] > 0]
    periodos_pago_capital = periodos_con_ingresos[-2:] if len(periodos_con_ingresos) >= 2 else periodos_con_ingresos
    periodos_pago_restantes = len(periodos_pago_capital)

    primer_periodo_ingreso = min(periodos_con_ingresos) if periodos_con_ingresos else None
    ultimo_periodo_ingreso = max(periodos_con_ingresos) if periodos_con_ingresos else None

    saldo_credito = Decimal("0")
    interes_por_pagar = Decimal("0")
    flujo_acumulado = Decimal("0")
    cupo_restante = cupo_total
    maximo_mensual = cupo_total * porcentaje_mensual

    creditos: List[Dict[str, Decimal]] = []
    aportes: List[Dict[str, Decimal]] = []
    test: List[Dict[str, Decimal]] = []

    for periodo in periodos:
        datos = movimientos_por_periodo[periodo]
        ingresos = datos["ingresos"]
        costos = datos["costos"]
        flujo_operativo = ingresos - costos

        interes_pagado = interes_por_pagar
        interes_por_pagar = Decimal("0")

        desembolso = Decimal("0")
        necesidad = max(Decimal("0"), -flujo_operativo)
        dentro_de_ventana = periodo_inicial_credito <= periodo <= periodo_final_credito
        if dentro_de_ventana and necesidad > 0 and cupo_restante > 0 and primer_periodo_ingreso is not None and primer_periodo_ingreso <= periodo <= ultimo_periodo_ingreso:
            desembolso = min(necesidad, maximo_mensual, cupo_restante)
            saldo_credito += desembolso
            cupo_restante -= desembolso

        interes_generado = saldo_credito * tasa_mensual
        interes_por_pagar = interes_generado

        pago_credito = Decimal("0")
        if periodo in periodos_pago_capital and periodos_pago_restantes:
            if saldo_credito > 0:
                pago_credito = saldo_credito / Decimal(str(periodos_pago_restantes))
                saldo_credito -= pago_credito
            periodos_pago_restantes -= 1

        flujo_neto = flujo_operativo + desembolso - interes_pagado - pago_credito

        # https: // storage.googleapis.com / siga - cdn - bucket / temporal_dm / datos_gerpro_prueba_v2.json
        # Porcentaje máximo mensual 20 %

        if flujo_neto > 0:
            flujo_acumulado += flujo_neto


        if flujo_acumulado > 0 and flujo_neto < 0:
            diferencia = flujo_acumulado - abs(flujo_neto)
            if diferencia > 0:
                flujo_acumulado = diferencia
                flujo_neto2 = Decimal("0")
            else:  # -1000
                flujo_neto2 = diferencia
                valor = flujo_neto - diferencia
                flujo_acumulado += valor
        else:
            flujo_neto2 = flujo_neto

        aporte_capital = max(Decimal("0"), -flujo_neto2)
        flujo_apalancado = flujo_neto2 + aporte_capital

        creditos.append(
            {
                "periodo": Decimal(periodo),
                "ingresos": ingresos,
                "costos": costos,
                "fco": flujo_operativo,
                "desembolso": desembolso,
                "saldo": saldo_credito,
                "interes_generado": interes_generado,
                "interes_pagado": interes_pagado,
                "pago_credito": pago_credito,
                "fcn": flujo_neto,
            }
        )
        aportes.append(
            {
                "periodo": Decimal(periodo),
                "aporte_capital": aporte_capital,
                "flujo_apalancado": flujo_apalancado,
                "flujo_acumulado": flujo_acumulado,
            }
        )

        test.append(
            {
                "periodo": Decimal(periodo),
                "flujo neto": flujo_neto,
                "aporte capital": aporte_capital,
                "flujo apalancado": flujo_apalancado,
                "flujo acumulado": flujo_acumulado,
            }
        )

    return {"creditos": creditos, "aportes": aportes}

    # return {"test": test}