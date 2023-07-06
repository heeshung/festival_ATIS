import os
import requests
import time
import math
from interactions import slash_command, slash_option, SlashContext, Client, Intents, listen, OptionType, Task, IntervalTrigger, AutocompleteContext
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

#read atis channel
channelfile = open ("channelid","r")

#convert to int
channelid = int(channelfile.read())
channelfile.close()

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



#refreshes artistlist and sorts
async def artistlistmaintain():
	global artistlist
	artistlist=[]
	for x in setdata:
		for y in x:
			if (y["artistname"] not in artistlist):
				artistlist.append(y["artistname"])

	artistlist.sort()

async def scheduleparser():
	#parse schedule data
	for x in range(3,numstages+3):
		#separate stage name and set data
		stagedata = schedule_parsed[x].split("^")
		sets_parsed = stagedata[1].split(",")
		setdatabystage=[]
		for z in range(0,len(sets_parsed),2):
			#convert string into datetime
			formattedtime = datetime.strptime(currentyear+currentmonth+sets_parsed[z],'%y%m%d%H%M')
			#add UTC offset
			formattedtime -= timedelta(hours=utcoffset)
			set_dict = {"stagename": stagedata[0], "artistname": sets_parsed[z+1], "settime": formattedtime, "addedby": bot.owner}
			setdatabystage.append(set_dict)
		setdata.append(setdatabystage)
	#refresh artistlist
	await artistlistmaintain()


additionalrmks=[]

currentatistext=[]
currentatisindex=0

markedsets=[]


async def schedulesorter():
	global setdata
	#sort schedule data
	sortedsetdata=[]
	for stagedict in setdata:
		sortedstage=sorted(stagedict, key=lambda d: d["settime"])
		sortedsetdata.append(sortedstage)
	setdata=sortedsetdata[:]

@Task.create(IntervalTrigger(seconds=20))
async def alerter():
	global markedsets

	#get current time
	currentdatetime=datetime.utcnow()
	markedsetscopy=[]

	#iterate through alert list
	for x in markedsets:
		#if time to set is below the alert interval and set is still in the future
		if ((x["settime"]-currentdatetime).total_seconds()/60 <= x["alertinterval"] and (x["settime"]-currentdatetime).total_seconds() > 0):
			if ((x["settime"]-currentdatetime).total_seconds()/60 < 2):
				await channel.send("ATTENTION ALL AIRCRAFT @here: **" + x["artistname"] + "** BEGINS **NOW** AT **" + x["stagename"] + "** (alert set by " + x["author"].mention + ").")
			else:
				await channel.send("ATTENTION ALL AIRCRAFT @here: **" + x["artistname"] + "** BEGINS IN **" + str(math.ceil((x["settime"]-currentdatetime).total_seconds()/60)) + " MIN** AT **" + x["stagename"] + "** (alert set by " + x["author"].mention + ").")
		#append to list to copy over if not alerted
		else:
			markedsetscopy.append(x)
	markedsets = markedsetscopy[:]

@listen()
async def on_ready():
	global channel
	channel = await bot.fetch_channel(channel_id=channelid)
	await scheduleparser()
	#await channel.send("EVENT ATIS/TAF SERVICE ONLINE " + atisepoch.strftime("%d%H%M") + "Z")
	await schedulesorter()
	alerter.start()

@listen()
async def on_message_create(event):
	if (("what song is this" in event.message.content.lower() or "what is this song" in event.message.content.lower()) and event.message.guild == None):
		await event.message.channel.send(event.message.author.mention + " It's Darude - Sandstorm.")
	elif (event.message.guild==None and event.message.author == bot.owner):
		await channel.send(event.message.content)

@slash_command(name="help", description="Show the help menu with all available commands")
async def help(ctx: SlashContext):
	await ctx.send("## Commands\n>>>  \
- **/addalert <artist>** <stage> <alert_interval>: adds artists that match search term into alert list with respective alert interval (default is 15 minutes)\n \
- **/addremarks <remarks>**: adds additional remarks to be displayed in ATIS and TAF\n \
- **/alertlist**: replies with full alert list\n \
- **/atis** <zulu>: replies with the area ATIS, current artists on stage, and time remaining in sets (set zulu flag to true for Zulu times)\n \
- **/clearremarks**: clears all of your remarks\n \
- **/createset <stage> <set_time> <artist> <set_length>**: create a new set and it to the schedule\n \
- **/fullschedule <stage>**: replies with the full schedule for the specified stage\n \
- **/help**: replies with this help message\n \
- **/rmalert <artist>** <stage>: removes artists that match seach term from alert list\n \
- **/rmset <stage> <set_time> <artist>**: remove a set you created from the schedule\n \
- **/searchsets <artist>**: replies with a list of all sets for the specified artist\n \
- **/taf** <zulu>: replies with the area TAF, upcoming sets and times by stage (set zulu flag to true for Zulu times) \n\n \
NOTE: **bold** flags are required")

@slash_command(name="alertlist", description="List all sets on the alert list")
async def alertlist(ctx: SlashContext):
	listcompose = ""
	if (len(markedsets)==0):
		await ctx.send('No alerts set.')
	else:
		listcompose+='## ALERT LIST:'
		for x in markedsets:
			listcompose+="\n- " + (x["settime"]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " - " + x["artistname"] + " at " + x["stagename"] + " T-" + str(x["alertinterval"]) + " (" + str(x["author"]) + ")"
		await ctx.send(listcompose)

@slash_command(name="addremarks", description="Add additional remarks")
@slash_option(name="remarks", description="Remarks text", required=True, opt_type=OptionType.STRING, min_length=2)
async def addremarks(ctx: SlashContext, remarks: str):
	global additionalrmks
	remarks_dict={"remarktext": remarks, "author": ctx.author}
	additionalrmks.append(remarks_dict)
	await ctx.send("Remarks added.")

@slash_command(name="clearremarks", description="Clear all of your remarks")
async def clearremarks(ctx: SlashContext):
	global additionalrmks
	remarkstoclear=False
	additionalrmkscopy=[]
	for x in additionalrmks:
		if (x["author"]!=ctx.author):
			additionalrmkscopy.append(x)
		else:
			remarkstoclear=True

	additionalrmks = additionalrmkscopy[:]
	if (remarkstoclear == True):
		await ctx.send("Remarks cleared.")
	else:
		await ctx.send("You have no remarks to clear.")
	

@slash_command(name="addalert", description="Add an existing set to the alert list")
@slash_option(name="artist", description="Artist search term", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
@slash_option(name="stage", description="Artist search term", required=False, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
@slash_option(name="alert_interval", description="Number of minutes prior to set to be alerted", required=False, opt_type=OptionType.INTEGER, min_value=1)
async def addalert(ctx: SlashContext, artist: str, stage: str='', alert_interval: int = 15):
	global markedsets

	#get current time
	currentdatetime=datetime.utcnow()

	searchterm = artist.lower()
	matchfound = False

	#iterate through all sets and mark priority sets
	for x in setdata:
		for a in x:
			#check if alert is already added
			if (searchterm in a["artistname"].lower() and stage.lower() in a["stagename"].lower() and (a["settime"]-currentdatetime).total_seconds()/60 > alert_interval):
				alreadyadded = False
				for y in markedsets:
					if (a["artistname"] == y["artistname"] and a["stagename"] == y["stagename"] and a["settime"] == y["settime"] and alert_interval == y["alertinterval"]):
						alreadyadded = True
						break
				#skip if already added
				if (alreadyadded == True):
					continue
				else:
					set_dict={"stagename": a["stagename"], "artistname": a["artistname"], "settime": a["settime"], "author": ctx.author, "alertinterval": alert_interval}
					markedsets.append(set_dict)
					matchfound = True
					await ctx.send(ctx.author.mention + " added " + a["artistname"] + "'s " + a["stagename"] + " set at " + (a["settime"]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " to the alert list. :white_check_mark:")
					#sort alert list
					sortedsets=sorted(markedsets, key=lambda d: (d["settime"], d["artistname"], d["alertinterval"]))
					markedsets=sortedsets[:]
			
	#if no match is found
	if (matchfound == False):
		await ctx.send("Couldn't find any artists with '"+artist+"' in their name with sets and alert intervals that are not already on the alert list.")


#addalert artist autocomplete
@addalert.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in artistlist:		
		if (ctx.input_text.lower() in x.lower()):
				artist_dict = {"name": x,"value": x}
				choicelist.append(artist_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])

#addalert stage autocomplete
@addalert.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in setdata:
		if (ctx.input_text.lower() in x[0]["stagename"].lower()):
			stage_dict = {"name": x[0]["stagename"],"value": x[0]["stagename"]}
			choicelist.append(stage_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])

@slash_command(name="rmalert", description="Remove a set from the alert list")
@slash_option(name="artist", description="Artist search term", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
@slash_option(name="stage", description="Artist search term", required=False, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
async def rmalert(ctx: SlashContext, artist: str, stage: str=""):
	global markedsets

	matchfound = False
	markedsetscopy = []
	searchterm = (artist).lower()
	for x in markedsets:
		if (searchterm in x["artistname"].lower() and stage.lower() in x["stagename"].lower() and ctx.author == x["author"]):
			matchfound = True
			await ctx.send(ctx.author.mention + " removed " + x["artistname"] + "'s " + x["stagename"] + " set at " + (x["settime"]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " from the alert list. :x:")
		else:
			#add undeleted sets back in
			markedsetscopy.append(x)
	markedsets=markedsetscopy[:]
	if (matchfound == False):
		await ctx.send("Couldn't find any artists with '"+artist+"' in their name in the alert list.")

#rmalert artist autocomplete (only need to populate with artists in the alert list)
@rmalert.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in markedsets:
		if (ctx.input_text.lower() in x["artistname"].lower()):
				artist_dict = {"name": x["artistname"],"value": x["artistname"]}
				choicelist.append(artist_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])

#rmalert stage autocomplete (only need to populate with stages in the alert list)
@rmalert.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in markedsets:
		if (ctx.input_text.lower() in x["stagename"].lower()):
			stage_dict = {"name": x["stagename"],"value": x["stagename"]}
			choicelist.append(stage_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])

@slash_command(name="atis", description="Show the ATIS, including current weather and sets")
@slash_option(name="zulu", description="Zulu flag (true/false)", required=False, opt_type=OptionType.BOOLEAN)
async def atis(ctx: SlashContext, zulu: bool = False):

	global currentatisindex
	global currentatistext


	#get current time
	currentdatetime=datetime.utcnow()


	#get METAR
	c_atis=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&stationString='+icao+'&hoursBeforeNow=2')
	atisoutput = (c_atis.text)
	begin=atisoutput.find("Z ")
	end=atisoutput.find("</raw_text>")

	atiscompare=[]
	atiscompare.append(atisoutput[begin+2:end] + "\n\nREMARKS")
	timeremaintext=[]

	#iterate through each stage
	for stageindex in range(0,len(setdata)):
		#add stage name
		atiscompose = "\n**" + setdata[stageindex][0]["stagename"] + "**: "
		timeremaincompose=""
		for idx, x in reversed(list(enumerate(setdata[stageindex]))):
			if (currentdatetime >= setdata[stageindex][idx]["settime"]):
				currentartist=setdata[stageindex][idx]["artistname"]
				#check if current artist is not last
				if (idx < len(setdata[stageindex])-1):
					nextartist = setdata[stageindex][idx+1]["artistname"]
					#get minutes remaining in set
					timeremain = (setdata[stageindex][idx+1]["settime"]-currentdatetime).total_seconds()
					timeremain = math.ceil(timeremain/60)
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
			nextartist = setdata[stageindex][0]["artistname"]
			#get minutes before set
			timeremain = (setdata[stageindex][0]["settime"]-currentdatetime).total_seconds()
			timeremain = math.ceil(timeremain/60)
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

	#add remarks into last entry of atiscompare list
	if (len(additionalrmks)>0):
		atiscompare[len(atiscompare)-1]="\n\nADDITIONAL REMARKS"
		for j in additionalrmks:
			atiscompare[len(atiscompare)-1]+="\n- "+j["remarktext"] + " (" + str(j["author"]) + ")"

	#check if new ATIS matches old, if not advance ATIS letter
	if (len(currentatistext)==0):
		currentatistext=atiscompare.copy()

	elif (len(currentatistext)>0 and (atiscompare != currentatistext)):
		currentatisindex=(currentatisindex+1)%26
		currentatistext=atiscompare.copy()


	if (zulu == True):
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


	await ctx.send(combined)


@slash_command(name="taf", description="Show the TAF, including forecast weather and future sets")
@slash_option(name="zulu", description="Zulu flag (true/false)", required=False, opt_type=OptionType.BOOLEAN)
async def taf(ctx: SlashContext, zulu: bool = False):

	#get current time
	currentdatetime=datetime.utcnow()

	c_taf=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&stationString='+icao+'&hoursBeforeNow=4')
	tafoutput = (c_taf.text)
	begin=tafoutput.find("Z ")
	end=tafoutput.find("</raw_text>")

	if (zulu == True):
		combined = eventvenuename + " TAF " + currentdatetime.strftime("%d%H%M**Z** ") + tafoutput[begin+2:end]

	else:
		combined = eventvenuename + " TAF " + (currentdatetime+timedelta(hours=utcoffset)).strftime("%d%H%M**L** **(%a %b%d %H%ML)** ").upper() + tafoutput[begin+2:end]

	combined += "\n\nREMARKS"

	for stageindex in range(0,len(setdata)):
		combined += "\n**" + setdata[stageindex][0]["stagename"] + "**: FM"
		for idx, x in reversed(list(enumerate(setdata[stageindex]))):
			#if current time is past time of first set
			if (currentdatetime >= setdata[stageindex][idx]["settime"]):
				#check if current artist is last
				if (idx == len(setdata[stageindex])-1):
					nextartist=setdata[stageindex][idx]["artistname"]
					nextsettime=setdata[stageindex][idx]["settime"]
					if (zulu == True):
						combined += nextsettime.strftime("%d%H%M**Z** ") + nextartist
					else:
						combined += (nextsettime+timedelta(hours=utcoffset)).strftime(" %a %b%d %H%ML ").upper() + nextartist
					break
				else:
					nextartist=setdata[stageindex][idx+1]["artistname"]
					nextsettime=setdata[stageindex][idx+1]["settime"]
					if (zulu == True):
						combined += nextsettime.strftime("%d%H%M**Z** ") + nextartist
					else:
						combined += (nextsettime+timedelta(hours=utcoffset)).strftime(" %a %b%d %H%ML ").upper() + nextartist
					break
			#if current time is before first set
			elif (currentdatetime < setdata[stageindex][0]["settime"]):
				nextartist = setdata[stageindex][0]["artistname"]
				nextsettime = setdata[stageindex][0]["settime"]
				if (zulu == True):
					combined += nextsettime.strftime("%d%H%M**Z** ") + nextartist
				else:
					combined += (nextsettime+timedelta(hours=utcoffset)).strftime(" %a %b%d %H%ML ").upper() + nextartist
				break
			else:
				continue

	if (len(additionalrmks)>0):
		combined+="\n\nADDITIONAL REMARKS"
		for j in additionalrmks:
			combined+="\n- "+j["remarktext"] + " (" + str(j["author"]) + ")"

	await ctx.send(combined)

@slash_command(name="createset", description="Create a new set and add it to the schedule")
@slash_option(name="stage", description="Stage name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
@slash_option(name="artist", description="Name of artist", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
@slash_option(name="set_time", description="LOCAL Set time (use DDHHMM)", required=True, opt_type=OptionType.STRING, min_length=6, max_length=6)
@slash_option(name="set_length", description="Length of set in minutes", required=True, opt_type=OptionType.INTEGER)
async def createset(ctx: SlashContext, stage: str, artist: str, set_time: str, set_length: int):

	setadded = False
	formattedsettime = datetime.strptime(currentyear+currentmonth+set_time,'%y%m%d%H%M')
	

	#add UTC offset
	formattedsettime -= timedelta(hours=utcoffset)
	#compute set end time
	formattedendtime = formattedsettime +timedelta(minutes=set_length)

	set_dict = {"artistname": artist, "stagename": stage, "settime": formattedsettime, "addedby": ctx.author}
	end_dict = {"artistname": "STGE CLSD", "stagename": stage, "settime": formattedendtime, "addedby": ctx.author}
	for x in setdata:
		if (x[0]["stagename"]==stage):
			x.append(set_dict)
			x.append(end_dict)
			setadded = True
			break

	#if stage not already in list
	if (setadded == False):	
		newsetlist=[]
		newsetlist.append(set_dict)
		newsetlist.append(end_dict)
		setdata.append(newsetlist)
		setadded = True

	if (setadded == True):
		#refresh artistlist
		await artistlistmaintain()
		#sort schedule after addition
		await schedulesorter()
		await ctx.send(ctx.author.mention + " created a new " + str(set_length) + " minute long **" + artist + "** set at **" + stage + "**, starting at **" + (formattedsettime+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + "**. :sparkles::sparkles:")
	else:
		await ctx.send("Error creating new set.")


#createset stage autocomplete
@createset.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in setdata:
		if (ctx.input_text.lower() in x[0]["stagename"].lower()):
			stage_dict = {"name": x[0]["stagename"],"value": x[0]["stagename"]}
			choicelist.append(stage_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])
	

#createset artist autocomplete
@createset.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in artistlist:		
		if (ctx.input_text.lower() in x.lower()):
				artist_dict = {"name": x,"value": x}
				choicelist.append(artist_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])
		

@slash_command(name="rmset", description="Remove a set you created from the schedule")
@slash_option(name="stage", description="Stage name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
@slash_option(name="artist", description="Name of artist", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
@slash_option(name="set_time", description="LOCAL Set time (use DDHHMM)", required=True, opt_type=OptionType.STRING, min_length=6, max_length=6)
async def rmset(ctx: SlashContext, stage: str, artist: str, set_time: str):
	global setdata
	setremoved = False
	formattedsettime = datetime.strptime(currentyear+currentmonth+set_time,'%y%m%d%H%M')

	#add UTC offset
	formattedsettime -= timedelta(hours=utcoffset)

	#empty lists for list comprehension
	setdatacopy=[]
	for x in setdata:
		stagecopy=[]
		for y in x:
			if (y["stagename"].lower()==stage.lower() and y["artistname"].lower()==artist.lower() and y["settime"]==formattedsettime and y["addedby"]==ctx.author):
				await ctx.send(":exclamation: " + ctx.author.mention + " removed " + y["artistname"] + "'s " + y["stagename"] + " set at " + (y["settime"]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " from the schedule.")
				setremoved = True
			else:
				stagecopy.append(y)
		setdatacopy.append(stagecopy)

	setdata=setdatacopy[:]

	if (setremoved == False):
		await ctx.send("Couldn't find any sets with the entered parameters that you created, " + ctx.author.mention + ".")
	else:
		#refresh artistlist
		await artistlistmaintain()
	

#rmset autocomplete
@rmset.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in setdata:
		if (ctx.input_text.lower() in x[0]["stagename"].lower()):
			stage_dict = {"name": x[0]["stagename"],"value": x[0]["stagename"]}
			choicelist.append(stage_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])

#rmset artist autocomplete
@rmset.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in artistlist:		
		if (ctx.input_text.lower() in x.lower()):
				artist_dict = {"name": x,"value": x}
				choicelist.append(artist_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])

@slash_command(name="fullschedule", description="List the full schedule for a stage")
@slash_option(name="stage", description="Stage name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
async def fullschedule(ctx: SlashContext, stage: str):
	stagefound = False
	#step through schedule
	for x in setdata:
		if (stage.lower() in x[0]["stagename"].lower()):
			listcompose = "## **" + x[0]["stagename"] + " FULL SCHEDULE:**"
			stagefound = True
			for y in x:
				listcompose+="\n" + (y["settime"]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " - " + y["artistname"]
			await ctx.send(listcompose)
			break

	#return error if stage isn't found
	if (stagefound == False):
		await ctx.send("Couldn't find '"+stage+"' in list of stages.")

#fullschedule autocomplete
@fullschedule.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in setdata:
		if (ctx.input_text.lower() in x[0]["stagename"].lower()):
			stage_dict = {"name": x[0]["stagename"],"value": x[0]["stagename"]}
			choicelist.append(stage_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])

@slash_command(name="searchsets", description="Find and list all sets for the specified artist")
@slash_option(name="artist", description="Name of artist", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=3)
async def searchsets(ctx: SlashContext, artist: str):
	artistfound = False
	#find artist
	for x in setdata:
		for y in x:
			if (artist.lower() in y["artistname"].lower()):
				listcompose = "## All " + artist + " Sets:"
				artistfound=True

	if (artistfound==True):
		#step through schedule
		for x in setdata:
			for y in x:
				if (artist.lower() in y["artistname"].lower()):
					listcompose += "\n- " + (y["settime"]+timedelta(hours=utcoffset)).strftime("%a %b%d %H%ML").upper() + " - " + y["artistname"] + " - " + y["stagename"]

		await ctx.send(listcompose)

	else:
		await ctx.send("Couldn't find any sets with '" + artist + "' in the artist name.")

#searchsets artist autocomplete
@searchsets.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	choicelist=[]
	for x in artistlist:		
		if (ctx.input_text.lower() in x.lower()):
				artist_dict = {"name": x,"value": x}
				choicelist.append(artist_dict)

	if (len(choicelist)>25):
		await ctx.send(choices=choicelist[:25])
	else:
		await ctx.send(choices=choicelist[:])
	
bot.start(token)
