# Pacote utils para o FIDC Calculator

# Importações principais
from .calculador_correcao import CalculadorCorrecao
from .calculador_voltz import CalculadorVoltz
from .calculador_remuneracao_variavel import (
    CalculadorRemuneracaoVariavel,
    calcular_remuneracao_variavel_padrao,
    calcular_remuneracao_variavel_voltz,
    obter_faixas_aging_padrao,
    obter_faixas_aging_voltz
)

__all__ = [
    'CalculadorCorrecao',
    'CalculadorVoltz', 
    'CalculadorRemuneracaoVariavel',
    'calcular_remuneracao_variavel_padrao',
    'calcular_remuneracao_variavel_voltz',
    'obter_faixas_aging_padrao',
    'obter_faixas_aging_voltz'
]
