from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')
driver = webdriver.Chrome("C:/Users/saina/AppData/Local/Google/Chrome/Application/chrome.exe", chrome_options=options)

driver.get('https://www.goconqr.com/en-US/search?q=electrodynamics%20quiz')
driver.implicitly_wait(10)

page = driver.page_source
print(page)