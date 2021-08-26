import requests 
import bs4
import time
import json
import sys
import os
from urllib.parse import urlparse

mediaMimes = ['jpg', 'webp', 'png', 'mp3', 'mp4', 'gif', 'jpeg', 'jfif', 'pdf', 'rar', 'zip', 'exe']

def excluded(link, exclusionRules):
    for substring in exclusionRules:
        if substring in link:
            return True
    return False

def getCode(link):
    try:
        return requests.head(link, timeout=10).status_code
    except:
        return 'ERROR'

def getYoutubeCode(link):
    if 'youtube.com/embed/' in link:
        pos = link.find('embed/') + len('embed/')
        yId = link[pos:pos + 11]
    elif 'youtube.com/watch?v=' in link:
        pos = link.find('watch?v=') + len('watch?v=')
        yId = link[pos:pos + 11]
    elif 'youtu.be/' in link:
        pos = link.find('youtu.be/') + len('youtu.be/')
        yId = link[pos:pos + 11]
    else:
        return getCode(link)
    return getCode('https://img.youtube.com/vi/' + yId + '/mqdefault.jpg')

def request(page):
    req = requests.get(page)
    res = req.content 
     
    soup = bs4.BeautifulSoup(res,'html5lib') 
    anchor_tags = soup.find_all("a") 
    links = [tag.get('href') for tag in anchor_tags]

    anchor_tags = soup.find_all("img") 
    links += [tag.get('src') for tag in anchor_tags]

    anchor_tags = soup.find_all("iframe") 
    links += [tag.get('src') for tag in anchor_tags]

    anchor_tags = soup.find_all("source") 
    links += [tag.get('src') for tag in anchor_tags]

    results = []
    urlParse = urlparse(page)
    for e in links:
        if e:
            if e[0] == '#':
                pass
            elif e[:2] == '//':
                results += [urlParse.scheme + ':' + e]
            elif e[0] == '/':
                results += [urlParse.scheme + '://' + urlParse.netloc + e]
            elif e[:7] == 'http://':
                results += [e]
            elif e[:8] == 'https://':
                results += [e]
            elif e[:3] == '../':
                parentFolder = '/'.join(page.split('/')[:-1]) + '/'
                results += [parentFolder + e[3:]]
            else:
                parentFolder = '/'.join(page.split('/')[:-1]) + '/'
                results += [parentFolder + e]
                
    return results

                


configPath = sys.argv[1]



with open(configPath, 'r') as f:
    data = json.load(f)
    currentPage = data['startingPage']
    domain = data['domain']
    exclusionRules = data['excludes']

pageToCrawl = [currentPage]
visitedPages = []
outboundPages = []
medias = []

visitedPagesCSV = []
outboundPagesCSV = []
mediasCSV = []

while pageToCrawl:
    currentPage = pageToCrawl[0]
    print('Current page:', currentPage)
    linksInPage = request(currentPage)

    # Apply exclusionRules
    linksToKeep = []
    for link in linksInPage:
        if not excluded(link, exclusionRules):
            linksToKeep += [link]
    linksInPage = linksToKeep

    for link in linksInPage:
        if domain not in link:
            if link not in outboundPages:
                #print('Outbound found:', link)
                outboundPages += [link]
                if 'youtube.com' in link:
                    outboundPagesCSV += [[link, currentPage, str(getYoutubeCode(link))]]
                else:
                    outboundPagesCSV += [[link, currentPage, str(getCode(link))]]
        elif link.split('.')[-1] in mediaMimes or ('data:' in link and 'base64' in link):
            if link not in medias:
                #print('Media found:', link)
                medias += [link]
                mediasCSV += [[link, currentPage, str(getCode(link))]]
        elif link not in pageToCrawl:
            if link not in visitedPages:
                pageToCrawl += [link]
            
    pageToCrawl.remove(currentPage)
    visitedPages += [currentPage]
    visitedPagesCSV += [[currentPage, str(getCode(currentPage))]]

outputFolder = configPath[:-5] + '/'
os.mkdir(outputFolder)

with open(outputFolder + "visitedPages.csv", "w") as f:
    for link in visitedPagesCSV:
        f.write('"' + '","'.join(link) + '"' + '\n')

with open(outputFolder + "outboundPages.csv", "w") as f:
    for link in outboundPagesCSV:
        f.write('"' + '","'.join(link) + '"' + '\n')

with open(outputFolder + "medias.csv", "w") as f:
    for link in mediasCSV:
        f.write(','.join(link) + '\n')

