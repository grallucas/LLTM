import llm as L

def _extract_words(sentence):
    return sentence.split() # TODO : split better (handle punctuation)

def _highlight_word(idx, words):
    highlighted = words.copy()
    highlighted[idx] = '{{' + highlighted[idx] + '}}'
    highlighted = ' '.join(highlighted)
    return highlighted

def grade_per_word(sentence, language):
    llm = L.LLM(f'You are a {language} language teacher.')

    cot = llm(
        'Is there a clear mistake in this sentence? Give (English) feedback for this sentence.\n\n' +
        # 'Give concise feedback/grading for this sentence:\n\n' +
        sentence
    )

    print(cot)
    print('\n-----')

    errs = llm(
        'Does your feedback indicate the presence of any improvements to be made?',
        response_format=['y/n']
    )['y/n']
    # errs = llm('Does your feedback indicate the presence of any improvements to be made?')

    # print(errs)
    # print('\n-----')

    words = _extract_words(sentence)

    # if errs == 'n':
    #     return words, [], None

    s = llm.save_state()

    incorrect = []
    for i in range(len(words)):
        sentence_w_highlight = _highlight_word(i, words)
        
        applies = llm(
            f'Does your feedback affect the highlighted word? Remember to use proper JSON formatting.\n\n{sentence_w_highlight}',
            response_format=['y/n']
        )['y/n']

        # applies = llm(
        #     f'Does your feedback affect the highlighted word?\n\n{sentence_w_highlight}'
        # )

        # print(applies, sentence_w_highlight)
        if applies == 'y':
            incorrect.append(i)

        llm.restore_state(s) # we shouldn't keep all words in history while grading them

    return words, incorrect, s

def get_word_feedback(idx, words, state):
    llm = L.LLM()
    llm.restore_state(state)

    sentence_w_highlight = _highlight_word(idx, words)

    expl = llm(
        f'Give a consice explanation for why the highlighted word is incorrect\n\n{sentence_w_highlight}',
        response_format='stream'
    )

    return expl
