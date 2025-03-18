import requests
from bs4 import BeautifulSoup

WORD_TYPES = ['Adjective', 'Noun', 'Verb', 'Adverb', 'Article']

def _parse_def_list(ol, raw_text):
    decode = (lambda x: x.text) if raw_text else (lambda x: x.decode_contents())

    result = {}
    for li in ol.find_all('li', recursive=False):
        sub_ol = li.select_one('ol')

        a_definition = decode(li.select_one('a'))
        description = li.select(':scope > *:not(ol):not(dl):not(style)')
        description = [decode(x) for x in description]

        if len(description) == 4 and description[-1] == ')' and description[-3] == '(':
            description = description[-2]
        else:
            description = ' '.join(description)

        if sub_ol:
            result[(a_definition, description)] = _parse_def_list(sub_ol, raw_text)
        else:
            examples = [decode(ex) for ex in li.select('.h-usage-example')]
            result[(a_definition, description)] = examples
    return result

# TODO: parse data better - maybe llm structuring
# TODO: cache results
def get_word_info(word, language, raw_text=False):
    html = requests.get(f'https://en.wiktionary.org/api/rest_v1/page/html/{word}').text
    soup = BeautifulSoup(html, 'html.parser')

    # --- get sections ---

    fn = soup.select_one(f'section:has(> h2:-soup-contains("{language}"))')

    pronunciation = fn.select_one('section:has(> h3:-soup-contains("Pronunciation"))')
    word_type_data = {
        t: fn.select_one(f'section:has(> h3:-soup-contains("{t}"))')
        for t in WORD_TYPES
    }

    # --- parse definitions ---

    section_titles = [x.text for x in fn.select('h3', recursive=False)]
    for title in WORD_TYPES + ['Etymology', 'Pronunciation', 'References', 'Further reading', 'Anagrams', 'See also']:
        if title in section_titles:
            section_titles.remove(title)

    if section_titles:
        print('UNHANDLED SECTION TITLES:', section_titles)

    definitions = {
        t: _parse_def_list(d.select_one('ol'), raw_text)
        for t, d in word_type_data.items()
        if d
    }

    # --- parse IPA ---

    ipa = None
    if pronunciation:
        ipa = next(ipa.text for ipa in pronunciation.select('.IPA') if ipa.text[0]=='/')

    # --- img ---

    img = fn.select_one('figure[typeof="mw:File/Thumb"] img')
    if img:
        img = 'https:' + img['src']

    # ---

    return {
        'ipa': ipa,
        'img': img,
        'definitions': definitions
    }
