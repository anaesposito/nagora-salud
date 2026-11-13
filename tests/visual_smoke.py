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
                kpiAmountsFit: [...document.querySelectorAll('.home-metrics .card strong')].every(el => el.scrollWidth <= el.clientWidth + 1 && el.getBoundingClientRect().height < 55),
                navFits: [...document.querySelectorAll('.shell nav button')].every(el => el.getBoundingClientRect().right <= document.querySelector('.shell aside').getBoundingClientRect().right + 1)
            })""")
            assert metrics["documentWidth"] <= metrics["viewport"] + 1, f"Horizontal overflow at {width}: {metrics}"
            assert metrics["navFits"], f"Sidebar navigation overlaps content at {width}: {metrics}"
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
        # Reject invalid amounts without creating an extra movement.
        await page.locator('[data-action="page:Inicio"]').first.click()
        await page.locator(".home-next details summary").click()
        await page.locator('[data-action="expense"]').first.click()
        invalid_form = page.locator('dialog form[data-endpoint="movements"]')
        await invalid_form.locator('[name="concept"]').fill("QA monto inválido")
        await invalid_form.locator('[name="amount"]').fill("0")
        await invalid_form.get_by_role("button", name="Guardar gasto").click()
        await invalid_form.locator('[role="alert"]').wait_for(timeout=10000)
        invalid_state = await page.evaluate("async () => (await (await fetch('/api/state')).json()).records")
        assert len(invalid_state) == len(after), "Invalid amount unexpectedly persisted"
        assert not any(x["concept"] == "QA monto inválido" for x in invalid_state)
        await page.locator('[data-action="close"]').first.click()
        print("PASS invalid zero amount rejected without persistence")

        # Edit the saved expense and verify that its amount changed in storage.
        await page.locator('[data-action="page:Gastos"]').first.click()
        expense = next(x for x in after if x["concept"] == "QA gasto navegador")
        expense_entry = page.locator("article.entry").filter(has_text="QA gasto navegador")
        await expense_entry.locator("summary").click()
        await page.locator(f'[data-action="edit:{expense["id"]}"]').first.click()
        edit_form = page.locator(f'dialog form[data-endpoint="movements/{expense["id"]}/edit"]')
        await edit_form.locator('[name="amount"]').fill("3400")
        await edit_form.get_by_role("button", name="Guardar cambios").click()
        edited = await page.evaluate("async () => (await (await fetch('/api/state')).json()).records")
        assert next(x for x in edited if x["id"] == expense["id"])["amount"] == 340000, "Expense edit not persisted"
        print("PASS expense amount edited and persisted")

        # Register an unpaid income, then collect only part of its balance.
        await page.locator('[data-action="page:Inicio"]').first.click()
        await page.locator('[data-action="income"]').first.click()
        await page.locator('[data-action="source:2"]').click()
        unpaid_form = page.locator('dialog form[data-endpoint="movements"]')
        await unpaid_form.locator('[name="concept"]').fill("QA cobro parcial")
        await unpaid_form.locator('[name="amount"]').fill("10000")
        await unpaid_form.locator('[name="paid"][value="off"]').check()
        await unpaid_form.get_by_role("button", name="Guardar ingreso").click()
        await page.get_by_text("QA cobro parcial").first.wait_for(timeout=15000)
        unpaid = await page.evaluate("async () => (await (await fetch('/api/state')).json()).records")
        income = next(x for x in unpaid if x["concept"] == "QA cobro parcial")
        assert income["balance"] == 1000000, "New unpaid income must have full balance"
        await page.locator('[data-action="page:Pendientes"]').first.click()
        partial_entry = page.locator("article.entry").filter(has_text="QA cobro parcial")
        await partial_entry.locator(f'[data-action="settle:{income["id"]}"]').click()
        payment_form = page.locator(f'dialog form[data-endpoint="movements/{income["id"]}/settle"]')
        await payment_form.locator('[name="amount"]').fill("4000")
        await payment_form.locator('button.primary').click()
        collected = await page.evaluate("async () => (await (await fetch('/api/state')).json()).records")
        result = next(x for x in collected if x["id"] == income["id"])
        assert result["balance"] == 600000, f"Expected remaining balance of $6,000, got {result['balance']}"
        assert result["cash"] == 400000, f"Expected $4,000 collected, got {result['cash']}"
        assert result["state"] == "Parcialmente cobrado", f"Unexpected collection state: {result['state']}"
        print("PASS partial collection: 4000 paid, 6000 pending, correct status")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
