from decimal import Decimal

from django import forms


class CronogramaForm(forms.Form):
    proyecto = forms.CharField(
        max_length=100,
        initial="Central Park",
        label="Nombre del proyecto",
    )
    dataset_url = forms.URLField(
        label="URL del JSON",
        help_text="Enlace al archivo JSON con los movimientos por subetapa.",
        initial="https://storage.googleapis.com/siga-cdn-bucket/temporal_dm/datos_gerpro_prueba.json",
    )
    cupo_credito = forms.DecimalField(
        label="Cupo del crédito",
        min_value=Decimal("0.01"),
        decimal_places=2,
        max_digits=14,
        initial=Decimal("7000.00"),
    )
    porcentaje_maximo_mensual = forms.DecimalField(
        label="Porcentaje máximo mensual",
        min_value=Decimal("0.01"),
        decimal_places=2,
        max_digits=5,
        initial=Decimal("8.00"),
        help_text="Puede ingresar el porcentaje como 8 o 0.08.",
    )
    periodo_inicial_credito = forms.IntegerField(
        label="Periodo inicial del crédito",
        min_value=1,
        initial=7,
    )
    periodo_final_credito = forms.IntegerField(
        label="Periodo final del crédito",
        min_value=1,
        initial=30,
    )
    tasa_interes_anual = forms.DecimalField(
        label="Tasa de interés anual",
        min_value=Decimal("0.00"),
        decimal_places=2,
        max_digits=5,
        initial=Decimal("12.00"),
        help_text="Puede ingresar la tasa como 12 o 0.12.",
    )

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("periodo_inicial_credito")
        fin = cleaned.get("periodo_final_credito")
        if inicio and fin and inicio > fin:
            self.add_error(
                "periodo_final_credito",
                "El periodo final debe ser igual o mayor que el periodo inicial.",
            )
        return cleaned

