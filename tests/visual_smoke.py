"""Browser smoke tests against the actual local Nagora Salud server."""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE = os.getenv("NAGORA_TEST_URL", "http://127.0.0.1:8000")
OUT = Path(os.getenv("NAGORA_SCREENSHOT_DIR", "artifacts/visual"))
OUT.mkdir(parents=True, exist_ok=True)

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        for width, height in [(360, 800), (390, 844), (768, 1024), (1366, 900)]:
            page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            errors = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            await page.goto(BASE, wait_until="networkidle")
            demo = page.get_by_role("button", name="Entrar a la demo")
            if await demo.count():
                await demo.click()
                await page.locator(".home-overview").wait_for(timeout=15000)
            else:
                raise AssertionError("Demo mode not available; run server with NAGORA_DEMO_ONLY=1")
            await page.screenshot(path=str(OUT / f"home-{width}.png"), full_page=True)
            metrics = await page.evaluate("""() => ({
                viewport: innerWidth,
                documentWidth: document.documentElement.scrollWidth,
                mainWidth: document.querySelector('main')?.getBoundingClientRect().width,
                homeTop: document.querySelector('.home-overview')?.getBoundingClientRect().top,
                kpiAmountsFit: [...document.querySelectorAll('.home-metrics .card strong')].every(el => el.scrollWidth <= el.clientWidth + 1 && el.getBoundingClientRect().height < 55)
            })""")
            assert metrics["documentWidth"] <= metrics["viewport"] + 1, f"Horizontal overflow at {width}: {metrics}"
            assert metrics["kpiAmountsFit"], f"Financial amounts wrap or overflow at {width}: {metrics}"
            assert not errors, f"JavaScript errors at {width}: {errors}"
            print(f"PASS {width}px: {metrics}")
            await page.close()

        # Functional smoke: persist an income and expense through the UI.
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        await page.goto(BASE, wait_until="networkidle")
        await page.get_by_role("button", name="Entrar a la demo").click()
        await page.locator(".home-overview").wait_for(timeout=15000)
        before = await page.evaluate("async () => (await (await fetch('/api/state')).json()).records.length")
        await page.locator('[data-action="income"]').first.click()
        await page.locator('[data-action="source:2"]').click()
        form = page.locator('dialog form[data-endpoint="movements"]')
        await form.locator('[name="concept"]').fill("QA ingreso navegador")
        await form.locator('[name="amount"]').fill("12500")
        await form.get_by_role("button", name="Guardar ingreso").click()
        await page.get_by_text("QA ingreso navegador").first.wait_for(timeout=15000)
        await page.locator('[data-action="page:Inicio"]').first.click()
        await page.locator(".home-next details summary").click()
        await page.locator('[data-action="expense"]').first.click()
        form = page.locator('dialog form[data-endpoint="movements"]')
        await form.locator('[name="concept"]').fill("QA gasto navegador")
        await form.locator('[name="amount"]').fill("2300")
        await form.locator('[name="paid"]').check()
        await form.get_by_role("button", name="Guardar gasto").click()
        await page.get_by_text("QA gasto navegador").first.wait_for(timeout=15000)
        after = await page.evaluate("async () => (await (await fetch('/api/state')).json()).records")
        assert len(after) == before + 2, f"Expected two persisted movements, got {len(after) - before}"
        assert any(x["concept"] == "QA ingreso navegador" and x["kind"] == "income" for x in after)
        assert any(x["concept"] == "QA gasto navegador" and x["kind"] == "expense" for x in after)
        await page.screenshot(path=str(OUT / "expenses-after-create-390.png"), full_page=True)
        print("PASS income and expense persisted through UI")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
