import json
import os
import time
import glob
import shutil
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import ddddocr  # pip install ddddocr

# --- CONFIGURATION ---
JSON_FILENAME = 'bb_circulars.json'
DOWNLOAD_FOLDER = os.path.abspath('BB_Circulars_Downloads')

def get_latest_file(folder):
    """Returns the most recently created file, IGNORING temp files."""
    # Get all files
    files = glob.glob(os.path.join(folder, '*'))
    
    # FILTER: Exclude .tmp, .crdownload, and directories
    valid_files = [
        f for f in files 
        if os.path.isfile(f) 
        and not f.endswith('.tmp') 
        and not f.endswith('.crdownload')
    ]

    if not valid_files:
        return None

    # Sort by modification time (newest first)
    valid_files.sort(key=os.path.getmtime, reverse=True)
    return valid_files[0]

def wait_and_rename(folder, target_filename, timeout=15):
    """Waits for a new download to finish and renames it."""
    start_time = time.time()
    
    # 1. Capture files before we start waiting (to compare later)
    # (Simple approach: just watch for the newest file changing)
    
    while (time.time() - start_time) < timeout:
        latest = get_latest_file(folder)
        
        if latest:
            # Check if it's a temporary download file
            if latest.endswith('.crdownload') or latest.endswith('.tmp'):
                time.sleep(1)
                continue
            
            # If the filename is already correct, we are done
            if os.path.basename(latest) == target_filename:
                return True

            # If it's a new PDF (not the one we are trying to overwrite)
            # We assume the newest file is the one we just triggered
            try:
                target_path = os.path.join(folder, target_filename)
                
                # Delete existing if needed
                if os.path.exists(target_path):
                    os.remove(target_path)
                    
                # Rename the server's random name to our nice name
                os.rename(latest, target_path)
                return True
            except Exception as e:
                # File might still be busy/locking
                time.sleep(1)
                pass
        
        time.sleep(1)
    return False

def solve_captcha_if_present(driver):
    """Checks for CAPTCHA and solves it if found."""
    try:
        # Check for the specific captcha image used by Bangladesh Bank
        captcha_elements = driver.find_elements(By.XPATH, '//img[contains(@src, "captcha")]')
        
        if captcha_elements:
            print("   [!] CAPTCHA detected. Solving...")
            captcha_img = captcha_elements[0]
            
            # Get image
            captcha_base64 = captcha_img.screenshot_as_base64
            
            # Solve
            ocr = ddddocr.DdddOcr(show_ad=False)
            code = ocr.classification(captcha_base64)
            print(f"   [>] Code: {code}")
            
            # Type and Submit
            input_box = driver.find_element(By.NAME, 'captcha_code')
            input_box.clear()
            input_box.send_keys(code)
            
            submit_btn = driver.find_element(By.XPATH, '//input[@type="submit" or @value="Submit"]')
            submit_btn.click()
            
            # Wait for redirect/download trigger
            time.sleep(3)
            return True
    except Exception:
        pass
    return False

def main():
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    # Load JSON
    with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Initialize Chrome Options
    options = uc.ChromeOptions()
    options.add_argument('--no-first-run')
    
    # CRITICAL: Configure download behavior
    prefs = {
        "download.default_directory": DOWNLOAD_FOLDER,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True, # Force Download, don't preview
        "profile.default_content_settings.popups": 0
    }
    options.add_experimental_option("prefs", prefs)

    print("Starting Browser...")
    driver = uc.Chrome(options=options)

    # Establish Session
    driver.get("https://www.bb.org.bd/")
    time.sleep(3)

    for item in data:
        date_str = item.get('date', 'no_date').replace('/', '-')
        # Clean title deeply to prevent file system errors
        safe_title = "".join([c if c.isalnum() else "_" for c in item.get('title', 'doc')])[:60]

        # Check English
        if item.get('english_pdf'):
            target_name = f"{date_str}_ENG_{safe_title}.pdf"
            target_path = os.path.join(DOWNLOAD_FOLDER, target_name)
            
            if not os.path.exists(target_path):
                print(f"[ENG] {date_str}...")
                try:
                    driver.get(item['english_pdf'])
                    
                    # 1. Check for CAPTCHA
                    solve_captcha_if_present(driver)
                    
                    # 2. Wait for download and rename
                    if wait_and_rename(DOWNLOAD_FOLDER, target_name):
                        print("   [OK] Downloaded.")
                    else:
                        print("   [FAIL] Download timed out.")
                except Exception as e:
                    print(f"   [ERR] {e}")
                
                time.sleep(2) # Pause to be polite

        # Check Bangla
        if item.get('bangla_pdf'):
            target_name = f"{date_str}_BAN_{safe_title}.pdf"
            target_path = os.path.join(DOWNLOAD_FOLDER, target_name)
            
            if not os.path.exists(target_path):
                print(f"[BAN] {date_str}...")
                try:
                    driver.get(item['bangla_pdf'])
                    solve_captcha_if_present(driver)
                    if wait_and_rename(DOWNLOAD_FOLDER, target_name):
                        print("   [OK] Downloaded.")
                    else:
                        print("   [FAIL] Download timed out.")
                except Exception as e:
                    print(f"   [ERR] {e}")
                
                time.sleep(2)

    print("Done.")
    driver.quit()

if __name__ == "__main__":
    main()