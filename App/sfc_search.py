import asyncio
from pyppeteer import launch
import time


async def sfc_search(candidate_name):
    browser = await launch(executablePath=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
    page = await browser.newPage()
    
    # Navigate directly to the search page
    await page.goto('https://apps.sfc.hk/publicregWeb/searchByName')
    print("Navigated to search page")
    
    # Type the name into the search box
    await page.type('input[id^="searchtextname-"]', candidate_name)
    print(f"Typed name: {candidate_name}")

    # Select Individual radio button
    await page.click('#radiofield-1027-inputEl')
    print("Selected Individual radio button")
    
    # Click the search button
    await page.waitForSelector("div.sfcButton")
    await page.click("div.sfcButton")
    print("Clicked search button")
    
    # Wait for results to load
    await page.waitForFunction('''
        () => document.querySelector('div.x-grid-panel[id^=grid]') || document.querySelector('div.x-form-display-field')
    ''', {'timeout': 20000})
    
    time.sleep(1)

    # Check for no results message
    no_result_handle = await page.querySelector('div.x-form-display-field')
    
    if no_result_handle:
        search_result_text = await page.evaluate('(element) => element.textContent', no_result_handle)
        print(f"Text content found: '{search_result_text.strip()}'")
        
        if "no name matched" in search_result_text.lower():
            print("NO LICENSE FOUND")
            return "NO LICENSE FOUND"
        else:
            # Check if there are actual results by looking for the grid header
            results_grid = await page.querySelector('#headercontainer-1033')
            if results_grid:
                #time.sleep(1)
                page_content = await page.content()
                with open('sfc_screenshot.html', 'w', encoding='utf-8') as f:
                    f.write(page_content)
                
                # Target the specific SFO and AMLO license status columns using their class names
                # SFO license status is in gridcolumn-1040, AMLO license status is in gridcolumn-1041
                sfo_cell = await page.querySelector('td.x-grid-cell-gridcolumn-1040 div.x-grid-cell-inner')
                amlo_cell = await page.querySelector('td.x-grid-cell-gridcolumn-1041 div.x-grid-cell-inner')
                
                if sfo_cell:
                    sfo_status = await page.evaluate('(element) => element.textContent', sfo_cell)
                    sfo_status = sfo_status.strip()
                    print(f"SFO License Status: {sfo_status}")
                    
                    if sfo_status == "Yes":
                        print("ACTIVE SFO LICENSE CONFIRMED")
                    elif sfo_status == "No":
                        print("NO ACTIVE SFO LICENSE")
                    else:
                        print(f"UNKNOWN SFO STATUS - '{sfo_status}'")
                        return "NO LICENSE FOUND"
                else:
                    print("SFO LICENSE STATUS CELL NOT FOUND")
                    return "NO LICENSE FOUND"
                    
                if amlo_cell:
                    amlo_status = await page.evaluate('(element) => element.textContent', amlo_cell)
                    amlo_status = amlo_status.strip()
                    print(f"AMLO License Status: {amlo_status}")
                    
                    if amlo_status == "Yes":
                        print("ACTIVE AMLO LICENSE CONFIRMED")
                    elif amlo_status == "No":
                        print("NO ACTIVE AMLO LICENSE")
                    else:
                        print(f"UNKNOWN AMLO STATUS - '{amlo_status}'")
                        return "NO LICENSE FOUND"
                else:
                    print("AMLO LICENSE STATUS CELL NOT FOUND")
                    return "NO LICENSE FOUND"
                
                if amlo_cell == "Yes" and sfo_cell == "Yes":
                    return "ACTIVE SFO AND AMLO LICENSE FOUND"
                elif amlo_cell == "Yes" and sfo_cell == "No":
                    return "ACTIVE AMLO LICENSE FOUND"
                elif amlo_cell == "No" and sfo_cell == "Yes":
                    return "ACTIVE SFO LICENSE FOUND"
            else:
                print("UNKNOWN - No grid found")
                return "NO LICENSE FOUND"
    
    
    await browser.close()
