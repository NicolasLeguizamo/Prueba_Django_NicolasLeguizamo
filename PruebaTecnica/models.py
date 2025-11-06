from django.db import models


class Proyecto(models.Model):
    """Proyecto inmobiliario que agrupa varias subetapas (torres)."""

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre


class Subetapa(models.Model):
    """Cada torre o fase constructiva que pertenece a un proyecto."""

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="subetapas",
    )
    nombre = models.CharField(max_length=100)
    periodo_inicio_ventas = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Periodo inicial (mes consecutivo) en el que se registran ingresos.",
    )
    periodo_fin_ventas = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Último periodo con ingresos registrados.",
    )
    periodo_inicio_construccion = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Periodo inicial en el que se registran costos.",
    )
    periodo_fin_construccion = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Último periodo con costos registrados.",
    )

    class Meta:
        unique_together = ("proyecto", "nombre")
        ordering = ["proyecto__nombre", "nombre"]

    def __str__(self) -> str:
        return f"{self.proyecto} · {self.nombre}"


class MovimientoFinanciero(models.Model):
    """Registra ingresos o costos mensuales por subetapa."""

    class Concepto(models.TextChoices):
        INGRESO = "ingresos", "Ingresos"
        COSTO = "costos", "Costos"

    subetapa = models.ForeignKey(
        Subetapa,
        on_delete=models.CASCADE,
        related_name="movimientos",
    )
    periodo = models.PositiveIntegerField(help_text="Número consecutivo del mes dentro del proyecto.")
    concepto = models.CharField(
        max_length=10,
        choices=Concepto.choices,
    )
    valor = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["subetapa__proyecto__nombre", "subetapa__nombre", "periodo", "concepto"]
        unique_together = ("subetapa", "periodo", "concepto")

    def __str__(self) -> str:
        return f"{self.subetapa} · P{self.periodo} · {self.get_concepto_display()}"


class CreditoConstructor(models.Model):
    """Parámetros contractuales del crédito constructor asignado a un proyecto."""

    proyecto = models.OneToOneField(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="credito_constructor",
    )
    cupo_total = models.DecimalField(max_digits=14, decimal_places=2)
    porcentaje_maximo_mensual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Porcentaje máximo mensual del cupo (ej. 8.00 = 8 %).",
    )
    periodo_inicial = models.PositiveIntegerField()
    periodo_final = models.PositiveIntegerField()
    tasa_interes_anual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Tasa nominal anual en porcentaje (ej. 12.00 = 12 %).",
    )

    class Meta:
        ordering = ["proyecto__nombre"]

    def __str__(self) -> str:
        return f"Crédito {self.proyecto}"


class DesembolsoCredito(models.Model):
    """Detalle mensual del uso del crédito constructor."""

    credito = models.ForeignKey(
        CreditoConstructor,
        on_delete=models.CASCADE,
        related_name="desembolsos",
    )
    periodo = models.PositiveIntegerField()
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    saldo_despues_del_desembolso = models.DecimalField(max_digits=14, decimal_places=2)
    interes_generado = models.DecimalField(max_digits=14, decimal_places=2)
    interes_pagado = models.DecimalField(max_digits=14, decimal_places=2)
    pago_capital = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        ordering = ["periodo"]
        unique_together = ("credito", "periodo")

    def __str__(self) -> str:
        return f"{self.credito} · P{self.periodo} · Desembolso {self.monto}"


class AporteCapital(models.Model):
    """Aportes propios de la constructora para cubrir déficit de caja."""

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name="aportes_capital",
    )
    periodo = models.PositiveIntegerField()
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    flujo_caja_apalancado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Flujo neto después de considerar el aporte del periodo.",
    )

    class Meta:
        ordering = ["periodo"]
        unique_together = ("proyecto", "periodo")

    def __str__(self) -> str:
        return f"{self.proyecto} · P{self.periodo} · Aporte {self.monto}"
