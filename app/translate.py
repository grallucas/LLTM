import llm as L

def format_word_data(word_data):
    word_data_fmted = ''

    for word_type, defs in word_data['definitions'].items():
        word_data_fmted += word_type + '\n'
        for d in defs:
            word_data_fmted += f'\t{d[0]}\n'

    return word_data_fmted

def translate_in_ctx(context, word, word_lexicon_data):
    if word_lexicon_data:
        word_lexicon_data = format_word_data(word_lexicon_data)

    llm = L.LLM('You are a Finnish -> English translator.')

    translated_word = llm(
        f'{context}' +
        f'\n\nGiven the prior context, translate the Finnish word "{word}" into english' + 
        (f' from one of these definitions:\n{word_lexicon_data}' if word_lexicon_data else '.')
        ,
        response_format=['english_word']
    )['english_word']

    explanation = llm(
        # 'Give a brief, one-sentence explanation generalizable to other sentences (i.e., your explanation should be unconnected from the context).',
        'Give a concise explanation unconnected from the context.',
        response_format=['explanation']
    )['explanation']

    breakdown = llm(
        'Break the word into its root and inflections separated by dashes. It may just be one morpheme.',
        response_format=['parts_or_n/a']
    )['parts_or_n/a']

    return translated_word, explanation, breakdown
