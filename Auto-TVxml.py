"""
//*Copyright(C),贝壳智慧家工作室
//*FileName:IPTV-自动爬取EPG 生成TVXML文件
//*Author:@珊瑚
//*Version:v1.5
//*Date:2023.11.21
//*Description:用于爬取本地IPTV频道列表对应的TVXML 测试环境Ubuntu+Python3.10.11
//*Others:后续按EPG API接口更新版本
"""

import re,time
import json
import requests
import codecs

# 原始数据来源地址

m3u_url='https://raw.githubusercontent.com/chenzj511/TVlive/main/m3u/chenzj_tvlive.m3u'
epg1_api='https://epg.112114.xyz/?ch='
epg2_api='https://diyp.112114.xyz/?ch='
epg3_api='http://epg.erw.cc/api/diyp/?ch='
epg4_api='http://epg.51zmt.top:8000/api/diyp/?ch='
header={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'}

# 定义频道原始数据获取函数
def fetch_m3u_data(m3u_url):
    response = requests.get(m3u_url,headers=header)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch M3U data. Status code: {response.status_code}")

# 定义道ID和频道名提取字典建立函数
def extract_tvg_info_from_m3u(m3u_data):
    pattern = re.compile(r'#EXTINF:-1 tvg-id="(.*?)" tvg-name="(.*?)"', re.DOTALL|re.I)
    matches = pattern.findall(m3u_data)
    
    tvg_dict = {}
    for match in matches:
        tvg_id, title = match[0], match[1]
        tvg_dict[tvg_id] = title 
    print('节目列表提取成功，共计',len(tvg_dict),'个频道')
    # print(tvg_dict)
    tvg_list = []

    for key in tvg_dict:
        tvg_list.append('<channel id=\"'+key+'\">\n')
        tvg_list.append('<display-name lang="zh">'+tvg_dict[key]+'</display-name>\n')
        tvg_list.append('</channel>\n')       
    tvg_string = "".join(tvg_list)
    # print(my_string)
    
    return tvg_string,tvg_dict

# 定义频道TVXML数据API数据获取函数
def epg_api_data(tvg_id,tvg_name):
    epg_date=requests.get(epg1_api+tvg_name,headers=header)
    if tvg_name == 'CCTV1':
        s = epg_date.json()['epg_data'][0]["title"]
       # print(s,":orgin")
       # if isinstance(s,str):
            #print(s.encode('GBK').decode('GBK'),':str')
      #  else:
          #  print (s.decode('GBK'),'unicode')
  #    print(tvg_name, '==',codecs.encode(str(epg_date.json()['epg_data'][0]),'gb2312') , '!!\n')
    search_string = "精彩节目"
    
    # str_title = epg_date.content.decode('GBK')
    str_title = epg_date.json()['epg_data'][0]["title"]
   # print (str_title,"==\n")
    if '精彩节目' in str_title or tvg_name in '卡酷少儿 纪实科教':
        print(tvg_name,'的EPG节目信息在API1中不存在或不准确 已更换为API2')
        epg_date=requests.get(epg3_api+tvg_name,headers=header)
        str_title2 = epg_date.json()['epg_data'][0]["title"]
        print(tvg_name, '=2=',str_title2, '!2!\n')
        if  '精彩节目' in str_title2:  
           print(tvg_name,'的EPG节目信息在API1和API2中不存在或不准确 已更换为API3')
         #  epg_date=requests.get(epg3_api+tvg_name,headers=header)
         #  str_title3 = epg_date.json()['epg_data'][0]["title"]
         #  print(epg_date.text,"333\n")
    json_data = epg_date.json()

    # 创建空字符串用于存放 epg 内容
    xml_list = []
 
    # 遍历该频道当天所有节目信息
    for epg in json_data["epg_data"]:
        if epg['start'] == '00:00' and epg['end'] == '23:59':   # 剔除错误数据，此处为00:00开始，23:59结束的节目-明显错误内容
            print(tvg_name,'包含重复错误节目信息，已剔除') # 输出包含错误信息的频道名
            continue           
        
        start_time = f"{json_data['date'].replace('-', '')}{epg['start'].replace(':', '')}00 +0800"
        end_time = f"{json_data['date'].replace('-', '')}{epg['end'].replace(':', '')}00 +0800"
        title = epg["title"].replace("<", "《").replace(">", "》").replace("&", "&amp;") #替换xml文件中的一些禁用字符

        xml_list.append('<programme start=\"'+start_time+'\" stop=\"'+end_time+'\" channel=\"'+tvg_id+'\">\n')
        xml_list.append('<title lang="zh">'+title+'</title><desc lang="zh"></desc>\n')
        xml_list.append('</programme>\n')

    xml_string = "".join(xml_list)
  
    return xml_string

m3u_data = fetch_m3u_data(m3u_url)

tvg_info,tvg_info_dict = extract_tvg_info_from_m3u(m3u_data)

# 创建一个空列表存储所有EPG数据
tvxml_list = []
tvxml_list.append('<?xml version=\"1.0\" encoding=\"UTF-8\"?><!DOCTYPE tv SYSTEM \"http://api.torrent-tv.ru/xmltv.dtd\">\n')
tvxml_list.append('<tv generator-info-name=\"https://epg.shellykoral.com\" generator-info-url=\"koral@shellykoral.com\">\n')

#输出频道ID和频道名到TVXML
tvxml_list.append(tvg_info)

#输出输出节目EPG到TVXML
for key in tvg_info_dict:
    xml_string = epg_api_data(key,tvg_info_dict[key])
    # time.sleep(0.1)
    print(tvg_info_dict[key],'已完成')
    tvxml_list.append(xml_string)

tvxml_list.append('</tv>')
tvxml_string = "".join(tvxml_list)


with open("tvxml.xml", "w", encoding="utf-8") as xml_file:
    xml_file.write(tvxml_string)

#测试
# xml_string = epg_api_data('A03','CNA')
# time.sleep(0.3)
# print(xml_string)
# # with open("TVXML.xml", "a", encoding="utf-8") as xml_file:
# #     xml_file.write(xml_string)
