"""
Configuração centralizada de logging para produção.
Chama setup_logging() uma única vez na inicialização — seguro para reimportação.

Formato de linha:
    2026-04-27 09:00:00,000 | INFO | services.factor_service | FATOR_CRIADO | ...
"""
import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_configured = False


def setup_logging(log_dir: Path, level: int = logging.INFO) -> None:
    """
    Configura handlers de logging: arquivo rotativo (30 dias) + stderr.
    Idempotente — chamadas subsequentes são ignoradas.

    Args:
        log_dir: diretório onde o arquivo retanfactor.log será gravado.
        level:   nível mínimo de log (padrão INFO).
    """
    global _configured
    if _configured:
        return

    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- Handler de arquivo com rotação diária e retenção de 30 dias (AC1) ---
    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "retanfactor.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # --- Handler de stderr para desenvolvimento e journald ---
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    _configured = True

    logging.getLogger(__name__).info(
        "Logging configurado | log_dir=%s | level=%s",
        log_dir,
        logging.getLevelName(level),
    )
