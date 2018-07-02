#!/usr/bin/env python

class Team:

    def __init__(self):
        self.team = {}
        self.team["country"] = None
        self.team["pt_name"] = None
        self.team["code"] = None
        self.team["flag"] = None
        self.team["group"] = None

class Statistic:

    def __init__(self):
        self.stat = {}
        self.stat["wins"] = None
        self.stat["draws"] = None
        self.stat["losses"] = None
        self.stat["games_played"] = None
        self.stat["points"] = None
        self.stat["goals_for"] = None
        self.stat["goals_against"] = None
        self.stat["goals_differential"] = None

class Event:

    def __init__(self):
        self.event = {}
        self.event["event_type"] = None
        self.event["player"] = None
        self.event["time"] = None

class Match:

    def __init__(self):
        home_team = Team()
        away_team = Team()

        self.match = {}
        self.match["date"] = None
        self.match["time"] = None
        self.match["wday"] = None
        self.match["phase"] = None
        self.match["status"] = None
        self.match["stadium"] = None
        self.match["city"] = None
        self.match["home_team"] = home_team.team
        self.match["home_goals"] = None
        self.match["home_penalties"] = None
        self.match["home_event"] = []
        self.match["away_team"] = away_team.team
        self.match["away_goals"] = None
        self.match["away_penalties"] = None
        self.match["away_event"] = []
        self.match["time_match"] = None

    def add_home_event(self, event):
        self.match["home_event"].append(event.event)

    def add_away_event(self, event):
        self.match["away_event"].append(event.event)

class MatchList:

    def __init__(self):
        self.matches = []
        self.team_list = []
        self.days_of_match = []

    def add_match(self, match):
        if (match.match["date"] not in self.days_of_match):
            self.days_of_match.append(match.match["date"])

        if (len(list(filter(lambda t: match.match["home_team"]["country"] == t["country"], self.team_list))) == 0) and (match.match["home_team"]["code"] != "TBD"):
            self.team_list.append(match.match["home_team"])

        if (len(list(filter(lambda t: match.match["away_team"]["country"] == t["country"], self.team_list))) == 0) and (match.match["away_team"]["code"] != "TBD"):
            self.team_list.append(match.match["away_team"])

        self.matches.append(match.match)


