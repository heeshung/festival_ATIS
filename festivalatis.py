import discord
import os
import requests
#import datetime
from datetime import timezone, timedelta, datetime

#prompt for current year
#currentyearmonth = input("Enter last two digits of year and month: ")
currentyearmonth = "23"

atisletters=["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
lastdatetime=datetime.utcnow()
atisepoch=datetime.utcnow()

#read client token
tokenfile = open ("token","r")
token = tokenfile.read()
tokenfile.close()

#read schedule
schedule = open("schedule","r")
schedule_data = schedule.read()
schedule_parsed = schedule_data.split("\n")
schedule.close()

#get venue name
eventvenuename=schedule_parsed[0]

#get UTC offset
utcoffset = int(schedule_parsed[1])

#get icao airport code
icao = schedule_parsed[2]

#get number of stages
numstages=int(schedule_parsed[3])

setdata=[]

#parse schedule data
for x in range(4,4+numstages):
	#y is iterator for times/artists part of data
	y = x+numstages
	setdata.append(schedule_parsed[x])
	sets_parsed = schedule_parsed[y].split(",")
	times_parsed = []
	artists_parsed = []
	for z in range(0,len(sets_parsed),2):
		#convert string into datetime
		formattedtime = datetime.strptime(currentyearmonth+sets_parsed[z],'%y%m%d%H%M')
		#add UTC offset
		formattedtime -= timedelta(hours=utcoffset)
		times_parsed.append(formattedtime)
	for a in range(1,len(sets_parsed),2):
		artists_parsed.append(sets_parsed[a])
	setdata.append(times_parsed)
	setdata.append(artists_parsed)

additionalrmks=""

currentatistext=[]
currentatisindex=0

client=discord.Client()

#@client.event
#async def on_ready():
#    await client.get_channel(746263960646451241).send("EVENT ATIS/TAF SERVICE ONLINE " + atisepoch.strftime("%d%H%M") + "Z")

@client.event
async def on_message(message):
	if message.author == client.user:
		return

	if message.content.lower().startswith('hello'):
		await message.channel.send('Hello!')

	if message.content.lower().startswith('additional'):
		global additionalrmks
		additionalrmks=(message.content)[11:]


	if message.content.lower().startswith('atis'):
		global lastdatetime
		global currentatisindex
		global currentatistext
		

		if 'z' in message.content.lower():
			zulureq = True
		else:
			zulureq = False

		#get current time
		currentdatetime=datetime.utcnow()


		#get METAR
		c_atis=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&stationString='+icao+'&hoursBeforeNow=2')
		atisoutput = (c_atis.text)
		begin=atisoutput.find("Z ")
		end=atisoutput.find("</raw_text>")

		#increment ATIS letter by hour
		#timediff=currentdatetime-atisepoch
		#hourdiff=timediff.total_seconds()/3600
		#currentatisindex = int((hourdiff) % 26)
		atiscompare=[]
		atiscompare.append(atisoutput[begin+2:end] + "\n\nREMARKS \n")
		timeremaintext=[]

		#iterate through each stage
		for stageindex in range(0,len(setdata),3):
			settimeindex = stageindex+1
			artistindex = stageindex+2
			atiscompose = setdata[stageindex] + ": "
			timeremaincompose=""
			for idx, x in reversed(list(enumerate(setdata[settimeindex]))):
				if (currentdatetime >= setdata[settimeindex][idx]):
					currentartist=setdata[artistindex][idx]
					#check if current artist is not last
					if (idx < len(setdata[settimeindex])-1):
						nextartist = setdata[artistindex][idx+1]
						#get minutes remaining in set
						timeremain = (setdata[settimeindex][idx+1]-currentdatetime).total_seconds()
						timeremain = round(timeremain/60)
						if (timeremain>60):
							timesuffix = str(int(timeremain/60)) + " hr " + str(int(timeremain%60)) + " min"
						else:
							timesuffix = str(timeremain) + " min"
						timeremaincompose=" (" + nextartist + " in " + timesuffix + ")\n"
					#if current artist is last
					else:
						timeremaincompose="\n"
					break
				#if current artist is before first
				nextartist = setdata[artistindex][0]
				#get minutes before set
				timeremain = (setdata[settimeindex][0]-currentdatetime).total_seconds()
				timeremain = round(timeremain/60)
				if (timeremain>60):
					timesuffix = str(int(timeremain/60)) + " hr " + str(int(timeremain%60)) + " min"
				else:
					timesuffix = str(timeremain) + " min"
				timeremaincompose=" (" + nextartist + " in " + timesuffix + ")\n"
				currentartist="STGE CLSD"

			timeremaintext.append(timeremaincompose)
			atiscompose += currentartist
			atiscompare.append(atiscompose)

		#initialize blank remarks to end of list
		atiscompare.append("")

		#add remarks
		if (len(additionalrmks)>0):
			atiscompare[len(atiscompare)-1]="\n\nADDITIONAL RMKS: " + additionalrmks

		#check if new ATIS matches old, if not advance ATIS letter
		if (len(currentatistext)==0):
			currentatistext=atiscompare.copy()

		elif (len(currentatistext)>0 and (atiscompare != currentatistext)):
			currentatisindex=(currentatisindex+1)%26
			currentatistext=atiscompare.copy()


		if (zulureq == True):
			combined = eventvenuename + " ATIS INFO " + atisletters[currentatisindex] + " " + currentdatetime.strftime("%d%H%M**Z** ") + currentatistext[0]
			for x in range(1,len(currentatistext)):
				combined += currentatistext[x]
				#add time remaining text
				if (x < len(currentatistext)-1):
					combined += timeremaintext[x-1]

		else:
			combined = eventvenuename + " ATIS INFO " + atisletters[currentatisindex] + " " + (currentdatetime+timedelta(hours=utcoffset)).strftime("%d%H%M**L** **(%a %b%d %H%ML)** ").upper() + currentatistext[0]
			for x in range(1,len(currentatistext)):
                                combined += currentatistext[x]
                                #add time remaining text
                                if (x < len(currentatistext)-1):
                                        combined += timeremaintext[x-1]


		await message.channel.send(combined)


	if message.content.lower().startswith('taf'):
		

		
		if 'z' in message.content.lower():
			zulureq = True
		else:
			zulureq = False

		#get current time
		currentdatetime=datetime.utcnow()

		c_taf=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&stationString='+icao+'&hoursBeforeNow=4')
		tafoutput = (c_taf.text)
		begin=tafoutput.find("Z ")
		end=tafoutput.find("</raw_text>")

		if (zulureq == True):
			combined = eventvenuename + " TAF " + currentdatetime.strftime("%d%H%M**Z** ") + tafoutput[begin+2:end] + "\n\nREMARKS\n"

		else:
			combined = eventvenuename + " TAF " + (currentdatetime+timedelta(hours=utcoffset)).strftime("%d%H%M**L** **(%a %b%d %H%ML)** ").upper() + tafoutput[begin+2:end] + "\n\nREMARKS\n"

		for stageindex in range(0,len(setdata),3):
			settimeindex = stageindex+1
			artistindex = stageindex+2
			combined += "\n" + setdata[stageindex] + ": FM"
			timeremaintext = ""
			for idx, x in reversed(list(enumerate(setdata[settimeindex]))):
				#if current time is past time of first set
				if (currentdatetime >= setdata[settimeindex][idx]):
					#check if current artist is last
					if (idx == len(setdata[settimeindex])-1):
						nextartist="STGE CLSD"
						nextsettime=setdata[settimeindex][idx]
						if (zulureq == True):
							combined += nextsettime.strftime("%d%H%M**Z** ") + nextartist
						else:
							combined += (nextsettime+timedelta(hours=utcoffset)).strftime("%d%H%M**L** **(%a %b%d %H%ML)** ").upper() + nextartist
						break
					else:
						nextartist=setdata[artistindex][idx+1]
						nextsettime=setdata[settimeindex][idx+1]
						if (zulureq == True):
							combined += nextsettime.strftime("%d%H%M**Z** ") + nextartist
						else:
							combined += (nextsettime+timedelta(hours=utcoffset)).strftime("%d%H%M**L** **(%a %b%d %H%ML)** ").upper() + nextartist
						break
				#if current time is before first set
				elif (currentdatetime < setdata[settimeindex][0]):
					nextartist = setdata[artistindex][0]
					nextsettime = setdata[settimeindex][0]
					combined += nextsettime.strftime("%d%H%M") + zululocalsuffix + " " + nextartist
					break
				else:
					continue

		if (len(additionalrmks)>1):
			combined+="\n\nADDITIONAL RMKS: " + additionalrmks
		await message.channel.send(combined)

client.run(token)
