import argparse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from PIL import Image
import io
import os
import time

def take_screenshot(url, output_path):
    """
    Visits a URL in a headless browser and saves a full-page screenshot as a PDF.
    """
    print(f"--> Capturing screenshot for: {url}")
    
    # --- Setup Headless Browser ---
    options = Options()
    options.add_argument("--headless")
    # Point selenium to the local geckodriver
    service = webdriver.FirefoxService(executable_path='geckodriver.exe') 
    
    try:
        driver = webdriver.Firefox(options=options, service=service)
        # Set a generous timeout for the page to load
        driver.set_page_load_timeout(30)
        # Set window size for a comprehensive screenshot
        driver.set_window_size(1200, 800) 

        # --- Navigation and Screenshot ---
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        driver.get(url)
        
        # Give the page a moment to render any dynamic elements
        time.sleep(3) 

        # Get the screenshot as binary data
        png_data = driver.get_full_page_screenshot_as_png()
        
        # --- Convert PNG to PDF using Pillow ---
        image = Image.open(io.BytesIO(png_data))
        # Convert to RGB if it's RGBA to avoid transparency issues in PDF
        if image.mode == 'RGBA':
            image = image.convert('RGB')
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, "PDF", resolution=100.0)
        
        print(f"[+] Screenshot saved successfully to: {output_path}")
        return True

    except Exception as e:
        print(f"[!] Error taking screenshot for {url}: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.quit()

# --- Main execution block for testing ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take a screenshot of a URL and save it as a PDF.")
    parser.add_argument("url", help="The URL to capture.")
    parser.add_argument("output", help="The output path for the PDF file (e.g., evidences/example.pdf).")
    args = parser.parse_args()
    
    # --- SAFETY WARNING ---
    print("⚠️ WARNING: This tool will visit the specified URL. Only run this in a safe, sandboxed environment.")
    
    take_screenshot(args.url, args.output)