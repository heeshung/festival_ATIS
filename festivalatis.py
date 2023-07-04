import os
import requests
import time
import math
from interactions import slash_command, slash_option, SlashContext, Client, Intents, listen, OptionType, Task, IntervalTrigger
from interactions.api.events import Component
from interactions.ext import prefixed_commands
from datetime import timezone, timedelta, datetime


#bot setup
bot = Client(intents=Intents.DEFAULT, sync_interactions=True, asyncio_debug=True)
prefixed_commands.setup(bot)

atisletters=["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
atisepoch=datetime.utcnow()

currentyear = datetime.utcnow().strftime("%y")
currentmonth = datetime.utcnow().strftime("%m")

#read client token
tokenfile = open ("token","r")
token = tokenfile.read()
tokenfile.close()

#read schedule
schedule = open("schedule","r")

#remove newlines
schedule_data = schedule.read()
schedule_parsed = schedule_data.split("\n")
schedule.close()

#get venue name
eventvenuename=schedule_parsed[0]

#get UTC offset
utcoffset = int(schedule_parsed[1])

#get icao airport code
icao = schedule_parsed[2]

#get number of stages based on number of colons
numstages=(len(''.join(schedule_parsed[3:]).split("^"))-1)

setdata=[]

#parse schedule data
for x in range(3,numstages+3):
	#separate stage name and set data
	stagedata = schedule_parsed[x].split("^")
	setdata.append(stagedata[0])
	sets_parsed = stagedata[1].split(",")
	times_parsed = []
	artists_parsed = []
	for z in range(0,len(sets_parsed),2):
		#convert string into datetime
		formattedtime = datetime.strptime(currentyear+currentmonth+sets_parsed[z],'%y%m%d%H%M')
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

markedsets=[]

alertinterval=15

@Task.create(IntervalTrigger(seconds=10))
async def alerter():
	global markedsets

	#get current time
	currentdatetime=datetime.utcnow()
	markedsetscopy=[]

	#iterate through alert list
	for x in range(0,len(markedsets),4):
		if ((markedsets[x]-currentdatetime).total_seconds()/60 < alertinterval and (markedsets[x]-currentdatetime).total_seconds() > 0):
			await client.get_channel(746263960646451241).send("ATTENTION ALL AIRCRAFT: " + markedsets[x+2] + " BEGINS IN **" + str(math.ceil((markedsets[x]-currentdatetime).total_seconds()/60)) + " MINUTES** AT " + markedsets[x+1] + " (alert set by " + markedsets[x+3].mention + ").")
		else:
			markedsetscopy.extend(markedsets[x:x+4])
	markedsets = markedsetscopy[:]
	print ("alerter")

#alerter.start()

#@listen()
#async def on_ready(ctx: SlashContext):
#	await ctx.send("EVENT ATIS/TAF SERVICE ONLINE " + atisepoch.strftime("%d%H%M") + "Z")


print ("Here")

@slash_command(name="maincommand", description="main command")
async def hello(ctx: SlashContext):
	await ctx.send("Hello World")

@slash_command(name="help", description="Shows the help menu")
async def help(ctx: SlashContext):
	#global markedsets
	#global alertinterval
	#global additionalrmks
	#global setdata
	#global currentatisindex
	#global currentatistext

	await ctx.send("## Commands\n>>> **help**: replies with this help message\n**atis**: replies with the area ATIS, current artists on stage, and time remaining in sets\n**taf**: replies with the area TAF, and upcoming sets and \
times by stage\n**add <searchterm>**: adds artists that match search term into alert list\n**remove <searchterm>**: removes artists that match seach term from alert list\n**alertlist**: replies with full alert list\n**alertint <minutes>**: changes the alert \
interval to the specified number of minutes\n**remarks <remarks>**: adds additional remarks to be displayed in ATIS and TAF")

@slash_command(name="alertint", description="Sets the alert interval in minutes")
@slash_option(name="minutes",description="Alert interval in minutes",required=True,opt_type=OptionType.INTEGER)
async def alertint(ctx: SlashContext, minutes: int):
	global alertinterval
	try:
		await ctx.send(f"Alert interval: {minutes}")
		alertinterval = minutes
	except:
		await ctx.send('Error setting alert interval.')
	else:
		await ctx.send(('Set alert interval to ') + str(alertinterval) + (' minutes.'))
"""
	if message.content.lower().startswith('alertlist'):
		listcompose = ""
		if (len(markedsets)==0):
			await message.channel.send('No alerts set.')
		else:
			listcompose+='ALERT LIST:'
			for x in range(0,len(markedsets),4):
				listcompose+="\n" + markedsets[x+2] + "'s " + markedsets[x+1] + " set at " + (markedsets[x]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " (" + str(markedsets[x+3]) + ")"
			await message.channel.send(listcompose)

	if message.content.lower().startswith('remark'):
		additionalrmks=(message.content)[7:]

	if message.content.lower().startswith('add'):
		#get current time
		currentdatetime=datetime.utcnow()

		searchterm = (message.content)[4:].lower()
		matchfound = False

		#check for empty search
		if (len(searchterm)==0):
			await message.channel.send("Search term is empty.")

		else:
			#iterate through all sets and mark priority sets
			for stageindex in range(0,len(setdata),3):
				settimeindex = stageindex+1
				artistindex = stageindex+2
				for x in range(0,len(setdata[artistindex])):
					if (searchterm in setdata[artistindex][x].lower() and (setdata[settimeindex][x] - currentdatetime).total_seconds()/60 > alertinterval):
						#check if set is already added
						alreadyadded = False
						for y in range(0,len(markedsets),4):
							if (markedsets[y+2]==setdata[artistindex][x] and markedsets[y]==setdata[settimeindex][x] and markedsets[y+1]==setdata[stageindex]):
								alreadyadded = True
						#skip if set is already in list
						if (alreadyadded == True):
							continue
						markedsets.append(setdata[settimeindex][x])
						markedsets.append(setdata[stageindex])
						markedsets.append(setdata[artistindex][x])
						markedsets.append(message.author)
						#set match found to true
						matchfound = True
						await message.channel.send(message.author.mention + " added " + setdata[artistindex][x] + "'s " + setdata[stageindex] + " set at " + (setdata[settimeindex][x]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " to the alert list. :white_check_mark:")

			#if no match is found
			if (matchfound == False):
				await message.channel.send("Couldn't find any artists with '"+(message.content)[4:]+"' in their name with future sets.")

	if message.content.lower().startswith('remove'):
		matchfound = False
		markedsetscopy = []
		searchterm = (message.content)[7:].lower()
		for x in range(0,len(markedsets),4):
			if (searchterm in markedsets[x+2].lower()):
				matchfound = True
				await message.channel.send(message.author.mention + " removed " + markedsets[x+2] + "'s " + markedsets[x+1] + " set at " + (markedsets[x]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " from the alert list. :x:")
			else:
				#add undeleted sets back in
				markedsetscopy.extend(markedsets[x:x+4])
		markedsets=markedsetscopy[:]
		if (matchfound == False):
			await message.channel.send("Couldn't find any artists with '"+(message.content)[7:]+"' in their name in the alert list.")


	if message.content.lower().startswith('atis'):

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
		atiscompare.append(atisoutput[begin+2:end] + "\n\nREMARKS\n")
		timeremaintext=[]

		#iterate through each stage
		for stageindex in range(0,len(setdata),3):
			settimeindex = stageindex+1
			artistindex = stageindex+2
			#add stage name
			atiscompose = "\n**" + setdata[stageindex] + "**: "
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
						timeremaincompose=" (" + nextartist + " in " + timesuffix + ")"
					#if current artist is last
					else:
						timeremaincompose=""
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
				timeremaincompose=" (" + nextartist + " in " + timesuffix + ")"
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

	#TAF
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
			combined += "\n**" + setdata[stageindex] + "**: FM"
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
							combined += (nextsettime+timedelta(hours=utcoffset)).strftime(" %a %b%d %H%ML ").upper() + nextartist
						break
					else:
						nextartist=setdata[artistindex][idx+1]
						nextsettime=setdata[settimeindex][idx+1]
						if (zulureq == True):
							combined += nextsettime.strftime("%d%H%M**Z** ") + nextartist
						else:
							combined += (nextsettime+timedelta(hours=utcoffset)).strftime(" %a %b%d %H%ML ").upper() + nextartist
						break
				#if current time is before first set
				elif (currentdatetime < setdata[settimeindex][0]):
					nextartist = setdata[artistindex][0]
					nextsettime = setdata[settimeindex][0]
					if (zulureq == True):
						combined += nextsettime.strftime("%d%H%M**Z** ") + nextartist
					else:
						combined += (nextsettime+timedelta(hours=utcoffset)).strftime(" %a %b%d %H%ML ").upper() + nextartist
					break
				else:
					continue

		if (len(additionalrmks)>1):
			combined+="\n\nADDITIONAL RMKS: " + additionalrmks
		await message.channel.send(combined)

client.run(token)
"""
bot.start(token)
