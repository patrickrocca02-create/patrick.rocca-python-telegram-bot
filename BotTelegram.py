import logging
import json

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,ConversationHandler)
from random import shuffle

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    #filename="log.txt",
                    #filemode='a'
                    )
logger = logging.getLogger(__name__)

#variabili contenenti i messaggi che il bot invierà nella chat
domande = ["Mangi almeno 5 porzioni di frutta e verdura al giorno?",
           "Mangi al massimo 3 volte carne alla settimana?",
           "Fai almeno 10 minuti di attività fisica al giorno?",
           "Fai almeno 150 minuti di attività' fisica alla settimana?"]

domande_approfondimento = ["Mi diresti per favore come mai non ci riesci?",
                           "Bene, ora immagina di avere un amico con lo stesso problema che ti chiede un consiglio. Che cosa gli consiglieresti?",
                           "Questa potrebbe essere una possibile soluzione, perché non la metti in pratica?",
                           "Cosa diresti a un amico in questa stessa situazione?"]

primo_messaggio = "Ciao {}, sono il tuo Bot per la dieta Mediterranea e cercherò di capire le tue difficoltà."
ultimo_messaggio = "Ho registrato tutto, grazie mille della tua disponibilità!"
messaggio_cancel = "Va bene {}, possiamo ricominciare la conversazione più tardi, ti basterà digitare il comando /start. A presto!"

# keyword per le domande intelligenti nell'approfondimento, l'indice rappresenta la priorità
keywords = [
    ['tempo', 'occupato', 'occupate', 'occupati', 'occupata', 'impegnata', 'impegnato', 'impegnati', 'impegnate',
     'impegni'],
    ['non'],
    ['causa', 'perché', 'dato che', 'per il fatto che', 'in quanto', 'poiché']
]
# domande approfondimento, l'indice della domanda corrisponde all'indice delle sue keywords, l'ultima è la predefinita
domande_dimmidipiu = [
    'Vedo che è una questione di tempo, potresti dirmi qualcosa in più?',
    'Come mai?',
    'Capisco queste motivazioni ma potresti andare più nel dettaglio per favore?',
    'Potresti dirmi qualcosa di più per favore?'
]

#parole minime da dire per una risposta ad un approfondimento, se non ripettate viene
#fatta una domanda dimmidipiu
parole_minime = 5
reply_keyboard = [['Si', 'No'], ['Non ora']]
#creazione degli stati per il conversation handler (range(3) restituisce 0, 1 e 2, come una tupla)
QUESTIONARIO, APPROFONDIMENTO, DIMMIDIPIU = range(3)

#funzione chiamata al comando /start
def start(update, context):
    #mescola la lista di domande in modo randomico
    shuffle(domande)
    #viene inviato il primo messaggio contenente i saluti e la prima domanda
    update.message.reply_text(
        primo_messaggio.format(update.message.from_user.first_name) + "\n\n"
        + domande[0],
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    )
    logger.info(update.message.from_user.first_name + ' si è connesso')
    #inzializza l'indice dell'utente utilizzato per contare le domande inviate (ogni utente ha il proprio indice)
    context.user_data["indice"] = 0

    #imposta il conversation handler sullo stato QUESTIONARIO
    return QUESTIONARIO

#fuzione che fa la domanda si/no, chiamata in stato QUESTIONARIO
def domanda(update, context):
    #incrementa l'indice dell'utente
    context.user_data["indice"] += 1
    #salviamo l'indice utente in una variabile i per comodità
    i = context.user_data["indice"]
    #testo ricevuto (in lower-case)
    testo = update.message.text.lower()
    #se le domande non sono finite
    if (i < len(domande)):
        # se la risposta è si risponde con la prossima domanda e rimane in stato QUESTIONARIO
        if (testo == 'si'):
            update.message.reply_text(
                domande[i],
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
            )
            # return QUESTIONARIO
        #se la risposta è no inizializza l'approfondimento e va in stato APPROFONDIMENTO
        else:
            inizializza_approfondimento(update, context, i - 1)
            return APPROFONDIMENTO
    #se le domande sono finite
    else:
        # se la risposta è no inizializza l'approfondimento e va in stato APPROFONDIMENTO
        if (testo == 'no'):
            inizializza_approfondimento(update, context, i - 1)
            return APPROFONDIMENTO
        #se la risposta è si risponde con il messaggio di ringraziamento e saluti e terminiamo la conversazione
        update.message.reply_text('Grazie per le tue risposte!', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


# metodo per l'inizializzaione dello stato APPROFONDIMENTO
def inizializza_approfondimento(update, context, i):
    # inzializza il dizionario dell'utente che conterrà le risposte approfondimento
    context.user_data["risposte"] = {}
    # salva con la key 'goal' la domanda da approfondire (ovvero quella a cui ha risposto no)
    context.user_data["risposte"]["goal"] = domande[i]

    # ciclo for che crea una lista per ogni risposta che verrà ricevuta
    # ogni risposta ha come key il suo indice, partendo da 1 (1,2,3,...)
    for j in range(len(domande_approfondimento)):
        context.user_data["risposte"][str(j + 1)] = []

    # l'indice per le domande si/no una volta in stato di approfondimento non è più necessario,
    # quindi viene azzerato per poterlo riutilizzare come indice per le domande di approfondimento
    context.user_data["indice"] = 0

    # viene fatta la prima domanda di approfondimento
    update.message.reply_text(
        domande_approfondimento[0],
        reply_markup=ReplyKeyboardMarkup([reply_keyboard[1]], resize_keyboard=True)
    )

#metodo chiamato in stato APPROFONDIMENTO
def approfondimento(update, context):
    #incrementa l'indice dell'utente
    context.user_data["indice"] += 1
    #salva la rispota dell'utente nella giusta lista
    context.user_data["risposte"][str(context.user_data["indice"])].append(update.message.text)

    #se il numero delle parole è >= al minimo
    if (len(update.message.text.split()) >= parole_minime):
        # se le domande approfondimento non sono finite viene fatta la prossima domanda
        if (context.user_data["indice"] < len(domande_approfondimento)):
            update.message.reply_text(
                domande_approfondimento[context.user_data["indice"]],
            )
            # return APPROFONDIMENTO
        # se le domande approfondimento sono finite vengono salvate e si conclude la conversazione
        else:
            salva(update, context)
            return ConversationHandler.END
    else:
        #risponde con una domanda dimmidipiu
        update.message.reply_text(
            scegli_domanda_dimmidipiu(update.message.text.lower()),
        )
        #passa allo stato DIMMIDIPIU
        return DIMMIDIPIU

def dimmidipiu(update, context):
    #riceve e inserisce la risposta dimmmidpiu nella giusta lista
    context.user_data["risposte"][str(context.user_data["indice"])].append(update.message.text)
    #viene fatta la prossima domanda di approfondimento
    update.message.reply_text(
        domande_approfondimento[context.user_data["indice"]],
    )
    #ritorna in stato APPROFONDIMENTO
    return APPROFONDIMENTO

def scegli_domanda_dimmidipiu(testo):
    # le parole chiave potrebbero essere all'inizio o alla fine della frase
    testo = " " + testo + " "
    domanda_scelta = domande_dimmidipiu[len(domande_dimmidipiu) - 1]

    trovato = False
    i = 0
    while not trovato and i < len(keywords):
        for key in keywords[i]:
            if ((" " + key + " ") in testo):
                domanda_scelta = domande_dimmidipiu[i]
                trovato = True
                break
        i += 1

    return domanda_scelta

#metodo chiamato a fine conversazione per il salvataggio dei dati in un json
def salva(update, context):
    #veine inviato il messaggio di ringraziamento e saluti
    update.message.reply_text(ultimo_messaggio, reply_markup=ReplyKeyboardRemove())
    #salva l'utente nella variabile user
    user = update.message.from_user
    logger.info(str(user.first_name) + " ha terminato la conversazione")
    #crea il nome del file con l'ID chat e il suo nome
    nomeFile = str(update.message.chat_id) + "_" + str(user.first_name) + ".json"
    try:
        #salva il dizionario 'risposte' in un file json con nome 'nomeFile'
        with open('risposte/' + nomeFile, 'w') as outfile:
            json.dump(context.user_data["risposte"], outfile)
    except:
        logger.warning("Il nome utente '" + str(user.first_name) + "' non può essere utilizzato come nome per un file")
        nomeFile = str(update.message.chat_id) + ".json"
        with open('risposte/' + nomeFile, 'w') as outfile:
            json.dump(context.user_data["risposte"], outfile)

#metodo chiamato nel caso in cui l'utente si stufi (pulsante 'non ora')
def cancel_message(update, context):
    user = update.message.from_user
    logger.info(str(user.first_name) + " ha annullato la conversazione")
    #resetta i dati utente
    context.user_data.clear()
    #saluta l'utente col messaggio di cancel
    update.message.reply_text(
        messaggio_cancel.format(update.message.from_user.first_name),
        reply_markup=ReplyKeyboardRemove()
    )
    #termina la conversazione
    return ConversationHandler.END

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater("952351024:AAGKMvjjwB3_KL61cAAj6bkNsUHXLxArLz4", use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            QUESTIONARIO: [MessageHandler(Filters.regex('^(Si|No|si|no)$'), domanda)],

            APPROFONDIMENTO: [MessageHandler(Filters.text, approfondimento)],

            DIMMIDIPIU: [MessageHandler(Filters.text, dimmidipiu)]
        },

        fallbacks=[MessageHandler(Filters.regex('^(Non ora|non ora)$'), cancel_message)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
