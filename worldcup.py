#!/usr/bin/env python

import urllib.request
import json
from datetime import datetime, timedelta
import pytz
import pycountry
import gettext
import matches

date_frmt = "%d/%m/%Y"
time_frmt = "%H:%M"
pt_br = gettext.translation('iso3166', pycountry.LOCALES_DIR, languages=['pt_BR'])
tmz_brasil = pytz.timezone("America/Sao_Paulo")
week_days = {0: "Segunda",
             1: "Terça",
             2: "Quarta",
             3: "Quinta",
             4: "Sexta",
             5: "Sábado",
             6: "Domingo"}
stage_name = {"First stage": "Primeira Fase",
              "Round of 16": "Oitavas de Final",
              "Quarter-finals": "Quartas de Final",
              "Semi-finals": "Semifinal",
              "Play-off for third place": "Disputa Terceiro Lugar",
              "Final": "Final"}

class WorldCup:

    def __init__(self):
        try:
            self.classification = []

            self.load_all_matches()

            self.load_match_results()
        except Exception as e:
            print("Método: {}-Erro: {}".format("__init__",str(e)))

    def load_all_matches(self):
        try:
            self.matches = matches.MatchList()
            wc_list = load_json_wc(url_js="https://worldcup.sfg.io/matches", chave=None)

            for wc in wc_list:
                date = wc["datetime"].split("T")[0]
                time = wc["datetime"].split("T")[1][0:5]
                dt_local = match_time_local(date,
                                            time,
                                            tmz_brasil)

                m = matches.Match()
                m.match["date"] = dt_local.strftime(date_frmt)
                m.match["time"] = dt_local.strftime(time_frmt)
                m.match["wday"] = week_days[dt_local.weekday()]
                m.match["phase"] = stage_name[wc["stage_name"]]
                m.match["status"] = wc["status"]
                m.match["stadium"] = wc["location"]
                m.match["city"] = wc["venue"]

                if (wc["home_team"]["code"] == "TBD") or (wc["away_team"]["code"] == "TBD"):
                    m.match["home_team"]["country"] = "A Confirmar"
                    m.match["home_team"]["code"] = "TBD"
                    m.match["home_team"]["pt_name"] = "A Confirmar"
                    m.match["home_team"]["flag"] = "\U0001F3F3"
                    m.match["home_goals"] = ""
                    
                    m.match["away_team"]["country"] = "A Confirmar"
                    m.match["away_team"]["code"] = "TBD"
                    m.match["away_team"]["pt_name"] = "A Confirmar"
                    m.match["away_team"]["flag"] = "\U0001F3F3"
                    m.match["away_goals"] = ""
                    self.matches.add_match(m)
                    continue
                
                ## Home Team ##
                m.match["home_team"]["country"] = wc["home_team"]["country"]
                m.match["home_team"]["code"] = wc["home_team"]["code"]

                if (m.match["home_team"]["country"] == "England"):
                    m.match["home_team"]["pt_name"] = "Inglaterra"
                elif (m.match["home_team"]["country"] == "South Korea"):
                    m.match["home_team"]["pt_name"] = "Coreia do Sul"
                else:
                    pt_br.install()
                    m.match["home_team"]["pt_name"] = _(wc["home_team"]["country"])

                m.match["home_team"]["flag"] = emoji_code_flag(wc["home_team"]["country"],
                                                               wc["home_team"]["code"])

                m.match["home_goals"] = wc["home_team"]["goals"]

                ## Away Team ##
                m.match["away_team"]["country"] = wc["away_team"]["country"]
                m.match["away_team"]["code"] = wc["away_team"]["code"]

                if (m.match["away_team"]["country"] == "England"):
                    m.match["away_team"]["pt_name"] = "Inglaterra"
                elif (m.match["away_team"]["country"] == "South Korea"):
                    m.match["away_team"]["pt_name"] = "Coreia do Sul"
                else:
                    pt_br.install()
                    m.match["away_team"]["pt_name"] = _(wc["away_team"]["country"])

                m.match["away_team"]["flag"] = emoji_code_flag(wc["away_team"]["country"],
                                                               wc["away_team"]["code"])

                m.match["away_goals"] = wc["away_team"]["goals"]

                ## Events = Goals ##
                load_team_events(m, wc)

                self.matches.add_match(m)
        except Exception as e:
            print("Método: {}-Erro: {}".format("load_all_matches",str(e)))

    def load_match_results(self):
        try:
            rs_list = load_json_wc(url_js="https://worldcup.sfg.io/teams/results", chave=None)
            for rs in rs_list:
                for e_team in enumerate(self.matches.team_list):
                    if (e_team[1]["code"] == rs["fifa_code"]):
                        self.matches.team_list[e_team[0]]["group"] = rs["group_letter"]
                        s = matches.Statistic()
                        s.stat["wins"] = rs["wins"]
                        s.stat["draws"] = rs["draws"]
                        s.stat["losses"] = rs["losses"]
                        s.stat["games_played"] = rs["games_played"]
                        s.stat["points"] = rs["points"]
                        s.stat["goals_for"] = rs["goals_for"]
                        s.stat["goals_against"] = rs["goals_against"]
                        s.stat["goals_differential"] = rs["goal_differential"]
                        self.matches.team_list[e_team[0]]["statistic"] = s.stat
                    for e_match in enumerate(self.matches.matches):
                        if (e_match[1]["home_team"]["code"] == self.matches.team_list[e_team[0]]["code"]) and (e_match[1]["home_team"]["group"] == None):
                            self.matches.matches[e_match[0]]["home_team"]["group"] = self.matches.team_list[e_team[0]]["group"]
                        if (e_match[1]["away_team"]["code"] == self.matches.team_list[e_team[0]]["code"]) and (e_match[1]["away_team"]["group"] == None):
                            self.matches.matches[e_match[0]]["away_team"]["group"] = self.matches.team_list[e_team[0]]["group"]
        except Exception as e:
            print("Método: {}-Erro: {}".format("load_match_results",str(e)))

    def group_classification(self, group=None):
        try:
            classif_list = list(sorted(self.matches.team_list, key=lambda k:(k["group"],
                                                                             -k["statistic"]["points"],
                                                                             -k["statistic"]["goals_differential"])))
            if (group != None):
                self.classification = list(filter(lambda g: group == g["group"] , classif_list))
            else:
                self.classification = classif_list
        except Exception as e:
            print("Método: {}-Erro: {}".format("group_classification",str(e)))

    def match_by_team(self, team_name):
        try:
            match_list = list(filter(lambda t: team_name in (t["home_team"]["country"],
                                                             t["home_team"]["pt_name"],
                                                             t["away_team"]["country"],
                                                             t["away_team"]["pt_name"]), self.matches.matches))
            return match_list
        except Exception as e:
            print("Método: {}-Erro: {}".format("match_by_team",str(e)))

    def match_by_date(self, match_date):
        try:
            match_list = list(filter(lambda d: datetime.strptime(match_date, date_frmt) == datetime.strptime(d["date"], date_frmt), self.matches.matches))
            return match_list
        except Exception as e:
            print("Método: {}-Erro: {}".format("match_by_date",str(e)))

    def match_by_phase(self, match_phase):
        try:
            match_list = list(filter(lambda p: match_phase == p["phase"], self.matches.matches))
            return match_list
        except Exception as e:
            print("Método: {}-Erro: {}".format("match_by_phase",str(e)))

    def get_current_matches(self):
        try:
            self.current_matches = list()
            match_list = load_json_wc("http://worldcup.sfg.io/matches/current", chave=None)
            for mt in match_list:
                if (mt["status"] in ("in progress", "half-time")):
                    date = mt["datetime"].split("T")[0]
                    time = mt["datetime"].split("T")[1][0:5]
                    dt_local = match_time_local(date,
                                                time,
                                                tmz_brasil)

                    m = matches.Match()
                    m.match["date"] = dt_local.strftime(date_frmt)
                    m.match["time"] = dt_local.strftime(time_frmt)
                    m.match["wday"] = week_days[dt_local.weekday()]

                    l_phase = list(filter(lambda l: (mt["home_team"]["code"] == l["home_team"]["code"]) and (mt["away_team"]["code"] == l["away_team"]["code"]), self.matches.matches))
                    if (len(l_phase) > 0):
                        m.match["phase"] = l_phase[0]["phase"]
                    m.match["status"] = mt["status"]
                    m.match["stadium"] = mt["location"]
                    m.match["city"] = mt["venue"]
                    m.match["time_match"] = mt["time"]

                    ## Home Team ##
                    team = list(filter(lambda t: mt["home_team"]["country"] == t["country"], self.matches.team_list))
                    m.match["home_team"] = team[0]

                    m.match["home_goals"] = mt["home_team"]["goals"]

                    ## Away Team ##
                    team = list(filter(lambda t: mt["away_team"]["country"] == t["country"], self.matches.team_list))
                    m.match["away_team"] = team[0]

                    m.match["away_goals"] = mt["away_team"]["goals"]

                    ## Events = Goals ##
                    load_team_events(m, mt)

                    self.current_matches.append(m.match)
        except Exception as e:
            print("Método: {}-Erro: {}".format("get_current_matches",str(e)))

    def get_next_match(self):
        try:
            self.next_match = list()
            today_now = datetime.now()
            local_datetime = match_time_local(today_now.strftime("%Y-%m-%d"),
                                              today_now.strftime("%H:%M"),
                                              pytz.timezone("UTC"))
            local_time = local_datetime.strftime(time_frmt)
            count = 1
            
            while count <= 30:
                count += 1
                all_matches_today = list(filter(lambda lbd: today_now.date() == datetime.strptime(lbd["date"], date_frmt).date(), self.matches.matches))
                if (len(all_matches_today) > 0):
                    self.next_match = list(filter(lambda lbd: datetime.strptime(local_time, time_frmt) <= datetime.strptime(lbd["time"], time_frmt), all_matches_today))
                    if (len(self.next_match) > 0):
                        break
                today_now += timedelta(days=1)
                local_time = "00:00"
        except Exception as e:
            print("Método: {}-Erro: {}".format("get_next_match",str(e)))

def load_team_events(match, match_events):
    try:
        if ("home_team_events" in match_events):
            for ev in match_events["home_team_events"]:
                if (ev["type_of_event"] in ["goal", "goal-own", "goal-penalty"]):
                    e = matches.Event()
                    e.event["event_type"] = ev["type_of_event"]
                    e.event["time"] = ev["time"]
                    e.event["player"] = " ".join(list(p.capitalize() for p in ev["player"].split(" ")))
                    if (ev["type_of_event"] == "goal-own"):
                        e.event["player"] += "(GC)"
                    if (ev["type_of_event"] == "goal-penalty"):
                        e.event["player"] += "(P)"
                    match.add_home_event(e)

        if ("away_team_events" in match_events):
            for ev in match_events["away_team_events"]:
                if (ev["type_of_event"] in ["goal", "goal-own", "goal-penalty"]):
                    e = matches.Event()
                    e.event["event_type"] = ev["type_of_event"]
                    e.event["time"] = ev["time"]
                    e.event["player"] = " ".join(list(p.capitalize() for p in ev["player"].split(" ")))
                    if (ev["type_of_event"] == "goal-own"):
                        e.event["player"] += "(GC)"
                    if (ev["type_of_event"] == "goal-penalty"):
                        e.event["player"] += "(P)"
                    match.add_away_event(e)
    except Exception as e:
        print("Método: {}-Erro: {}".format("load_team_events",str(e)))

def load_json_wc(url_js, chave=None):
    try:
        with urllib.request.urlopen(url_js) as url:
            data = json.loads(url.read().decode())
        if (chave != None):
            result = data[chave]
        else:
            result = data
        return result
    except Exception as e:
        print("Método: {}-Erro: {}".format("load_json_wc",str(e)))

def match_time_local(date, time, timezone):
    try:
        fmt_datetime = "%Y-%m-%d %H:%M:%S"
        tmz_brasil = pytz.timezone("America/Sao_Paulo")
        if (timezone == tmz_brasil):
            timezone = pytz.timezone("UTC")
        match_time = timezone.localize(datetime.strptime(date + " " + time + ":00" ,fmt_datetime))
        result = match_time.astimezone(tmz_brasil)
        return result
    except Exception as e:
        print("Método: {}-Erro: {}".format("match_time_local",str(e)))
        
def emoji_code_flag(teamName, teamCode):
    try:
        OFFSET = 127462 - ord('A')
        if (teamName == "England"):
            code = "GB"
        else:
            try:
                code = pycountry.countries.get(name=teamName).alpha_2
            except KeyError:
                code = pycountry.countries.get(alpha_3=teamCode).alpha_2
        code = code.upper()
        if (teamName == "England"):
            return "\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f"
        else:
            return chr(ord(code[0]) + OFFSET) + chr(ord(code[1]) + OFFSET)
    except Exception as e:
        print("Método: {}-Erro: {}".format("emoji_code_flag",str(e)))
