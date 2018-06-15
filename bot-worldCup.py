#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Chat, Contact, constants
from telegram.error import BadRequest
import worldCup
from datetime import datetime
import emoji
import gettext

fmt_datetime = "%d/%m/%Y"
##def start(bot, update):
##    bot.send_message(chat_id=update.message.chat_id, text="Bem vindo ao " + bot.first_name + "!")
##
##def echo(bot, update):
##    user_name = update.message.chat['first_name'] + " " + update.message.chat['last_name']
##    user_msg = update.message.text
##    bot.send_message(chat_id=update.message.chat_id, text="Olá " + user_name + ", você enviou a mensagem: " + user_msg)
##
##def unknown(bot, update):
##    bot.send_message(chat_id=update.message.chat_id, text="Desculpe, não entendi o comando:" + update.message.text)
##
##def finish(bot, update):
##    bot.send_message(chat_id=update.message.chat_id, text="Atividades encerradas! Até mais...")
##    updater.stop()

def getPartida(bot, update, args):
    try:
        apenasResultado = False
        match_str = ""
        
        if (len(args) > 0):
            apenasResultado = ("resultado" in args)

        for a in args:
            if (a in worldCup.countries):
                match_str = getByTeam(wc, a, apenasResultado)
            if (a in worldCup.matche_date):
                match_str = getByDate(wc, a, apenasResultado)
                
        if (match_str == ""):
            match_str = getMatches(wc, apenasResultado)

        if (len(match_str) > constants.MAX_MESSAGE_LENGTH):
            msg = [match_str[i:i + 4096] for i in range(0, len(match_str), 4096)]
            for txt in msg:
                bot.send_message(chat_id=update.message.chat_id, text=txt)
        else:
            bot.send_message(chat_id=update.message.chat_id, text=match_str)
    except BadRequest:
        Exception(BadRequest)

def getByTeam(wc, teamName, resultado=False):
    mt_str = ""
    for match in wc:
        mt = list(filter(lambda lbd: teamName in (lbd["team1"]["name"],
                                                  lbd["team1"]["name_local"],
                                                  lbd["team2"]["name"],
                                                  lbd["team2"]["name_local"]),
                         match["matches"]))
        if (len(mt) > 0):
            mt_str += formatMatchResult(mt, resultado)                
    return mt_str


##def getByTeam(wc):
##    mt_str = ""
##    teamName = "Brazil"
##    for match in wc:
##        mt = list(filter(lambda lbd: teamName in (lbd["team1"]["name"], lbd["team2"]["name"]), match["matches"]))
##        if (len(mt) > 0):
##            print(formatMatchResult(mt))

def getByDate(wc, DateMatch, resultado=False):
    mt_str = ""
    for match in wc:
        mt = list(filter(lambda lbd: datetime.strptime(DateMatch, fmt_datetime) == datetime.strptime(lbd["date_local"], fmt_datetime), match["matches"]))
        if (len(mt) > 0):
            mt_str += formatMatchResult(mt, resultado)   
    return mt_str

def getMatches(wc, resultado=False):
    mt_str = ""
    for match in wc:
        mt_str += formatMatchResult(match["matches"], resultado)
    return mt_str

def formatMatchResult(matches_list, resultado=False):
    match_str = ""
    for match_dic in matches_list:
        if (resultado == True) and (match_dic["score1"] == None):
            continue
        match_str += "Partida %s - %s\n" % ((match_dic["num"]), (match_dic["group"]))
        match_str += "%s - %s às %s\n" % (match_dic["weekday"],
                                          match_dic["date_local"],
                                          match_dic["time_local"])

        if (match_dic["score1"] != None):
            match_str += "%s %s %s X %s %s %s\n" % (match_dic["team1"]["flag"],
                                                    match_dic["team1"]["name_local"],
                                                    match_dic["score1"],
                                                    match_dic["score2"],
                                                    match_dic["team2"]["flag"],
                                                    match_dic["team2"]["name_local"])
            for i in [1, 2]:
                goals = list()
                if (len(match_dic["goals"+str(i)]) > 0):
                    for g in match_dic["goals"+str(i)]:
                        player = g["name"]
                        if "offset" in g: 
                            minute = str(g["minute"]) + "+" + str(g["offset"])
                        else:
                            minute = str(g["minute"])
                        goals.append("%s %s'" % (player, minute))
                    match_str += "%s(%s)\n" % (match_dic["team"+str(i)]["code"], ",".join(goals))
        else:
            match_str += "%s %s X %s %s\n" % (match_dic["team1"]["flag"],
                                              match_dic["team1"]["name_local"],
                                              match_dic["team2"]["flag"],
                                              match_dic["team2"]["name_local"])
            
        match_str += "Estádio: %s\n" % (match_dic["stadium"]["name"])
        match_str += "Cidade: %s\n" % (match_dic["city"])
        match_str += "\n"
    return match_str

def loadMessage(bot, update):
    args = list()
    for user_msg in update.message.text.split(" "):
        user_msg = user_msg.capitalize()
        print(user_msg)
        if (user_msg in worldCup.countries) | (user_msg in worldCup.matche_date):
            args.append(user_msg)
        elif (user_msg.lower() in ["resultado", "resultados"]):
            args.append("resultado")
    if (len(args) > 0):
        getPartida(bot, update, args)
    

wc = worldCup.main()
#getCountries(countries)
TOKEN=os.environ['TELEGRAM_TOKEN']
PORT = int(os.environ.get('PORT',os.environ['TELEGRAM_PORT']))

updater = Updater(TOKEN)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

dispatcher = updater.dispatcher

match_handler= CommandHandler('partida', getPartida, pass_args=True)

dispatcher.add_handler(match_handler)

msg_handler = MessageHandler(Filters.text, loadMessage)

dispatcher.add_handler(msg_handler)
##
##unknown_handler = MessageHandler(Filters.text, unknown)
##
##dispatcher.add_handler(unknown_handler)
##
##finish_handler = CommandHandler('finish', finish)
##
##dispatcher.add_handler(finish_handler)

if (__name__ == '__main__'):
    updater.start_webhook(listen='0.0.0.0',
                          port=PORT,
                          url_path=TOKEN)
    updater.bot.set_webhook('https://bot-borges.herokuapp.com/' + TOKEN)
    updater.idle()
##    updater.start_polling()



    


