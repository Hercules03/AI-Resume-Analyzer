import asyncio
from pyppeteer import launch
import time
import os
from datetime import datetime


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
            
            # Take screenshot for verification purposes (no results found)
            screenshots_dir = "sfc_screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = candidate_name.replace(" ", "_").replace(".", "")
            screenshot_filename = f"sfc_license_{safe_name}_{timestamp}.png"
            screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
            
            await page.screenshot({'path': screenshot_path, 'fullPage': True})
            print(f"SCREENSHOT_CAPTURED: {screenshot_path}")
            print(f"SCREENSHOT_PATH: {screenshot_path}")
            
            await browser.close()
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
                
                sfo_status = "No"
                amlo_status = "No"
                screenshot_path = None
                
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
                        # Take screenshot for verification purposes (unknown status)
                        screenshots_dir = "sfc_screenshots"
                        if not os.path.exists(screenshots_dir):
                            os.makedirs(screenshots_dir)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_name = candidate_name.replace(" ", "_").replace(".", "")
                        screenshot_filename = f"sfc_license_{safe_name}_{timestamp}.png"
                        screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                        
                        await page.screenshot({'path': screenshot_path, 'fullPage': True})
                        print(f"SCREENSHOT_CAPTURED: {screenshot_path}")
                        print(f"SCREENSHOT_PATH: {screenshot_path}")
                        
                        await browser.close()
                        return "NO LICENSE FOUND"
                else:
                    print("SFO LICENSE STATUS CELL NOT FOUND")
                    # Take screenshot for verification purposes (SFO cell not found)
                    screenshots_dir = "sfc_screenshots"
                    if not os.path.exists(screenshots_dir):
                        os.makedirs(screenshots_dir)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = candidate_name.replace(" ", "_").replace(".", "")
                    screenshot_filename = f"sfc_license_{safe_name}_{timestamp}.png"
                    screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                    
                    await page.screenshot({'path': screenshot_path, 'fullPage': True})
                    print(f"SCREENSHOT_CAPTURED: {screenshot_path}")
                    print(f"SCREENSHOT_PATH: {screenshot_path}")
                    
                    await browser.close()
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
                        # Take screenshot for verification purposes (unknown AMLO status)
                        screenshots_dir = "sfc_screenshots"
                        if not os.path.exists(screenshots_dir):
                            os.makedirs(screenshots_dir)
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_name = candidate_name.replace(" ", "_").replace(".", "")
                        screenshot_filename = f"sfc_license_{safe_name}_{timestamp}.png"
                        screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                        
                        await page.screenshot({'path': screenshot_path, 'fullPage': True})
                        print(f"SCREENSHOT_CAPTURED: {screenshot_path}")
                        print(f"SCREENSHOT_PATH: {screenshot_path}")
                        
                        await browser.close()
                        return "NO LICENSE FOUND"
                else:
                    print("AMLO LICENSE STATUS CELL NOT FOUND")
                    # Take screenshot for verification purposes (AMLO cell not found)
                    screenshots_dir = "sfc_screenshots"
                    if not os.path.exists(screenshots_dir):
                        os.makedirs(screenshots_dir)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = candidate_name.replace(" ", "_").replace(".", "")
                    screenshot_filename = f"sfc_license_{safe_name}_{timestamp}.png"
                    screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                    
                    await page.screenshot({'path': screenshot_path, 'fullPage': True})
                    print(f"SCREENSHOT_CAPTURED: {screenshot_path}")
                    print(f"SCREENSHOT_PATH: {screenshot_path}")
                    
                    await browser.close()
                    return "NO LICENSE FOUND"
                
                # Always take screenshot for verification purposes (both positive and negative results)
                # Create screenshots directory if it doesn't exist
                screenshots_dir = "sfc_screenshots"
                if not os.path.exists(screenshots_dir):
                    os.makedirs(screenshots_dir)
                
                # Generate timestamp-based filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = candidate_name.replace(" ", "_").replace(".", "")
                screenshot_filename = f"sfc_license_{safe_name}_{timestamp}.png"
                screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                
                # Take screenshot
                await page.screenshot({'path': screenshot_path, 'fullPage': True})
                print(f"SCREENSHOT_CAPTURED: {screenshot_path}")
                
                # Process results and return with screenshot info
                if sfo_status == "Yes" and amlo_status == "Yes":
                    result_msg = "ACTIVE SFO AND AMLO LICENSE FOUND"
                elif sfo_status == "Yes" and amlo_status == "No":
                    result_msg = "ACTIVE SFO LICENSE FOUND"
                elif sfo_status == "No" and amlo_status == "Yes":
                    result_msg = "ACTIVE AMLO LICENSE FOUND"
                else:
                    result_msg = "NO ACTIVE LICENSE FOUND"
                
                # Always include screenshot path for verification
                print(f"SCREENSHOT_PATH: {screenshot_path}")
                
                await browser.close()
                return result_msg
            else:
                print("UNKNOWN - No grid found")
                # Take screenshot for verification purposes (no grid found)
                screenshots_dir = "sfc_screenshots"
                if not os.path.exists(screenshots_dir):
                    os.makedirs(screenshots_dir)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_name = candidate_name.replace(" ", "_").replace(".", "")
                screenshot_filename = f"sfc_license_{safe_name}_{timestamp}.png"
                screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                
                await page.screenshot({'path': screenshot_path, 'fullPage': True})
                print(f"SCREENSHOT_CAPTURED: {screenshot_path}")
                print(f"SCREENSHOT_PATH: {screenshot_path}")
                
                await browser.close()
                return "NO LICENSE FOUND"
    else:
        print("NO LICENSE FOUND")
        # Take screenshot for verification purposes (general no results)
        screenshots_dir = "sfc_screenshots"
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = candidate_name.replace(" ", "_").replace(".", "")
        screenshot_filename = f"sfc_license_{safe_name}_{timestamp}.png"
        screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
        
        await page.screenshot({'path': screenshot_path, 'fullPage': True})
        print(f"SCREENSHOT_CAPTURED: {screenshot_path}")
        print(f"SCREENSHOT_PATH: {screenshot_path}")
        
        await browser.close()
        return "NO LICENSE FOUND"
