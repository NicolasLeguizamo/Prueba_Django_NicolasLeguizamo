import json
import requests
from decimal import Decimal, ROUND_HALF_UP
from typing import List

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render

from .calculos import calcular_cronograma
from .forms import CronogramaForm
from .models import (
    AporteCapital,
    CreditoConstructor,
    DesembolsoCredito,
    MovimientoFinanciero,
    Proyecto,
    Subetapa,
)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def cronograma_view(request):
    resultados = None
    rows = []

    if request.method == "POST":
        form = CronogramaForm(request.POST)
        if form.is_valid():
            cleaned = form.cleaned_data
            url = cleaned["dataset_url"]
            try:
                respuesta = requests.get(url, timeout=15)
                respuesta.raise_for_status()
                movimientos = respuesta.json()
            except requests.RequestException as exc:
                form.add_error("dataset_url", f"No se pudo cargar el JSON: {exc}")
            except ValueError as exc:
                form.add_error("dataset_url", f"No se pudo cargar el JSON: {exc}")
            else:
                try:
                    resultados = calcular_cronograma(
                        movimientos=movimientos,
                        cupo_credito=float(cleaned["cupo_credito"]),
                        porcentaje_maximo_mensual=float(cleaned["porcentaje_maximo_mensual"]),
                        periodo_inicial_credito=cleaned["periodo_inicial_credito"],
                        periodo_final_credito=cleaned["periodo_final_credito"],
                        tasa_interes_anual=float(cleaned["tasa_interes_anual"]),
                    )
                except Exception as exc:
                    form.add_error(None, f"Error al calcular el cronograma: {exc}")
                else:
                    rows = _preparar_filas(resultados)
                    _guardar_en_base(
                        movimientos,
                        resultados,
                        cleaned["proyecto"],
                        cleaned,
                        cleaned["dataset_url"],
                    )
                    messages.success(
                        request,
                        "Cronograma calculado y almacenado correctamente.",
                    )
    else:
        form = CronogramaForm()

    context = {
        "form": form,
        "rows": rows,
    }
    return render(request, "cronograma.html", context)


def _preparar_filas(resultados: dict) -> List[dict]:
    filas: List[dict] = []
    creditos = resultados.get("creditos", [])
    aportes = resultados.get("aportes", [])

    for credito, aporte in zip(creditos, aportes):
        filas.append(
            {
                "periodo": int(credito["periodo"]),
                "ingresos": _quantize(credito["ingresos"]),
                "costos": _quantize(credito["costos"]),
                "fco": _quantize(credito["fco"]),
                "desembolso": _quantize(credito["desembolso"]),
                "saldo": _quantize(credito["saldo"]),
                "interes_generado": _quantize(credito["interes_generado"]),
                "interes_pagado": _quantize(credito["interes_pagado"]),
                "pago_credito": _quantize(credito["pago_credito"]),
                "fcn": _quantize(credito["fcn"]),
                "aporte_capital": _quantize(aporte["aporte_capital"]),
                "flujo_apalancado": _quantize(aporte["flujo_apalancado"]),
                "flujo_acumulado": _quantize(aporte['flujo_acumulado']),
            }
        )
    return filas


@transaction.atomic
def _guardar_en_base(
    movimientos: List[dict],
    resultados: dict,
    nombre_proyecto: str,
    parametros: dict,
    dataset_url: str,
) -> None:
    proyecto, creado = Proyecto.objects.get_or_create(
        nombre=nombre_proyecto,
        defaults={"descripcion": f"Escenario importado desde {dataset_url}"},
    )
    if not creado:
        proyecto.descripcion = f"Escenario actualizado desde {dataset_url}"
        proyecto.save()

    credito, _ = CreditoConstructor.objects.get_or_create(
        proyecto=proyecto,
        defaults={
            "cupo_total": Decimal("0"),
            "porcentaje_maximo_mensual": Decimal("0"),
            "periodo_inicial": parametros["periodo_inicial_credito"],
            "periodo_final": parametros["periodo_final_credito"],
            "tasa_interes_anual": Decimal("0"),
        },
    )
    credito.cupo_total = _quantize(Decimal(str(parametros["cupo_credito"])))
    credito.porcentaje_maximo_mensual = _quantize(Decimal(str(parametros["porcentaje_maximo_mensual"])))
    credito.periodo_inicial = parametros["periodo_inicial_credito"]
    credito.periodo_final = parametros["periodo_final_credito"]
    credito.tasa_interes_anual = _quantize(Decimal(str(parametros["tasa_interes_anual"])))
    credito.save()

    subetapas_cache = {}
    periodos_por_subetapa = {}
    for movimiento in movimientos:
        subetapa_nombre = movimiento["subetapa"]
        periodo = int(movimiento["periodo"])
        concepto = movimiento["concepto"]

        subetapa = subetapas_cache.get(subetapa_nombre)
        if subetapa is None:
            subetapa, _ = Subetapa.objects.get_or_create(
                proyecto=proyecto,
                nombre=subetapa_nombre,
            )
            subetapas_cache[subetapa_nombre] = subetapa

        info = periodos_por_subetapa.setdefault(
            subetapa_nombre,
            {"ventas": set(), "costos": set(), "instancia": subetapa},
        )
        info["ventas" if concepto == "ingresos" else "costos"].add(periodo)

        MovimientoFinanciero.objects.update_or_create(
            subetapa=subetapa,
            periodo=periodo,
            concepto=concepto,
            defaults={"valor": _quantize(Decimal(str(movimiento["valor"])))},
        )

    for info in periodos_por_subetapa.values():
        ventas = sorted(info["ventas"]) or [None]
        costos = sorted(info["costos"]) or [None]
        subetapa = info["instancia"]
        subetapa.periodo_inicio_ventas = ventas[0]
        subetapa.periodo_fin_ventas = ventas[-1]
        subetapa.periodo_inicio_construccion = costos[0]
        subetapa.periodo_fin_construccion = costos[-1]
        subetapa.save()

    periodos_credito = []
    for registro in resultados.get("creditos", []):
        periodo = int(registro["periodo"])
        periodos_credito.append(periodo)
        DesembolsoCredito.objects.update_or_create(
            credito=credito,
            periodo=periodo,
            defaults={
                "monto": _quantize(registro["desembolso"]),
                "saldo_despues_del_desembolso": _quantize(registro["saldo"]),
                "interes_generado": _quantize(registro["interes_generado"]),
                "interes_pagado": _quantize(registro["interes_pagado"]),
                "pago_capital": _quantize(registro["pago_credito"]),
            },
        )
    DesembolsoCredito.objects.filter(credito=credito).exclude(periodo__in=periodos_credito).delete()

    periodos_aportes = []
    for registro in resultados.get("aportes", []):
        periodo = int(registro["periodo"])
        periodos_aportes.append(periodo)
        AporteCapital.objects.update_or_create(
            proyecto=proyecto,
            periodo=periodo,
            defaults={
                "monto": _quantize(registro["aporte_capital"]),
                "flujo_caja_apalancado": _quantize(registro["flujo_apalancado"]),
            },
        )
    AporteCapital.objects.filter(proyecto=proyecto).exclude(periodo__in=periodos_aportes).delete()
