import os, re, urllib3

host = "127.0.0.1:8000"
url = host

headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"}

non_html_suffix = ['css', 'log', 'png', 'jpg', 'svg']


# downloaded web pages cannot directly be use for static web bec of the incomplete or invalid href and src name
def localize(response, url):
    level = len(url.split('/')) - 1  # get the depth of target url
    pattern_href = re.compile(r"href=\"(.*?)\"")
    pattern_src = re.compile(r"src=\"(.*?)\"")
    new_response = response

    # The most annoying part !!!
    # The code block below replace \n with '\n'. Without this function, there will be line break inside js, which will
    # cause grammar error.
    # The function is achieved by first focus only on the \n between '[{' and '}]'. Then check if there is \n in the
    # focused region. If there is, replace one \n with 'xxx'. Keep doing this until there is no \n. Finally replace 'xxx'
    # with '\n'. Note: if we dont use 'xxx' as medium, the loop will be infinite, as python cant distinguish \n and '\n'
    r = re.compile(r'(\[\{.*)\n(.*\}\])', re.DOTALL)  # with re.DOTALL, dot(.) will represent all the symbol, otherwise dot does not include \n, which will failed the match when there are more than one \n in between
    while r.findall(new_response):
        new_response = r.sub(r'\1xxx\2', new_response)
    new_response = re.sub(r'xxx', r'\\n', new_response)

    for url in pattern_href.findall(new_response):
        if url and 'http' not in url and url[0] != '#':  # ignore cases of empty, http url and 'href="#id"'
            modified_url = url
            if url == '/':  # for case 'href="/"'
                modified_url = '/index'
            elif url[0] != '/':  # for case 'href="..."'
                modified_url = '/' + url
            elif '/#' in url:  # for case 'href="/#id"'
                modified_url = url.replace('/#', '/index#')
            if modified_url .split('.')[-1] not in non_html_suffix:  # for case the url is not html
                if '#' in url:
                    modified_url = modified_url.replace('#', '.html#')  # for case that 'href="/...#id"'
                else:
                    modified_url = modified_url + '.html'
            modified_url = re.sub(r'\?', '-', modified_url)

            # There is '?' inside url. if put it in regx, '?' will be regarded as a function mark rather than '?' itself
            url = re.sub(r'\?', r'\\?', url)
            pat = r"(href=\")\s*{}\s*(\")".format(url)  # add \s to make it robust to space

            if level == 2:
                new_response = re.sub(pat, r'\1../..' + modified_url + r'\2', new_response)  # partial replacement
            elif level == 1:
                new_response = re.sub(pat, r'\1..' + modified_url + r'\2', new_response)
            elif level == 0:
                new_response = re.sub(pat, r'\1.' + modified_url + r'\2', new_response)


    for url in pattern_src.findall(response):
        if url and 'http' not in url:
            modified_url = url
            pat = r"(src=\"){}(\")".format(url)
            if url[0] != '/':  # for case 'src="..."'
                modified_url = '/' + url
            if level == 2:
                new_response = re.sub(pat, '\\1../..' + modified_url + '\\2', new_response)
            elif level == 1:
                new_response = re.sub(pat, '\\1..' + modified_url + '\\2', new_response)
            elif level == 0:
                new_response = re.sub(pat, '\\1.' + modified_url + '\\2', new_response)

    return new_response


# fully traverse the target website and download all the .html files meanwhile localize them.
def getStatic(host, path=''):
    not_visited = ['/']
    links = ['/']
    http = urllib3.connection_from_url(host)

    while not_visited:
        url = not_visited.pop()
        if url.split('.')[-1] not in non_html_suffix:
            request = http.request('GET', url, headers=headers)
            response = request.data.decode('unicode_escape')
            if url == '/':
                url = 'index'
            if url[0] == '/':  # remove slash for both side
                url = url[1:]
            if url[-1] == '/':
                url = url[:-1]
            if '/' in url:
                dir = path + '/'.join(url.split('/')[:-1])
                if not os.path.exists(dir):
                    os.makedirs(dir)

            target_url = path + url + '.html'
            target_url = re.sub(r'\?', '-', target_url)  # '?' is invalid for file name. "?" may appear on url
            with open(target_url, "w", encoding='utf-8') as file:
                file.write(localize(response, url))
                print(url + '.html finished')

            pattern = re.compile(r"href=\"(.*?)\"")
            for candidate_url in pattern.findall(response):
                candidate_url = re.sub(r'#.*', '', candidate_url)
                if candidate_url and 'http' not in candidate_url and 'https' not in candidate_url and candidate_url not in links:
                    not_visited.append(candidate_url)
                    links.append(candidate_url)


def verify(host):
    http = urllib3.connection_from_url(host)
    not_visited = ['/']
    links = ['/']
    while not_visited:
        url = not_visited.pop()
        if url.split('.')[-1] not in non_html_suffix:
            request = http.request('GET', url, headers=headers)
            print(url, request.status)
            response = request.data.decode('unicode_escape')
            print(response)
            pattern = re.compile(r"href=\"(.*?)\"")
            for candidate_url in pattern.findall(response):
                candidate_url = re.sub(r'#.*', '', candidate_url)
                if candidate_url and 'http' not in candidate_url and 'https' not in candidate_url and candidate_url not in links:
                    not_visited.append(candidate_url)
                    links.append(candidate_url)
        print(not_visited)


if __name__ == "__main__":
    getStatic(url, '')
    # a = "[{'desc': '<h2 id='three-colors'>Three colors</h2> \n <p>What is the color of 'dawn- \n Scarlet</p>'ssssss}][a\nb]"
    # b = "{asad\nasdasd}"
    # r = re.compile(r'\[.*\n.*\]', re.DOTALL)
    # r1 = re.compile(r'(\[.*)\n(.*\])', re.DOTALL)
    # while r.findall(a):
    #     a = r1.sub(r'\1xxx\2', a)
    #     #print(a)
    # a = re.sub(r'xxx', r'\\n', a)
    # print(a)



