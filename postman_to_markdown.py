# -*- coding: UTF-8 -*-
# python 3

import os
import re
import requests
import json
from os.path import isfile, join

config = {}
template = 'temp2.md'

def list_all_files(file_path):
    return [f for f in os.listdir(file_path) if isfile(join(file_path, f))]


# 读取json文件
def load_json(path, isurl=False):
    if isurl:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0'}
        req = requests.get(path, headers=headers)
        res = json.load(req)
    else:
        with open(path, 'r', encoding='UTF-8') as load_f:
            res = json.load(load_f)
    return res


def save_file(path, string):
    with open(path, "w", encoding='UTF-8') as f:
        f.write(string)
        print(path + " - 保存文件完成")


def check_path():
    if not os.path.exists('config'):
        os.mkdir('config')
    if not os.path.exists('json'):
        os.mkdir('json')
    if not os.path.exists('markdown'):
        os.mkdir('markdown')


def run():
    check_path()
    json_path = './json'
    config_path = 'config'
    filelist = list_all_files(json_path)
    for i in range(0, len(filelist)):
        global config
        if '.json' not in filelist[i]:
            continue
        config = load_json(config_path + '/' + filelist[i])
        res = load_json(json_path + '/' + filelist[i])
        doc = view_postman(res, {})
        for ls in doc:
            url = pluck_url(doc[ls])
            filename = pluck_filename(doc[ls], '/' + re.sub('.json$', '', filelist[i]))
            description = pluck_description(doc[ls])
            method = pluck_method(doc[ls])
            header = pluck_header(doc[ls])
            query = pluck_query(doc[ls])
            body = pluck_body(doc[ls])
            result = pluck_result(doc[ls])
            explan = pluck_explan(doc[ls])
            save_markdown(url, filename, description, method, header, query, body, result, explan)


def view_postman(postman_json, doc):
    if "item" in postman_json:
        for i in postman_json['item']:
            view_postman(i, doc)
    else:
        doc[len(doc)] = postman_json
    return doc


def pluck_url(detail):
    return detail['request']['url']['raw']


def pluck_method(detail):
    return detail['request']['method']


def pluck_header(detail):
    header = ""
    if "header" in detail['request']:
        for v in detail['request']['header']:
            header += "\n" + v['key'] + ":" + v['value']
        if not header:
            return ""
    else:
        return ""
    return "**Header：**\n```%s\n```\n" % header


def pluck_body(detail):
    body = ""
    if "body" in detail['request']:
        mode = detail['request']['body']['mode']
        if mode == 'raw':
            body += detail['request']['body'][mode] + '\n';
        else:
            for v in detail['request']['body'][mode]:
                description = ''
                types = v['type']
                value = ''
                if 'disabled' in v.keys():
                    continue
                if 'ignoreBody' in config and v['key'] in config['ignoreBody']:
                    continue
                if 'value' in v.keys():
                    value = v['value']
                    if v['value'] is None:
                        value = ''
                elif 'src' in v.keys():
                    value = v['src']
                if "description" in v:
                    if "|" in v['description']:
                        description = v['description'].replace('|', ' | ')
                    else:
                        description = types + "|" + v['description'] + "| 否"
                body += "| " + v['key'] + " | " + description + " | " + value + " |\n"
        if not body:
            return ""
    else:
        return ""
    return "**Body参数：**\n\n|参数名|类型|必填|说明|参考参数|\n|:---- |:-----|:----- |:----- |----- |\n%s" % body


def pluck_query(detail):
    query = ""
    if "query" in detail['request']['url']:
        for v in detail['request']['url']['query']:
            description = ''
            types = 'string'
            value = ''
            if 'disabled' in v.keys():
                continue
            if 'ignoreQuery' in config and v['key'] in config['ignoreQuery']:
                continue
            if 'value' in v.keys():
                value = v['value']
                if v['value'] is None:
                    value = ''
            elif 'src' in v.keys():
                value = v['src']
            if "description" in v:
                if "|" in v['description']:
                    description = v['description'].replace('|', ' | ')
                else:
                    description = types + "|" + v['description'] + "| 否"
            query+= "| " + v['key'] + " | " + description + " | " + value + " |\n"
        if not query:
            return ""
    else:
        return ""
    return "**URL参数：**\n\n|参数名|类型|必填|说明|参考参数|\n|:---- |:-----|:----- |:----- |----- |\n%s" % query


def pluck_description(detail):
    if 'request' in detail:
        if 'description' in detail['request']:
            return detail['request']['description']
    return ""


def pluck_result(detail):
    result = ""
    if "response" in detail:
        if detail['response']:
            for v in detail['response']:
                vv = json.loads(v['body'])
                result += "```\n" + json.dumps(vv, indent=4, ensure_ascii=False) + "\n```\n"
            result = "**返回示例**\n\n" + result
            return result
    return ""


def pluck_explan(detail, use_def_parame=True):
    name = detail['name']
    if 'response' in detail:
        if detail['response']:
            v = json.loads(detail['response'][0]['body'])
            explan = build_explan(name, v, '', 0)
            return "**返回参数说明** \n\n|参数|类型|描述|\n|:-------|:-------|:-------|\n%s" % explan
    return ""


# 判断是否为数字
def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


def build_explan(name, body, explan, level):
    level_str = ''
    for i in range(0, level):
        level_str += "- "
    if isinstance(body, list):
        if body:
            explan = build_explan(name, body[0], explan, level + 1)
    elif isinstance(body, dict):
        for k in body:
            explan += "| " + level_str + set_def_parame(name, k)
            explan = build_explan(name, body[k], explan, level + 1)
            if is_number(k):
                break
    return explan


def pluck_filename(detail, path=''):
    path = './markdown' + path
    filename = ""
    if not os.path.exists(path):
        os.mkdir(path)
    if "response" in detail:
        filename += detail['name']
        description = pluck_description(detail)
        if description:
            filename += " " + description
    return path + "/" + filename.replace('/', '.') + ".md"


def set_def_parame(name, key, use_def_parame=True):
    param_str = ''
    param = key
    param_type = 'string'
    if is_number(key) and name in config['api'] and '#is_number' in config['api'][name]:
        if "|" in config['api'][name]['#is_number']:
            param_arr = config['api'][name]['#is_number'].split("|")
            param = param_arr[0]
            param_type = param_arr[1]
            param_str = param_arr[2]
        else:
            param = config['api'][name]['#is_number']
    if name in config['api'] and key in config['api'][name]:
        if "|" in config['api'][name][key]:
            param_arr = config['api'][name][key].split("|")
            param_type = param_arr[0]
            param_str = param_arr[1]
        else:
            param_str = config['api'][name][key]
    elif (key in config['parame']) and use_def_parame:
        if "|" in config['parame'][key]:
            param_arr = config['parame'][key].split("|")
            param_type = param_arr[0]
            param_str = param_arr[1]
        else:
            param_str = config['parame'][key]
    return param + " | %s | %s |\n" % (param_type, param_str)


"""
save_markdown:
url 读取配置文件内的参数
filename 文件类型
description 接口说明
method 请求类型
header 头部内容
query GET接口参数
body POST接口参数
result 返回示例
explan 返回参数说明
"""


def save_markdown(url='', filename='makedown.md', description='', method='', header='', query='', body='', result='',
                  explan=''):
    url = config['host'] + re.sub("{{host}}", '', url)
    url = re.sub("/[0-9]+", '/{{id}}', url)
    if "module" in config:
        if 'description' in config['module']:
            description = description if config['module']['description'] else ''
        if 'url' in config['module']:
            url = url if config['module']['url'] else ''
        if 'method' in config['module']:
            method = method if config['module']['method'] else ''
        if 'header' in config['module']:
            header = header if config['module']['header'] else ''
        if 'query' in config['module']:
            query = query if config['module']['query'] else ''
        if 'body' in config['module']:
            body = body if config['module']['body'] else ''
        if 'result' in config['module']:
            result = result if config['module']['result'] else ''
        if 'explan' in config['module']:
            explan = explan if config['module']['explan'] else ''
    string = load_template(template) % (description, url, method, header, query, body, result, explan)
    save_file(filename, string)
    return True


def load_template(filename='temp1.md'):
    return open('./template/' + filename, 'r', encoding='UTF-8').read()


run()
print(list_all_files("./json"))
