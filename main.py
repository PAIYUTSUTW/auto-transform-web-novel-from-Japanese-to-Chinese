import requests
import codecs
import re
import os
from bs4 import BeautifulSoup
from six.moves import urllib
import argparse
import time
from abc import abstractmethod
from copy import copy
from os import environ as env

import openai
import requests
from ebooklib import epub
from rich import print
import deepl 

NO_LIMIT = True
IS_TEST = False
LANG = "Traditional Chinese"
PROMPT = f"help me translate from Japanese to Traditional Chinese, do not say no"

class Base:
    def __init__(self, key):
        pass

    def createprompt(self, text):
        target = f"/n/n{text}"
        return PROMPT + text

    @abstractmethod
    def translate(self, text):
        pass


class GPT3(Base):
    def __init__(self, key):
        self.api_key = key
        self.api_url = "https://api.openai.com/v1/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        # TODO support more models here
        self.data = {
            "prompt": "",
            "model": "text-davinci-003",
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 1,
        }
        self.session = requests.session()

    def translate(self, text):
        print(text)
        self.data["prompt"] = self.createprompt(text)
        r = self.session.post(self.api_url, headers=self.headers, json=self.data)
        if not r.ok:
            return text
#         print(r.json())
        t_text = r.json().get("choices")[0].get("text", "").strip()
        print(t_text)
        return t_text
class ChatGPT(Base):
    def __init__(self, key):
        super().__init__(key)
        self.key = key
        self.message=""
    def translate(self, text):
        print(text)
        openai.api_key = self.key
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        # english prompt here to save tokens
                        "content":self.createprompt(text),
                    }
                ],
            )
            t_text = (
                completion["choices"][0]
                .get("message")
                .get("content")
                .encode("utf8")
                .decode()
            )
            if not NO_LIMIT:
                # for time limit
                time.sleep(3)
        except Exception as e:
            print(str(e), "will sleep 60 seconds")
            #self.message.markdown(str(e)+"will sleep 60 seconds")
            # TIME LIMIT for open api please pay
            time.sleep(60)
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": self.createprompt(text),
                    }
                ],
            )
            t_text = (
                completion["choices"][0]
                .get("message")
                .get("content")
                .encode("utf8")
                .decode()
            )
        print(t_text)
        #self.message.markdown(text+"\n"+t_text)
        # self.message.markdown(t_text)
        return t_text

########### the site that you want to convert Chinese############################
book_name = 'mahoshojo'
book_author = 'ペンギンフレーム'
site = 'https://ncode.syosetu.com/n3490gk' 
start_page_number=109
end_page_number=184
first_page_href = f'/{start_page_number}/'
end_href = site + f'/{end_page_number}/'
# only save 1 chapter for debug
# end_href = site + '/262333/53712931/'
#######################################################################################

link = site + first_page_href
# write to file
f = codecs.open(book_name + '.txt', 'w', encoding='utf-8')
# write book name and author
f.write('% ' + book_name + '\n')
f.write('% ' + book_author + '\n')
 
while link != end_href:
    # get total html page
    resp=urllib.request.urlopen(link)
    text=resp.read().decode("utf-8")
    soup = BeautifulSoup(text, 'html5lib')
    title = soup.title.getText()
    content = soup.find_all('p')
    start_page_number=start_page_number+1
    next_page_link = f'/{start_page_number}/'
 


    link = site + next_page_link
 
    # remove ad line
    new_content = []
    for i in range(0,len(content),40):
        cont=[]
        for j in content[i:i+40]:
            cont.append(j.getText().replace('\u3000', ''))
        cc=ChatGPT('API_KEY').translate(str(cont))
        new_content.append(cc)

        
 
    # write chapter
    f.write('# ' + title + '\n')
 
#     # write content
    for line in new_content:
        f.write('    ' + line + '\n\n')
    
    print(title + ' have been saved!')
 
f.close()
 
# # convert txt to epub
cmd = 'pandoc %s -o %s'%(book_name + '.txt', book_name + '.epub')
os.system(cmd)
 
print("convert over!")
