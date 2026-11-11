"""Números con coma decimal y espacio de miles, como se escriben en el Perú (1,31 ha; 4 400 kg).

Los espacios son de no separación (U+00A0) para que «US$ 32 720» o «48 %» no se partan en dos líneas en el celular.
"""
NBSP = " "


def num(valor, decimales=2):
    """num(1.309) -> '1,31'; num(4400, 0) -> '4 400'."""
    if valor is None:
        return "—"
    texto = f"{valor:,.{decimales}f}"            # 4,400.50 (formato inglés)
    return texto.replace(",", NBSP).replace(".", ",")  # 4 400,50


def ha(valor, decimales=2):
    return f"{num(valor, decimales)}{NBSP}ha"


def pct(valor, decimales=0):
    return f"{num(valor, decimales)}{NBSP}%"
