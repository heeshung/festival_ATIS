import requests
import math
import logging
import sys
from interactions import slash_command, slash_option, SlashContext, Client, Intents, listen, OptionType, Task, IntervalTrigger, AutocompleteContext, ActionRow, Button, spread_to_rows, ButtonStyle
from interactions.ext import prefixed_commands
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from asyncio import TimeoutError

#logger
logging.basicConfig(filename="log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
cls_log = logging.getLogger()
cls_log.setLevel(logging.INFO)

#bot setup
bot = Client(intents=Intents.DEFAULT, sync_interactions=True, asyncio_debug=True, logger=cls_log)
prefixed_commands.setup(bot)

atisletters=["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
atisepoch=datetime.utcnow()
atisepoch = atisepoch.replace(tzinfo=ZoneInfo("UTC"))

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
schedule = open(sys.argv[1],"r")

#remove newlines
schedule_data = schedule.read()
schedule_parsed = schedule_data.split("\n")
schedule.close()

#get venue name
eventvenuename=schedule_parsed[0]

#get time zone
time_zone = schedule_parsed[1]

#get icao airport code
icao = schedule_parsed[2]

#get number of stages based on number of colons
numstages=(len(''.join(schedule_parsed[3:]).split("^"))-1)

setdata=[]

additionalrmks=[]

currentatistextcompare=[]
currentatisindex=0

#refreshes artistlist and sorts
async def artistlistmaintain():
	global artistlist
	artistlist=[]
	for x in setdata:
		for y in x:
			if (y["artistname"] not in artistlist and y["artistname"] != "STGE CLSD"):
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
			#set time zone
			formattedtime = formattedtime.replace(tzinfo=ZoneInfo(time_zone))
			alert_list = []
			set_dict = {"stagename": stagedata[0], "artistname": sets_parsed[z+1], "settime": formattedtime, "addedby": bot.owner, "alerts": alert_list}
			setdatabystage.append(set_dict)
		setdata.append(setdatabystage)
	#refresh artistlist
	await artistlistmaintain()


#sorts schedule and removes stages without sets
async def schedulesorter():
	global setdata
	#sort schedule data
	sortedsetdata=[]
	for stage in setdata:
		#check if stage has any sets
		stagehassets=False
		for set in stage:
			if (set["artistname"]!="STGE CLSD"):
				stagehassets=True
				break
		if (stagehassets==True):
			sortedstage=sorted(stage, key=lambda d: d["settime"])
			sortedsetdata.append(sortedstage)
	setdata=sortedsetdata[:]

#assigns stars based on interest level
async def startier(alerts):
	uniquelist=[]
	for x in alerts:
		if (x["author"] not in uniquelist):
			uniquelist.append(x["author"])
	if (len(uniquelist)==1):
		return (":small_blue_diamond:")
	elif(len(uniquelist)==2):
		return (":small_orange_diamond:")
	elif(len(uniquelist)>2):
		return (" :fire:")
	else:
		return ("")
	
async def artistautocomplete(input):
	choicelist=[]
	for x in artistlist:		
		if (input.lower() in x.lower()):
				artist_dict = {"name": x,"value": x}
				choicelist.append(artist_dict)

	if (len(choicelist)>25):
		choices=choicelist[:25]
		return (choices)
	else:
		choices=choicelist[:]
		return (choices)
	
async def stageautocomplete(input):
	choicelist=[]
	for x in setdata:
		if (input.lower() in x[0]["stagename"].lower()):
			stage_dict = {"name": x[0]["stagename"],"value": x[0]["stagename"]}
			choicelist.append(stage_dict)

	if (len(choicelist)>25):
		choices=choicelist[:25]
		return (choices)
	else:
		choices=choicelist[:]
		return (choices)


@Task.create(IntervalTrigger(seconds=20))
async def alerter():

	#get current time
	currentdatetime=datetime.utcnow()

	#set UTC on currentdatetime
	currentdatetime=currentdatetime.replace(tzinfo=ZoneInfo("UTC"))


	#iterate through alert list, for each stage
	for stage in setdata:
		#for each set
		for set in stage:
			alertauthors=[]
			#for each alert in set
			for alert in set["alerts"]:
				#if time to set is below the alert interval and set is still in the future, and alert hasn't been triggered before
				if ((set["settime"]-currentdatetime).total_seconds()/60 <= alert["alertinterval"] and (set["settime"]-currentdatetime).total_seconds() > 0 and alert["alerted"]==False):
					alertauthors.append(alert["author"])
					alert["alerted"] = True

			#if there were triggered alerts
			if (len(alertauthors)>0):
				if ((set["settime"]-currentdatetime).total_seconds()/60 < 2):
					messagecompose=("ATTENTION ALL AIRCRAFT: **" + set["artistname"] + "** BEGINS **NOW** AT **" + set["stagename"] + "** (starred by")
					for x in alertauthors:
						messagecompose+=" "+str(x)
					messagecompose+="). <a:POGSLIDE:833580864688095262><a:POGSLIDE:833580864688095262>  @everyone"
					await channel.send(messagecompose)
				else:
					messagecompose=("ATTENTION ALL AIRCRAFT: **" + set["artistname"] + "** BEGINS IN **" + str(math.ceil((set["settime"]-currentdatetime).total_seconds()/60)) + " MIN** AT **" + set["stagename"] + "** (starred by")
					for x in alertauthors:
						messagecompose+=" "+str(x)
					messagecompose+="). <a:peepoDJ:972197117584080996> <a:PepoDance:746268833890828388>  @everyone"
					await channel.send(messagecompose)

@listen()
async def on_ready():
	global channel
	channel = await bot.fetch_channel(channel_id=channelid)
	await scheduleparser()
	await schedulesorter()
	alerter.start()
	await channel.send(eventvenuename + " ATIS/TAF SERVICE ONLINE " + atisepoch.astimezone(ZoneInfo("UTC")).strftime("%d%H%M") + "Z", silent=True)

@listen()
async def on_message_create(event):
	#if DM and author is not bot itself
	if (event.message.guild == None and event.message.author != bot.user):
		if (("what song is this" in event.message.content.lower() or "what is this song" in event.message.content.lower())):
			await event.message.channel.send(event.message.author.mention + " It's Darude - Sandstorm.")
		elif (event.message.author == bot.owner):
			await channel.send(event.message.content)
			
		#only log if DM
		cls_log.info("DM - " + str(event.message.author) + ": " + event.message.content)

@slash_command(name="help", description="Show the help menu with all available commands")
async def help(ctx: SlashContext):
	try:
		await ctx.send("## COMMANDS\n\
	> - **/addremarks <remarks>**: adds additional remarks to be displayed in ATIS and TAF\n\
	> - **/atis**: replies with the area ATIS, current artists on stage, and time remaining in sets\n\
	> - **/clearremarks**: clears all of your remarks\n\
	> - **/createset <stage> <artist> <set_start_time> <set_length> <does_stage_close>**: creates a new set and adds it to the schedule; set <does_stage_close> to True if there is no set immediately following the created set\n\
	> - **/fullschedule <stage>**: replies with the full schedule for the specified stage\n\
	> - **/help**: replies with this help message\n\
	> - **/liststarredsets**: replies with list of all starred sets, including who starred the set and alert intervals\n\
	> - **/removeset <stage> <artist>**: removes all sets with the specified stage and artist that you created from the schedule\n\
	> - **/searchsets <artist>**: replies with a list of all sets for the specified artist\n\
	> - **/star <artist>** <stage> <alert_interval>: stars a set and sets up an alert with the specified alert interval (default is 15 minutes)\n\
	> - **/taf** <zulu>: replies with the area TAF, upcoming sets and times by stage; set <zulu> to True for Zulu times (default is False)\n\
	> - **/unstar <artist>** <stage>: unstars all sets with the specified artist and stage\n\n### **Notes**:\n- **bold** flags are required\n- :small_blue_diamond:, :small_orange_diamond:, :fire: denote starred sets by popularity\n\
	 - :small_blue_diamond: = set starred by one person\n - :small_orange_diamond: = set starred by two people \n - :fire: = set starred by more than two people", ephemeral=True)
		
		#log
		cls_log.info(str(ctx.author) + " used /help")

	except:
		await ctx.send("Error running command.", ephemeral=True)

@slash_command(name="liststarredsets", description="List all starred sets")
async def liststarredsets(ctx: SlashContext):
	try:
		listcompose = ""
		#step through stages
		for x in setdata:
			#step through sets
			for y in x:
				foundalerts=[]
				#step through alerts in each set
				for z in y["alerts"]:
					foundalerts.append(z)
				if (len(foundalerts)>0):
					listcompose += "\n- " + (y["settime"].astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + " - " + y["artistname"] + " at " + y["stagename"]
					#loop through found alerts
					for b in foundalerts:
						listcompose += "\n - (" + str(b["author"]) + ", T-" + str(b["alertinterval"])
						if (b["alerted"]==True):
							listcompose += ", alert sent :ballot_box_with_check:)"
						else:
							listcompose += ")"


		if (len(listcompose)==0):
			await ctx.send('No starred sets.', ephemeral=True)
		else:
			finalcompose='## ALL STARRED SETS:'
			finalcompose+=listcompose
			await ctx.send(finalcompose, ephemeral=True)
		
		#log
		cls_log.info(str(ctx.author) + " used /liststarredsets")

	except:
		await ctx.send("Error running command.", ephemeral=True)

@slash_command(name="addremarks", description="Add additional remarks")
@slash_option(name="remarks", description="Remarks text", required=True, opt_type=OptionType.STRING, min_length=2)
async def addremarks(ctx: SlashContext, remarks: str):
	try:
		global additionalrmks
		remarks_dict={"remarktext": remarks, "author": ctx.author}
		additionalrmks.append(remarks_dict)
		await ctx.send("'" + remarks + "' added to the additional remarks.", ephemeral=True)

		#log
		cls_log.info(str(ctx.author) + " used /addremarks")

	except:
		await ctx.send("Error running command.", ephemeral=True)

@slash_command(name="clearremarks", description="Clear all of your remarks")
async def clearremarks(ctx: SlashContext):
	try:
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
			await ctx.send("Remarks cleared.", ephemeral=True)
		else:
			await ctx.send("You have no remarks to clear.", ephemeral=True)

		#log
		cls_log.info(str(ctx.author) + " used /clearremarks")

	except:
		await ctx.send("Error running command.", ephemeral=True)
	

@slash_command(name="star", description="Star a set and create a new alert")
@slash_option(name="artist", description="Artist name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
@slash_option(name="stage", description="Stage name", required=False, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
@slash_option(name="alert_interval", description="Number of minutes prior to set to be alerted (default = 15)", required=False, opt_type=OptionType.INTEGER, min_value=1)
async def star(ctx: SlashContext, artist: str, stage: str='', alert_interval: int = 15):
	try:
		#get current time
		currentdatetime=datetime.utcnow()

		#set UTC on currentdatetime
		currentdatetime=currentdatetime.replace(tzinfo=ZoneInfo("UTC"))

		searchterm = artist.lower()
		matchfound = False

		#iterate through all sets and mark priority sets
		for x in setdata:
			for a in x:
				#check if alert is valid
				if (searchterm in a["artistname"].lower() and stage.lower() in a["stagename"].lower() and (a["settime"]-currentdatetime).total_seconds()/60 > alert_interval):
					alreadyadded = False
					#check if alert is already added
					for alert in a["alerts"]:
						if (alert_interval == alert["alertinterval"] and ctx.author == alert["author"]):
							alreadyadded = True
							break
					#skip if already added
					if (alreadyadded == True):
						continue
					else:
						alert_dict = {"author": ctx.author, "alertinterval": alert_interval, "alerted": False}
						a["alerts"].append(alert_dict)
						
						matchfound = True
						await ctx.send("You starred " + a["artistname"] + "'s " + a["stagename"] + " set at " + (a["settime"].astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + " (T-" + str(alert_interval) + "). :white_check_mark:", ephemeral=True)
				
		#if no match is found
		if (matchfound == False):
			await ctx.send("Couldn't find any sets with '"+artist+"' in the artist name that are not already starred, with that alert interval, or have not already begun.", ephemeral=True)

		#log
		cls_log.info(str(ctx.author) + " used /star")

	except:
		await ctx.send("Error running command.", ephemeral=True)

#star artist autocomplete
@star.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await artistautocomplete(ctx.input_text))

#star stage autocomplete
@star.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await stageautocomplete(ctx.input_text))

@slash_command(name="unstar", description="Unstar a set and remove all of its alerts")
@slash_option(name="artist", description="Artist name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
@slash_option(name="stage", description="Stage name", required=False, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
async def unstar(ctx: SlashContext, artist: str, stage: str=""):
	try:
		matchfound = False
		#for each stage
		for x in setdata:
			#for each set
			for y in x:
				alertscopy = []
				#if artist matches and stage matches
				if (artist.lower() in y["artistname"].lower() and stage.lower() in y["stagename"].lower()):
					#for each alert in set
					for z in y["alerts"]:
						#if requestor is author of alert
						if (ctx.author == z["author"]):
							matchfound = True
						else:
							alertscopy.append(z)
					#if matches were found
					if (len(alertscopy)<len(y["alerts"])):
						await ctx.send("You unstarred " + y["artistname"] + "'s " + y["stagename"] + " set at " + (y["settime"].astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + ". :x:", ephemeral=True)
					y["alerts"] = alertscopy[:]

		if (matchfound == False):
			await ctx.send("Couldn't find any sets with the entered parameters that you starred.", ephemeral=True)

		#log
		cls_log.info(str(ctx.author) + " used /unstar")

	except:
		await ctx.send("Error running command.", ephemeral=True)

#unstar artist autocomplete
@unstar.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await artistautocomplete(ctx.input_text))

#unstar stage autocomplete
@unstar.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await stageautocomplete(ctx.input_text))

@slash_command(name="atis", description="Show the ATIS, including current weather and sets")
async def atis(ctx: SlashContext):
	try:

		global currentatisindex
		global currentatistextcompare


		#get current time
		currentdatetime=datetime.utcnow()

		#set UTC on currentdatetime
		currentdatetime=currentdatetime.replace(tzinfo=ZoneInfo("UTC"))


		#get METAR
		c_atis=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&stationString='+icao+'&hoursBeforeNow=2')
		atisoutput = (c_atis.text)
		begin=atisoutput.find("Z ")
		end=atisoutput.find("</raw_text>")

		#atiscompare to compare next atis with current to determine if atis index should be advanced

		atiscompare=[]
		finalatis = []
		atiscompare.append(atisoutput[begin+2:end])
		finalatis.append(atisoutput[begin+2:end] + "\n\nREMARKS")
		timeremaintext=[]

		#iterate through each stage
		for stageindex in range(0,len(setdata)):
			#add stage name
			atiscompare.append(setdata[stageindex][0]["stagename"])
			finalatiscompose = "\n**" + setdata[stageindex][0]["stagename"] + "**: "
			timeremaincompose=""
			for idx, x in reversed(list(enumerate(setdata[stageindex]))):
				if (currentdatetime >= setdata[stageindex][idx]["settime"]):
					currentartist=setdata[stageindex][idx]["artistname"]
					#add star if currentartist is starred
					currentartist=currentartist + await startier(setdata[stageindex][idx]["alerts"])
					#adding currentartist with star to compare
					currentartistcompare = currentartist
					#check if current artist is not last
					if (idx < len(setdata[stageindex])-1):
						nextartist = setdata[stageindex][idx+1]["artistname"]
						#add star if next artist is starred
						nextartist=nextartist + await startier(setdata[stageindex][idx+1]["alerts"])
						#adding nextartist with star to compare
						nextartistcompare = nextartist
						#get minutes remaining in set
						timeremain = (setdata[stageindex][idx+1]["settime"]-currentdatetime).total_seconds()
						timeremain = math.ceil(timeremain/60)
						timesuffix = ""
						#if timeremain is greater than a day
						if (timeremain/60 > 24):
							timesuffix = str(int(timeremain/60/24)) + " d "
						#if timeremain is greater than or equal to an hour after subtracting days
						if (timeremain/60%24>=1):
							timesuffix += str(int(timeremain/60%24)) + " hr "
						#add minutes
						timesuffix += str(int(timeremain%60)) + " min"
						timeremaincompose=" (" + nextartist + " in " + timesuffix + ")"
					#if current artist is last
					else:
						nextartistcompare=""
						timeremaincompose=""
					break
				#if current artist is before first
				nextartist = setdata[stageindex][0]["artistname"]
				#add star if next artist is starred
				nextartist=nextartist + await startier(setdata[stageindex][0]["alerts"])
				#adding nextartist with star to compare
				nextartistcompare = nextartist
				#get minutes before set
				timeremain = (setdata[stageindex][0]["settime"]-currentdatetime).total_seconds()
				timeremain = math.ceil(timeremain/60)
				timesuffix = ""
				#if timeremain is greater than a day
				if (timeremain/60 > 24):
					timesuffix = str(int(timeremain/60/24)) + " d "
				#if timeremain is greater than or equal to an hour after subtracting days
				if (timeremain/60%24>=1):
					timesuffix += str(int(timeremain/60%24)) + " hr "
				#add minutes
				timesuffix += str(int(timeremain%60)) + " min"
				timeremaincompose=" (" + nextartist + " in " + timesuffix + ")"
				currentartist="STGE CLSD"
				currentartistcompare = currentartist

			timeremaintext.append(timeremaincompose)

			#add current artist to compare
			atiscompare.append(currentartistcompare)
			#add next artist to compare
			atiscompare.append(nextartistcompare)

			finalatiscompose += currentartist
			
			finalatis.append(finalatiscompose)

		#add remarks into last entry of atiscompare list
		if (len(additionalrmks)>0):
			finalatis.append("\n\nADDITIONAL REMARKS")
			for j in additionalrmks:
				atiscompare.append("\n- "+j["remarktext"] + " (" + str(j["author"]) + ")")
				finalatis.append("\n- "+j["remarktext"] + " (" + str(j["author"]) + ")")

		#check if new ATIS matches old, if not advance ATIS letter
		if (len(currentatistextcompare)==0):
			currentatistextcompare=atiscompare.copy()

		elif (len(currentatistextcompare)>0 and (atiscompare != currentatistextcompare)):
			currentatisindex=(currentatisindex+1)%26
			currentatistextcompare=atiscompare.copy()

		#compose atis
		combined = eventvenuename + " (" + icao + ")" + " ATIS INFO " + atisletters[currentatisindex] + " " + currentdatetime.astimezone(ZoneInfo("UTC")).strftime("%d%H%MZ ") + (currentdatetime.astimezone(ZoneInfo(time_zone))).strftime("**(%a %b%d %H%ML)** ").upper()
		for x in range(0,len(finalatis)):
			combined += finalatis[x]
			#add time remaining text
			if (x>0 and x < len(timeremaintext)+1):
					combined += timeremaintext[x-1]


		await ctx.send(combined, silent=True)

		#log
		cls_log.info(str(ctx.author) + " used /atis")

	except:
		await ctx.send("Error running command.", ephemeral=True)


@slash_command(name="taf", description="Show the TAF, including forecast weather and future sets")
@slash_option(name="zulu", description="Zulu flag (default = False)", required=False, opt_type=OptionType.BOOLEAN)
async def taf(ctx: SlashContext, zulu: bool = False):
	try:

		#get current time
		currentdatetime=datetime.utcnow()

		#set UTC on currentdatetime
		currentdatetime=currentdatetime.replace(tzinfo=ZoneInfo("UTC"))

		c_taf=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&stationString='+icao+'&hoursBeforeNow=4')
		tafoutput = (c_taf.text)
		begin=tafoutput.find("Z ")
		end=tafoutput.find("</raw_text>")

		if (zulu == True):
			combined = eventvenuename  + " (" + icao + ")" + " TAF " + currentdatetime.astimezone(ZoneInfo("UTC")).strftime("%d%H%MZ ") + tafoutput[begin+2:end]

		else:
			combined = eventvenuename  + " (" + icao + ")" + " TAF " + currentdatetime.astimezone(ZoneInfo("UTC")).strftime("%d%H%MZ ") +  currentdatetime.astimezone(ZoneInfo(time_zone)).strftime("**(%a %b%d %H%ML)** ").upper() + tafoutput[begin+2:end]

		combined += "\n\nREMARKS"

		for stageindex in range(0,len(setdata)):
			combined += "\n**" + setdata[stageindex][0]["stagename"] + "**: FM"
			for idx, x in reversed(list(enumerate(setdata[stageindex]))):
				#if current time is past time of first set
				if (currentdatetime >= setdata[stageindex][idx]["settime"]):
					#check if current artist is last
					if (idx == len(setdata[stageindex])-1):
						nextartist=setdata[stageindex][idx]["artistname"]
						#add star if next artist is starred
						nextartist=nextartist + await startier(setdata[stageindex][idx]["alerts"])
						nextsettime=setdata[stageindex][idx]["settime"]
						if (zulu == True):
							combined += nextsettime.astimezone(ZoneInfo("UTC")).strftime("%d%H%MZ ") + nextartist
						else:
							combined += (nextsettime.astimezone(ZoneInfo(time_zone))).strftime(" %a %b%d %H%ML ").upper() + nextartist
						break
					else:
						nextartist=setdata[stageindex][idx+1]["artistname"]
						#add star if next artist is starred
						nextartist=nextartist + await startier(setdata[stageindex][idx+1]["alerts"])
						nextsettime=setdata[stageindex][idx+1]["settime"]
						if (zulu == True):
							combined += nextsettime.astimezone(ZoneInfo("UTC")).strftime("%d%H%MZ ") + nextartist
						else:
							combined += (nextsettime.astimezone(ZoneInfo(time_zone))).strftime(" %a %b%d %H%ML ").upper() + nextartist
						break
				#if current time is before first set
				elif (currentdatetime < setdata[stageindex][0]["settime"]):
					nextartist = setdata[stageindex][0]["artistname"]
					#add star if next artist is starred
					nextartist=nextartist + await startier(setdata[stageindex][0]["alerts"])
					nextsettime = setdata[stageindex][0]["settime"]
					if (zulu == True):
						combined += nextsettime.astimezone(ZoneInfo("UTC")).strftime("%d%H%MZ ") + nextartist
					else:
						combined += (nextsettime.astimezone(ZoneInfo(time_zone))).strftime(" %a %b%d %H%ML ").upper() + nextartist
					break
				else:
					continue

		if (len(additionalrmks)>0):
			combined+="\n\nADDITIONAL REMARKS"
			for j in additionalrmks:
				combined+="\n- "+j["remarktext"] + " (" + str(j["author"]) + ")"

		await ctx.send(combined, silent=True)

		#log
		cls_log.info(str(ctx.author) + " used /taf")

	except:
		await ctx.send("Error running command.", ephemeral=True)

@slash_command(name="createset", description="Create a new set and add it to the schedule")
@slash_option(name="stage", description="Stage name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
@slash_option(name="artist", description="Artist name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
@slash_option(name="set_start_time", description="LOCAL set starting time (use DDHHMM)", required=True, opt_type=OptionType.STRING, min_length=6, max_length=6)
@slash_option(name="set_length", description="Length of set in minutes", required=True, opt_type=OptionType.INTEGER)
@slash_option(name="does_stage_close", description="Denotes if stage closes after added set", required=True, opt_type=OptionType.BOOLEAN)
async def createset(ctx: SlashContext, stage: str, artist: str, set_start_time: str, set_length: int, does_stage_close: bool):
	#try:

	setadded = False
	setcollision = False
	confirm_timeout = False
	formattedsettime = datetime.strptime(currentyear+currentmonth+set_start_time,'%y%m%d%H%M')
	

	#set time zone
	formattedsettime = formattedsettime.replace(tzinfo=ZoneInfo(time_zone))
	#compute set end time
	formattedendtime = formattedsettime +timedelta(minutes=set_length)

	#set time zone
	formattedendtime = formattedendtime.replace(tzinfo=ZoneInfo(time_zone))

	set_alerts_list = []
	end_alerts_list = []

	set_dict = {"artistname": artist, "stagename": stage, "settime": formattedsettime, "addedby": ctx.author, "alerts": set_alerts_list}
	end_dict = {"artistname": "STGE CLSD", "stagename": stage, "settime": formattedendtime, "addedby": ctx.author, "alerts": end_alerts_list}
	for x in setdata:
		if (x[0]["stagename"]==stage):
			#check if set at that time already exists
			for y in x:
				if (y["settime"]==formattedsettime):
					setcollision = True
			#stop if setcollision was detected
			if (setcollision == True):
				break
			components: list[ActionRow] = spread_to_rows(Button(style=ButtonStyle.GREEN,label="Yes, create the set!",custom_id="confirm"),Button(style=ButtonStyle.SECONDARY,label="No, cancel.",custom_id="cancel"))
			message = await ctx.send("Are you sure you want to create a new " + str(set_length) + " min long **" + artist + "** set at **" + stage + "**, starting at **" + (formattedsettime.astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + "**?", components=components, ephemeral=True)
			try:
				button_timeout = await bot.wait_for_component(components=components, timeout=5)

			except TimeoutError:
				#set confirm timeout to true
				confirm_timeout = True
				components[0].components[0].disabled = True
				await message.edit(components=components)
			else:
				x.append(set_dict)
				#add STGE CLSD if stage closes
				if (does_stage_close==True):
					x.append(end_dict)
				setadded = True
				break

	#if stage not already in list
	if (setadded == False and setcollision == False and confirm_timeout == False):
		newsetlist=[]
		newsetlist.append(set_dict)
		if (does_stage_close==True):
			newsetlist.append(end_dict)
		setdata.append(newsetlist)
		setadded = True

	if (setadded == True):
		#refresh artistlist
		await artistlistmaintain()
		#sort schedule after addition
		await schedulesorter()
		await button_timeout.ctx.send(ctx.author.mention + " created a new " + str(set_length) + " min long **" + artist + "** set at **" + stage + "**, starting at **" + (formattedsettime.astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + "**. :sparkles::sparkles:")
	#handle errors
	else:
		if (confirm_timeout == True):
			errorcompose = "Confirmation timed out.  Please try creating your set again."
		elif (setcollision == True):
			errorcompose = ":exclamation: Another set already exists at **" + stage + "** at **" + (formattedsettime.astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + "**"
		else:
			errorcompose = "Error creating new set."
		await ctx.send(errorcompose, ephemeral=True)

	#log
	cls_log.info(str(ctx.author) + " used /createset")

	#except:
	#	await ctx.send("Error running command.", ephemeral=True)

#createset stage autocomplete
@createset.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await stageautocomplete(ctx.input_text))
	

#createset artist autocomplete
@createset.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await artistautocomplete(ctx.input_text))
		

@slash_command(name="removeset", description="Remove a set you created from the schedule")
@slash_option(name="stage", description="Stage name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
@slash_option(name="artist", description="Artist name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
async def removeset(ctx: SlashContext, stage: str, artist: str):
	try:
		global setdata
		setremoved = False

		#empty lists for list comprehension
		setdatacopy=[]
		for x in setdata:
			stagecopy=[]
			for y in x:
				if (y["stagename"].lower()==stage.lower() and y["artistname"].lower()==artist.lower() and y["addedby"]==ctx.author):
					await ctx.send(":exclamation: " + ctx.author.mention + " removed " + y["artistname"] + "'s " + y["stagename"] + " set at " + (y["settime"].astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + " from the schedule.")
					setremoved = True
				else:
					stagecopy.append(y)
			setdatacopy.append(stagecopy)

		setdata=setdatacopy[:]

		if (setremoved == False):
			await ctx.send("Couldn't find any sets with the entered parameters that you created.", ephemeral=True)
		else:
			#refresh artistlist
			await artistlistmaintain()
			#sort schedule and garbage collect any empty stages
			await schedulesorter()

		#log
		cls_log.info(str(ctx.author) + " used /removeset")

	except:
		await ctx.send("Error running command.", ephemeral=True)
	

#removeset autocomplete
@removeset.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await stageautocomplete(ctx.input_text))

#removeset artist autocomplete
@removeset.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await artistautocomplete(ctx.input_text))

@slash_command(name="fullschedule", description="List the full schedule for a stage")
@slash_option(name="stage", description="Stage name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
async def fullschedule(ctx: SlashContext, stage: str):
	try:
		stagefound = False
		#step through schedule
		for x in setdata:
			if (stage.lower() in x[0]["stagename"].lower()):
				listcompose = "## **" + x[0]["stagename"] + " FULL SCHEDULE:**"
				stagefound = True
				for y in x:
					listcompose+="\n" + (y["settime"].astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + " - " + y["artistname"]
					#add star if set is starred
					listcompose+=await startier(y["alerts"])
				await ctx.send(listcompose, ephemeral=True)
				break

		#return error if stage isn't found
		if (stagefound == False):
			await ctx.send("Couldn't find any stages with '"+stage+"' in the stage name.", ephemeral=True)

		#log
		cls_log.info(str(ctx.author) + " used /fullschedule")

	except:
		await ctx.send("Error running command.", ephemeral=True)

#fullschedule autocomplete
@fullschedule.autocomplete("stage")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await stageautocomplete(ctx.input_text))

@slash_command(name="searchsets", description="Find and list all sets for the specified artist")
@slash_option(name="artist", description="Artist name", required=True, opt_type=OptionType.STRING, autocomplete=True, min_length=2)
async def searchsets(ctx: SlashContext, artist: str):
	try:
		artistfound = False
		#find artist
		for x in setdata:
			for y in x:
				if (artist.lower() in y["artistname"].lower()):
					listcompose = "## ALL " + artist + " SETS:"
					artistfound=True

		if (artistfound==True):
			#step through schedule
			for x in setdata:
				for y in x:
					if (artist.lower() in y["artistname"].lower()):
						listcompose += "\n- " + (y["settime"].astimezone(ZoneInfo(time_zone))).strftime("%a %b%d %H%ML").upper() + " - " + y["artistname"] + " - " + y["stagename"]
						#add star if set is starred
						listcompose+=await startier(y["alerts"])
			await ctx.send(listcompose, ephemeral=True)

		else:
			await ctx.send("Couldn't find any sets with '" + artist + "' in the artist name.", ephemeral=True)

		#log
		cls_log.info(str(ctx.author) + " used /searchsets")

	except:
		await ctx.send("Error running command.", ephemeral=True)

#searchsets artist autocomplete
@searchsets.autocomplete("artist")
async def autocomplete(ctx: AutocompleteContext):
	await ctx.send(await artistautocomplete(ctx.input_text))
	
bot.start(token)