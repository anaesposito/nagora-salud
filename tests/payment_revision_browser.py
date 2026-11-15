"""Run the payment correction flow against a local server in demo mode."""
import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright, expect

BASE = os.getenv("NAGORA_TEST_URL", "http://127.0.0.1:8000")
OUT = Path(os.getenv("NAGORA_SCREENSHOT_DIR", "artifacts/visual"))


async def read_state(page):
    return await page.evaluate("async () => (await fetch('/api/state')).json()")


async def verify_flow(browser, width, height):
    page = await browser.new_page(viewport={"width": width, "height": height})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    await page.goto(BASE)
    await page.get_by_role("button", name="Entrar a la demo").click()
    await expect(page.locator(".home-overview")).to_be_visible()
    before = await read_state(page)
    sample = next(r for r in before["records"] if r["concept"] == "Liquidación con pago parcial")
    trigger = f'[data-action="show:{sample["id"]}"]'
    await page.get_by_role("button", name="Ingresos", exact=True).click()
    await page.locator(trigger).click()
    modal = page.get_by_role("dialog")
    # Opening and cancelling a reversal must never mutate the ledger.
    await modal.get_by_role("button", name="Modificar cobro").click()
    await modal.get_by_role("button", name="Revertir cobro", exact=True).click()
    await modal.get_by_label("Motivo").fill("Cancelado antes de confirmar")
    await modal.get_by_role("button", name="Volver al detalle").click()
    assert (await read_state(page)) == before
    await modal.get_by_role("button", name="Modificar cobro").click()
    await expect(modal.get_by_label("Monto en pesos")).to_have_value("300000,00")
    await modal.get_by_label("Monto en pesos").fill("299999,99")
    await modal.get_by_role("button", name="Guardar corrección").click()
    await expect(modal.get_by_label("Motivo")).to_be_focused()
    assert (await read_state(page))["totals"] == before["totals"]
    await modal.get_by_label("Motivo").fill("Importe mal registrado")
    # A connection error preserves the draft and allows the same request to retry.
    route = "**/api/movements/*/payments/*/correct"
    await page.route(route, lambda request: request.abort("failed"))
    await modal.get_by_role("button", name="Guardar corrección").click()
    await expect(modal.get_by_role("alert")).to_be_focused()
    await expect(modal.get_by_role("alert")).to_contain_text("Tus datos siguen acá")
    await expect(modal.get_by_label("Monto en pesos")).to_have_value("299999,99")
    await expect(modal.get_by_label("Motivo")).to_have_value("Importe mal registrado")
    assert (await read_state(page))["totals"] == before["totals"]
    await page.unroute(route)
    assert await modal.evaluate("(el) => el.scrollWidth <= el.clientWidth")
    await page.screenshot(path=OUT / f"issue-9-correccion-{width}.png")
    await modal.get_by_role("button", name="Guardar corrección").click()
    await expect(modal.get_by_role("status")).to_have_text("Cobro corregido.")
    changed = await read_state(page)
    assert changed["totals"]["received"] == before["totals"]["received"] - 1
    assert changed["totals"]["pending"] == before["totals"]["pending"] + 1
    await modal.get_by_role("button", name="Modificar cobro").click()
    await modal.get_by_role("button", name="Revertir cobro").click()
    await expect(modal.get_by_label("Motivo")).to_be_focused()
    await modal.get_by_label("Motivo").fill("Cobro registrado por duplicado")
    if width == 375:
        await page.screenshot(path=OUT / f"issue-9-reversion-{width}.png")
    await modal.get_by_role("button", name="Confirmar reversión").click()
    await expect(modal.get_by_role("status")).to_have_text("Cobro revertido.")
    await expect(modal.get_by_text("Cobro original", exact=True)).to_be_visible()
    await expect(modal.get_by_text("Cobro corregido", exact=True)).to_be_visible()
    await expect(modal.get_by_text("Motivo: Cobro registrado por duplicado")).to_be_visible()
    await page.screenshot(path=OUT / f"issue-9-historial-{width}.png")
    current = await read_state(page)
    entry = next(r for r in current["records"] if r["id"] == sample["id"])
    assert entry["cash"] == 0 and entry["balance"] == entry["amount"] and entry["state"] == "Por cobrar"
    assert current["totals"]["received"] == before["totals"]["received"] - sample["cash"]
    assert current["totals"]["net"] == before["totals"]["net"] - sample["cash"]
    await page.reload()
    await page.get_by_role("button", name="Ingresos", exact=True).click()
    await page.locator(trigger).click()
    await modal.get_by_text("Historial de cambios en cobros").click()
    await expect(modal.get_by_text("Cobro revertido", exact=True)).to_be_visible()
    await expect(modal.get_by_role("button", name="Modificar cobro")).to_have_count(0)
    assert (await read_state(page))["totals"] == current["totals"]
    assert not errors, errors
    await page.close()
    print(f"PASS {width}px: cancelación, error de red recuperable, motivo, centavos, corrección, reversión, historial y recarga")


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=os.getenv("NAGORA_TEST_CHROMIUM"))
        for width, height in [(320,740),(375,812),(768,1024),(1280,900)]:
            await verify_flow(browser,width,height)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
