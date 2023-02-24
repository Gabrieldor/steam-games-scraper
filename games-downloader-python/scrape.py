import datetime
from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
import os

import time

allTabs = ['contenthub_all', 'contenthub_newandtrending', 'contenthub_topsellers', 'contenthub_toprated', 'popularpurchaseddiscounted', 'popularcomingsoon']
tabs = [1, 3] # tabs that we want to parse in parallel

class Scraper():
    URL = "https://store.steampowered.com/tags/en/Indie?flavor="
    CLICK_TIMES = 50

    def __init__(self, tabIndex):
        self.tabIndex = tabIndex
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver.set_page_load_timeout(60)
        self.wait = WebDriverWait(self.driver, 60)
        
        self.driver.get(self.URL + allTabs[self.tabIndex])

    def save(self):
        time.sleep(1)
        html = self.driver.page_source
        
        # override main file
        with open('page_source_' + str(self.tabIndex) + '.html', 'w', encoding="utf-8") as f:
            f.write(html)

        # timestamped file
        with open('page_source_' + str(self.tabIndex) + '_' + str(int(time.time())) + '.html', 'w', encoding="utf-8") as f:
            f.write(html)
            
    def findLoadButtonAndClick(self):
        try:
            more = self.driver.find_element(By.XPATH, "//div[@class='saleitembrowser_ShowContentsContainer_3IRkb']/button")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", more)
            more.click()
            return True
        except:
            return False

    def clickOnButton(self, current, sleepArr):
        if current >= len(sleepArr):
            self.save()
            return False
        
        if not self.findLoadButtonAndClick():
            time.sleep(sleepArr[current])
            return self.clickOnButton(current + 1, sleepArr)
        else:
            return True

    def scrap(self):
        
        self.x = 0
        time.sleep(2)
        # we don't need this line if we pass the tab because the document is already scrolled
        # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        while self.x < self.CLICK_TIMES:
            time.sleep(1)

            # setting short sleep time initially so we improve the parse speed
            self.sleepTimes = [0.2, 0.4, 0.4, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 5, 8, 10, 60]

            if not self.clickOnButton(0, self.sleepTimes):
                break
            
            self.x+=1

            # save periodically in case of a crash, we have the saved data
            if self.x % 5 == 0:
                self.save()
            
        self.save()


def createScraper(tab):
    s = Scraper(tab)
    s.scrap()

def main():
    with Pool(processes=os.cpu_count()) as pool:
        res = pool.imap_unordered(createScraper, tabs)
        for _ in res:
            pass

if __name__ == '__main__':
    main()

