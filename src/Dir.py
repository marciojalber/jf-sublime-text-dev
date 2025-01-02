import sublime
import os

from .Settings import Settings

# Classé para manipular arquivos e pastas
class Dir:

    # Indica se uma pasta contém determinado fragmento de texto
    @staticmethod
    def pathContains(path, needle):
        return path.find( needle ) != -1

    # Retorna a pasta raiz do projeto feito em JF
    @staticmethod
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

    # Checa se uma pasta ou arquivo pertence a um projeto feito em JF
    @staticmethod
    def checkJFProject(path):
        root_dir    = Settings().get('rootDir')
      
        if not Dir.pathContains( path, root_dir ):
            sublime.error_message("Execute o script a partir da pasta de aplicações - " + root_dir)
            return False
        
        if not Dir.getJFrootPath( path ):
            sublime.error_message( "Execute o script a partir de um projeto feito em JF." )
            return False

        return True
