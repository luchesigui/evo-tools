#!/usr/bin/env python3
"""
Utilitários para gerenciamento de contatos no Kommo CRM.

Reutiliza KommoAPI do broadcast.py para:
- Buscar/criar contatos
- Validar e adicionar o campo "Evo ID"
- Disparar sales bots
"""

import re
import logging
from typing import Optional, Tuple, Dict, Any

from broadcast import KommoAPI, KommoChatsAPI

logger = logging.getLogger(__name__)


def sanitize_phone(phone: str) -> str:
    """Remove tudo que não for dígito do telefone."""
    return re.sub(r"\D", "", str(phone))


def find_evo_id_field(kommo_api: KommoAPI) -> Optional[int]:
    """Busca o field_id do campo customizado 'Evo ID' nos contatos."""
    try:
        fields = kommo_api.get_custom_fields()
        for f in fields:
            name = (f.get("name") or "").lower()
            code = (f.get("code") or "").lower()
            if "evo" in name or "evo" in code:
                logger.info(f"Campo 'Evo ID' encontrado: id={f['id']} name='{f.get('name')}' code='{f.get('code')}'")
                return f["id"]
        logger.warning("Campo 'Evo ID' não encontrado nos custom fields do Kommo.")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar custom fields: {e}")
        return None


def _get_evo_id_from_contact(contact: Dict[str, Any], evo_field_id: int) -> Optional[str]:
    """Extrai o valor do Evo ID de um contato existente."""
    for cf in contact.get("custom_fields_values") or []:
        if cf.get("field_id") == evo_field_id:
            values = cf.get("values") or []
            if values:
                return str(values[0].get("value", ""))
    return None


def find_or_create_contact(
    kommo_api: KommoAPI,
    nome: str,
    telefone_raw: str,
    evo_id: str,
    evo_field_id: Optional[int],
) -> Tuple[Optional[str], str]:
    """
    Busca contato pelo telefone no Kommo.
    - Se encontrar: verifica Evo ID e atualiza se necessário.
    - Se não encontrar: cria novo contato com Evo ID.

    Retorna (kommo_contact_id, acao) onde acao é 'encontrado', 'criado' ou 'erro'.
    """
    phone = sanitize_phone(telefone_raw)
    if not phone or len(phone) < 10:
        logger.warning(f"Telefone inválido para {nome}: '{telefone_raw}'")
        return None, "sem_telefone"

    # 1. Busca contato existente
    try:
        contact = kommo_api.search_contact_by_phone(phone)
    except Exception as e:
        logger.error(f"Erro ao buscar contato {nome} ({phone}): {e}")
        return None, "erro"

    if contact:
        contact_id = str(contact["id"])
        logger.info(f"Contato encontrado: {nome} → kommo_id={contact_id}")

        # Verifica se Evo ID já está preenchido
        if evo_field_id:
            current_evo = _get_evo_id_from_contact(contact, evo_field_id)
            if not current_evo:
                _patch_evo_id(kommo_api, contact_id, evo_field_id, evo_id)
            else:
                logger.debug(f"Evo ID já preenchido ({current_evo}) para contato {contact_id}")

        return contact_id, "encontrado"

    # 2. Cria novo contato
    return _create_contact(kommo_api, nome, phone, evo_id, evo_field_id)


def _patch_evo_id(kommo_api: KommoAPI, contact_id: str, evo_field_id: int, evo_id: str) -> None:
    """Atualiza o campo Evo ID em um contato existente via PATCH."""
    try:
        kommo_api._make_request(
            "PATCH",
            f"/api/v4/contacts/{contact_id}",
            json={
                "custom_fields_values": [
                    {
                        "field_id": evo_field_id,
                        "values": [{"value": str(evo_id)}],
                    }
                ]
            },
        )
        logger.info(f"Evo ID atualizado no contato {contact_id}")
    except Exception as e:
        logger.warning(f"Falha ao atualizar Evo ID no contato {contact_id}: {e}")


def _create_contact(
    kommo_api: KommoAPI,
    nome: str,
    phone: str,
    evo_id: str,
    evo_field_id: Optional[int],
) -> Tuple[Optional[str], str]:
    """Cria um novo contato no Kommo via POST /api/v4/contacts."""
    parts = nome.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else ""

    custom_fields = []
    if kommo_api.phone_field_id:
        custom_fields.append({
            "field_id": kommo_api.phone_field_id,
            "values": [{"value": phone, "enum_code": "WORK"}],
        })
    if evo_field_id:
        custom_fields.append({
            "field_id": evo_field_id,
            "values": [{"value": str(evo_id)}],
        })

    body = [
        {
            "first_name": first_name,
            "last_name": last_name,
            "custom_fields_values": custom_fields,
        }
    ]

    try:
        resp = kommo_api._make_request("POST", "/api/v4/contacts", json=body)
        data = resp.json()
        contacts = data.get("_embedded", {}).get("contacts", [])
        if contacts:
            contact_id = str(contacts[0]["id"])
            logger.info(f"Contato criado: {nome} → kommo_id={contact_id}")
            return contact_id, "criado"
        logger.warning(f"Contato criado mas ID não retornado para {nome}: {data}")
        return None, "erro"
    except Exception as e:
        logger.error(f"Erro ao criar contato {nome} ({phone}): {e}")
        return None, "erro"


def trigger_sales_bot(
    chats_api: KommoChatsAPI,
    phone: str,
    nome: str,
    sales_bot_id: str,
    dry_run: bool = False,
) -> bool:
    """
    Dispara o sales bot para um contato via Kommo Chats API.

    Cria o chat (se não existe) para o contato. No Kommo, a automação
    (sales bot) é configurada no painel para responder automaticamente
    a novas conversas iniciadas pelo sistema.

    sales_bot_id é utilizado para rastreamento nos logs e no banco de dados.
    Certifique-se de que o bot correspondente esteja ativo no Kommo.

    Retorna True se o chat foi criado com sucesso, False caso contrário.
    """
    if dry_run:
        logger.info(
            f"[DRY RUN] Trigger sales bot {sales_bot_id} para {nome} ({phone})"
        )
        return True

    try:
        chat_result = chats_api.create_chat(phone, nome)
        logger.info(
            f"Chat criado/atualizado para {nome} ({phone}) "
            f"| bot={sales_bot_id} | result={chat_result}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Erro ao criar chat para {nome} ({phone}): {e}"
        )
        return False
