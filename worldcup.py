import urllib.request, json
from datetime import datetime
import pytz
import pycountry
import gettext

pt = gettext.translation('iso3166', pycountry.LOCALES_DIR, languages=['pt_BR'])
OFFSET = 127462 - ord('A')
countries = list()
matche_date = list()

def MatchTimeLocal(date, time, timezone):
    fmt_datetime = "%Y-%m-%d %H:%M:%S"
    tmz_brasil = pytz.timezone("America/Sao_Paulo")
    match_time = timezone.localize(datetime.strptime(date + " " + time + ":00" ,fmt_datetime))
    result = match_time.astimezone(tmz_brasil)
    return result

def LoadJsonWC(url_js):
    with urllib.request.urlopen(url_js) as url:
        data = json.loads(url.read().decode())
    result = data["rounds"]
    return result

def main():
    matchesWC = LoadJsonWC("https://raw.githubusercontent.com/openfootball/world-cup.json/master/2018/worldcup.json")
    for rd in matchesWC:
        for mt in rd["matches"]:
            if mt["timezone"] == "UTC+2":
                tmz_russia = pytz.timezone("Europe/Kaliningrad")
            if mt["timezone"] == "UTC+3":
                tmz_russia = pytz.timezone("Europe/Moscow")
            if mt["timezone"] == "UTC+4":
                tmz_russia = pytz.timezone("Europe/Samara")
            if mt["timezone"] == "UTC+5":
                tmz_russia = pytz.timezone("Asia/Yekaterinburg")
                
            matcheDateTimeLocal = MatchTimeLocal(mt["date"],
                                                 mt["time"], tmz_russia)
            
            mt["date_local"] = matcheDateTimeLocal.strftime("%d/%m/%Y")
            mt["time_local"] = matcheDateTimeLocal.strftime("%H:%M")
            mt["weekday"] = matcheDateTimeLocal.strftime("%A")
            
            mt["team1"]["flag"] = getFlagEmojiCode(mt["team1"]["name"],
                                                   mt["team1"]["code"])
            mt["team2"]["flag"] = getFlagEmojiCode(mt["team2"]["name"],
                                                   mt["team2"]["code"])

            if ("England" == mt["team1"]["name"]):
                mt["team1"]["name_local"] = "Inglaterra"

            if ("England" == mt["team2"]["name"]):
                mt["team2"]["name_local"] = "Inglaterra"

            if ("England" not in (mt["team1"]["name"],
                                  mt["team2"]["name"])):
                pt.install()
                mt["team1"]["name_local"] = _(mt["team1"]["name"])
                mt["team2"]["name_local"] = _(mt["team2"]["name"])
    getCountries(matchesWC, countries)
    getMatchDate(matchesWC, matche_date)
    return matchesWC

def getCountries(wc, countries_list):
    for match in wc:
        for mt in match["matches"]:
            if (mt["team1"]["name"] not in countries_list):
                countries_list.append(mt["team1"]["name"])
            if (mt["team2"]["name"] not in countries_list):
                countries_list.append(mt["team2"]["name"])
            if (mt["team1"]["name_local"] not in countries_list):
                countries_list.append(mt["team1"]["name_local"])
            if (mt["team2"]["name_local"] not in countries_list):
                countries_list.append(mt["team2"]["name_local"])

def getMatchDate(wc, matches_list):
    for match in wc:
        for mt in match["matches"]:
            if (mt["date_local"] not in matches_list):
                matches_list.append(mt["date_local"])

def getFlagEmojiCode(teamName, teamCode):
    if (teamName == "England"):
        code = "GB"
    else:
        try:
            code = pycountry.countries.get(name=teamName).alpha_2
        except KeyError:
            code = pycountry.countries.get(alpha_3=teamCode).alpha_2
        
    code = code.upper()
    return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)
