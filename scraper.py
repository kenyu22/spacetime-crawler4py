import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

WORD_THRESHOLD = 300
unique_links = set()
max_word_link = ''
max_words = 0

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    # check that the return code is valid 
    if resp == None or resp.status != 200:
        return list()
    soup = BeautifulSoup(resp.raw_response.content, 'lxml') # convert the content of the website to BeautifulSoup

    if len(soup.get_text()) <= WORD_THRESHOLD:
        return list()

    words = [word.lower() for word in re.findall(r"[a-zA-Z][a-zA-Z0-9]*'?[a-zA-Z0-9]*", soup.get_text())]
    num_words = len(words)
    global max_words
    if max_words is None:
        max_words = num_words
    elif max_words < num_words:
        max_words = num_words
        global max_word_link
        max_word_link = url
    
    unique_links.add(url) # keep track of the valid links in a set

    urls = []
    for link in soup.find_all('a'): # retrieve all urls from the soup
        link = link.get('href')
        if link != None:
            urls.append(link.split('#')[0])
            
        #print(urls[-1])
    
    return urls

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)

        if parsed is None or parsed.hostname is None:
            return False

        if parsed.scheme not in set(["http", "https"]):
            return False

        # check that we have a valid domain specified by the assignment constraints
        valid_suffix_list = [r'^.+\.ics\.uci\.edu.*$', r'^.+\.cs\.uci\.edu.*$'\
                            , r'^.+\.informatics\.uci\.edu.*$', r'^.+\.stat\.uci\.edu.*$']
        if all([re.match(domain, parsed.hostname)==None for domain in valid_suffix_list]):
            return False
        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

def generate_report():
    # generate the report with all questions from canvas and their corresponding answers
    report = open('report.txt', 'w')

    # Question 1
    question_1 = ['1. How many unique pages did you find? \n', f'There are {len(unique_links)} unique links.\n\n']
    # Question 2
    question_2 = ['2. What is the longest page in terms of the number of words? \n', f'The longest page in terms of the number of words is {max_word_link}.\n\n']
    # Question 3

    # write answers to report file
    for i in range(4):
        report.writelines(f'question_{i+1}')
    # close the report after all questions have been answered
    report.close()