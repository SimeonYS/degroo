import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import DegrooItem
from itemloaders.processors import TakeFirst

pattern = r'(\xa0)?'

class DegrooSpider(scrapy.Spider):
	name = 'degroo'
	offset = 1
	base = 'https://press.degroofpetercam.com/?offset={}&limit=12&layout=cascade&xhr=1'
	start_urls = ['https://press.degroofpetercam.com/']

	def parse(self, response):
		articles = response.xpath('//div[@class="story-card story-card--cascade story-card--with-subtitle story-card--with-date story-card--with-image story-card--with-well story-card--with-well-border story-cards-list__card"]')
		for article in articles:
			date = article.xpath('.//span[contains(@class,"story-date")]/text()').get()
			date = re.findall(r'\w+\s\d+\,\s\d+',date)
			post_links = article.xpath('.//a/@href').get()
			yield response.follow(post_links, self.parse_post,cb_kwargs=dict(date=date))

		if response.xpath('//div[contains(@class,"story-card")]/a'):
			self.offset += 12
			yield response.follow(self.base.format(self.offset), self.parse)

	def parse_post(self, response, date):
		try:
			title = response.xpath('//h1/text()').get() + response.xpath('//h2/text()').get()
		except TypeError:
			title = response.xpath('//h1/text()').get()
		content = response.xpath('//div[@class="story__column story__column--content"]//text()[not (ancestor::h1) and not (ancestor::h2) and not (ancestor::span[@class="story-date"])] | //section[contains(@class,"content")]//text()').getall()
		content = [p.strip() for p in content if p.strip()]
		content = re.sub(pattern, "",' '.join(content))

		item = ItemLoader(item=DegrooItem(), response=response)
		item.default_output_processor = TakeFirst()

		item.add_value('title', title)
		item.add_value('link', response.url)
		item.add_value('content', content)
		item.add_value('date', date)

		yield item.load_item()
