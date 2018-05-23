#coding:utf-8

import json
import os
import sys
import asyncio
import time

import aiohttp
from bs4 import BeautifulSoup
import xlwt

URL_PATTERN = "https://solutions.oracle.com/scwar/scr/Partner/{0}.html"


class AsyncCrawler():
    def __init__(self, file_path, results_file, max_threads=10):
        self.json_data = None
        self.file_path = file_path
        self.results_file = results_file
        self.max_threads = max_threads

    
    async def _crawl_website(self, session, item):
        """爬对应公司的网站"""
        print("* 正在请求网址:", item['url'])
        r = await session.get(item['url'])
        if r.status == 404:
            return None
        html = await r.read()
        print("* {0}请求成功，正在解析网页内容...".format(item['id']))
        self._parse_html(html, item)
        return 'ok'

    
    def _parse_html(self, html, item):
        """解析网页内容"""
        soup = BeautifulSoup(html, 'html.parser')
        a_tag = soup.find('div', attrs={"class":  "partner-contact"}).find("a", attrs={"class": "url"})
        item['website'] = a_tag['href']
        infos = soup.find('div', attrs={"class": "tab-content", "id": "overview"}).find("div").find("div", attrs={"class": "tab-inner"})
        index = 0
        keys = ["level", "area", "HQ", "attr", "emp_bum"]
        for p in infos.find_all("p"):
            item[keys[index]] = p.text.strip()
            index += 1


    async def _handle_task(self, queue):
        """处理任务"""
        async with aiohttp.ClientSession() as session:
            while not queue.empty():
                item = await queue.get()
                try:
                    result = await self._crawl_website(session, item)
                except Exception:
                    pass


    def _save_data(self):
        """保存数据到文件"""
        wb = xlwt.Workbook()
        ws = wb.add_sheet('oracle_asia_partners')
        ws.write(0, 0, '公司名')
        ws.write(0, 1, '公司地址')
        ws.write(0, 2, '公司网站')
        ws.write(0, 3, '会员级别')
        ws.write(0, 4, '所属地区')
        ws.write(0, 5, '总部所在地')
        ws.write(0, 6, '公有或私有企业')
        ws.write(0, 7, '员工数量')
        line = 1
        for item in self.json_data:
            print ('* 正在保存第[{0}]条数据[id:{1}]...'.format(line, item['id']))
            ws.write(line, 0, item.get('name'))
            ws.write(line, 1, item.get('add'))
            ws.write(line, 2, item.get('website'))
            ws.write(line, 3, item.get('level'))
            ws.write(line, 4, item.get("area"))
            ws.write(line, 5, item.get("HQ"))
            ws.write(line, 6, item.get("attr"))
            ws.write(line, 7, item.get("emp_num"))
            line += 1
        wb.save(self.results_file)


    def run(self):
        with open(self.file_path, 'r') as f:
            try:
                self.json_data = json.load(f)
            except Exception:
                raise Exception("加载地图数据不成功")
        if self.json_data:
            try:
                q = asyncio.Queue()
                for item in self.json_data:
                    item['url'] = URL_PATTERN.format(item['id'])
                    q.put_nowait(item)
                loop = asyncio.get_event_loop()
                tasks = [self._handle_task(q) for _ in range(self.max_threads)]
                print("* 开始抓取数据，按 Ctrl+C 中断。")
                loop.run_until_complete(asyncio.wait(tasks))
                loop.close()
                self._save_data()
                print("* 数据成功保存到{0}".format(self.results_file))
            except KeyboardInterrupt:
                print("* 手动中断...")
                self._save_data()
        else:
            raise Exception("加载地图数据为空")
        


if __name__ == "__main__":
    start = time.time()
    print("---------start----------", start)
    if len(sys.argv) >= 2:
        c = AsyncCrawler(sys.argv[1], "results.xls")
        c.run()
    else:
        print("* 未指定json文件，使用默认测试文件")
        c = AsyncCrawler("test_data.json", "results.xls")
        c.run()
    print("-----------end----------\n* 共计耗时：{0}s".format(time.time() - start))
        

