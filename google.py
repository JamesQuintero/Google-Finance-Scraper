#Scraper to get stock price and option data from google finance

import urllib.request           #script for URL request handling
import urllib.parse             #script for URL handling
from urllib import request
import html.parser              #script for HTML handling
import os.path                  #script for directory/file handling
import csv                      #script for CSV file handling
import time                     #scripting timing handling
import datetime                   #data and time handling
from datetime import date
import json											#handle google finance returning json data
import random



class Google:

	cj = None
	opener = None
	#EX: "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:25.0)"
	user_agents=[]

	def __init__(self):
		self.user_agents.append("Mozilla/5.0 (X10; Ubuntu; Linux x86_64; rv:25.0)")
		self.user_agents.append("Mozilla/5.0 (Windows NT 6.0; WOW64; rv:12.0)")
		self.user_agents.append("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537")
		self.user_agents.append("Mozilla/5.0 (Windows NT 6.1) AppleWebKit/540 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/540")
		self.user_agents.append("Mozilla/5.0 (Windows; U; Windows NT 5.2; it; rv:1.8.1.11) Gecko/20071327 Firefox/2.0.0.10")
		self.user_agents.append("Opera/9.3 (Windows NT 5.1; U; en)")

		#initializes url opener
		self.opener=urllib.request.build_opener(urllib.request.HTTPRedirectHandler(),urllib.request.HTTPHandler(debuglevel=0))


	#downloads and returns regular single day price history
	def historicalPrices(self, stock_symbol, num_years):

		try:
			today=datetime.date.today()
			cur_month=today.month
			cur_day=today.day
			cur_year=today.year

			months=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

			cid=self.optionChainCID(stock_symbol)

			self.httpRequest("http://www.google.com/finance/historical?cid="+str(cid)+"&startdate="+months[cur_month-1]+"+"+str(cur_day)+"%2C+"+str(cur_year-num_years)+"&enddate="+months[cur_month-1]+"+"+str(cur_day)+"%2C+"+str(cur_year)+"&num=10000&output=csv")
			h=html.parser.HTMLParser()
			data=h.unescape(data)


			#joins data into list format
			new_list=[]
			index=0
			new_str=""
			while index<len(data):
				if data[index]!="\n":
					new_str+=data[index]
				else:
					new_list.append(new_str)
					new_str=""
				index+=1
			data=new_list

			#removes column titles
			data.pop(0)

			new_data=[]
			for x in range(0, len(data)):
				try:
					data[x]=data[x].split(",")

					adj_open=self.convertNumber(float(data[x][1]))
					adj_high=self.convertNumber(float(data[x][2]))
					adj_low=self.convertNumber(float(data[x][3]))

					date=data[x][0].split("-")
					date=str(months.index(date[1])+1)+"/"+str(date[0])+"/"+str(2000+int(date[2]))

					temp_list={}
					temp_list['date']=date
					temp_list['open']=adj_open
					temp_list['high']=adj_high
					temp_list['low']=adj_low
					temp_list['close']=self.convertNumber(float(data[x][4]))
					temp_list['volume']=data[x][5]
					new_data.append(temp_list)
				except Exception as error:
					#bad price data, so start history again
					new_data=[]

			new_data.reverse()

			return new_data
		except Exception as error:
			print("URL error (google.py donwload_history()): "+str(error)+" | "+str(stock_symbol)+" "+str(num_years)+" years")
			return []

	#gets current stock price
	def currentPrice(self, stock_symbol):
		try:
			data=self.httpRequest("https://www.google.com/finance?q="+str(stock_symbol))
			h=html.parser.HTMLParser()
			data=h.unescape(data)
			
			temp_data=data.split('<meta itemprop="price"')
			temp_data=temp_data[1]
			temp_data=temp_data.split("/>")
			temp_data=temp_data[0]
			temp_data=temp_data.strip()
			temp_data=temp_data.split('"')
			temp_data=temp_data[1].replace(",", "")
			return float(temp_data)

		except Exception as error:
			print("Error occcured google.py for "+str(stock_symbol)+": "+str(error))
			return 0


	#date
	#[0]=month
	#[1]=day
	#[2]=year
	def optionPrices(self, stock_symbol, date):

		month=str(date[0])
		day=str(date[1])
		year=str(date[2])

		data=self.httpRequest("https://www.google.com/finance/option_chain?q="+str(stock_symbol))
		h=html.parser.HTMLParser()
		data=h.unescape(data)


		if "underlying_id" not in data:
			return []

		temp_data=data.split('underlying_id:"')
		temp_data=temp_data[1]
		temp_data=temp_data.split('"')
		temp_data=temp_data[0]
		underlying_id=int(temp_data.strip())
		
		#gets option prices from August 16, 2014
		url="https://www.google.com:443/finance/option_chain?cid="+str(underlying_id)+"&expd="+str(day)+"&expm="+str(month)+"&expy="+str(year)+"&output=json"
		try:
			data=self.httpRequest(url)
		except Exception as error:
			print("Google threw error. Retrying in 10 seconds")
			time.sleep(10)
			#retries
			data=self.httpRequest(url)

		#gets current price
		temp_data=data.split('underlying_price:')
		temp_data=temp_data[1]
		temp_data=temp_data.split('}')
		temp_data=temp_data[0]
		underlying_price=float(temp_data.strip())

		if "calls" not in data:
			return []

		data=data.split("calls")
		data=data[1]
		new_data=data.split("cid")

		for x in range(0, len(new_data)):
			new_data[x]=new_data[x].split(",")
			for y in range(0, len(new_data[x])):
				new_data[x][y]=new_data[x][y].replace("'", "")
				new_data[x][y]=new_data[x][y].replace('"', "")
				new_data[x][y]=new_data[x][y].replace("{", "")
				new_data[x][y]=new_data[x][y].replace("}", "")
				new_data[x][y]=new_data[x][y].split(":")
		new_data.pop(0)

		for x in range(0, len(new_data)):
			y=0
			while y<len(new_data[x]):
				if len(new_data[x][y])>1:
					if new_data[x][y][0]!="a" and new_data[x][y][0]!="strike":
						new_data[x].pop(y)
					else:
						y+=1
				else:
					new_data[x].pop(y)


		#converts option data 
		new_list=[]
		for x in range(0, len(new_data)):
			temp_list={}

			for y in range(0, len(new_data[x])):
				title=new_data[x][y][0]
				if title=="strike":
					temp_list['strike']=new_data[x][y][1]
				elif title=="p":
					temp_list['price']=new_data[x][y][1]
				elif title=="b":
					temp_list['bid']=new_data[x][y][1]
				elif title=="a":
					temp_list['ask']=new_data[x][y][1]
				
			new_list.append(temp_list)
		new_data=new_list


		index=0
		while index<len(new_list):
			if new_list[index][1]==0:
				new_list.pop(index)
			else:
				index+=1

		return new_list

	#downloads 1min intraday history
	#interval is in minutes
	#timeframe is in days to get (14 is most you can go)
	def intradayPrices(self, stock_symbol, interval, timeframe):


		#interval=1 gets 1 minute
		interval=interval*60

		try:
			url="http://www.google.com/finance/getprices?i="+str(interval)+"&p="+str(timeframe)+"d&f=o,h,l,c,v&df=cpct&q="+str(stock_symbol.upper())
			data=self.httpRequest(url)
		except urllib.request.HTTPError as error:
			print("Error downloading intraday history "+str(stock_symbol)+":  "+str(error))
			return []

		data=data.split("\n")


		###data: 
		# EXCHANGE%3DNYSE
		# MARKET_OPEN_MINUTE=570
		# MARKET_CLOSE_MINUTE=960
		# INTERVAL=60
		# COLUMNS=CLOSE,HIGH,LOW,OPEN
		# DATA=
		# TIMEZONE_OFFSET=-240
		# 89.05,89.25,89.05,89.1
		# 88.71,89.1499,88.5,89.1499
		# 88.75,88.97,88.72,88.72
		# 88.915,88.96,88.69,88.7505
		# 88.895,89,88.77,88.92
		# 88.92,88.92,88.85,88.875
		# 89.05,89.1,88.87,88.92
		# TIMEZONE_OFFSET=-300
		# 89.3437,89.53,89.07,89.075
		# 89.165,89.3799,89.16,89.33
		# 89.005,89.17,89,89.168

		#removes beginning information
		for x in range(0, 7):
			data.pop(0)

		new_list=[]
		for x in range(0, len(data)):
			data[x]=data[x].split(",")

			#can have "TIMEZONE_OFFSET=-300" in row. If it doesn't have it in row,
			if len(data[x])!=1:
				temp={}
				temp['open']=data[x][3]
				temp['high']=data[x][1]
				temp['low']=data[x][2]
				temp['close']=data[x][0]
				temp['volume']=data[x][4]
				temp['date']=""
				new_list.append(temp)

		return new_list

	#gets stock ID for retrieving option data
	def optionChainUnderlyingID(self, stock_symbol):
		data=self.httpRequest("https://www.google.com/finance/option_chain?q="+str(stock_symbol))
		h=html.parser.HTMLParser()
		data=h.unescape(data)

		if "underlying_id" not in data:
			return ""

		temp_data=data.split('underlying_id:"')
		temp_data=temp_data[1]
		temp_data=temp_data.split('"')
		temp_data=temp_data[0]
		underlying_id=int(temp_data.strip())
		return underlying_id


	#date
	#[0]=month
	#[1]=day
	#[2]=year

	#returns
	#[x]=
		#[0]=Strike
		#[1]=Volume
		#[2]=Open int
		#[3]=price
		#[4]=Bid
		#[5]=Ask
	def optionData(self, stock_symbol, date):

		month=str(date[0])
		day=str(date[1])
		year=str(date[2])

		underlying_id=self.optionChainUnderlyingID(stock_symbol)
		if underlying_id=="":
			return []

		url="https://www.google.com:443/finance/option_chain?cid="+str(underlying_id)+"&expd="+str(day)+"&expm="+str(month)+"&expy="+str(year)+"&output=json"
		try:
			data=self.httpRequest(url)
		except Exception as error:
			print("Google threw error. Retrying in 10 seconds")
			time.sleep(10)
			#retries
			data=self.httpRequest(url)


		#gets current price
		temp_data=data.split('underlying_price:')
		temp_data=temp_data[1]
		temp_data=temp_data.split('}')
		temp_data=temp_data[0]
		underlying_price=float(temp_data.strip())

		#if price is less than 10, or calls aren't returned
		if underlying_price<10 or "calls" not in data or "puts" not in data:
			return []

		###gets calls###
		to_return={}
		option_type="call"
		for temp in range(1, 3):
			if temp%2==0:
				option_type="put"

			#gets correct data for scraping
			temp_data=data.split(option_type)
			temp_data=temp_data[1]
			if option_type=="put":
				temp_data=temp_data.split(",calls")
				temp_data=temp_data[0]
			new_data=temp_data.split("cid")

			for x in range(0, len(new_data)):
				new_data[x]=new_data[x].split(",")
				for y in range(0, len(new_data[x])):
					new_data[x][y]=new_data[x][y].replace("'", "")
					new_data[x][y]=new_data[x][y].replace('"', "")
					new_data[x][y]=new_data[x][y].replace("{", "")
					new_data[x][y]=new_data[x][y].replace("}", "")
					new_data[x][y]=new_data[x][y].split(":")
			new_data.pop(0)

			for x in range(0, len(new_data)):
				#removes any data that isn't important
				y=0
				while y<len(new_data[x]):
					if len(new_data[x][y])>1:
						data_type=new_data[x][y][0]
						#p = price, b = bid, a = ask, oi = open interest, vol = volume, strike = strike
						if data_type!="p" and data_type!="b" and data_type!="a" and data_type!="oi" and data_type!="vol" and data_type!="strike": 
							new_data[x].pop(y)
						else:
							y+=1
					else:
						new_data[x].pop(y)

			##Example output
			# [['p', '14.60'], ['b', '11.60'], ['a', '14.45'], ['oi', '7'], ['vol', '-'], ['strike', '24.00']]
			# [['p', '12.10'], ['b', '11.60'], ['a', '12.80'], ['oi', '57'], ['vol', '14'], ['strike', '25.00']]
			# [['p', '-'], ['b', '9.60'], ['a', '11.85'], ['oi', '0'], ['vol', '-'], ['strike', '26.00']]
			# [['p', '12.25'], ['b', '9.00'], ['a', '10.80'], ['oi', '3'], ['vol', '-'], ['strike', '27.00']]
			# [['p', '9.45'], ['b', '8.60'], ['a', '9.80'], ['oi', '45'], ['vol', '-'], ['strike', '28.00']]
			# [['p', '10.25'], ['b', '7.65'], ['a', '8.85'], ['oi', '6'], ['vol', '-'], ['strike', '29.00']]
			# [['p', '7.75'], ['b', '6.70'], ['a', '7.75'], ['oi', '175'], ['vol', '17'], ['strike', '30.00']]
			# [['p', '6.55'], ['b', '5.80'], ['a', '6.75'], ['oi', '57'], ['vol', '-'], ['strike', '31.00']]
			# [['p', '6.10'], ['b', '4.90'], ['a', '5.75'], ['oi', '39'], ['vol', '-'], ['strike', '32.00']]
			# [['p', '4.75'], ['b', '3.95'], ['a', '4.75'], ['oi', '6008'], ['vol', '-'], ['strike', '33.00']]
			# [['p', '4.30'], ['b', '3.10'], ['a', '3.80'], ['oi', '20'], ['vol', '-'], ['strike', '34.00']]
			# [['p', '2.97'], ['b', '2.40'], ['a', '2.96'], ['oi', '238'], ['vol', '9'], ['strike', '35.00']]
			# [['p', '2.42'], ['b', '1.82'], ['a', '2.03'], ['oi', '299'], ['vol', '-'], ['strike', '36.00']]
			# [['p', '1.55'], ['b', '1.30'], ['a', '1.46'], ['oi', '3101'], ['vol', '828'], ['strike', '37.00']]
			# [['p', '0.92'], ['b', '0.89'], ['a', '0.96'], ['oi', '1781'], ['vol', '5849'], ['strike', '38.00']]
			# [['p', '0.65'], ['b', '0.57'], ['a', '0.68'], ['oi', '9940'], ['vol', '264'], ['strike', '39.00']]
			# [['p', '0.45'], ['b', '0.39'], ['a', '0.45'], ['oi', '6665'], ['vol', '1230'], ['strike', '40.00']]
			# [['p', '0.28'], ['b', '0.24'], ['a', '0.33'], ['oi', '2022'], ['vol', '31'], ['strike', '41.00']]
			# [['p', '0.22'], ['b', '0.14'], ['a', '0.22'], ['oi', '1100'], ['vol', '6'], ['strike', '42.00']]
			# [['p', '0.18'], ['b', '0.07'], ['a', '0.15'], ['oi', '271'], ['vol', '17'], ['strike', '43.00']]
			# [['p', '0.17'], ['b', '0.07'], ['a', '0.13'], ['oi', '255'], ['vol', '-'], ['strike', '44.00']]
			# [['p', '0.13'], ['b', '0.05'], ['a', '0.12'], ['oi', '452'], ['vol', '-'], ['strike', '45.00']]
			# [['p', '0.05'], ['b', '0.01'], ['a', '0.10'], ['oi', '201'], ['vol', '53'], ['strike', '46.00']]
			# [['p', '0.10'], ['b', '0.02'], ['a', '0.10'], ['oi', '130'], ['vol', '-'], ['strike', '47.00']]
			# [['p', '-'], ['b', '0.01'], ['a', '0.10'], ['oi', '0'], ['vol', '-'], ['strike', '48.00']]
			# [['p', '-'], ['b', '0.01'], ['a', '0.12'], ['oi', '0'], ['vol', '-'], ['strike', '49.00']]
			# [['p', '0.05'], ['b', '0.01'], ['a', '0.09'], ['oi', '14'], ['vol', '-'], ['strike', '50.00']]

			#converts option data 
			new_list=[]
			for x in range(0, len(new_data)):
				temp_list={}

				for y in range(0, len(new_data[x])):
					title=new_data[x][y][0]
					if title=="strike":
						temp_list['strike']=new_data[x][y][1]
					elif title=="p":
						temp_list['price']=new_data[x][y][1]
					elif title=="b":
						temp_list['bid']=new_data[x][y][1]
					elif title=="a":
						temp_list['ask']=new_data[x][y][1]
					elif title=="oi":
						temp_list['open_int']=new_data[x][y][1]
					elif title=="vol":
						temp_list['volume']=new_data[x][y][1]
				new_list.append(temp_list)

			new_data=new_list


			#removes any illiquid strike prices
			new_list=[]
			for x in range(0, len(new_data)):
				if new_data[x]['open_int']!="0":
					new_list.append(new_data[x].copy())

			to_return[option_type]=new_list

		return to_return



	#gets stock_symbol's available option expiration dates 
	def expirationDates(self, stock_symbol):
		#each stcok has a unique id for option chains
		underlying_id=self.optionChainUnderlyingID(stock_symbol)
		if underlying_id=="":
			return []

		url="https://www.google.com:443/finance/option_chain?cid="+str(underlying_id)+"&output=json"
		try:
			data=self.httpRequest(url)
		except Exception as error:
			print("Google threw error: "+str(error)+". Retrying in 10 seconds")
			time.sleep(10)
			#retries
			data=self.httpRequest(url)

		if "expirations:[" in data:
			#gets expiration 
			temp=data.split("expirations:[")
			temp=temp[1].split("],puts:")
			temp=temp[0]
			#temp: 
			# {y:2014,m:11,d:14},{y:2014,m:11,d:22},{y:2014,m:11,d:28},{y:2014,m:12,d:5},{y:2014,m:12,d:12},{y:2014,m:12,d:20},{y:2014,m:12,d:26},{y:2015,m:1,d:17},{y:2015,
			# m:2,d:20},{y:2015,m:3,d:20},{y:2015,m:5,d:15},{y:2016,m:1,d:15},{y:2017,m:1,d:20}

			temp=temp.split("},{")

			for x in range(0, len(temp)):
				temp[x]=temp[x].replace("{", "")
				temp[x]=temp[x].replace("}", "")

				temptemp=temp[x].split(",")
				year=int(temptemp[0].replace("y:", ""))
				month=int(temptemp[1].replace("m:", ""))
				day=int(temptemp[2].replace("d:", ""))

				new_list={}
				new_list['year']=year
				new_list['month']=month
				new_list['day']=day
				temp[x]=new_list

			return temp
			
		else:
			return []

	#requests 30 pages of google finance's list of stocks
	def stockScreener(self):
		start=0
		total=30
		stock_list=[]
		while start<total:
			try:
				market_cap_min=0
				market_cap_max=2700000000000
				pe_ratio_min=0
				pe_ratio_max=49887
				price_min="1.00"
				price_max="1000.00"
				#decoded url: http://www.google.com:80/finance?output=json&start=0&num=20&noIL=1&q=[currency == "USD" & ((exchange == "OTCMKTS") | (exchange == "OTCBB") | (exchange == "NYSEMKT") | (exchange == "NYSEARCA") | (exchange == "NYSE") | (exchange == "NASDAQ")) & (market_cap >= 2000000000) & (market_cap <= 2700000000000) & (pe_ratio >= 0) & (pe_ratio <= 49887) & (dividend_yield >= 0) & (dividend_yield <= 306) & (price_change_52week >= -101) & (price_change_52week <= 79901) & (last_price >= ) & (last_price <= 100.00)]&restype=company
				url="http://www.google.com:80/finance?output=json&start="+str(start)+"&num=30&noIL=1&q=[currency%20%3D%3D%20%22USD%22%20%26%20%28%28exchange%20%3D%3D%20%22OTCMKTS%22%29%20%7C%20%28exchange%20%3D%3D%20%22OTCBB%22%29%20%7C%20%28exchange%20%3D%3D%20%22NYSEMKT%22%29%20%7C%20%28exchange%20%3D%3D%20%22NYSEARCA%22%29%20%7C%20%28exchange%20%3D%3D%20%22NYSE%22%29%20%7C%20%28exchange%20%3D%3D%20%22NASDAQ%22%29%29%20%26%20%28market_cap%20%3E%3D%20"+str(market_cap_min)+"%29%20%26%20%28market_cap%20%3C%3D%20"+str(market_cap_max)+"%29%20%26%20%28pe_ratio%20%3E%3D%20"+str(pe_ratio_min)+"%29%20%26%20%28pe_ratio%20%3C%3D%20"+str(pe_ratio_max)+"%29%20%26%20%28dividend_yield%20%3E%3D%200%29%20%26%20%28dividend_yield%20%3C%3D%20306%29%20%26%20%28price_change_52week%20%3E%3D%20-101%29%20%26%20%28price_change_52week%20%3C%3D%2079901%29%20%26%20%28last_price%20%3E%3D%20"+str(price_min)+"%29%20%26%20%28last_price%20%3C%3D%20"+str(price_max)+"%29]&restype=company&ei=soHPUqj-F-qtiQLKWw"
				html=self.httpRequest(url)
				html=html.replace("\\", "")
				data=json.loads(html)

				start+=30
				total=int(data['num_company_results'])

				for x in range(0, len(data['searchresults'])):
					symbol=data['searchresults'][x]['ticker']
					if symbol.find('.')==-1 and symbol.find('-')==-1:
						stock_list.append(symbol)
				
			except urllib.error.URLError as error:
				#saves what has been acquired
				self.saveToTXT('./stock_lists/stocks.txt', stock_list)
				print("Error: Disconnected from server.")
			except urllib.error.HTTPError as error:
				#saves what has been acquired
				self.saveToTXT('./stock_lists/stocks.txt', stock_list)
				print("Error: Disconnected from server.")
			#waits 1 second inbetween page loads
			time.sleep(1)
			
		self.saveToTXT("./stock_lists/stocks.txt", stock_list)


	#gets number of days until beginning of next month (next expiration)
	def nextExpirationDate(self):
		today=date.fromtimestamp(time.time())
		beginning=datetime.date(today.year, today.month, 1)

		num_fridays=0
		for x in range(0, 30):
			if beginning.weekday()==4:
				num_fridays+=1
				if num_fridays==3:
					break
			beginning=beginning.replace(day=beginning.day+1)

		days_diff=abs(beginning-today)
		if days_diff.days>=0:
			beginning=beginning.replace(month=beginning.month+1)
			beginning=beginning.replace(day=1)

			num_fridays=0
			for x in range(0, 30):
				if beginning.weekday()==4:
					num_fridays+=1
					if num_fridays==3:
						break
				beginning=beginning.replace(day=beginning.day+1)

		days_until=abs(today-beginning)
		#gets weekdays remaining
		weekdays=int(days_until.days*.75)
		return weekdays

	#gets cid required for option chain request
	def optionChainCID(self, stock_symbol):
		data=self.httpRequest("https://www.google.com/finance/option_chain?q="+str(stock_symbol))
		h=html.parser.HTMLParser()
		data=h.unescape(data)

		if "underlying_id" not in data:
			return []

		temp_data=data.split('underlying_id:"')
		temp_data=temp_data[1]
		temp_data=temp_data.split('"')
		temp_data=temp_data[0]
		underlying_id=int(temp_data.strip())

		return underlying_id

	#returns request results from url
	def httpRequest(self, url):
		#sets random user agent
		self.opener.addheaders=[('User-agent', random.choice(self.user_agents))]

		response = self.opener.open(url, timeout=30)
		data=response.read()
		data=data.decode('UTF-8', errors='ignore')
		return data

	def saveToTXT(self, path, data):
		output=open(path, 'wb')
		for x in range(0, len(data)):
			output.write(bytes(data[x]+'\n', 'UTF-8'))

	#rounds number to 100th decimal place
	def convertNumber(self, number):
		return int(number*100)/100



if __name__=="__main__":
	google=Google()

	symbol="AAPL"
	cur_price=google.currentPrice(symbol)
	print(symbol+"'s current price: "+str(cur_price))
