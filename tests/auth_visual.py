"""Authentication UI QA with a disposable fictional account only."""
import asyncio
from playwright.async_api import async_playwright
from visual_smoke import BASE, OUT, audit_accessibility


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for width in (375, 1280):
            page = await browser.new_page(viewport={'width':width,'height':900})
            await page.goto(BASE, wait_until='networkidle')
            await audit_accessibility(page, f'login-{width}')
            await page.screenshot(path=str(OUT / f'login-{width}.png'), full_page=True)
            await page.evaluate("""async width => {
              const response = await fetch('/api/register', {method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({email:`qa-${width}@example.test`,name:'Cuenta ficticia QA',password:'fictional-qa-password'})});
              if (!response.ok) throw new Error('QA registration failed');
            }""", width)
            await page.reload(wait_until='networkidle')
            await page.locator('.nav-more > summary').click()
            await page.locator('.nav-more [data-action="page:Perfil"]').click()
            await page.locator('[data-action="recovery"]').click()
            await page.locator('dialog input[name="password"]').fill('fictional-qa-password')
            await page.locator('dialog button.primary').click()
            await page.locator('input[name="recovery-code"]').wait_for()
            assert await page.get_by_text('Dura 30 días y sirve una sola vez.', exact=False).is_visible()
            await audit_accessibility(page, f'recovery-{width}')
            await page.screenshot(path=str(OUT / f'recovery-{width}.png'), full_page=True)
            await page.keyboard.press('Escape')
            assert not await page.locator('dialog').is_visible()
            print(f'PASS login, recovery notice, Escape and accessibility at {width}')
            await page.close()
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
