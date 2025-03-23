import llm as L

# This will come from SRS
allowed_vocab = [
        # greetings
        'terve', 'hei',

        # nouns
        'talo',     # house
        'vesi',     # water
        'ystävä',   # friend
        'huomenta', # morning
        'velho',    # wizard
        'suomi',    # Finland
        'koira',    # dog
        'nimi',     # name

        # singular possessive nouns for 'nimi'
        'nimeni',   # first person "my name"
        'nimesi',   # second person "your name"
        'nimensä',  # third person "his name"

        # singular posessive nous for 'ystävä'
        'ystäväni',  # first person
        'ystäväsi',  # second person
        'ystävänsä', # third person

        # adjectives
        'vanha',       # old
        'hyvää',       # good
        'suomalainen', # Finnish
        'mukava',      # nice

        # pronouns, posesives, "to be" verbs
        'minä', 'minun', 'olen', 'olenko', # first person
        'sinä', 'sinun', 'olet', 'oletko', # second person
        'hän', 'hänen', 'on', 'onko',      # third person

        # names
        'matti', 'aleksi', 'sami'

        # useful words
        'kyllä', # yes
        'ei', # no
        'mitä', # "what/how" as in "what did you say?" or "how are you" -- about more abstract things
        'mikä', # "what" as in "what is this?" or "what is your name?" -- about specific things
    ]

TEACHER_NAME = 'Rossi' # localized to target language (regular 'e' for Finnish)
LEARNER_NAME = 'Lucas' # obtained from user profile

allowed_vocab += [TEACHER_NAME.lower(), LEARNER_NAME.lower()]

def make_chat_llm(allowed_vocab):
    # sys_prompt = (
    #     f'You are a Finnish teacher named {TEACHER_NAME}. I am a Finnish learner named {LEARNER_NAME}.' +
    #     '\nRespond to future messages with SINGLE, SHORT responses and nothing else. ' +
    #     'Use a lot of EMOJIS - at least one per message.' +
    #     '\n\nThis is the set of allowed vocab you can draw from for responses:\n{' + ', '.join(allowed_vocab) + '}' +
    #     '\n\nIMPORTANT: All word usage must be grammatically correct Finnish -- if the available words cannot express something, then DON\'T try expressing it.'
    # )

    sys_prompt = (
        f'You are a Finnish language teacher named {TEACHER_NAME}. I am a Finnish learner named {LEARNER_NAME}.'
        '\nUse lots of emojis. All of your responses must be grammatically correct Finnish.'
        f'\n\nIMPORTANT: Your responses must only use words in this allowed vocab: {allowed_vocab} and any emoji/punctuation.'
    )

    l = L.LLM(sys_prompt)

    l('Given the words allowed, what could be a goal of this conversation to help me learn more? (respond in english this time)')
    # l("You start. Keep this interactive by asking ME questions.")

    return l
