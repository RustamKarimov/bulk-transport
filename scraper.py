# scrape the company name, address, city, state zip, phone # and
# list of services from a website and put that information into
# separate rows and columns in an excel spreadsheet. The directory
# can be found here:
# https://www.bulktransporter.com/cargo-tank-repair-directory/cargo-tank-repair-directory
# and you must page through each state. Then the multiple companies on each page need to be put in a separate record.

import requests
import bs4
import re
import pandas as pd


website = 'https://www.bulktransporter.com/cargo-tank-repair-directory/'


class Scrapper:
    def __init__(self, website):
        self.website = website
        self.dictionary = []
        
    def get_link(self, link):
        return requests.get(link)
    
    def get_content(self, link):
        return link.content
    
    def get_soup(self, content, parser='html.parser'):
        return bs4.BeautifulSoup(content, parser)
    
    def get_soup_from_link(self, link):
        webpage = self.get_link(link)
        webcontent = self.get_content(webpage)
        return self.get_soup(webcontent)
        
    def get_links_from_website(self):
        soup = self.get_soup_from_link(self.website)
        links = soup.find_all('a')
        return links
    
    def create_empty_dataframe(self):
        self.columns = ['Company', 'Address', 'City', 'Zip', 'Phone', 'Fax', 'Services']
        df = pd.DataFrame(columns=self.columns)
        return df
    
    def unzip_address(self, postal_address):
        address = re.search(r'(?P<address>[\s\w\d]+),.*', postal_address)
        if address:
            address = address['address']
        zipcode = re.search(r'.*,.*(?P<zipcode>\d{5})', postal_address)
        if zipcode:
            zipcode = zipcode['zipcode']
#         return re.search(r'([\s\w\d\(\)]+).*(\d{5})?', postal_address).groups()
        return address, zipcode
        
    def unzip_phone_fax(self, contacts):
        phones = re.findall(r'(\(\d{3}\) \d{3}-\d{4})', contacts)
        fax = re.findall(r'\d{3}-\d{3}-\d{4}', contacts)
        return "/".join(phones), "/".join(fax)
    
    def unzip_services(self, services):
        return re.search(r'Services: (.*)', services).groups()[0]
    
    def extract_information(self, link):
        soup = self.get_soup_from_link(link)
        header = soup.find('h4')
        if header is None:
            return
        df = []
        tag = header
        row = {}
        row['City'] = header.text
        for tag in header.next_siblings:
            if type(tag) == bs4.element.Tag and len(tag.text) > 0:
                if tag.name == 'h4':
                    df.append(row)
                    row = {}
                    row['City'] = tag.text
                elif 'Company' not in row.keys():
                    row['Company'] = tag.text
                elif 'Address' not in row.keys():
                    row['Address'], row['Zip'] = self.unzip_address(tag.text)
                elif 'Phone' not in row.keys() and tag.text.startswith('Phone:'):
                    row['Phone'], row['Fax'] = self.unzip_phone_fax(tag.text)
                elif 'Services' not in row.keys():
                    if tag.text.startswith('Services'):
                        row['Services'] = self.unzip_services(tag.text)
                elif len(tag.text) > 1 and 'Services' in row.keys():
                    city = row['City']
                    df.append(row)
                    row = {}
                    row['City'] = city
                    row['Company'] = tag.text
        if "Address" in row.keys():
            df.append(row)
        return df
                        
    def convert_to_dataframe(self):
        self.dataframe = pd.DataFrame(self.dictionary[0])
        for dictionary in self.dictionary[1:]:
            dataframe = pd.DataFrame(dictionary)
            self.dataframe = pd.concat([self.dataframe, dataframe], sort=False, ignore_index=True)
                          
    def write_to_excel(self):
        self.dataframe.to_excel('data.xlsx')
                          
    def search_through_the_links(self):
        links = self.get_links_from_website()
        number = 1
        for link in links:
            sub_link = link.get('href')
            if not sub_link or sub_link.startswith('/cargo-tank-repair-directory/cargo-tank-repair-directory'):
                continue
            if sub_link.startswith('/cargo-tank-repair-directory'):
                main_link = self.website[:-29] + sub_link
                print(f'{number} => Scrabbling through {main_link}')
                sub_dictionary = self.extract_information(main_link)
                self.dictionary.append(sub_dictionary)
                number += 1
                

if __name__ == '__main__':
    scrapper = Scrapper(website)
    scrapper.search_through_the_links()
    scrapper.write_to_excel()