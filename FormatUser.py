"""
Goal
1. Use Pandas to combine Dataminr User Data by combining the old interaction code with the new interaction code
2. Turn the interaction user log into a readable format
3. Outputs .csv to allow Director of Product to understand who are power users
"""
 #Libraries
import pandas as pd
import numpy as np
import datetime
import workdays

#Read in Files
d1 = pd.read_csv("ClientInteraction.csv") 
stats1 = pd.read_csv("OldCodetoNewCode.csv")
stats2 = pd.read_csv("CodeDescription.csv")
stats3 = pd.read_csv("CodeScreen.csv")

#Change from Dataminr user time to Python Date Object
d1["TIME"] = d1["TIME"].str.replace("EDT", "") #Safer would be to replace all three letter time zones with space
d1["TIME"] = d1["TIME"].str.replace("EST", "") #Safer would be to replace all three letter time zones with space

d2 = []
d2date = []
for time in d1["TIME"]:
    timeobject = datetime.datetime.strptime(time, "%a %b %d %H:%M:%S %Y")
    d2.append(timeobject)
    d2date.append(timeobject.date())

d1["DATETIME"] = d2
d1["JUSTDATE"] = d2date
del d1["TIME"]

#Change Old Dataminr Interaction Code to New Interaction Code
stats1.index = stats1["Old Code"]
del stats1["Old Code"]
d3 = []
dcode = d1["INTERACTION_CODE"]

for row in dcode:
    if str(row) in stats1.index:
        d3.append(stats1.loc[str(row)]["New Code"])
    else:
        d3.append(str(row))
d1["New Interaction Code"] = d3

#Insert Splice Code of last 4 digits to figure out description
d1int = []
for line in d1["New Interaction Code"].str[4:]:
    d1int.append(int(line))
d1["New Splice"] = d1int

#Insert in Description
#1) Check User Interaction Spliced is convertible to description
#2) If Spliced is convertible to description, add the description to the list
stats2.index = stats2["New Code"]
del stats2["New Code"]


d4 = []
dcode2 = d1["New Splice"]

for row in dcode2:
     if row in stats2.index:
         d4.append(stats2.loc[row]["New Descriptions"])
     else:
         d4.append("N/A")

d1["Description"] = d4
#Remove unnecessary columns
del d1["INTERACTION_CODE"]
del d1["New Splice"]
#Delete Duplicates
d1 = d1.drop_duplicates(["ACCOUNT_ID", "DATETIME", "New Interaction Code"])
#Sort rows by account and time for
d1 = d1.sort(["ACCOUNT_ID", "DATETIME"])
d1 = d1.reset_index()
del d1["index"]
#Print results of d1
#d1.to_csv("d1print.csv")


#Create User Profile
#Store unique users sorted in a list 
users = d1["ACCOUNT_ID"].drop_duplicates("ACCOUNT_ID").reset_index()
del users["index"]
users.sort("ACCOUNT_ID")


totalinteraction = []
firstdate = []
lastdate = []
companylastdate = []
totalcompanydate = []
company = []
#Active Days is defined as number of days user used the product at least once.
activedays = []
activitylevel = []
interactionperday = []
count = 0

numberofusers = len(users["ACCOUNT_ID"])

for i in users["ACCOUNT_ID"]:
    #print("User: " + str(i)  + " " + "Total Interaction: " + str(len(d1[d1["ACCOUNT_ID"] == i])))
    company.append(d1[d1["ACCOUNT_ID"] == i]["COMPANY_ID"].max())
    companylastdate.append(d1[d1["COMPANY_ID"] == company[count]]["DATETIME"].max())
    totalinteraction.append(len(d1[d1["ACCOUNT_ID"] == i]))
    firstdate.append(d1[d1["ACCOUNT_ID"] == i]["DATETIME"].min())
    lastdate.append(d1[d1["ACCOUNT_ID"] == i]["DATETIME"].max())
    totalcompanydate.append(workdays.networkdays(firstdate[count], companylastdate[count]))
    activedays.append(len(d1[d1["ACCOUNT_ID"]== i]["JUSTDATE"].drop_duplicates()))
    activitylevel.append(float(activedays[count])/totalcompanydate[count])
    interactionperday.append(totalinteraction[count]/activedays[count])
    count = count + 1

users["Company"] = company
users["Total Interaction"] = totalinteraction
users["First Date"] = firstdate
users["Last Date"] = lastdate
users["Last Company Date"] = companylastdate
users["Total Company Days"] = totalcompanydate
users["Active Days"] = activedays 
users["Interaction Per Day"] = interactionperday
users["Activity Level"] = activitylevel

users = users.sort(["Total Interaction"], ascending = False)
users["Rank Total Interaction"] = range(numberofusers)

users = users.sort(["Interaction Per Day"], ascending = False)
users["Rank Interaction Per Day"] = range(numberofusers)

users = users.sort(["Active Days"], ascending = False)
users["Rank Active Days"] = range(numberofusers)

SumofRank = []
RankofRank = []

users = users.sort()

count = 0
for i in users["ACCOUNT_ID"]:
    SumofRank.append(users["Rank Total Interaction"][count] + users["Rank Interaction Per Day"][count] + users["Rank Active Days"][count])
    count = count + 1 

#Sort users by aggregate sum of total interactino, interaction per day, active days
users["Sum of Ranks"] = SumofRank
users = users.sort(["Sum of Ranks"])
users["Rank of Ranks"] = range(numberofusers)


#Determine Power Users
#User used product within last 3 weeks
activeuser = (users["Last Date"] > users["Last Date"].max() - pd.DateOffset(months = 0, weeks = 3, days = 0))
#User used product at least 7 active days
activedayshi = users["Active Days"] > 7

#User used product at x% of days available to him/her
#activitylevelhi = users["Activity Level"] > 0.4

#User is top 20% user when averaging rank of total interaction ,interaction per day, active days
hipower = users["Rank of Ranks"] < round(numberofusers*(0.20))
users["Power User?"] = activeuser & activedayshi & hipower
users["Active User?"] = activeuser

#Print ALL User Profile and Power Users while resetting index for readability 
users = users.reset_index()
del users["index"]
users.to_csv("Users.csv")
PowerUsers = users[users["Power User?"]]
PowerUsers = PowerUsers.reset_index()
del PowerUsers["index"]
PowerUsers.to_csv("PowerUsers.csv")
