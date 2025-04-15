import requests
from bs4 import BeautifulSoup, element

WORD_TYPES = ['Adjective', 'Noun', 'Verb', 'Adverb', 'Article', 'Interjection', 'Pronoun', 'Conjunction', 'Determiner']

def lookup_word(word, language):
    html = requests.get(f'https://en.wiktionary.org/api/rest_v1/page/html/{word}').text
    soup = BeautifulSoup(html, 'html.parser')

    # --- get sections ---

    section = soup.select_one(f'section:has(> h2:-soup-contains("{language}"))')

    if not section: return {}

    pronunciation = section.select_one('section:has(> h3:-soup-contains("Pronunciation"))')
    word_type_data = {
        t: section.select_one(f'section:has(> *:-soup-contains("{t}"))')
        for t in WORD_TYPES
    }

    # --- handle section titles, all must be handled ---

    section_titles = [x.text for x in section.select('h3', recursive=False)]
    for title in WORD_TYPES + ['Etymology', 'Etymology 1', 'Etymology 2', 'Pronunciation', 'References', 'Further reading', 'Anagrams', 'See also']:
        if title in section_titles:
            section_titles.remove(title)

    if section_titles:
        print('UNHANDLED SECTION TITLES:', section_titles)

    # --- parse IPA ---

    ipa = None
    if pronunciation:
        ipa = next(ipa.text for ipa in pronunciation.select('.IPA') if ipa.text[0]=='/')

    # --- parse img ---

    img = section.select_one('figure[typeof="mw:File/Thumb"] img')
    if img:
        img = 'https:' + img['src']

    # --- parse definitions ---

    definitions = {}

    for word_type, data in word_type_data.items():
        if not data: continue
        sub_defs = definitions[word_type] = []

        for li in data.select_one('ol').select('li'):
            # print('\n---\n')
            # print(li.text)

            for element in soup.find_all(class_="citation-whole"):
                element.decompose()

            dl = li.select_one('ul')
            if not dl:
                dl = li.select_one('dl')
            if not dl:
                definition = []
                for e in li.children:
                    if e.name not in ['ul', 'ol', 'dl', 'style']:
                        definition += e.text
                definition = ''.join(definition).strip()
                if definition:
                    sub_defs.append((definition, []))
            else:
                definition = ''
                for e in li.children:
                    if e.name == 'style': continue
                    # print(e.name, e, e.text)
                    if e.name == 'dl' or e.name == 'ul': break
                    definition += e.text
                definition = definition.strip()

                examples = []
                for ex in dl.children:
                    ex = ex.text.strip()
                    if not ex: continue
                    examples.append(ex)

                # print('(')
                # print(definition)
                # print()
                # print(examples)
                # print(')')

                if definition:
                    sub_defs.append((definition, examples))
    # --- ---

    return {
        'url': f'https://en.wiktionary.org/wiki/{word}#{language}',
        'ipa': ipa,
        'img': img,
        'definitions': definitions
    }