from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import InvalidSessionIdException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json
import os

goal = 200

currentTime = datetime.now()

suffix = str(int(time.time()) % 10000)

filename = 'scrape_' + currentTime.strftime("%d-%b-%Y_") + suffix + '.txt'
failingLinksArray = []
allTagsArray = []
currentLink = ""


linkCache = {}
queuedLinks = []

def addLinkToQueue(obj):
    keyLink = obj['link']
    if(keyLink not in linkCache):
        queuedLinks.append(obj)
        linkCache[keyLink] = True


def getMoreLikeThis(pageContent):
    lstProduct = []
    lstItemTag = pageContent.find_all("a", {"class": "small_cap"})
    if len(lstItemTag):
        for item in lstItemTag:
            lstProduct.append(item["href"])

    return lstProduct

def parseCompany(pageContent):

    packGameInfo = {
        "company_name" : "",
        "website"     : "",
        "twitter"     : "",
        "youtube"     : "",
    }
    
    # Get App Site Link
    siteLink = ''
    siteLinkTag = pageContent.select("a.curator_url.ttip")
    if len (siteLinkTag):
        if siteLinkTag[0]['href']:
            siteLink = siteLinkTag[0]['href']
    packGameInfo["website"] = siteLink

    # Get Social Link
    socialWrapper = pageContent.select("div.socialmedia_accounts")
    if len(socialWrapper):
        socialTagList = socialWrapper[0].find_all('span' , recursive=False)
        if len(socialTagList):
            # socialTagList[0].select('a')[0]['href'] # facebook
            # socialTagList[1].select('a')[0]['href'] # steam community
            # packGameInfo['twitter'] = socialTagList[2].select('a')[0]['href'] # twitter
            # packGameInfo['youtube'] = socialTagList[3].select('a')[0]['href'] # youtube
            for eachSpan in socialTagList:
                if "twitter" in eachSpan.select('a')[0]['href']:
                    packGameInfo['twitter'] = eachSpan.select('a')[0]['href']
                if "youtube" in eachSpan.select('a')[0]['href']:
                    packGameInfo['youtube'] = eachSpan.select('a')[0]['href']               

    gameList = []
    listWrapper = pageContent.select("img.capimg")
    if len(listWrapper):
        for imgTag in listWrapper:
            gameList.append(imgTag.parent['href'])

    return packGameInfo , gameList

def parseAGame(pageContent, driver):

    aGameInfo = {}

    appNameTagList = pageContent.select("div#appHubAppName")
    if len(appNameTagList):
        aGameInfo["gameName"] = appNameTagList[0].text

    gameInfoPanel = pageContent.select("div.glance_ctn_responsive_left")
    if len(gameInfoPanel):
        gameInfoWrap = gameInfoPanel[0]

        # Get App Release Date
        releaseDateTagList = gameInfoWrap.find("div" , class_="release_date")
        if releaseDateTagList is not None and len(releaseDateTagList):
            releaseDateTag = releaseDateTagList.select("div.date")
            if releaseDateTag is not None and len(releaseDateTag):
                aGameInfo["releaseDate"] = releaseDateTag[0].text

        # Get App Developer Information
        developerRowTag = gameInfoWrap.find("div" , id="developers_list")
        developerLink = ''
        if len(developerRowTag):
            appDeveloperTagList = developerRowTag.select("a")
            if len(appDeveloperTagList):
                aGameInfo["developer"] = appDeveloperTagList[0].text
                developerLink = appDeveloperTagList[0]['href']

        # Get App Publisher Information
        publisherRowTagWrapper = gameInfoWrap.select("div.dev_row")
        if len(publisherRowTagWrapper):
            publisherRowTag = publisherRowTagWrapper[len(publisherRowTagWrapper) - 1]
            if publisherRowTag:
                appPublisherTagList = gameInfoWrap.select("a")
                if len(appPublisherTagList):
                    aGameInfo["publisher"] = appPublisherTagList[0].text

    # Get App ScreenShot Links
    screenshots = []
    # scroll to right so that loading the image
    # horizontal_bar_width = driver.find_element_by_id('highlight_slider').parent.rect['width']
    # slider = driver.select('div.slider_ctn')[0]
    # header_columns = []

    # Using iteration as span values won't show went they are hidden
    # for _ in range(4):
    #     for el in driver.find_elements_by_css_selector('#columntablejqxgrid [role="columnheader"] span'):
    #         if el.text not in header_columns and el.text != '':
    #             header_columns.append(el.text)
    #     # Ensure the slider is in view
    #     slider.location_once_scrolled_into_view
    #     ActionChains(driver).click_and_hold(slider).move_by_offset(horizontal_bar_width/4, 0).release().perform()
    # get image link

    # appLeftColPanel = pageContent.select("div#highlight_player_area a")
    # if len(appLeftColPanel):
    #     for imgTag in appLeftColPanel:
    #         screenshots.append(imgTag['href'])

    videoScreenShots = pageContent.select("div.highlight_movie")
    for videoScreenShot in videoScreenShots:
        screenshots.append({ "type": "video", "link": videoScreenShot['data-mp4-hd-source']})

    dicts = driver.execute_script("return rgScreenshotURLs;")
    for url in dicts.values():
        screenshots.append({ "type": "screenshot", "link": url.replace("_SIZE_" , ".1920x1080")})

    aGameInfo['media'] = screenshots

    # Get App Popular Tag
    tags = []
    tagsListWrapper = pageContent.select("div.glance_tags.popular_tags a")
    if len(tagsListWrapper):
        for tag in tagsListWrapper:
            tags.append(tag.text.replace("\t" , "").replace("\n" , ""))
    aGameInfo['tags'] = tags

    # Add unique tags to allTags array
    for tag in tags:
        if tag not in allTagsArray:
            allTagsArray.append(tag)

    # Get App Description
    descTag = pageContent.select("div.game_description_snippet")
    if len(descTag):
        aGameInfo["description"] = descTag[0].text.replace("\t" , "")   

    return aGameInfo , developerLink


def categoryPageParse():
    delay = 30 # load page timeout
    results = []

    inputFile = open('input_link.txt', 'r')
    inputLinks = inputFile.readlines()
    targetLink = inputLinks.pop()
    # driverCategory = webdriver.Firefox()
    driverCategory = webdriver.Chrome()

    # logFile = open('log.txt', 'a')
    # json.dump(queuedLinks, logFile, indent=4)

    addLinkToQueue({ 'link': targetLink, 'isMore': True })

    while True:

        try:
            outfile = open(filename, 'w')
            json.dump(results, outfile, indent=4)

            if len(queuedLinks) > 0:
                cuLink = queuedLinks.pop(0)
            elif len(inputLinks) > 0: 
                cuLink = inputLinks.pop(0)
            else:
                break

            linkToLoad = cuLink['link']
            currentLink = linkToLoad
            driverCategory.get(linkToLoad)

            try:
                wait = WebDriverWait(driverCategory, delay)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.block_content.page_content')))
            except TimeoutException:

                # if this page is age detect page
                pageContent = BeautifulSoup(driverCategory.page_source , "html.parser")
                ageDetectTags = pageContent.select("div.agegate_birthday_selector")
                if len (ageDetectTags): # set user's age is Jan 1, 1951
                    yearDrop = driverCategory.find_element(By.ID,'ageYear')
                    dropdown = Select(yearDrop)
                    dropdown.select_by_visible_text('1951')
                    viewPageBtns = driverCategory.find_elements(By.CSS_SELECTOR,"a.btnv6_blue_hoverfade")
                    if len(viewPageBtns):
                        viewPageBtns[0].click()
                        
                        driverCategory.get(linkToLoad)
                        wait = WebDriverWait(driverCategory, delay)
                        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.block_content.page_content')))
                else:
                    raise Exception("Timeout reached, skipping page...")

            # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.block_responsive_horizontal_scroll.store_horizontal_autoslider.block_content')))
            pageContent = BeautifulSoup(driverCategory.page_source , "html.parser")

            if cuLink['isMore']:
                moreLinks = getMoreLikeThis(pageContent)
                for eLink in moreLinks:
                    addLinkToQueue({ 'link': eLink, 'isMore': True })

            gameInfo , developerLink = parseAGame(pageContent, driverCategory)

            # set steam_link for the game
            gameInfo['steam_link'] = linkToLoad

            if developerLink.find('/search/?') < 0:
                
                companyName = gameInfo['publisher']

                driverCategory.get(developerLink)
                WebDriverWait(driverCategory, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.page_content_ctn')))
                pageContent = BeautifulSoup(driverCategory.page_source , "html.parser")
                comInfo , gameList = parseCompany(pageContent)

                comInfo['company_name'] = companyName
                comInfo['games'] = []
                comInfo['games'].append(gameInfo)

                isInserted = False
                for i in range(len(results)):
                    if results[i]['company_name'] == companyName:
                        isExistGameInfo = False
                        for eachGameInfo in results[i]['games']:
                            if eachGameInfo['publisher'] == gameInfo['publisher']:
                                isExistGameInfo = True
                        if not isExistGameInfo:
                            results[i]['games'].append(gameInfo)
                        isInserted = True

                if not isInserted:
                    results.append(comInfo)

                for eachGame in gameList:
                    addLinkToQueue({ 'link': eachGame, 'isMore': False })

                # for eachGame in gameList:
                #     driverCategory.get(eachGame)
                #     WebDriverWait(driverCategory, delay).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.block_content.page_content')))
                #     pageContent = BeautifulSoup(driverCategory.page_source , "html.parser") 
                #     gameInfo , developerLink = parseAGame(pageContent, driverCategory)
                #     if comInfo['games'].count(gameInfo) == 0:
                #         comInfo['games'].append(gameInfo)

                # results.append(comInfo)

            if len(queuedLinks) == 0 and len(inputLinks) == 0:
                break

            if len(results) >= goal:
                break
        except Exception as ex:
            failingLinksArray.append(currentLink)

    driverCategory.close()
    
    obj = {
        "failing_links": failingLinksArray,
        "all_tags": sorted(allTagsArray),
        "data": results
    }

    return obj

res = categoryPageParse ()
outfile = open(filename, 'w')
json.dump(res, outfile, indent=4)
