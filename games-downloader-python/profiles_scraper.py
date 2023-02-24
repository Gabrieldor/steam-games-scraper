from cmath import exp
import pandas as pd
from multiprocessing import Pool
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import traceback
import sqlite3
import time
import string

def get_maxes(a):
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
        driver.set_page_load_timeout(60)
        wait = WebDriverWait(driver, 60)

        driver.get(f"https://www.jemepropose.com/profils/{a}")
        wait.until(EC.presence_of_element_located((By.XPATH, "//span[@rel='last']")))
        max = int(driver.find_element(By.XPATH, "//span[@rel='last']").text)

        driver.close()
        driver.quit()
        print(f"Letter {a} has {max} pages")
        return {a:max+1}
    except Exception as e:
        time.sleep(90)
        return get_maxes(a)

def get_links(par):
    try:
        alp, max = par
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
        driver.set_page_load_timeout(60)
        wait = WebDriverWait(driver, 60)
        links = []

        driver.get(f"https://www.jemepropose.com/profils/{alp}/?page={max}")
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='col s12 m4']/div/div[2]/a")))
        for e in driver.find_elements(By.XPATH, "//div[@class='col s12 m4']/div/div[2]/a"):
            links.append(e.get_attribute('href'))

        driver.close()
        driver.quit()       
        return links
    except Exception as e:
        time.sleep(90)
        return []

def get_info(link):
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(ChromeDriverManager().install(),chrome_options=chrome_options)
        driver.set_page_load_timeout(60)
        wait = WebDriverWait(driver, 60)

        id = link.split('+')[-1][:-1]

        driver.get(link)
        wait.until(EC.presence_of_element_located((By.XPATH, "//h1[@id='profil-title']")))
        names = driver.find_element(By.XPATH, "//h1[@id='profil-title']").text
        ns = names.split(" - ")
        name = ns[0]
        try:
            subname = ns[1]
        except:
            subname = ''
        table = driver.find_element(By.XPATH, "//table[@class='striped info-profile']/tbody")
        for t in table.find_elements(By.XPATH, "tr"):
            if t.find_element(By.XPATH,'td').text == "Statut":
                statut = t.find_element(By.XPATH,'td[2]').text
                continue
            if t.find_element(By.XPATH,'td').text == "Date d'inscription":
                date = t.find_element(By.XPATH,'td[2]').text
                continue
            if t.find_element(By.XPATH,'td').text == "Je suis":
                gender = t.find_element(By.XPATH,'td[2]').text
                continue
        experience = driver.find_element(By.XPATH, '//blockquote').text
        competences = []
        for compentence in driver.find_elements(By.XPATH,"//div[@class='chip gradient-45deg-amber-amber white-text']"):
            competences.append(compentence.text)
        competence = ";".join(competences)

        driver.close()
        driver.quit()
        con = sqlite3.connect("profiles.db")
        con.row_factory = lambda cursor, row: row[0]
        cur = con.cursor()
        cur.execute("INSERT INTO Profile (id, name, subname, status, date, gender, experience, competence) values (?, ?, ?, ?, ?, ?, ?, ?);", (id, name, subname, statut, date, gender, experience, competence))
        con.commit()
        print("Info Collected!")

    except Exception as e:
        time.sleep(90)
        return []

def main():
    con = sqlite3.connect("profiles.db")
    con.row_factory = lambda cursor, row: row[0]
    cur = con.cursor()
    cur.execute(f"CREATE TABLE IF NOT EXISTS Profile ('id','name', 'subname', 'status', 'date', 'gender', 'experience', 'competence');")
    cur.execute("SELECT name FROM sqlite_master WHERE type = 'index';")
    index = cur.fetchone()

    if index == None:
        print("Creating an INDEX")
        cur.execute("CREATE INDEX id ON Profile (id)")

    alp = list(string.ascii_uppercase)
    maxes = []
    links = []
    info = []
    print("Starting Scraping")
    with Pool(processes=8) as pool:
        res = pool.imap_unordered(get_maxes, alp, chunksize=3)
        for r in res:
            if r not in maxes:
                maxes.append(r)

    for m in maxes:
        i = 0
        p = list(range(1,list(m.values())[0]+1))
        p = [(list(m.keys())[0], x) for x in p]
        with Pool(processes=20) as pool:
            res = pool.imap_unordered(get_links, p, chunksize=10)
            for r in res:
                if r not in links:
                    links += r
                    i+=1
                    print(f"new links in {list(m.keys())[0]}, page {i}")
        with Pool(processes=20) as pool:
            res = pool.imap_unordered(get_info, links, chunksize=100)
            for r in res:
                if r not in info:
                    pass
    
    

if __name__ == '__main__':
    main()