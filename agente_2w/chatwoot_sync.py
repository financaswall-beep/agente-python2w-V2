"""Sincronizacao com Chatwoot — atualiza contato, labels e notas em tempo real."""

import logging
import httpx
from agente_2w.config import CHATWOOT_BASE_URL, CHATWOOT_API_TOKEN, CHATWOOT_ACCOUNT_ID

logger = logging.getLogger("chatwoot_sync")

# Labels usadas por etapa do fluxo
_LABEL_POR_ETAPA = {
    "identificacao": "identificacao",
    "busca": "buscando",
    "oferta": "oferta_enviada",
    "confirmacao_item": "confirmando_item",
    "entrega_pagamento": "dados_entrega",
    "fechamento": "em_fechamento",
}


def _headers() -> dict:
    return {"api_access_token": CHATWOOT_API_TOKEN}


def _base() -> str:
    return f"{CHATWOOT_BASE_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}"


def _habilitado() -> bool:
    return bool(CHATWOOT_BASE_URL and CHATWOOT_API_TOKEN and CHATWOOT_ACCOUNT_ID)


def atualizar_contato(contact_id: int, dados: dict) -> None:
    """Atualiza nome, email ou atributos customizados do contato no Chatwoot."""
    if not _habilitado() or not contact_id or not dados:
        return
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.patch(
                f"{_base()}/contacts/{contact_id}",
                json=dados,
                headers=_headers(),
            )
            resp.raise_for_status()
            logger.info("Contato Chatwoot %s atualizado: %s", contact_id, list(dados.keys()))
    except Exception as e:
        logger.warning("Falha ao atualizar contato Chatwoot: %s", e)


def adicionar_label(conv_id: int, label: str) -> None:
    """Adiciona label em uma conversa (label precisa existir no Chatwoot)."""
    if not _habilitado() or not conv_id or not label:
        return
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(
                f"{_base()}/conversations/{conv_id}/labels",
                json={"labels": [label]},
                headers=_headers(),
            )
            resp.raise_for_status()
            logger.info("Label '%s' adicionado na conversa %s", label, conv_id)
    except Exception as e:
        logger.warning("Falha ao adicionar label Chatwoot: %s", e)


def nota_privada(conv_id: int, texto: str) -> None:
    """Adiciona nota privada na conversa (visivel apenas para a equipe)."""
    if not _habilitado() or not conv_id or not texto:
        return
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(
                f"{_base()}/conversations/{conv_id}/messages",
                json={"content": texto, "message_type": "outgoing", "private": True},
                headers=_headers(),
            )
            resp.raise_for_status()
            logger.info("Nota privada adicionada na conversa %s", conv_id)
    except Exception as e:
        logger.warning("Falha ao adicionar nota privada Chatwoot: %s", e)


def resolver_conversa(conv_id: int) -> None:
    """Marca a conversa como resolvida no Chatwoot."""
    if not _habilitado() or not conv_id:
        return
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.patch(
                f"{_base()}/conversations/{conv_id}/toggle_status",
                json={"status": "resolved"},
                headers=_headers(),
            )
            resp.raise_for_status()
            logger.info("Conversa Chatwoot %s marcada como resolvida", conv_id)
    except Exception as e:
        logger.warning("Falha ao resolver conversa Chatwoot: %s", e)


def sincronizar_etapa(conv_id: int, etapa: str) -> None:
    """Adiciona label correspondente a etapa atual do fluxo."""
    label = _LABEL_POR_ETAPA.get(etapa)
    if label:
        adicionar_label(conv_id, label)


def sincronizar_nome_cliente(contact_id: int, nome: str) -> None:
    """Atualiza o nome do contato no Chatwoot quando coletado pelo agente."""
    if nome:
        atualizar_contato(contact_id, {"name": nome})


def sincronizar_pedido_criado(conv_id: int, numero_pedido: str, valor_total) -> None:
    """Adiciona label pedido_criado e nota privada com resumo do pedido."""
    adicionar_label(conv_id, "pedido_criado")
    nota_privada(
        conv_id,
        f"Pedido #{numero_pedido} criado automaticamente pelo agente. "
        f"Valor total: R$ {valor_total}",
    )
