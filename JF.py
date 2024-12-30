import sublime
import sublime_plugin
import os

class CreateNewJfRuleCommand(sublime_plugin.TextCommand):
    def run(self, edit):
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
            sublime.error_message(f"Erro ao criar a regra de negócio: {str(e)}")

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
        ns              = self.rule_path
        ns              = ns[ns.rfind('\\App\\Services\\') + 1:]
        ns              = ns[0:ns.rfind('\\')]
        content = f"""<?php

namespace {ns};

use JF\\Exceptions\\ErrorException as Error;

/**
 * {desc}.
 */
class {self.rule_class} extends \\JF\\Domain\\Rule
{'{'}
    /**
     * Perfil da restrição.
     */
    protected $rulePerfil = ['gestor_sistema'];

    /**
     * Implementa a regra  de negócio.
     */
    public function execute()
    {'{'}
        foreach ( $this->rulePerfil as $perfil )
            if ( $this->usuario->temPerfil( $perfil ) )
                return;

        throw new Error( "Usuário sem perfil para executar a operação." );
    {'}'}
{'}'}
"""
        with open(self.rule_path, 'w') as f:
            f.write(content)
        self.view.window().open_file(self.rule_path)
        
        #sublime.message_dialog("Teste")
