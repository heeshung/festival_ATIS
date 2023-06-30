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

walterbussettimes=["230100","230700","232200","240200","242200","242300","250200"]
meadowsettimes=["230100","230200","230300","230400","230530","230700","232110","232130","232250","232310","240010","240030","240130","240150","240300","242000","242100","242110","242200","242210","242350","250030","250130","250300"]
campsitesettimes=["231700","232000","240700","240730","241200","241600","241900","250600","251200"]
shalasettimes=["221900","230100","230600","231200","231600","231700","231730","231855","241600","241700","241730","241830"]
gorgesettimes=["232100","232200","232300","240000","240100","240200","240300","240400","240500","240700","240800","241930","242030","242200","242330","250100","250230","250400","250530","250700"]

walterbusartists=["Above & Beyond and Friends","U/S","Artist Meet & Greets","U/S","A&R Demo Drop w/Anjunabeats","Artist Meet & Greets","U/S"]

meadowartists=["Naz","Rodg","Nourey","Bexxie","Chris Giuliano","U/S","A&B Classics perf. by Soundwave Barbershop Quartet","Daybreaker","U/S","Jono Grant speaks to Andrew Bayer & Alison May","U/S","We're All In This Together Climate Q&A","A&B Classics perf. by Soundwave Barbershop Quartet",\
"Anjuna Pub Quiz w/ Anjuna HQ","U/S","Acro Yoga by Daybreaker","U/S","Flow State Meditation w/ Paavo & Elena Brower","U/S","Leave the Bones Film Preview & Haitian Rhythm & Dance Workshop","U/S","Genix 199X Album Chill Set","Qrion Ambient Set","U/S"]

campsiteartists=["Anjunafamily Room pres by The Instigators","U/S","Anjunafamily Room pres by The Instigators","Trance Classics Food Truck Aftershow SIMUL Anjunafamily Room pres by The Instigators","U/S","Anjunafamily Room pres by The Instigators","U/S",\
"Anjunafamily Room pres by The Instigators","U/S"]

shalaartists=["Anjunafamily Room pres by The Instigators","U/S","Eurodance Food Truck Aftershow w/ Fatum SIMUL Anjunafamily Room pres by The Instigators","U/S","Euphoria Effect Yoga w/ Katelyn Means","U/S","Yin Yang Yoga w/ Fitzjoy & Joan","U/S",\
"Euphoria Effect Yoga w/ Katelyn Means","U/S","Self Care Sunday w/ Dru West & Stephanie Bard","U/S"]

gorgeartists=["Nourey","Bexxie","Amy Wiles","aname","Fatum","Oliver Smith","Andrew Bayer","Mat Zo","Above & Beyond","Genix","U/S","Lakou Mizik & Joseph Ray pres Leave The Bones","OLAN","Qrion","Franky Wah","Marsh","James Grant & Jody Wisternoff","Eli & Fur","Ben Bohmer","U/S"]



currentwalterbusartist="UNDEFINED"
currentmeadowartist="UNDEFINED"
currentcampsiteartist="UNDEFINED"
currentshalaartist="UNDEFINED"
currentgorgeartist="UNDEFINED"

additionalrmks=""

currentatistext=""
currentatisindex=0

client=discord.Client()

@client.event
async def on_ready():
    await client.get_channel(746263960646451241).send("GORGE ATIS/TAF SERVICE ONLINE " + atisepoch.strftime("%d%H%M") + "Z")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
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

      #teststr=(message.content)[5:]
      #print (teststr)
      #currentdatetime=datetime.datetime.strptime(teststr, '%d%H%M')

      #get METAR
      c_atis=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&stationString=KMWH&hoursBeforeNow=2')
      atisoutput = (c_atis.text)
      begin=atisoutput.find("Z ")
      end=atisoutput.find("</raw_text>")

      #increment ATIS letter by hour
      #timediff=currentdatetime-atisepoch
      #hourdiff=timediff.total_seconds()/3600
      #currentatisindex = int((hourdiff) % 26)


      for idx, x in reversed(list(enumerate(walterbussettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(walterbussettimes[idx])):
          currentwalterbusartist=walterbusartists[idx]
          break
        else:
          currentwalterbusartist="U/S"

      for idx, x in reversed(list(enumerate(meadowsettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(meadowsettimes[idx])):
          currentmeadowartist=meadowartists[idx]
          break
        else:
          currentmeadowartist="U/S"

      for idx, x in reversed(list(enumerate(campsitesettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(campsitesettimes[idx])):
          currentcampsiteartist=campsiteartists[idx]
          break
        else:
          currentcampsiteartist="U/S"

      for idx, x in reversed(list(enumerate(shalasettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(shalasettimes[idx])):
          currentshalaartist=shalaartists[idx]
          break
        else:
          currentshalaartist="U/S"

      for idx, x in reversed(list(enumerate(gorgesettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(gorgesettimes[idx])):
          currentgorgeartist=gorgeartists[idx]
          break
        else:
          currentgorgeartist="U/S"

      atiscompare=(atisoutput[begin+2:end] + "\n\nREMARKS \nWALTERBUS: " + currentwalterbusartist + "\nMEADOW: " + currentmeadowartist + \
        "\nCAMPSITE: " + currentcampsiteartist + "\nSHALA: " + currentshalaartist + "\nAMPHI: " + currentgorgeartist)
      if (len(additionalrmks)>0):
        atiscompare+=additionalrmks

      #check if new ATIS matches old, if not advance ATIS letter
      if (len(currentatistext)==0):
        currentatistext=atiscompare

      elif (len(currentatistext)>0 and (atiscompare != currentatistext)):
        currentatisindex=(currentatisindex+1)%26
        currentatistext=atiscompare



      combined = "GORGE ATIS INFO " + atisletters[currentatisindex] + " " + currentdatetime.strftime("%d%H%M") + "Z " + atisoutput[begin+2:end] + "\n\nREMARKS \nWALTERBUS: " + currentwalterbusartist + "\nMEADOW: " + currentmeadowartist + \
        "\nCAMPSITE: " + currentcampsiteartist + "\nSHALA: " + currentshalaartist + "\nAMPHI: " + currentgorgeartist
      #add additional remarks
      if (len(additionalrmks)>0):
        combined+="\n\nADDITIONAL RMKS: " + additionalrmks

      await message.channel.send(combined)


    if message.content.lower().startswith('taf'):
      #get current time
      currentdatetime=datetime.datetime.utcnow()

      #teststr=(message.content)[4:]
      #print (teststr)
      #currentdatetime=datetime.datetime.strptime(teststr, '%d%H%M')

      c_taf=requests.get('https://aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&stationString=KMWH&hoursBeforeNow=4')
      tafoutput = (c_taf.text)
      begin=tafoutput.find("Z ")
      end=tafoutput.find("</raw_text>")


      for idx, x in reversed(list(enumerate(walterbussettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(walterbussettimes[idx])):
          if (idx == len(walterbussettimes)-1):
            nextwalterbusartist="U/S"
            nextwalterbussettime=walterbussettimes[idx]
            break
          else:
            nextwalterbusartist=walterbusartists[idx+1]
            nextwalterbussettime=walterbussettimes[idx+1]
            break
        elif (int(currentdatetime.strftime("%d%H%M")) < int(walterbussettimes[0])):
          nextwalterbusartist=walterbusartists[0]
          nextwalterbussettime=walterbussettimes[0]
          break
        else:
          continue

      for idx, x in reversed(list(enumerate(meadowsettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(meadowsettimes[idx])):
          if (idx == len(meadowsettimes)-1):
            nextmeadowartist="U/S"
            nextmeadowsettime=meadowsettimes[idx]
            break
          else:
           nextmeadowartist=meadowartists[idx+1]
           nextmeadowsettime=meadowsettimes[idx+1]
           break
        elif (int(currentdatetime.strftime("%d%H%M")) < int(meadowsettimes[0])):
          nextmeadowartist=meadowartists[0]
          nextmeadowsettime=meadowsettimes[0]
          break
        else:
          continue

      for idx, x in reversed(list(enumerate(campsitesettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(campsitesettimes[idx])):
          if (idx == len(campsitesettimes)-1):
            nextcampsiteartist="U/S"
            nextcampsitesettime=campsitesettimes[idx]
            break
          else:
           nextcampsiteartist=campsiteartists[idx+1]
           nextcampsitesettime=campsitesettimes[idx+1]
           break
        elif (int(currentdatetime.strftime("%d%H%M")) < int(campsitesettimes[0])):
          nextcampsiteartist=campsiteartists[0]
          nextcampsitesettime=campsitesettimes[0]
          break
        else:
          continue

      for idx, x in reversed(list(enumerate(shalasettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(shalasettimes[idx])):
          if (idx == len(shalasettimes)-1):
            nextshalaartist="U/S"
            nextshalasettime=shalasettimes[idx]
            break
          else:
           nextshalaartist=shalaartists[idx+1]
           nextshalasettime=shalasettimes[idx+1]
           break
        elif (int(currentdatetime.strftime("%d%H%M")) < int(shalasettimes[0])):
          nextshalaartist=shalaartists[0]
          nextshalasettime=shalasettimes[0]
          break
        else:
          continue

      for idx, x in reversed(list(enumerate(gorgesettimes))):
        if (int(currentdatetime.strftime("%d%H%M")) >= int(gorgesettimes[idx])):
          if (idx == len(gorgesettimes)-1):
            nextgorgeartist="U/S"
            nextgorgesettime=gorgesettimes[idx]
            break
          else:
           nextgorgeartist=gorgeartists[idx+1]
           nextgorgesettime=gorgesettimes[idx+1]
           break
        elif (int(currentdatetime.strftime("%d%H%M")) < int(gorgesettimes[0])):
          nextgorgeartist=gorgeartists[0]
          nextgorgesettime=gorgesettimes[0]
          break
        else:
          continue

      combined = "GORGE TAF " + currentdatetime.strftime("%d%H%M") + "Z " + tafoutput[begin+2:end] + "\n\nREMARKS"
      combined+="\nWALTERBUS: FM" + nextwalterbussettime + " " + nextwalterbusartist
      combined+="\nMEADOW: FM" + nextmeadowsettime + " " + nextmeadowartist
      combined+="\nCAMPSITE: FM" + nextcampsitesettime + " " + nextcampsiteartist
      combined+="\nSHALA: FM" + nextshalasettime + " " + nextshalaartist
      combined+="\nAMPHI: FM" + nextgorgesettime + " " + nextgorgeartist
      #add additional remarks
      if (len(additionalrmks)>1):
        combined+="\n\nADDITIONAL RMKS: " + additionalrmks

      await message.channel.send(combined)


client.run(token)
