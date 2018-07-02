#!/usr/bin/env python
import os
import logging
from telegram import constants, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from datetime import  datetime
from telegram.error import BadRequest
import time
import worldcup
import pytz

global UPD, ACCESS, TOKEN, PORT

WC = worldcup.WorldCup()

def get_match(bot, update, args):
    try:
        result = False
        match_str = ""
        in_line = False
        if (len(args) > 0):
            arguments = " ".join(list(a for a in args))
            
            if (arguments in WC.matches.days_of_match):
                match_list = WC.match_by_date(arguments)
            elif (arguments in worldcup.stage_name.values()):
                in_line = True
                match_list = WC.match_by_phase(arguments)
            else:
                match_list = WC.match_by_team(arguments)

            match_str = load_match_formated(match_list, result, change_line=in_line, curr_match=False)
        else:
            match_str = load_match_formated(WC.matches.matches, result, change_line=True, curr_match=False)

        if (len(match_str) > constants.MAX_MESSAGE_LENGTH) or ("#" in match_str):
            for txt in match_str.split("#"):
                if (txt != ""):
                    bot.send_message(chat_id=update.message.chat_id,
                                     text=txt)
        else:
            if (match_str != ""):
                bot.send_message(chat_id=update.message.chat_id,
                                 text=match_str)
            else:
                bot.send_message(chat_id=update.message.chat_id,
                                 text="Nenhuma partida prevista.")
    except Exception as e:
         print("Método: {}-Erro: {}".format("get_match",str(e)))

def get_classif_group(bot, update, args):
    try:
        grp = None
        if (len(args) > 0):
            grp = args[0]
        WC.group_classification(group=grp)
        
        classification = ""
        group_before = ""
        for wc in WC.classification:
            if (wc["group"] != group_before):
                classification += "\n`Grupo {} PT VT EM DE GP GC SG`\n".format(wc["group"])
                group_before = (wc["group"])
                rank = 1
            classification += "`{}.{}{}{}{}{}{}{}{}{}`\n".format(rank,
                                                                 wc["flag"],
                                                                 wc["code"].ljust(3),
                                                                 str(wc["statistic"]["points"]).rjust(3),
                                                                 str(wc["statistic"]["wins"]).rjust(3),
                                                                 str(wc["statistic"]["draws"]).rjust(3),
                                                                 str(wc["statistic"]["losses"]).rjust(3),
                                                                 str(wc["statistic"]["goals_for"]).rjust(3),
                                                                 str(wc["statistic"]["goals_against"]).rjust(3),
                                                                 str(wc["statistic"]["goals_differential"]).rjust(3))
            rank += 1

        bot.send_message(chat_id=update.message.chat_id,
                         text=classification,
                         parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        print("Método: {}-Erro: {}".format("get_classif_group",str(e)))

def load_current_match(bot, job):
    try:
        WC.get_current_matches()
        if (len(WC.current_matches) > 0):
            for match in WC.current_matches:
                if (match["status"] == "in progress"):
                    match_str = load_match_formated([match], result=False, change_line=False, curr_match=True)
                    bot.send_message(chat_id=job.context, text=match_str, parse_mode=ParseMode.MARKDOWN)
                    if (match["time_match"] == "half-time"):
                        job.interval = wc.MATCH_INTERVAL
                    else:
                        job.interval = wc.CURR_MATCH_MONITOR
        else:
            job.schedule_removal()
            WC.get_next_match()
            match = WC.next_match
            if (len(match) > 0):
                if (len(match) == 1):
                    match_str = "Próxima partida\n"
                else:
                    match_str = "Próximas partidas\n"
                match_str += load_match_formated(match, result=False, change_line=False, curr_match=False)
            else:
                match_str = "Nenhuma partida prevista."
            bot.send_message(chat_id=job.context, text=match_str)
        print("load_current_match: {}, next in {} seconds".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")), str(job.interval))
    except Exception as e:
        print("Método: {}-Erro: {}".format("load_current_match",str(e)))
        job.schedule_removal()

def current_match(bot, update, job_queue):
    try:
        job_queue.run_repeating(load_current_match, interval=wc.CURR_MATCH_MONITOR, first=0, context=update.message.chat_id)
    except Exception as e:
        print("Método: {}-Erro: {}".format("current_match",str(e)))

def update_matches(bot, update):
    try:
        bot.send_message(chat_id=update.message.chat_id, text="Atualizando partidas...")
        WC.load_all_matches()
        
        bot.send_message(chat_id=update.message.chat_id, text="Atualizando resultados...")
        WC.load_match_results()
        
        bot.send_message(chat_id=update.message.chat_id, text="Resultados atualizados com sucesso.")
    except Exception as e:
        print("Método: {}-Erro: {}".format("update_matches",str(e)))

def load_match_formated(matches_list, result=False, change_line=False, curr_match=False):
    try:
        match_str = ""
        for match in sorted(matches_list, key=lambda k: (datetime.strptime(k["date"],"%d/%m/%Y"), datetime.strptime(k["time"], "%H:%M"))):
            if (result == True) and (match["score1"] == None):
                continue

            match_str += "Fase: {}".format(match["phase"])

            if (match["phase"] == "Primeira Fase"):
                match_str += " - Grupo {}".format(match["home_team"]["group"])

            match_str += "\n{} - {} às {}\n".format(match["wday"],
                                                    match["date"],
                                                    match["time"])
            ## Date/Time of Match ##
            if (curr_match == True):
                if (match["status"] == "in progress"):
                    match_str += "Partida em andamento: {}\n"
                    if (match["time_match"] == "half-time"):
                        match_str = match_str.format("Intervalo")
                    elif ("end of first half" in match["time_match"]):
                        match_str = match_str.format("Fim 1T Pr.")
                    elif ("end of second half" in match["time_match"]):
                        match_str = match_str.format("Fim 2T Pr.")
                    elif (match["time_match"] == "penalties"):
                        match_str = match_str.format("Disp.Penalti")
                    else:
                        match_str = match_str.format(match["time_match"])

            ## Match's Team ##
            match_str += "{} {} {} X {} {} {}\n".format(match["home_team"]["flag"],
                                                        match["home_team"]["pt_name"],
                                                        match["home_goals"],
                                                        match["away_goals"],
                                                        match["away_team"]["flag"],
                                                        match["away_team"]["pt_name"])

            ## Penalties ##
            if (match["home_penalties"] != None) and ((match["home_penalties"] != 0) or (match["away_penalties"] != 0)):
                match_str += "Penalti: {}({}) X ({}){}\n".format(match["home_team"]["flag"],
                                                            match["home_penalties"],
                                                            match["away_penalties"],
                                                            match["away_team"]["flag"])
            ## Team's Events ##
            goals = list()
            for g in match["home_event"]:
                goals.append(g["player"] + " " + g["time"])

            if (len(goals) > 0):
                match_str += "{}({})\n".format(match["home_team"]["code"],
                                             ",".join(goals))

            goals = list()
            for g in match["away_event"]:
                goals.append(g["player"] + " " + g["time"])

            if (len(goals) > 0):
                match_str += "{}({})\n".format(match["away_team"]["code"],
                                             ",".join(goals))

            ## Locality ##
            match_str += "Estádio: %s\n" % (match["stadium"])
            match_str += "Cidade: %s\n" % (match["city"])

            if (change_line == True):
                match_str += "#"
            else:
                match_str += "\n"

        return match_str
    except Exception as e:
        print("Método: {}-Erro: {}".format("load_match_formated",str(e)))

def menu_list(bot, update):
    try:
        txt = "Opções disponíveis:\n"
        txt += "*/partida*: todas as partidas do campeonato. Utilize as 'keywords': \n"

        for phase in worldcup.stage_name.values():
            txt += "   {}\n".format(phase)

        txt += "...ou informe o nome de alguma seleção ou data da partida.\n\n"

        txt += "*/grupo*: classificação de cada grupo ou do grupo informado.\n\n"

        txt += "*/jogo*: partidas em andamento e, caso não tenha nenhuma, apresenta a(s) próxima(s) partida(s).\n\n"

        txt += "*/atualizar*: atualiza as partidas e respectivos resultados." 

        bot.send_message(chat_id=update.message.chat_id, text=txt, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        print("Método: {}-Erro: {}".format("update_matches",str(e)))
        
def load_all_dispatcher():
    try:
        dispatcher = UPD.dispatcher

        match_handler= CommandHandler('partida', get_match, pass_args=True)
        dispatcher.add_handler(match_handler)

        class_handler= CommandHandler(['classificação', 'classificacao', 'grupos', 'grupo'], get_classif_group, pass_args=True)
        dispatcher.add_handler(class_handler)

        currMatch_handler= CommandHandler('jogo', current_match, pass_job_queue=True)
        dispatcher.add_handler(currMatch_handler)

        update_handler= CommandHandler('atualizar', update_matches)
        dispatcher.add_handler(update_handler)

        menu_handler= CommandHandler('menu', menu_list)
        dispatcher.add_handler(menu_handler)
    except Exception as e:
        print("Método: {}-Erro: {}".format("load_all_dispatcher",str(e)))


if (__name__ == '__main__'):
    try:
        ACCESS = os.environ["TELEGRAM_SERVER"]
        TOKEN = os.environ['TELEGRAM_TOKEN']
        PORT = int(os.environ.get('PORT',os.environ['TELEGRAM_PORT']))
        UPD = Updater(TOKEN)

        load_all_dispatcher()

        if (ACCESS == "HEROKU"):
            HEROKU_URL = os.environ['HEROKU_URL']
            UPD.start_webhook(listen='0.0.0.0',
                              port=PORT,
                              url_path=TOKEN)
            UPD.bot.set_webhook(HEROKU_URL + TOKEN)
            UPD.idle()
        else:
            UPD.start_polling()

        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)

    except Exception as e:
        print("Método: {}-Erro: {}".format("main",str(e)))







