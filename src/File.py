import json
import re

comment_re = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)

# Classe para manipulção de arquivos
class File:

    # Lê um arquivo JSON e onverte para dicionário
    @staticmethod
    def loadJson(filename):
        """ Parse a JSON file
            First remove comments and then use the json module package
            Comments look like :
                // ...
            or
                /*
                ...
                */
        """

        with open(filename, mode='r', encoding='utf-8') as f:
            content = ''.join(f.readlines())

            # Looking for comments
            match = comment_re.search(content)
            while match:
                # single line comment
                content = content[:match.start()] + content[match.end():]
                match = comment_re.search(content)

            # remove trailing commas
            content = re.sub(r',([ \t\r\n]+)}', r'\1}', content)
            content = re.sub(r',([ \t\r\n]+)\]', r'\1]', content)

            # Return json file
            return json.loads(content, encoding='utf-8')


    # Salva o conteúdo de um dicionário em arquivo JSON
    @staticmethod
    def saveJson(content, filename):
        with open(filename, mode='w', encoding='utf-8') as outfile:
            json.dump(content, outfile,
                      sort_keys=True, indent=2, separators=(',', ': '))
