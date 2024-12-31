def get_template():
    return """<?php

namespace %s;

use JF\\Exceptions\\ErrorException as Error;

/**
 * %s.
 */
class %s extends \\JF\\Domain\\Rule
{
    /**
     * Perfil da restrição.
     */
    protected $rulePerfil = ['gestor_sistema'];

    /**
     * Implementa a regra  de negócio.
     */
    public function execute()
    {
        foreach ( $this->rulePerfil as $perfil )
            if ( $this->usuario->temPerfil( $perfil ) )
                return;

        throw new Error( "Usuário sem perfil para executar a operação." );
    }
}
    """