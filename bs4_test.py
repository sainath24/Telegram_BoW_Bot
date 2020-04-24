from bs4 import BeautifulSoup
import requests

url = 'https://www.oercommons.org/search?f.search=algebra&f.general_subject=mathematics&f.sublevel=high-school&f.alignment_standard='


page = requests.get(url)

soup = BeautifulSoup(page.text,'html.parser')
div = soup.findAll('div',{'class':'item-title'})

for res in div:
    rurl = res.find('a',{'class':'item-link js-item-link'}).get('href')
    if '/courses/' in rurl:
        print(res.find('a',{'class':'item-link js-item-link'}).contents[0]) #Title
        print(rurl + '\n')
        u = rurl + '/view'  #Link to reource on oer
        print(u)
        p = requests.get(u)
        s = BeautifulSoup(p.text,'html.parser')
        d = s.findAll('div',{'class':'modal-footer'})
        for r in d:
            try:
                furl = r.find('a',{'class':'js-continue-redirect-button'}).get('href') #Link to actual reosource that will be sent to user
                print(furl + '\n\n')
            except:
                continue
        # for d1 in d:
        #     print(d1)
        #     for r in d1:
        #         print(r)
                
        #             furl = r.find('a',{'class':'js-continue-redirect-button'}).get('href')
        #             print(furl + '\n\n')

    
