__version__ = "v0.9.12"

import sublime
import sublime_plugin

import os
import shutil

import re
import time
import json

from .src import Utils

PACKAGE_PATH    = sublime.packages_path()
SETTINGS_PATH   = PACKAGE_PATH + '\\' + __package__ + '\\settings\\JF.sublime-settings'

# Indica a pasta raiz para projetos em JF
def now():
    return time.strftime('%X' )

# Indica a pasta raiz para projetos em JF
def getJFrootPath(path):
    root_dir    = Settings().get('rootDir')
    repetir     = 1
    base_path   = None

    if path.find( root_dir ) == -1:
        return base_path

    while repetir:
        jf_assign       = path + '\\jf-signature'

        if os.path.exists( jf_assign ):
            repetir     = 0
            base_path     = path

        if path == root_dir:
            repetir     = 0

        path            = os.path.dirname( path )

    return base_path

# Indica se uma pasta contém determinado fragmento de texto
def pathContains(path, needle):
    return path.find( needle ) != -1


# Classe base para as demais
class BaseClass(sublime_plugin.TextCommand):
    JF_ROOT_PATH    = None
    PANEL_NAME      = 'JF Results'

    def output(self, text=''):
        panel = self.view.window().find_output_panel(self.PANEL_NAME)
        
        if not panel:
            panel   = self.view.window().create_output_panel(self.PANEL_NAME)
            #panel.set_scratch(True)  # avoids prompting to save
            panel.settings().set("word_wrap", "false")
            panel.run_command('select_all')
            panel.run_command('left_delete')

        text        = re.sub('^', '           ', str(text),flags = re.MULTILINE)
        intro       = now() + ' - ' + type(self).__name__
        intro       += ":\n" if len(text) else " - [EMPTY]\n"
        text        += "\n\n" if len(text) else ""

        panel.set_read_only(False)
        panel.run_command('append', {'characters': intro + text})
        panel.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": 'output.' + self.PANEL_NAME})
        panel.show(panel.size())

    def path(self):
        return os.path.dirname(self.view.file_name())

    def alert(self, text):
        sublime.message_dialog('%s' % (text))

    def checkJFProject(self):
        root_dir    = Settings().get('rootDir')
      
        if not pathContains( self.path(), root_dir ):
            sublime.error_message("Execute o script a partir da pasta de aplicações - " + root_dir)
            return False
        
        if not getJFrootPath( self.path() ):
            sublime.error_message( "Execute o script a partir de um projeto feito em JF." )
            return False

        return True

# Capturar definições em arquivo de configurações
class Settings:
    def __init__(self):
        return

    def all(self):
        if os.path.exists(SETTINGS_PATH):
            self.items = Utils.parseJson(SETTINGS_PATH)
        else:
            self.items = {}

        return self.items

    def get(self, key_path='', default=None):
        items   = self.all()

        if len(key_path) <= 0:
            return

        res     = items
        keys    = key_path.split('.')

        for key in keys:
            res = res.get(key)
            
            if res is None:
                return default
        
        return res


# Criar regra de negócio
class CreateJfRule(BaseClass):
    def run(self, edit):
        if not pathContains( self.path(), "App\\Services" ):
            return self.alert( "Operação só é permitida na pasta App\\Services." )

        self.view.window().show_input_panel(
            "Nome do arquivo:",
            "",
            self.definirParametros,
            None,
            None
        )

    def definirParametros(self, file_path):
        current_file_path   = self.view.file_name()
        current_directory   = os.path.dirname(current_file_path)
        local_path          = current_directory[current_directory.rfind('\\')+1:]
        self.rule_class     = file_path + '__Rule'

        if local_path != 'Rules':
            current_directory += '\\Rules'

        self.rule_path      = current_directory + '\\' + self.rule_class + '.php'

        try:
            if not os.path.exists(self.rule_path):
                self.capturarDescricao()
            else:
                options = ["Sim", "Não"]
                self.view.window().show_quick_panel(
                    options,
                    self.sobrescerver
                )
        except Exception as e:
            sublime.error_message("Erro ao criar a regra de negócio: :s" % (str(e)))

    def sobrescerver(self, index):
        if index == 0:
            self.capturarDescricao()

    def capturarDescricao(self):
        self.view.window().show_input_panel(
            "Descrição da regra:",
            "Usuário sem permissão para executar a operação.",
            self.criarArquivo,
            None,
            None
        )

    def criarArquivo(self, desc):
        from .templates.rule_class import get_template
        ns      = self.rule_path
        path    = os.path.dirname(self.rule_path)
        ns      = ns[ns.rfind('\\App\\Services\\') + 1:]
        ns      = ns[0:ns.rfind('\\')]
        content = (get_template() % (ns, desc, self.rule_class))

        if not os.path.exists(self.rule_path):
            os.mkdir(path)

        with open(self.rule_path, 'w') as f:
            f.write(content)
        self.view.window().open_file(self.rule_path)


# Documentar um projeto em JF
class Git(BaseClass):
    def run(self, edit, cmd=None):
        if not self.checkJFProject():
            return

        base_path   = getJFrootPath( self.path() );
        cmd         = 'cd ' + base_path + ' && ' + Settings().get('git.' + cmd)
        self.output( os.popen( cmd ).read() )


# Importa o pacote JF para o Portal PMF
class ImportJfPhar(BaseClass):
    def run(self, edit):
        if not self.checkJFProject():
            return

        base_path   = getJFrootPath( self.path() );
        index_path  = base_path + '\\index.php';
        jfc_path    = base_path + '\\jfc';
        jf_path     = os.path.dirname( base_path ) + '\\jf-pmf\\dist'
        new_jfname  = None
        old_jfnames = []
        
        cmd         = 'cd ' + os.path.dirname( jf_path ) + ' && php dist.php'
        self.output( os.popen( cmd ).read() )

        for filename in os.listdir(jf_path):
            if not new_jfname:
                new_jfname = filename[7:-5] if filename.find( 'jf-pmf-' ) != -1 else -1

            if not new_jfname:
                new_jfname = filename[4:-5] if filename.find( 'jfc-' ) != -1 else -1

            source  = jf_path + '\\' + filename
            target  = base_path + '\\' + filename
            shutil.copy( source, target )

        for filename in os.listdir(base_path):
            if filename.find( 'jf-pmf-' ) != -1:
                if filename[7:-5] == new_jfname:
                    continue
                
                if filename[7:-5] not in old_jfnames:
                    old_jfnames.append( filename[7:-5] )

                os.remove( base_path + '\\' + filename )
        
            if filename.find( 'jfc-' ) != -1:
                if filename[4:-5] == new_jfname:
                    continue
                
                if filename[4:-5] not in old_jfnames:
                    old_jfnames.append( filename[4:-5] )

                os.remove( base_path + '\\' + filename )
        
        with open( index_path ) as f:
            index_content   = re.sub( 'pmf-(\d+-\d+)', 'pmf-' + new_jfname, f.read() )
        
        with open( jfc_path ) as f:
            jfc_content     = re.sub( 'jfc-(\d+-\d+)', 'jfc-' + new_jfname, f.read() )
        
        with open( index_path, 'w' ) as f:
            f.write( index_content )
            f.close()
        
        with open( jfc_path, 'w' ) as f:
            f.write( jfc_content )
            f.close()
        
        self.output( 'Novo JF copiado para o Portal PMF' )
        return

'''
dirpath = os.path.join(os.path.dirname(__file__), 'lib')
if dirpath not in sys.path:
    sys.path.append(dirpath)'''



# Documentar um projeto em JF
class RunAutodoc(BaseClass):
    contexts = ["domain", "models", "pages", "routines"]

    def run(self, edit, context=None):
        if not self.checkJFProject():
            return

        self.view.window().show_quick_panel(
            self.contexts,
            self.capturarContexto,
            0,
            0,
            None,
            'Contexto'
        )

    def capturarContexto(self, index):
        if index == -1:
            return

        self.executarAutodoc(self.path(), index)
    
    def executarAutodoc(self, path, index):
        base_path   = getJFrootPath( path );
        cmd         = 'cd ' + base_path + ' && php cmd\\autodoc.php -r -c:%s' % (self.contexts[index])
        self.output( os.popen( cmd ).read() )


'''
class EventDump(sublime_plugin.EventListener):
    def on_new(self, view):
    def on_load(self, view):
    def on_activated(self, view):
    def on_pre_save(self, view):
    def on_post_save(self, view):
    def on_modified(self, view):
    def on_close(self, view):
    def on_clone(self, view):
'''
