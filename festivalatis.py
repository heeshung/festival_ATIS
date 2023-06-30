import discord
import os
import requests
import datetime
from datetime import timezone

atisletters=["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
lastdatetime=datetime.datetime.utcnow()
atisepoch=datetime.datetime.utcnow()

#read client token
tokenfile = open ("/root/weekenderatis/token","r")
token = tokenfile.read()
tokenfile.close()

#read schedule
schedule = open("/root/weekenderatis/schedule","r")
#print (schedule.read())
schedule_data = schedule.read()
schedule_parsed = schedule_data.split("\n")
schedule.close()

#get icao airport code
icao = schedule_parsed[2]

#get UTC offset
utcoffset = int(schedule_parsed[1])

setdata=[]

numstages=int(schedule_parsed[3])

#get venue name
eventvenuename=schedule_parsed[0]

#parse schedule data
for x in range(4,4+numstages):
	#y is iterator for times/artists part of data
	y = x+numstages
	setdata.append(schedule_parsed[x])
	sets_parsed = schedule_parsed[y].split(",")
	times_parsed = []
	artists_parsed = []
	for z in range(0,len(sets_parsed),2):
		times_parsed.append(int(sets_parsed[z])+utcoffset)
	for a in range(1,len(sets_parsed),2):
		artists_parsed.append(sets_parsed[a])
	setdata.append(times_parsed)
	setdata.append(artists_parsed)

additionalrmks=""

currentatistext=""
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

		#get current time
		currentdatetime=datetime.datetime.utcnow()


		#get METAR
		c_atis=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&stationString='+icao+'&hoursBeforeNow=2')
		atisoutput = (c_atis.text)
		begin=atisoutput.find("Z ")
		end=atisoutput.find("</raw_text>")

		#increment ATIS letter by hour
		#timediff=currentdatetime-atisepoch
		#hourdiff=timediff.total_seconds()/3600
		#currentatisindex = int((hourdiff) % 26)
		
		atiscompare=(atisoutput[begin+2:end] + "\n\nREMARKS \n")

		for stageindex in range(0,len(setdata),3):
			settimeindex = stageindex+1
			artistindex = stageindex+2
			atiscompare += setdata[stageindex] + ": "
			for idx, x in reversed(list(enumerate(setdata[settimeindex]))):
				if (int(currentdatetime.strftime("%d%H%M")) >= int(setdata[settimeindex][idx])):
					currentartist=setdata[artistindex][idx]
					break
				else:
					currentartist="STGE CLSD"
			atiscompare += currentartist + "\n"



		if (len(additionalrmks)>0):
			atiscompare+="\n\nADDITIONAL RMKS: " + additionalrmks

		#check if new ATIS matches old, if not advance ATIS letter
		if (len(currentatistext)==0):
			currentatistext=atiscompare

		elif (len(currentatistext)>0 and (atiscompare != currentatistext)):
			currentatisindex=(currentatisindex+1)%26
			currentatistext=atiscompare



		combined = eventvenuename + " ATIS INFO " + atisletters[currentatisindex] + " " + currentdatetime.strftime("%d%H%M") + "Z " + currentatistext


		await message.channel.send(combined)


	if message.content.lower().startswith('taf'):
		#get current time
		currentdatetime=datetime.datetime.utcnow()

		c_taf=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&stationString='+icao+'&hoursBeforeNow=4')
		tafoutput = (c_taf.text)
		begin=tafoutput.find("Z ")
		end=tafoutput.find("</raw_text>")

		combined = eventvenuename + " TAF " + currentdatetime.strftime("%d%H%M") + "Z " + tafoutput[begin+2:end] + "\n\nREMARKS\n"


		for stageindex in range(0,len(setdata),3):
			settimeindex = stageindex+1
			artistindex = stageindex+2
			combined += "\n" + setdata[stageindex] + ": FM"
			for idx, x in reversed(list(enumerate(setdata[settimeindex]))):
				if (int(currentdatetime.strftime("%d%H%M")) >= int(setdata[settimeindex][idx])):
					#check if current artist is last
					if (idx == len(setdata[settimeindex])-1):
						nextartist="STGE CLSD"
						nextsettime=setdata[settimeindex][idx]
						combined += str(nextsettime) + " " + nextartist
						break
					else:
						nextartist=setdata[artistindex][idx+1]
						nextsettime=setdata[settimeindex][idx+1]
						combined += str(nextsettime) + " " + nextartist
						break
				elif (int(currentdatetime.strftime("%d%H%M")) < int(setdata[settimeindex][0])):
					nextartist = setdata[artistindex][0]
					nextsettime = setdata[settimeindex][0]
					combined += str(nextsettime) + " " + nextartist
					break
				else:
					continue

		if (len(additionalrmks)>1):
			combined+="\n\nADDITIONAL RMKS: " + additionalrmks
		await message.channel.send(combined)

"""
		combined = eventvenuename + " TAF " + currentdatetime.strftime("%d%H%M") + "Z " + tafoutput[begin+2:end] + "\n\nREMARKS"
		combined+="\n" + stagenamea + ": FM" + nextdreamsettime + " " + nextdreamartist
		combined+="\n" + stagenameb + ": FM" + nextvisionsettime + " " + nextvisionartist
		combined+="\n" + stagenamec + ": FM" + nextsequencesettime + " " + nextsequenceartist
		combined+="\n" + stagenamed + ": FM" + nextvoidsettime + " " + nextvoidartist
		#      combined+="\nAMPHI: FM" + nextgorgesettime + " " + nextgorgeartist
		#add additional remarks
		if (len(additionalrmks)>1):
		combined+="\n\nADDITIONAL RMKS: " + additionalrmks

		await message.channel.send(combined)
		"""

client.run(token)
