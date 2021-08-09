
import re
import requests
import sys
import argparse

class Scrappy:

    def get_url_response(self, url):
        
        # Some sites will deny requests if they do not have a valid User-Agent value which belongs to a browser.
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
        try:
            response = requests.get(url,headers={'User-Agent': user_agent})
        except Exception as e:
            return ""
        return response.text

    def get_links_to_scrape(self, url):
        print(f"scraping URLs from {url}")

        # 'https?:            --> This will match either http: or https:
        # [0-9A-Za-z/-_.=?]+  --> This will match the rest of the url part. A space denotes end or URL.
        #                         This is just a basic regex and works for most of the URLs, since webpages
        #                         contain valid URLs.
        url_pattern = r'https?:[0-9A-Za-z/-_.=?]+'

        response = self.get_url_response(url)
        matched_urls = re.findall(url_pattern, response)
        return list(set(matched_urls))         

    def get_sensitive_info(self, urls):

        # \.[cominrgetdugvlwk]{2,5}  --> This will match the common top level domains like:
        #                                .in .com .org .net .wiki .edu .gov . It may match
        #                                some invalid domains, but, since it's unlikely that real
        #                                webpages will contain invalid domains, the regex has been
        #                                kept simple and light.
        email_regex = re.compile(r'[0-9A-Za-z_.+-]+@[0-9A-Za-z]+\.(?:com|in|gov|org|net|edu)')

        results = []
        for url in urls:
            response = self.get_url_response(url.replace("\\",""))
            match = email_regex.findall(response)
            print(f"grepping emails in {url}                                                       ",end="\r")
            results.extend(match)
        return results
    
    def use_threading(self, urls):
        from concurrent.futures import ThreadPoolExecutor
        results = []
        threads = []
        max_threads = 25
        urls_len = len(urls)
        inc = urls_len//max_threads

        with ThreadPoolExecutor(max_threads) as executor:
            for i in range(0,urls_len,inc):
                if i+inc <= urls_len:
                    temp = urls[i:i+inc]
                    thread = executor.submit(self.get_sensitive_info, temp)
                else:
                    temp = urls[i:]
                    thread = executor.submit(self.get_sensitive_info, temp)
                threads.append(thread)

        for tr in threads:
            results.extend(tr.result())
        return results

def main():

    parser = argparse.ArgumentParser(prog="scrape", description="Scrape webpage(s) to extract email addresses.")
    parser.add_argument('-u', '--url', required=True, help="URL of webpage to scrape", type=str, )
    parser.add_argument('-d', '--depth', required=False, default=1, type=int,choices=[1,2], help="Level of recursion. default is 1, which will scrape only given URL webpage. 2 will scrape the webpages of URLs contained in input URL.")
    args = parser.parse_args()

    url = args.url
    if not (url.startswith("https://") or url.startswith("http://")):
        sys.exit(f"Invalid URL {url}. URL must start with https:// or http://\n")
    scrape = Scrappy()
    emails = []

    print(f"\nURL: {url}   DEPTH: {args.depth}")

    if args.depth == 2:
        urls = scrape.get_links_to_scrape(url)
        if len(urls) < 1:
            sys.exit(f"No matching url found in response for {url}")

        print(f"total URLs scraped: {len(urls)}")
    else:
        urls = [url]

    if len(urls) < 25 and len(urls) > 0:
        emails.extend(scrape.get_sensitive_info(urls))
    else:
        emails.extend(scrape.use_threading(urls))
    print("")
    if len(emails) < 1:
        sys.exit(f"No email addresses found")

    emails = list(set(emails))
    print("\t--------------------------------------------")    
    print(f"\n\tTotal emails found: {len(emails)}")
    print("\t--------------------------------------------")
    for emailid in emails:
        print(f"\t {emailid}")
    print(f"\t--------------------------------------------\n")

if __name__ == "__main__":
    main()
