import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

with open('example-model.json') as f:
    j = json.loads(f.read())

chrome_options = webdriver.ChromeOptions()
driver = webdriver.Chrome(ChromeDriverManager().install())
driver.set_page_load_timeout(60)
wait = WebDriverWait(driver, 60)

cache = {}

for d in j['data']:
    try:
        c_name = d['company']['company_name']
        sl = (d['company']['steam'])
        if c_name not in cache.keys():
            driver.get(sl)
            img = driver.find_element(By.XPATH, "//img[@class='curator_avatar']").get_attribute("src")
            d['company']['logo'] = img
            cache[c_name] = img
        else:
            d['company']['logo'] = cache[c_name]    
    except Exception as e:
        pass

with open('new_example-model.json', 'w') as f:
    json.dump(j, f, indent=4)