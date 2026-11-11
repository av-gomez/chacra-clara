"""Prueba de la app con Playwright como un usuario nuevo: recorre todas las páginas, toma capturas en
tamaño de celular (390 x 844) y corre axe-core (accesibilidad automática) en cada una.

Uso:
  python scripts/probar_app.py                                   # contra http://localhost:8601
  python scripts/probar_app.py --url https://chacra-clara.streamlit.app
Salida: docs/capturas/*.png y docs/validacion/axe.json
"""
import argparse
import json
from pathlib import Path

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
CAPTURAS = RAIZ / "docs" / "capturas"
CELULAR = {"width": 390, "height": 844}
ESCRITORIO = {"width": 1280, "height": 900}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8601")
    args = p.parse_args()
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    axe = Axe()
    resultados, errores = {}, []
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page(viewport=CELULAR, device_scale_factor=2, locale="es-PE")
        pagina.on("pageerror", lambda e: errores.append(str(e)))

        def listo(ms=3000):
            pagina.wait_for_timeout(ms)
            pagina.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=120_000)

        def revisar(nombre):
            pagina.set_viewport_size(CELULAR)
            pagina.wait_for_timeout(1500)
            pagina.screenshot(path=CAPTURAS / f"{nombre}.png")
            resultados[nombre] = axe.run(pagina)

        def ir_a(enlace):
            # En celular el menú está plegado en el panel lateral: se navega en tamaño escritorio
            pagina.set_viewport_size(ESCRITORIO)
            pagina.wait_for_timeout(800)
            pagina.get_by_role("link", name=enlace).filter(visible=True).first.click()
            listo(3500)

        pagina.goto(args.url, wait_until="networkidle", timeout=120_000)
        listo(5000)
        revisar("01_inicio")
        pagina.get_by_role("button", name="Cargar cooperativa de ejemplo").first.click()
        listo(7000)
        assert "Posible deforestación" in pagina.inner_text("body"), "No aparece ningún estado en Resultados"
        revisar("02_resultados")
        pagina.get_by_text("Evidencia por fuente").scroll_into_view_if_needed()
        pagina.wait_for_timeout(1000)
        pagina.screenshot(path=CAPTURAS / "03_evidencia.png")
        for nombre, enlace in [("04_tablero", "3. Tablero y visitas"), ("05_informe", "4. Informe para el comprador"),
                               ("06_guia", "Guía EUDR"), ("07_datos", "Sus datos"), ("08_ingresar", "1. Ingresar parcelas")]:
            ir_a(enlace)
            revisar(nombre)
        navegador.close()

    resumen = {nombre: [{"id": v["id"], "impacto": v["impact"], "nodos": len(v["nodes"]), "ayuda": v["help"]}
                        for v in r.response["violations"]] for nombre, r in resultados.items()}
    (RAIZ / "docs" / "validacion" / "axe.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1),
                                                         encoding="utf-8")
    total = sum(len(v) for v in resumen.values())
    print(f"Páginas revisadas: {len(resumen)}. Violaciones de axe: {total}.")
    print(json.dumps(resumen, ensure_ascii=False))
    print("Errores de JavaScript:", errores or "ninguno")


if __name__ == "__main__":
    main()
