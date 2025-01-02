import time

# Classe para manipular datas e horas
class dt:
    
    # Retorna a hora do sistema
    @staticmethod
    def now():
        return time.strftime('%X' )
