"""Browser acceptance on a local demo server; all data is fictitious."""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect

BASE=os.getenv('NAGORA_TEST_URL','http://127.0.0.1:8000')
OUT=Path(os.getenv('NAGORA_SCREENSHOT_DIR','artifacts/visual'))

async def state(page):
    return await page.evaluate("async()=> (await fetch('/api/state')).json()")

async def flow(browser,width,height):
    context=await browser.new_context(viewport=dict(width=width,height=height))
    page=await context.new_page()
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.goto(BASE);await page.get_by_role('button',name='Entrar a la demo',exact=True).click()
    await expect(page.locator('.home-overview')).to_be_visible()
    initial=await state(page)
    payer=next(p for p in initial['payers'] if p['kind']=='Obra social')
    await page.get_by_role('button',name='Ingresos',exact=True).click()
    await page.get_by_role('button',name='Liquidaciones de pagadores').click()
    dialog=page.get_by_role('dialog')
    await dialog.get_by_role('button',name='Cargar liquidación',exact=True).click()
    await expect(dialog.get_by_text('Paso 1 de 3 · Identificar',exact=True)).to_be_visible()
    await dialog.get_by_label('¿Quién liquidó?').select_option(str(payer['id']))
    await dialog.get_by_label('Referencia de la liquidación').fill(f'QA-L-{width}')
    await dialog.get_by_label('Dinero recibido en pesos').fill('100,01')
    await page.screenshot(path=OUT/f'liquidacion-paso1-{width}.png')
    await dialog.get_by_role('button',name='Continuar',exact=True).click()
    records=[r for r in initial['records'] if r['payer']==payer['id'] and r['balance']>0]
    first=dialog.locator(f'.allocation[data-movement="{records[0]["id"]}"]')
    second=dialog.locator(f'.allocation[data-movement="{records[1]["id"]}"]')
    await first.get_by_role('checkbox').check()
    await first.get_by_label('Importe incluido en pesos',exact=True).fill('100,01')
    await first.get_by_label('Recibido para esta prestación',exact=True).fill('80,01')
    await first.get_by_text('Descuentos y retenciones',exact=True).click()
    await first.get_by_label('Descuento aceptado en pesos',exact=True).fill('5')
    await first.get_by_label('Tipo de descuento').select_option('Comisión aceptada')
    await first.get_by_label('Retenido en pesos',exact=True).fill('10')
    await first.get_by_label('Tipo de retención').select_option('Tributaria')
    await first.get_by_label('Explicación administrativa (sin datos de pacientes)',exact=True).fill('Cinco pesos a consultar')
    await second.get_by_role('checkbox').check()
    await second.get_by_label('Importe incluido en pesos',exact=True).fill('30')
    await second.get_by_label('Recibido para esta prestación',exact=True).fill('19,99')
    await second.get_by_label('Explicación administrativa (sin datos de pacientes)',exact=True).fill('Pago parcial de la prestación')
    await dialog.get_by_role('button',name='Continuar',exact=True).click()
    await expect(dialog.get_by_role('alert')).to_contain_text('coincidir exactamente')
    await expect(first.get_by_label('Recibido para esta prestación',exact=True)).to_have_value('80,01')
    assert len((await state(page))['liquidations'])==0
    await second.get_by_label('Recibido para esta prestación',exact=True).fill('20')
    # Back preserves the draft rather than losing allocations.
    await dialog.get_by_role('button',name='Atrás',exact=True).click()
    await dialog.get_by_role('button',name='Continuar',exact=True).click()
    first=dialog.locator(f'.allocation[data-movement="{records[0]["id"]}"]')
    await expect(first.get_by_label('Recibido para esta prestación',exact=True)).to_have_value('80,01')
    await page.screenshot(path=OUT/f'liquidacion-paso2-{width}.png')
    await dialog.get_by_role('button',name='Continuar',exact=True).click()
    await expect(dialog.get_by_text('Paso 3 de 3 · Revisar',exact=True)).to_be_visible()
    await dialog.get_by_text('Ver descuentos, retenciones y diferencia',exact=True).first.click()
    await page.screenshot(path=OUT/f'liquidacion-paso3-{width}.png')
    assert await dialog.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
    await dialog.get_by_role('button',name='Confirmar liquidación',exact=True).click()
    await expect(dialog.get_by_role('heading',name='Detalle de liquidación')).to_be_visible()
    saved=await state(page);group=saved['liquidations'][0]
    assert saved['totals']['received']==initial['totals']['received']+10001
    assert saved['totals']['activity']==initial['totals']['activity']-500
    assert saved['totals']['retained']==1000
    assert len(saved['records'])==len(initial['records'])
    assert saved['totals']['pending']==initial['totals']['pending']-11501
    # Two stale correction forms: only one may commit.
    other=await page.context.new_page();await other.goto(BASE)
    await expect(other.locator('.home-overview')).to_be_visible()
    for current_page in [page,other]:
        if current_page==other:
            await other.get_by_role('button',name='Ingresos',exact=True).click()
            await other.get_by_role('button',name='Liquidaciones de pagadores').click()
            await other.get_by_role('button',name=f'Ver liquidación QA-L-{width}').click()
        modal=current_page.get_by_role('dialog')
        await modal.get_by_role('button',name='Corregir liquidación',exact=True).click()
        await modal.get_by_label('Motivo de la corrección').fill('Clasificación revisada')
        await modal.get_by_role('button',name='Continuar',exact=True).click()
        await modal.get_by_role('button',name='Continuar',exact=True).click()
    await page.get_by_role('button',name='Confirmar corrección',exact=True).click()
    await expect(page.get_by_role('heading',name='Detalle de liquidación')).to_be_visible()
    await other.get_by_role('button',name='Confirmar corrección',exact=True).click()
    await expect(other.get_by_role('alert')).to_contain_text('cambiaron')
    await page.get_by_text('Historial de la liquidación (2)',exact=True).click()
    await page.screenshot(path=OUT/f'liquidacion-historial-{width}.png')
    # Individual correction from PR42 changes one cash entry and keeps group totals coherent.
    await page.get_by_text('Ver desglose de la prestación',exact=True).first.click()
    await page.get_by_role('button',name='Ver prestación y corregir cobros',exact=True).first.click()
    # Seed may contain an older payment; select the cash row for this statement by its payment ID.
    latest=(await state(page))['liquidations'][0]
    item=latest['allocations'][0]
    payment=next(p for p in item['payments'] if p['component']=='cash')
    await page.locator(f'[data-action="correct-payment:{item["movement"]}:{payment["id"]}"]').click()
    await page.get_by_label('Monto en pesos',exact=True).fill('79,99' if payment['amount']==8001 else '19,98')
    await page.get_by_label('Motivo',exact=True).fill('Dos centavos de corrección')
    await page.get_by_role('button',name='Guardar corrección',exact=True).click()
    await expect(page.locator('.payment-feedback')).to_have_text('Cobro corregido.')
    revised=await state(page)
    assert revised['liquidations'][0]['received']==9999
    assert revised['totals']['received']==saved['totals']['received']-2
    await page.reload();await expect(page.locator('.home-overview')).to_be_visible()
    assert (await state(page))['liquidations'][0]['received']==9999
    assert not errors,errors
    assert await page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    await context.close()
    print(f'PASS {width}px: three steps, exact cents, partials, retention, conflict, PR42 and reload')

async def main():
    OUT.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=os.getenv('NAGORA_TEST_CHROMIUM'))
        for size in [(375,812),(1280,900),(320,740),(768,1024)]:await flow(browser,*size)
        await browser.close()

if __name__=='__main__':asyncio.run(main())
