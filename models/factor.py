from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FatorArtigo:
    codigo_artigo: str
    descricao_artigo: str
    fator: float
    data_inicio_vigencia: str          # ISO-8601: 'YYYY-MM-DD'
    data_fim_vigencia: Optional[str] = None
    observacao: Optional[str] = None
    status: str = "ativo"
    motivo_cancelamento: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    cancelled_at: Optional[str] = None

    def is_active(self) -> bool:
        return self.status == "ativo"

    def is_open_ended(self) -> bool:
        return self.data_fim_vigencia is None
