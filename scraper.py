import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from simhash import Simhash, SimhashIndex

CHAR_THRESHOLD = 300
MAX_SUBDOMAIN_THRESHOLD = 10
trap_subdomain_urls = dict()
# contains a dictionary of text data of all the urls with the same path but different queries
simhash_dict = dict()
simhash_indicies = SimhashIndex([(str(k), Simhash(get_features(v))) for k, v in simhash_dict.items()], k=3)

# report 1
unique_links = set()
# report 2
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
    if resp == None or resp.status != 200 or resp.raw_response == None:
        return list()
    soup = BeautifulSoup(resp.raw_response.content, 'lxml') # convert the content of the website to BeautifulSoup

    if len(soup.get_text()) <= CHAR_THRESHOLD:
        return list()

    #####################################  Simhash similarity
    sh_obj = Simhash(get_features(soup.get_text()))
    if sh_obj.value in simhash_dict: # check for exact duplicates
        return list()
    elif len(simhash_indicies.get_near_dups(sh_obj)) != 0: # check for near duplicates via simhash
        return list()
    else: # store simhash object data and indicies for future comparisons
        simhash_dict[sh_obj.value] = sh_obj
        simhash_indicies.add(sh_obj.value, sh_obj)

    ##################################### Longest page for report #2
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
        link = urljoin(url, link.get('href')) # convert relative url to absolute
        if link != None:
            urls.append(link.split('#')[0]) # defragment the url before appending it to the frontier
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

        # common trap patterns
        trap_detection_patterns = [
                                    r'.*/appointment.*', # for appointment trap detection
                                    r'.*/calendar.*'     # for calendar trap detection
                                    ]

        if any(re.match(pattern, parsed.path.lower()) != None for pattern in trap_detection_patterns):
            return False

        # avoid repeated patterns
        # r"^.*?(/.+?/).*?\1.*$"
        # r'^.*(/\S+)\1+.*$'
        if re.match(r'^.*?(/.+?/).*?\1.*$', parsed.path.lower()) != None:
            return False

        ##################################### website trap detection (swiki, wiki, gitlab, etc.)
        # for every path that we enter for websites such as swiki or wiki, only get max 
        # threshold # of websites of each path/subdirectory and disregard the query
        #
        # We don't want to completely disregard all paths, but since accessing every
        # possible query within the paths leads to a trap, we will only retrieve a 
        # certain threshold amount from each path within the website.
        #
        # We saw that query specific links within the same path didn't have any
        # additional useful information
        trap_patterns = [r'.*swiki.*', r'.*wiki.*', r'.*elms.*', r'.*gitlab.*']
        if any(re.match(pattern, parsed.hostname.lower()) != None for pattern in trap_patterns):
            # url without the query
            no_q = url.split('?')[0]
            if trap_subdomain_urls.get(no_q, 0) > MAX_SUBDOMAIN_THRESHOLD:
                return False
            else:
                trap_subdomain_urls[no_q] = trap_subdomain_urls.get(no_q, 0) + 1

        ##################################### gitlab specific "traps"
        # we will deem some parts of gitlab repos as pages with low information content
        # such as project specific commit/commit histories
        if re.match(r'.*gitlab.*', parsed.hostname.lower()) != None:
            gitlab_filters =   [r'.*/commits/.*', 
                                r'.*/commit/.*', 
                                r'.*/graphs/.*', 
                                r'.*/network/.*', 
                                r'.*/tree/.*',
                                r'.*/raw/.*',
                                r'.*/find_file/.*']
            if any(re.match(pattern, parsed.path.lower()) != None for pattern in gitlab_filters):
                return False

        # filter certain datasets in the ml archive
        if re.match(r'.*datasets.php.*', parsed.path.lower()) != None and re.match(f'.*format=.*', parsed.query) != None:
            return False

        
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|mpe?g|ppsx|img|war|py|java|c|asm|atom|apk|rs|ds_store|git" # additional extensions to filter
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

# Reference: https://leons.im/posts/a-python-implementation-of-simhash-algorithm/
def get_features(s):
    width = 3
    s = s.lower()
    s = re.sub(r'[^\w]+', '', s)
    return [s[i:i + width] for i in range(max(len(s) - width + 1, 1))]

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