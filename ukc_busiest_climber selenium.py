import requests
import urllib.request
import time
from bs4 import BeautifulSoup
import webbrowser
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import os
from googlesearch import search
from datetime import datetime
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
chrome_path = 'open -a /Applications/Google\ Chrome.app %s'
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DRIVER_BIN = os.path.join(PROJECT_ROOT, "chromedriver")
options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(executable_path = DRIVER_BIN, chrome_options=options)

choice = input("\nLook at single crag or multiple? Enter S or M: ").lower()

while choice not in ["s", "m"]:
    choice = input("\nEnter only S or M: ").lower()

multiple = False

# function returning BeautifulSoup from supplied url
def give_soup(url):
    response = requests.get(url, headers=headers)
    return BeautifulSoup(response.text, 'html.parser')

# returning BeautifulSoup from a site that requires Selenium to load
def give_selenium_soup(url):
    driver.get(url)
    return BeautifulSoup(driver.page_source, 'html.parser')

# if searching for multiple crags (within a guidebook)
if choice == "m":
    multiple = True
    # Enter guidebook here
    soup = give_soup(input("\nWhat is the guidebook url? "))
    # gets the guidebook name from the site
    guidebook = soup.find("div", {"class": "col-md-12"}).find("h1").text
    file_name = guidebook

    if " " in guidebook:
        file_name = guidebook.replace(" ", "_")
    
    craglist = {}

    for table in soup.findAll("table", {"class": "small table table-sm"}):
        
        for link in table.findAll("a"):
            craglist[link.text] = "https://www.ukclimbing.com" + link.get("href")

# if searching for a single crag
else:
    crag_search = input("\nWhat crag do you want to look at? ")
    url = list(search(crag_search + " ukc", tld="co.in", num=1, stop=1, pause=1))[0]
    soup = give_soup(url)
    craglist = {soup.find("title").text[14:]:url}
    file_name = soup.find("h1").text

    if " " in file_name:
        file_name = "_".replace(" ", "_")

# function for loading a crag page using Selenium as the javascript won't load through BeautifulSoup
def get_climbs(url, crag, retry = False):
    if data_choice == 'y' and not retry:

        try:
            results = json.load(open(crag.lower().replace(" ", "_") + "_climbs.txt"))
            print("Saved data found for {}!".format(crag))
            return results

        except FileNotFoundError:
            print("No saved data found for {}, scraping climbs now...".format(crag))
    
    driver.get(url)
    time.sleep(1)
    # pulling all the climbs from the page
    results = {str(i.text):str(i.get_attribute("href")) for i in driver.find_elements_by_xpath('//a[@class=" small not-small-md"]')}

    while not results:
        print("Issue loading {}, trying again.".format(crag))
        results = get_climbs(url, crag, True)

    if results and not retry:
        print("Download successful from {}, {} climbs downloaded!".format(crag, len(results)))
    
    # save climbs to .txt file so they don't have to be scraped every time
    json.dump(results, open(crag.lower().replace(" ", "_") + "_climbs.txt",'w'))
    return results

data_choice = input("\nUse existing data? Enter Y/N: ").lower()

print("Logging in...")
driver.get("https://www.ukclimbing.com/user/")
username = driver.find_element_by_id("email")
password = driver.find_element_by_id("password")
username.send_keys("t123")
password.send_keys("123456")
password.send_keys(Keys.ENTER)

crag_dict_of_dicts = {crag:get_climbs(craglist[crag], crag) for crag in craglist.keys()}
climber_dict_of_dicts = {}
text_file = open(file_name + "_busiest_climbers.txt","w")

# number of top climbers to have ranked
limit = 10

if multiple:
    print("Busiest climbers in the area covered by {} as of {}:\n".format(guidebook, datetime.now().strftime("%H:%M:%S, %d/%m/%Y")), file=text_file)

else:
    print("Busiest climbers in {} as of {}:\n".format([x for x in crag_dict_of_dicts.keys()][0], datetime.now().strftime("%H:%M:%S, %d/%m/%Y")), file=text_file)

for crag_dict in crag_dict_of_dicts.keys():
    climber_dict = {}

    if data_choice == "n":

        # this deletes existing file if it exists so a new one can replace it later
        try:
            os.remove(crag_dict.lower().replace(" ", "_") + "_climbers.txt")
        
        except FileNotFoundError:
            print("No existing data found for {}!".format(crag_dict))

    try:
        climber_dict = json.load(open(crag_dict.lower().replace(" ", "_") + "_climbers.txt"))

        if climber_dict:
            print("Loading {} from file...".format(crag_dict))

    except FileNotFoundError:
        print("\nNow scraping {}:".format(crag_dict))

        for climb in crag_dict_of_dicts[crag_dict]:
            print("\n" + climb)
            soup = give_selenium_soup(crag_dict_of_dicts[crag_dict][climb])
            
            # if this is a match then the climb has been done clean
            criteria = [
            "Lead O/S", "Lead β", "Lead RP", "Lead rpt", "Lead", "Lead G/U",
            "Sent O/S", "Sent β", "Sent x", "Sent",
            "Solo O/S", "Solo β", "Solo RP", "Solo rpt", "Solo", "Solo G/U",
            "AltLd O/S", "AltLd β", "AltLd RP", "AltLd rpt", "AltLd", "AltLd G/U",
            "-"]
            
            # check if climb is top-rope only (eg. Southern Sandstone)
            if "Top Rope" in soup.find("small", {"class": "text-nowrap text-dark"}).text:
                criteria += ["TR O/S", "TR β", "TR RP", "TR rpt", "TR", "TR G/U"]
            
            try:
                # returns set of climbers who have done this climb clean
                climbers = set(climber.find("a").text.strip("    \nu\n\n") for climber in soup.find("div", {"id": "public_logbooks"}).findAll("tr") if climber.find("td", {"class":"profile_name"}) if climber.findAll("td")[2].text in criteria)
                
                # if people have climbed this but no one has done it clean
                if not climbers:
                    print("No recorded clean or public ascents.")
                    continue

                print(climbers)

                # adding climbers to dict number of climbs they've done
                for climber in climbers:

                    if climber not in climber_dict.keys():
                        climber_dict[climber] = [climb]

                    else:
                        climber_dict[climber].append(climb)
            
            # this returns only if the ukc logbook for the climb states 'no ascents logged'
            except AttributeError:
                print("No ascents logged.")
                continue
        
        # saves data so that this doesn't need to be done every time
        json.dump(climber_dict, open(crag_dict.lower().replace(" ", "_") + "_climbers.txt",'w'))

    if multiple:
        climber_dict_of_dicts[crag_dict] = climber_dict

    top_climbers = sorted(climber_dict, key=lambda k: len(climber_dict[k]), reverse=True)[:limit]

    print("Top {} busiest climbers at {}:".format(limit, crag_dict), file=text_file)
    print("Top {} busiest climbers at {}:".format(limit, crag_dict))

    for climber in top_climbers:
        print("\n{}. {} with {}/{} climbs, {}% ticked.".format(top_climbers.index(climber)+1, climber, len(climber_dict[climber]), len(crag_dict_of_dicts[crag_dict]), round(len(climber_dict[climber])/len(crag_dict_of_dicts[crag_dict]) * 100, 2)))
        print("\n{}. {} with {}/{} climbs, {}% ticked.".format(top_climbers.index(climber)+1, climber, len(climber_dict[climber]), len(crag_dict_of_dicts[crag_dict]), round(len(climber_dict[climber])/len(crag_dict_of_dicts[crag_dict]) * 100, 2)), file=text_file)

    print("\n", file=text_file)
    print("")

driver.quit()
    
if multiple:
    combined_climber_dict = {}

    for crag_dict in climber_dict_of_dicts.keys():
        
        for climber in climber_dict_of_dicts[crag_dict].keys():

            if climber not in combined_climber_dict.keys():
                combined_climber_dict[climber] = climber_dict_of_dicts[crag_dict][climber]

            else:
                combined_climber_dict[climber] += climber_dict_of_dicts[crag_dict][climber]

    top_climbers = sorted(combined_climber_dict, key=lambda k: len(combined_climber_dict[k]), reverse=True)[:limit]
    climb_total = 0

    for crag in crag_dict_of_dicts:
        climb_total += len(crag_dict_of_dicts[crag])

    print("Top {} busiest climbers in the area covered by {}:".format(limit, guidebook))
    print("Top {} busiest climbers in the area covered by {}:".format(limit, guidebook), file=text_file)

    for climber in top_climbers:
        print("\n{}. {} with {}/{} climbs, {}% ticked.".format(top_climbers.index(climber)+1, climber, len(combined_climber_dict[climber]), climb_total, round(len(combined_climber_dict[climber])/climb_total * 100, 2)))
        print("\n{}. {} with {}/{} climbs, {}% ticked.".format(top_climbers.index(climber)+1, climber, len(combined_climber_dict[climber]), climb_total, round(len(combined_climber_dict[climber])/climb_total * 100, 2)), file=text_file)

text_file.close()