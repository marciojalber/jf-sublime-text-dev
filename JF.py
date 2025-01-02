__version__ = "v0.9.12"

import sublime
from sublime_plugin import TextCommand, WindowCommand, EventListener

import os
import shutil

import re
import json

from .src.dt import dt
from .src.File import File
from .src.Dir import Dir
from .src.Settings import Settings
from .src.Utils import *

# Classe base para as demais
class MySublime:
    PANEL_NAME      = 'JF Results'

    def output(self, text):
        panel = self.view.window().find_output_panel(MySublime.PANEL_NAME)
        
        if not panel:
            panel   = self.view.window().create_output_panel(MySublime.PANEL_NAME)
            #panel.set_scratch(True)  # avoids prompting to save
            panel.settings().set("word_wrap", "false")
            panel.run_command('select_all')
            panel.run_command('left_delete')

        text        = re.sub('^', '           ', str(text),flags = re.MULTILINE)
        intro       = dt.now() + ' - ' + type(self).__name__
        intro       += ":\n" if len(text) else " - [EMPTY]\n"
        text        += "\n\n" if len(text) else ""

        panel.set_read_only(False)
        panel.run_command('append', {'characters': intro + text})
        panel.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": '.' + MySublime.PANEL_NAME})
        panel.show(panel.size())

# Classe base para as demais
class BaseClass(TextCommand):
    JF_ROOT_PATH    = None

    def path(self):
        return os.path.dirname(self.view.file_name())

    def alert(self, text):
        sublime.message_dialog('%s' % (text))

# Classe base para criar regras de negócio
class CreateJfRuleTemplate:
    def __init__( self, window, filename ):
        self.window     = window
        self.filename   = filename
        return

    def run( self ):
        self.window.show_input_panel(
            "Nome do arquivo:",
            "",
            self.definirParametros,
            None,
            "Ex: UsuarioTemPermissao"
        )

    def definirParametros(self, file_path):
        current_file_path   = self.filename
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
                self.window.show_quick_panel(
                    options,
                    self.sobrescerver,
                    0,
                    0,
                    0,
                    "Deseja sobrescrever o arquivo existente?"
                )
        except Exception as e:
            sublime.error_message("Erro ao criar a regra de negócio: :s" % (str(e)))

    def sobrescerver(self, index):
        if index == 0:
            self.capturarDescricao()

    def capturarDescricao(self):
        self.window.show_input_panel(
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

        if not os.path.exists(path):
            os.mkdir(path)

        with open(self.rule_path, 'w') as f:
            f.write(content)
        self.window.open_file(self.rule_path)

# Criar regra de negócio
class CreateJfRule(BaseClass):
    def run(self, edit):
        filename   = self.view.file_name()
        window     = self.view.window()

        if not Dir.pathContains( self.path(), "App\\Services" ):
            return self.alert( "Operação só é permitida na pasta App\\Services." )

        CreateJfRuleTemplate( window, filename ).run()


# Ativar comandos do Git
class Git(BaseClass):
    def run(self, edit, cmd=None):
        if not Dir.checkJFProject(self.path()):
            return

        base_path   = Dir.getJFrootPath( self.path() );
        cmd         = 'cd ' + base_path + ' && ' + Settings().get('git.' + cmd)
        MySublime.output( self, os.popen( cmd ).read() )


# Importa o pacote JF para o Portal PMF
class ImportJfPhar(BaseClass):
    def run(self, edit):
        if not Dir.checkJFProject(self.path()):
            return

        base_path   = Dir.getJFrootPath( self.path() );
        index_path  = base_path + '\\index.php';
        jfc_path    = base_path + '\\jfc';
        jf_path     = os.path.dirname( base_path ) + '\\jf-pmf\\dist'
        new_jfname  = None
        old_jfnames = []
        
        cmd         = 'cd ' + os.path.dirname( jf_path ) + ' && php dist.php'
        MySublime.output( self, os.popen( cmd ).read() )

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
        
        MySublime.output( self, 'Novo JF copiado para o Portal PMF' )
        return

'''
dirpath = os.path.join(os.path.dirname(__file__), 'lib')
if dirpath not in sys.path:
    sys.path.append(dirpath)'''



# Documentar um projeto em JF
class RunAutodoc(BaseClass):
    contexts = ["domain", "models", "pages", "routines"]

    def run(self, edit, context=None):
        if not Dir.checkJFProject(self.path()):
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
        base_path   = Dir.getJFrootPath( path );
        cmd         = 'cd ' + base_path + ' && php cmd\\autodoc.php -r -c:%s' % (self.contexts[index])
        MySublime.output( self, os.popen( cmd ).read() )

# Exclui o arquivo da janela ativa
class ExcluirArquivo(TextCommand):
    def run(self, edit):
        options = ["Nada", "Excluir o arquivo", "Excluir a pasta"]
        self.view.window().show_quick_panel(
            options,
            self.excluir,
            0,
            0,
            0,
            "Você está prestes a excluir um documento. O que deseja fazer?"
        )

    def excluir(self, index):

        if not index:
            return

        if index == 1:
            os.remove( self.view.file_name() )

        if index == 2:
            path = os.path.dirname( self.view.file_name() )
            self.limparPasta( path )

    def limparPasta( self, path ):
        for (item_path, dirs, files) in os.walk(path):
            for item in dirs:
                self.limparPasta( path + '\\' + item )

            for item in files:
                os.remove( path + '\\' + item )

            break

        shutil.rmtree( path )


''' MENUS DE CONTEXTO '''
class DisableContextmenu:
    pass

class CreateJfRuleContextmenu(WindowCommand):
    def is_enabled(self, paths):
        allow_folder    = "\\App\\Services"
        allow_file      = "Service.php"
        error_files     = []

        for path in paths:
            if path.find( allow_folder ) == -1 or os.path.basename( path ) != allow_file:
                error_files.append( path )
        
        if len(error_files):
            print( "Não é permitido criar regra de negócio para os arquivos: ", error_files )
            return False
        
        return True

    def run(self, paths):
        self.window.show_input_panel(
            "Nome do arquivo:",
            "",
            self.definirParametros,
            None,
            None
        )

# Fazer merge request na pasta do projeto
class GitMergeRequestContextmenu(WindowCommand):
    def is_enabled(self, paths):
        print(paths)

        if len(paths) != 1:
            return False
        
        if not Dir.checkJFProject(paths[0]):
            return False

        return True


    def run(self, paths):
        base_path   = Dir.getJFrootPath( paths[0] );
        cmd         = 'cd ' + base_path + ' && ' + Settings().get('git.mergeRequest')
        os.popen( cmd ).read()
        sublime.status_message( "Merge request concluído." )


'''
class EventDump(EventListener):
    def on_new(self, view):
    def on_load(self, view):
    def on_activated(self, view):
    def on_pre_save(self, view):
    def on_post_save(self, view):
    def on_modified(self, view):
    def on_close(self, view):
    def on_clone(self, view):
'''
