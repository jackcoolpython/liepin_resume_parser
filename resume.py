from bs4 import BeautifulSoup
import pytesseract
import base64
import time
from PIL import Image
from io import BytesIO
from collections import defaultdict
import os

class Resume():

    def __init__(self, html):
        self.html = html
        self.file_folder = os.path.split(html)[0]
        with open(html, 'rb') as f:
            html_str = f.read()
            self.soup = BeautifulSoup(html_str, "html.parser", from_encoding='utf-8')
            self.resume_type = self.soup.find('li', attrs={'class': 'active'}).text
            if self.resume_type == '中文简历':
                self._spliter = "："
            else:
                self._spliter = ":"
            self._spliters = {}
            self._spliters["："] = ":"
            self._spliters[":"] = "："
            table = self.soup.find('table', attrs={'class': 'resume-basic-info'})
            self.resume_id = self.soup.find('title').text.split('_')[0]
            self.resume_basic_info = self._process_resume_basic(table)
            self.resume_basic_info['ID'] = self.resume_id
            self.current_info = self._process_current_info(self.soup)
            self.work_info = self._process_work_info(self.soup)
            self.edu_info = self._process_edu_info(self.soup)

    def _process_resume_basic(self, table):
        table_body = table.find('tbody')
        rows = table_body.find_all('tr')
        resume_basic = defaultdict(str)
        for row in rows:
            cols = row.find_all('td')
            for col in cols:
                text = col.text.strip()
                value = None
                if text.startswith("联系电话") or text.startswith("电子邮件"):

                    text = text.split(self._spliter)[0]
                    for con in col.contents:
                        if con.name == "img":
                            value = con.attrs['src']
                            if value.startswith("data:image"):
                                msg = base64.b64decode(value.split(",")[1])
                                bytIO = BytesIO()
                                bytIO.write(msg)
                                img = Image.open(bytIO)
                                if img.format == 'GIF':
                                    img = img.convert('RGB')
                                value = pytesseract.image_to_string(img)
                            else:
                               value = pytesseract.image_to_string(os.path.join(self.file_folder, value))
                            
                            break
                else:
                    ts = text.split(self._spliter)
                    text,value = ts[0], ts[1]
                
                resume_basic[text] = value
        return resume_basic

    def _process_current_info(self, soup):
        tabs = soup.findAll("table")
        current_info = defaultdict(str)
        for tab in tabs:
            if tab.text.strip().startswith("目前职业概况") or tab.text.strip().startswith("职业发展意向"):
                table_body = tab.find('tbody')
                rows = table_body.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    for col in cols:
                        text = col.text.strip().replace(" ", "").replace("\n", "")
                        ts = text.split(self._spliter)
                        current_info[ts[0]] = ts[1]
        return current_info


    def _process_work_info(self, soup):
        work_info_list = []
        work_info = defaultdict(str)
        divs = soup.find('div', attrs={'class': 'resume-work'})
        for div in divs:
            if hasattr(div, 'attrs') and 'class' in div.attrs:
                if 'resume-job-title' in div.attrs['class']: 
                    work_time = div.find('span', attrs={'class':'work-time'}).text
                    company_list = [i.replace(" ", '') for i in div.find('em', attrs={'class':'compony'}).text.split('\n')]
                    while '' in company_list:
                        company_list.remove('')
                    company, *work_time1 = company_list
                    work_info["工作时间"] = work_time
                    work_info['公司名称'] = company
                elif 'resume-indent' in div.attrs['class']:
                    tab = div.find('table', attrs={'class':'job-list'})
                    table_body = tab.find('tbody')
                    title_row, *arch_row = table_body.find_all('tr')
                    title = title_row.find("div", attrs={'class':'job-list-title'}).text.strip()
                    work_info["职务名称"] = title

                    if len(arch_row) == 2: 
                        subos = arch_row[0].find('th').text.replace('\xa0', '').strip().split('|')
                        for i in subos:
                            if self._spliter in i:
                                attr, value = i.split(self._spliter)
                            else:
                                attr, value = i.split(self._spliters[self._spliter])
                            work_info[attr]  = value
                        work_info[arch_row[1].find('th').text.strip().split(self._spliter)[0]] = arch_row[1].find('td').text.strip()

                    if len(arch_row) == 1:
                        if arch_row[0].find('td') == None:
                            subos = arch_row[0].find('th').text.replace('\xa0', '').strip().split('|')
                            for i in subos:
                                attr, value = i.split(self._spliter)
                                work_info[attr]  = value
                        else:
                            work_info[arch_row[0].find('th').text.strip().split(self._spliter)[0]] = arch_row[0].find('td').text.strip()
                    work_info_list.append(work_info.copy())
                    work_info = defaultdict(str)
        return work_info_list


    def _process_edu_info(self, soup):
        edu_info_list = []
        edus = soup.find('div', attrs={'class': 'resume-education'}).findAll('ul', attrs={'class': 'edu-ul'})
        for edu in edus:
            edu_text = edu.find('div', attrs={'class': 'info'}).find('p').text.strip().replace(" ", '').replace("\n", '')
            if '）（' in  edu_text:
                spliter = '）（' 
            else:
                spliter = '（'
            school, times = edu.find('div', attrs={'class': 'info'}).find('p').text.strip().replace(" ", '').replace("\n", '').split(spliter)
            
            degree, types = edu.find('div', attrs={'class': 'info'}).find('p', attrs={'class': 'degree'}).text.strip().replace(" ", '').replace("\n", '').split('|')
            tips = [i.text for i in edu.find('div', attrs={'class': 'info'}).findAll('span', attrs={'class': 'tips'})]
            edu_info_list.append({'学校名称':school, "在校时间":times, "学历":degree, "学制类型":types, "学业标签":tips})
        return edu_info_list

