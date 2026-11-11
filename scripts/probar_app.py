"""Prueba de humo de la app con Playwright: recorre el flujo principal como un usuario nuevo,
en tamaño de celular, toma capturas y corre axe (accesibilidad automática).

Uso:
  python scripts/probar_app.py                         # contra http://localhost:8601
  python scripts/probar_app.py --url https://...       # contra la URL pública
Salida: docs/capturas/*.png y docs/validacion/axe.json
"""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
CAPTURAS = RAIZ / "docs" / "capturas"


def esperar(pagina, ms=2500):
    pagina.wait_for_timeout(ms)
    pagina.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=90_000)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8601")
    p.add_argument("--celular", action="store_true", default=True)
    args = p.parse_args()
    CAPTURAS.mkdir(parents=True, exist_ok=True)
    errores = []
    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        tam = {"width": 390, "height": 844} if args.celular else {"width": 1280, "height": 900}
        contexto = navegador.new_context(viewport=tam, device_scale_factor=2, locale="es-PE")
        pagina = contexto.new_page()
        pagina.on("pageerror", lambda e: errores.append(str(e)))
        pagina.goto(args.url, wait_until="networkidle", timeout=120_000)
        esperar(pagina, 4000)
        pagina.screenshot(path=CAPTURAS / "01_inicio.png", full_page=False)

        # Accesibilidad automática en la portada
        from axe_playwright_python.sync_playwright import Axe
        axe = Axe()
        resultado_inicio = axe.run(pagina)

        pagina.get_by_role("button", name="Demo Puno (Sandia y Carabaya)").click()
        esperar(pagina, 5000)
        pagina.screenshot(path=CAPTURAS / "02_resultados.png", full_page=False)
        pagina.mouse.wheel(0, 1400)
        pagina.wait_for_timeout(1500)
        pagina.screenshot(path=CAPTURAS / "03_tabla.png", full_page=False)
        texto = pagina.inner_text("body")
        assert "Posible deforestación" in texto, "No aparece ningún estado en resultados"
        resultado_resultados = axe.run(pagina)

        pagina.screenshot(path=CAPTURAS / "02_resultados_completo.png", full_page=True)
        pagina.get_by_role("button", name="Ver el tablero y la ruta de visitas").click()
        esperar(pagina, 4000)
        pagina.screenshot(path=CAPTURAS / "04_tablero.png", full_page=False)
        pagina.screenshot(path=CAPTURAS / "04_tablero_completo.png", full_page=True)

        resumen = {}
        for nombre, r in [("inicio", resultado_inicio), ("resultados", resultado_resultados)]:
            resumen[nombre] = [{"id": v["id"], "impacto": v["impact"], "nodos": len(v["nodes"]),
                                "ayuda": v["help"]} for v in r.response["violations"]]
        (RAIZ / "docs" / "validacion" / "axe.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1),
                                                             encoding="utf-8")
        print(json.dumps(resumen, ensure_ascii=False, indent=1))
        navegador.close()
    print("Errores de JavaScript:", errores or "ninguno")


if __name__ == "__main__":
    main()
