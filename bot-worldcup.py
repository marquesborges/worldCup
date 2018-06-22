#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import logging
from telegram import Chat, Contact, constants, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest
import worldcup
from datetime import datetime, date, timedelta
import emoji
import gettext
import time

fmt_datetime = "%d/%m/%Y"

access_type = os.environ["TELEGRAM_SERVER"]

monitorar_partida = (os.environ['TELEGRAM_MONITOR'] == '1')
    
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
            if (a in worldcup.countries):
                match_str = getByTeam(wc, a, apenasResultado)
            if (a in worldcup.matche_date):
                match_str = getByDate(wc, a, apenasResultado)
                
        if (match_str == ""):
            match_str = getMatches(wc, apenasResultado)

        if (len(match_str) > constants.MAX_MESSAGE_LENGTH) or ("#" in match_str):
            for txt in match_str.split("#"):
                bot.send_message(chat_id=update.message.chat_id, text=txt)
        else:
            bot.send_message(chat_id=update.message.chat_id, text=match_str)
    except BadRequest:
        Exception(BadRequest)

def getClassif(bot, update, args):
    try:
        group = ""
        if (len(args) > 0):
            group = args[0]
            
        classificacao = worldcup.getClassificacao(group)
        
        bot.send_message(chat_id=update.message.chat_id,
                         text=classificacao,
                         parse_mode=ParseMode.MARKDOWN)
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
            mt_str += formatMatchResult(mt, resultado, False)                
    return mt_str

def getPartidaAtual(bot, job):
    intervalo = False
    matche_list = worldcup.getCurrMatche()
    if (len(matche_list) > 0):
        for matche in matche_list:
            if ("status" in matche) and (matche["status"] == "in progress"):
                match_str = "Partida em andamento: {}\n"
                if (matche["time"] == "half-time"):
                    intervalo = True
                    match_str = match_str.format("Intervalo")
                else:
                    match_str = match_str.format(matche["time"])
                match_str += "{} {} {} x {} {} {}\n".format(matche["home_team"]["flag"],
                                                         matche["home_team"]["country"],
                                                         matche["home_team"]["goals"],
                                                         matche["away_team"]["goals"],
                                                         matche["away_team"]["flag"],
                                                         matche["away_team"]["country"])
                if (matche["home_team"]["events"] != ""):
                    match_str += "{}({})\n".format(matche["home_team"]["code"], matche["home_team"]["events"])
                if (matche["away_team"]["events"] != ""):
                    match_str += "{}({})\n".format(matche["away_team"]["code"], matche["away_team"]["events"])
                match_str += "Estádio: {}\n".format(matche["stadium"])
                match_str += "Cidade: {}\n".format(matche["city"])
                bot.send_message(chat_id=job.context, text=match_str)
                if (intervalo == True):
                    job.schedule_removal()
                    job.run_repeating(getPartidaAtual, interval=60, first=(60*15), context=update.message.chat_id)
    else:
        job.schedule_removal()
        mt = getNextMatch()
        if (len(mt) > 0):
            match_str = "Próxima partida\n"
            match_str += formatMatchResult(mt, resultado=False, quebra_str=False)
        else:
            match_str = "Nenhuma partida prevista."
        bot.send_message(chat_id=job.context, text=match_str)

def getJogo(bot, update, job_queue):
    job_queue.run_repeating(getPartidaAtual, interval=60, first=0, context=update.message.chat_id)

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
            mt_str += formatMatchResult(mt, resultado, False)   
    return mt_str

def getNextMatch():
    fmt_datetime = "%d/%m/%Y"
    fmt_time = "%H:%M"
    horario = datetime.strftime(datetime.today(), fmt_time)
    DateMatch = date.today()
    count = 0
    while count < 10:
        count += 1
        for match in wc:
            mt = list(filter(lambda lbd: DateMatch == datetime.strptime(lbd["date_local"], fmt_datetime).date(), match["matches"]))
            if (len(mt) > 0):
                for h in sorted(mt, key=lambda k: k["time_local"]):
                    if (datetime.strptime(horario, fmt_time) <= datetime.strptime(h["time_local"], fmt_time)):
                        return [h]

        DateMatch += timedelta(days=1)
        horario = "00:00"
        

def getMatches(wc, resultado=False):
    mt_str = ""
    for match in wc:
        mt_str += formatMatchResult(match["matches"], resultado, True)
    return mt_str

def formatMatchResult(matches_list, resultado=False, quebra_str=False):
    match_str = ""
    for match_dic in sorted(matches_list, key=lambda k: (k["date_local"], k["time_local"])):
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
                        if ("owngoal" in g) and (g["owngoal"] == True):
                            player += "(GC)"
                        if ("penalty" in g) and (g["penalty"] == True):
                            player += "(P)"
                        minute = str(g["minute"])
                        if "offset" in g: 
                            minute += "+" + str(g["offset"])                            
                        goals.append("%s %s'" % (player, minute))
                        
                    match_str += "%s(%s)\n" % (match_dic["team"+str(i)]["code"], ",".join(goals))
        else:
            match_str += "%s %s X %s %s\n" % (match_dic["team1"]["flag"],
                                              match_dic["team1"]["name_local"],
                                              match_dic["team2"]["flag"],
                                              match_dic["team2"]["name_local"])
            
        match_str += "Estádio: %s\n" % (match_dic["stadium"]["name"])
        match_str += "Cidade: %s\n" % (match_dic["city"])
        if (quebra_str == True):
            match_str += "#"
        else:
            match_str += "\n"
    return match_str

def loadMessage(bot, update):
    args = list()
    if(update.message.text in worldcup.countries):
        args.append(update.message.text)
    elif (update.message.text.lower() == "hoje"):
        args.append(datetime.strftime(datetime.today(), fmt_datetime))
    else:
        for user_msg in update.message.text.split(" "):
            user_msg = user_msg.capitalize()
            if (user_msg in worldcup.countries) | (user_msg in worldcup.matche_date):
                args.append(user_msg)
            elif (user_msg.lower() in ["resultado", "resultados"]):
                args.append("resultado")
    if (len(args) > 0):
        getPartida(bot, update, args)
    

wc = worldcup.main()
#getCountries(countries)
TOKEN=os.environ['TELEGRAM_TOKEN']
PORT = int(os.environ.get('PORT',os.environ['TELEGRAM_PORT']))

updater = Updater(TOKEN)
j_queue = updater.job_queue

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

dispatcher = updater.dispatcher

match_handler= CommandHandler('partida', getPartida, pass_args=True)

dispatcher.add_handler(match_handler)

class_handler= CommandHandler(['classificação', 'classificacao', 'grupos', 'grupo'], getClassif, pass_args=True)

dispatcher.add_handler(class_handler)

currMatch_handler= CommandHandler('jogo', getJogo, pass_job_queue=True)

dispatcher.add_handler(currMatch_handler)

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
    print("access_type=%s" % (access_type))
    print("TELEGRAM_PORT=%s" % (PORT))
    print("TELEGRAM_MONITOR=%s" % os.environ["TELEGRAM_MONITOR"])
    if (access_type == "HEROKU"):
        HEROKU_URL = os.environ['HEROKU_URL']
        print("HEROKU_URL=%s" % (HEROKU_URL))
        updater.start_webhook(listen='0.0.0.0',
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook(HEROKU_URL + TOKEN)
        updater.idle()
    else:
        updater.start_polling()



    


