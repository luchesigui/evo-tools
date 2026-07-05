#!/usr/bin/env python3
"""
Script complementar para taguear contatos e leads no Kommo CRM a partir de um CSV.

Autor: EvoTools - Kommo Broadcast
Versão: 1.0.0
"""

import os
import sys
import csv
import logging
import argparse
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Garante que o diretório do script está no path para importar o broadcast.py
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from dataclasses import dataclass
from broadcast import KommoAPI, Contact, sanitize_phone, setup_logging

@dataclass
class TagContact:
    nome: str
    telefone: str
    telefone_sanitizado: str
    evo_id: Optional[str] = None
    kommo_contact: Optional[Dict[str, Any]] = None

def read_csv_contacts(file_path: str) -> List[TagContact]:
    """
    Lê contatos de um arquivo CSV.
    Detecta delimitadores (vírgula ou ponto e vírgula) e headers comuns de forma flexível.
    """
    logger = logging.getLogger(__name__)
    
    # Resolve caminhos relativos ou com ~ (home)
    expanded_path = os.path.expanduser(file_path)
    
    if not os.path.exists(expanded_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    
    logger.info(f"Lendo arquivo CSV: {expanded_path}")
    
    try:
        # Detecta delimitador (, ou ;) lendo a primeira linha
        with open(expanded_path, mode='r', encoding='utf-8-sig') as f:
            first_line = f.readline()
            if ';' in first_line:
                delimiter = ';'
            else:
                delimiter = ','
                
        logger.info(f"Delimitador detectado: '{delimiter}'")
        
        contacts = []
        with open(expanded_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)
            
        if not rows:
            logger.warning("O arquivo CSV está vazio.")
            return []
            
        # Tenta mapear colunas a partir do cabeçalho
        headers = {}
        first_row = rows[0]
        for idx, col in enumerate(first_row):
            if not col:
                continue
            col_lower = col.lower().strip()
            if 'nome' in col_lower or 'name' in col_lower:
                headers['nome'] = idx
            elif any(h in col_lower for h in ['telefone', 'phone', 'fone', 'celular', 'mobile']):
                headers['telefone'] = idx
            elif any(h in col_lower for h in ['idcliente', 'id_cliente', 'evo_id', 'evoid', 'id']):
                headers['evo_id'] = idx
                
        # Fallback caso não encontre cabeçalhos correspondentes
        if 'telefone' not in headers:
            headers = {'nome': 0, 'telefone': 1}
            start_row = 0
            logger.warning("Cabeçalhos não identificados. Assumindo coluna 0 como Nome e coluna 1 como Telefone.")
        else:
            start_row = 1
            logger.info(f"Colunas mapeadas: Nome na coluna {headers.get('nome')}, Telefone na coluna {headers.get('telefone')}, Evo ID na coluna {headers.get('evo_id')}")
            
        for row_idx, row in enumerate(rows[start_row:], start_row + 1):
            if not row or len(row) <= max(headers.values()):
                continue
                
            nome_val = row[headers.get('nome', 0)].strip() if headers.get('nome') is not None else f"Contato {row_idx}"
            telefone_raw = row[headers.get('telefone', 1)].strip()
            evo_id_val = row[headers.get('evo_id')].strip() if headers.get('evo_id') is not None else None
            
            if not telefone_raw or telefone_raw.lower() in ['none', 'null', '']:
                continue
            
            # Se houver múltiplos telefones (ex: separados por vírgula, barra ou ponto e vírgula), pega o primeiro
            for sep in [',', '/', ';', '|']:
                if sep in telefone_raw:
                    telefone_raw = telefone_raw.split(sep)[0].strip()
                    break
                
            telefone_sanitizado = sanitize_phone(telefone_raw)
            if len(telefone_sanitizado) < 10:
                logger.warning(f"Linha {row_idx}: Telefone inválido/curto ignorado: '{telefone_raw}'")
                continue
                
            contact = TagContact(
                nome=nome_val,
                telefone=telefone_raw,
                telefone_sanitizado=telefone_sanitizado,
                evo_id=evo_id_val
            )
            contacts.append(contact)
            
        logger.info(f"Total de {len(contacts)} contatos válidos carregados do CSV.")
        return contacts
        
    except Exception as e:
        logger.error(f"Erro ao ler arquivo CSV: {e}")
        raise


def search_contact_by_phone_with_leads(kommo_api: KommoAPI, phone: str) -> Optional[Dict[str, Any]]:
    """Busca um contato pelo telefone incluindo informações dos leads associados."""
    params = {'query': phone, 'limit': 1, 'with': 'leads'}
    response = kommo_api._make_request('GET', '/api/v4/contacts', params=params)
    
    # Se o contato não for encontrado, a API do Kommo retorna 204 (No Content) com body vazio.
    if response.status_code == 204 or not response.content:
        return None
        
    try:
        data = response.json()
        contacts = data.get('_embedded', {}).get('contacts', [])
        return contacts[0] if contacts else None
    except Exception as e:
        # Previne erros de parsing JSON se o conteúdo for inesperado
        logging.getLogger(__name__).warning(f"Erro ao processar JSON do telefone {phone}: {e}")
        return None


def get_pipelines(kommo_api: KommoAPI) -> List[Dict[str, Any]]:
    """Busca todos os pipelines de leads."""
    response = kommo_api._make_request('GET', '/api/v4/leads/pipelines')
    data = response.json()
    return data.get('_embedded', {}).get('pipelines', [])


def find_alunos_pipeline_and_stage(kommo_api: KommoAPI) -> Tuple[Optional[int], Optional[int]]:
    """Encontra o pipeline 'Alunos' e o estágio 'Agregadores'."""
    pipelines = get_pipelines(kommo_api)
    
    for pipeline in pipelines:
        if 'aluno' in pipeline.get('name', '').lower():
            pipeline_id = pipeline['id']
            
            # Busca o estágio 'Agregadores'
            if '_embedded' in pipeline and 'statuses' in pipeline['_embedded']:
                for status in pipeline['_embedded']['statuses']:
                    if 'agregador' in status.get('name', '').lower():
                        return pipeline_id, status['id']
            
            # Se não encontrou o estágio Agregadores, usa o primeiro
            if '_embedded' in pipeline and 'statuses' in pipeline['_embedded']:
                return pipeline_id, pipeline['_embedded']['statuses'][0]['id']
                
    # Fallback para o primeiro pipeline se nenhum contiver 'aluno'
    if pipelines:
        first_pipeline = pipelines[0]
        p_id = first_pipeline['id']
        s_id = None
        if '_embedded' in first_pipeline and 'statuses' in first_pipeline['_embedded'] and first_pipeline['_embedded']['statuses']:
            s_id = first_pipeline['_embedded']['statuses'][0]['id']
        return p_id, s_id
        
    return None, None


def get_or_create_evo_id_field(kommo_api: KommoAPI) -> Optional[int]:
    """Busca ou cria o campo customizado 'Evo ID' para contatos."""
    try:
        custom_fields = kommo_api.get_custom_fields()
        
        # Procura por campo existente
        for field in custom_fields:
            if field.get('code') == 'evo_id' or field.get('name') == 'Evo ID':
                return field['id']
        
        # Cria o campo caso não exista
        logging.getLogger(__name__).info("Campo 'Evo ID' não encontrado. Criando...")
        field_data = [{
            'name': 'Evo ID',
            'type': 'text'
        }]
        response = kommo_api._make_request('POST', '/api/v4/contacts/custom_fields', json=field_data)
        data = response.json()
        
        if '_embedded' in data and 'custom_fields' in data['_embedded']:
            return data['_embedded']['custom_fields'][0]['id']
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Erro ao buscar/criar campo 'Evo ID': {e}")
        
    return None


def create_contact(kommo_api: KommoAPI, name: str, phone: str, evo_id: Optional[str], evo_id_field_id: Optional[int]) -> Optional[int]:
    """Cria um contato no Kommo CRM e retorna seu ID."""
    custom_fields_values = []
    
    # Telefone
    if kommo_api.phone_field_id:
        custom_fields_values.append({
            'field_id': kommo_api.phone_field_id,
            'values': [{'value': phone}]
        })
        
    # Evo ID
    if evo_id and evo_id_field_id:
        custom_fields_values.append({
            'field_id': evo_id_field_id,
            'values': [{'value': evo_id}]
        })
        
    payload = [{
        'name': name,
        'custom_fields_values': custom_fields_values
    }]
    
    # Se não temos field_id do telefone, tenta adicionar no campo padrão
    if not kommo_api.phone_field_id:
        payload[0]['phone'] = phone
        
    try:
        response = kommo_api._make_request('POST', '/api/v4/contacts', json=payload)
        data = response.json()
        contacts = data.get('_embedded', {}).get('contacts', [])
        return contacts[0]['id'] if contacts else None
    except Exception as e:
        logging.getLogger(__name__).error(f"Erro ao criar contato '{name}': {e}")
        return None


def create_lead_for_contact(kommo_api: KommoAPI, contact_id: int, contact_name: str, pipeline_id: Optional[int], stage_id: Optional[int]) -> Optional[int]:
    """Cria um lead vinculado ao contato no Kommo CRM."""
    payload = [{
        'name': f"Lead - {contact_name}",
        '_embedded': {
            'contacts': [{'id': contact_id}]
        }
    }]
    
    if pipeline_id is not None:
        payload[0]['pipeline_id'] = pipeline_id
    if stage_id is not None:
        payload[0]['status_id'] = stage_id
        
    try:
        response = kommo_api._make_request('POST', '/api/v4/leads', json=payload)
        data = response.json()
        leads = data.get('_embedded', {}).get('leads', [])
        return leads[0]['id'] if leads else None
    except Exception as e:
        logging.getLogger(__name__).error(f"Erro ao criar lead para contato ID {contact_id}: {e}")
        return None


def add_tag_to_entities(kommo_api: KommoAPI, entity_type: str, entity_ids: List[int], tag_name: str):
    """Adiciona uma tag a múltiplos contatos ou leads no Kommo CRM em lotes."""
    logger = logging.getLogger(__name__)
    batch_size = 50
    total = len(entity_ids)
    
    logger.info(f"Adicionando tag '{tag_name}' para {total} {entity_type}...")
    
    for i in range(0, total, batch_size):
        batch = entity_ids[i:i+batch_size]
        payload = [
            {
                "id": entity_id,
                "tags_to_add": [{"name": tag_name}]
            }
            for entity_id in batch
        ]
        
        try:
            kommo_api._make_request('PATCH', f'/api/v4/{entity_type}', json=payload)
            logger.info(f"  ✓ Lote {i // batch_size + 1}: tagueado {len(batch)} {entity_type}.")
        except Exception as e:
            logger.error(f"  ✗ Erro ao taguear lote {i // batch_size + 1} de {entity_type}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Tagueamento em massa de contatos e leads no Kommo CRM')
    parser.add_argument('--csv', default='~/Desktop/CLIENTES.csv', help='Caminho do arquivo CSV (padrão: ~/Desktop/CLIENTES.csv)')
    parser.add_argument('--tag', default='Totalpass', help='Tag a ser aplicada (padrão: Totalpass)')
    parser.add_argument('--dry-run', action='store_true', help='Modo de simulação (nenhuma alteração será feita)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logs detalhados de depuração')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Carrega variáveis de ambiente
    load_dotenv(os.path.join(script_dir, '.env'))
    load_dotenv()
    
    # Valida variáveis obrigatórias do Kommo CRM
    required_vars = [
        'KOMMO_DOMAIN', 'KOMMO_CLIENT_ID', 'KOMMO_CLIENT_SECRET',
        'KOMMO_ACCESS_TOKEN'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}")
        logger.error("Configure o arquivo .env no diretório atual.")
        sys.exit(1)
        
    if not os.getenv('KOMMO_REFRESH_TOKEN'):
        logger.warning("KOMMO_REFRESH_TOKEN não está definido no .env. A renovação automática do token de acesso não funcionará.")
        
    if args.dry_run:
        logger.info("=== MODO DRY RUN ATIVADO - NENHUMA ALTERAÇÃO REAL SERÁ SALVA ===")
        
    try:
        # 1. Lê contatos do CSV
        contacts = read_csv_contacts(args.csv)
        if not contacts:
            logger.error("Nenhum contato encontrado no CSV para processar.")
            sys.exit(1)
            
        # 2. Inicializa o cliente API do Kommo
        kommo_api = KommoAPI(
            domain=os.getenv('KOMMO_DOMAIN', ''),
            client_id=os.getenv('KOMMO_CLIENT_ID', ''),
            client_secret=os.getenv('KOMMO_CLIENT_SECRET', ''),
            access_token=os.getenv('KOMMO_ACCESS_TOKEN', ''),
            refresh_token=os.getenv('KOMMO_REFRESH_TOKEN', ''),
            dry_run=args.dry_run
        )
        
        # O método initialize busca dados básicos de conta e ID do telefone
        kommo_api.initialize()
        
        # Busca ou cria o ID do campo customizado 'Evo ID' (apenas uma vez no início)
        evo_id_field_id = None
        if args.dry_run:
            evo_id_field_id = 77777
            logger.info(f"[DRY RUN] Usando Evo ID field ID {evo_id_field_id} simulado.")
        else:
            evo_id_field_id = get_or_create_evo_id_field(kommo_api)
            if evo_id_field_id:
                logger.info(f"Campo customizado 'Evo ID' (ID: {evo_id_field_id}) localizado com sucesso.")
            else:
                logger.warning("Não foi possível localizar/criar o campo 'Evo ID'. Novos contatos serão criados sem a associação do Evo ID.")
        
        # Busca pipeline e estágio para criação de novos leads (apenas uma vez no início)
        pipeline_id, stage_id = None, None
        if args.dry_run:
            pipeline_id, stage_id = 99999, 88888
            logger.info(f"[DRY RUN] Usando Pipeline ID {pipeline_id} e Estágio ID {stage_id} ('Agregadores') simulados.")
        else:
            try:
                pipeline_id, stage_id = find_alunos_pipeline_and_stage(kommo_api)
                if pipeline_id and stage_id:
                    logger.info(f"Pipeline 'Alunos' (ID: {pipeline_id}) e estágio 'Agregadores' (ID: {stage_id}) identificados para novos cadastros.")
                else:
                    logger.warning("Não foi possível identificar o pipeline 'Alunos' ou estágio 'Agregadores'. O lead será criado no estágio padrão.")
            except Exception as e:
                logger.error(f"Erro ao obter pipelines do Kommo: {e}")
        
        # 3. Busca contatos no Kommo para obter/gerar IDs
        logger.info("\nBuscando contatos correspondentes no Kommo CRM...")
        
        contact_ids_to_tag = []
        lead_ids_to_tag = []
        existing_contacts_count = 0
        created_contacts_count = 0
        created_leads_count = 0
        
        total_contacts = len(contacts)
        for idx, contact in enumerate(contacts, 1):
            logger.info(f"Processando {idx}/{total_contacts}: {contact.nome} ({contact.telefone_sanitizado})")
            
            try:
                kommo_contact = search_contact_by_phone_with_leads(kommo_api, contact.telefone_sanitizado)
                if kommo_contact:
                    # Caso 1: Contato já existe
                    c_id = kommo_contact.get('id')
                    if c_id:
                        contact_ids_to_tag.append(c_id)
                        existing_contacts_count += 1
                        
                    # Extrai os leads associados a este contato existente
                    leads_list = kommo_contact.get('_embedded', {}).get('leads', [])
                    if leads_list:
                        for lead in leads_list:
                            l_id = lead.get('id')
                            if l_id:
                                lead_ids_to_tag.append(l_id)
                        logger.debug(f"  ✓ Contato existente encontrado ID {c_id} com {len(leads_list)} lead(s).")
                    else:
                        # Contato existe, mas não possui nenhum lead vinculado. Cria um novo lead!
                        logger.info(f"  + Contato ID {c_id} existente não possui leads. Criando novo lead no estágio 'Agregadores'...")
                        if args.dry_run:
                            fake_lead_id = 888000 + idx
                            logger.info(f"  [DRY RUN] Criaria lead vinculado para contato existente ID {c_id} no estágio 'Agregadores' -> Novo ID: {fake_lead_id}")
                            lead_ids_to_tag.append(fake_lead_id)
                            created_leads_count += 1
                        else:
                            new_lead_id = create_lead_for_contact(
                                kommo_api, 
                                c_id, 
                                contact.nome, 
                                pipeline_id, 
                                stage_id
                            )
                            if new_lead_id:
                                lead_ids_to_tag.append(new_lead_id)
                                created_leads_count += 1
                                logger.info(f"  ✓ Lead criado com sucesso para o contato existente. ID: {new_lead_id}")
                            else:
                                logger.error(f"  ✗ Erro ao criar lead para o contato existente ID {c_id}")
                else:
                    # Caso 2: Contato não existe no CRM, cria contato + lead
                    logger.info(f"  + Não encontrado no CRM. Iniciando criação de novo cadastro...")
                    
                    if args.dry_run:
                        fake_contact_id = 999000 + idx
                        fake_lead_id = 888000 + idx
                        logger.info(f"  [DRY RUN] Criaria contato: '{contact.nome}' ({contact.telefone_sanitizado}) com Evo ID '{contact.evo_id}' -> Novo ID: {fake_contact_id}")
                        logger.info(f"  [DRY RUN] Criaria lead vinculado para contato ID {fake_contact_id} no estágio 'Agregadores' -> Novo ID: {fake_lead_id}")
                        
                        contact_ids_to_tag.append(fake_contact_id)
                        lead_ids_to_tag.append(fake_lead_id)
                        created_contacts_count += 1
                        created_leads_count += 1
                    else:
                        new_contact_id = create_contact(
                            kommo_api, 
                            contact.nome, 
                            contact.telefone_sanitizado, 
                            contact.evo_id, 
                            evo_id_field_id
                        )
                        if new_contact_id:
                            contact_ids_to_tag.append(new_contact_id)
                            created_contacts_count += 1
                            logger.info(f"  ✓ Contato criado com sucesso. ID: {new_contact_id}")
                            
                            # Cria o lead para este contato
                            new_lead_id = create_lead_for_contact(
                                kommo_api, 
                                new_contact_id, 
                                contact.nome, 
                                pipeline_id, 
                                stage_id
                            )
                            if new_lead_id:
                                lead_ids_to_tag.append(new_lead_id)
                                created_leads_count += 1
                                logger.info(f"  ✓ Lead criado com sucesso. ID: {new_lead_id}")
                            else:
                                logger.error(f"  ✗ Erro ao criar lead para o contato ID {new_contact_id}")
                        else:
                            logger.error(f"  ✗ Erro ao criar contato '{contact.nome}'")
            except Exception as e:
                logger.error(f"  ✗ Erro ao processar contato {contact.nome}: {e}")
                
        # Deduplica IDs antes do tagueamento
        contact_ids_to_tag = list(set(contact_ids_to_tag))
        lead_ids_to_tag = list(set(lead_ids_to_tag))
                
        # 4. Executa o tagueamento em lotes
        logger.info("\n" + "="*60)
        logger.info("RESUMO DO PROCESSAMENTO")
        logger.info("="*60)
        logger.info(f"Total de contatos no CSV:        {total_contacts}")
        logger.info(f"Contatos existentes encontrados:  {existing_contacts_count}")
        logger.info(f"Novos contatos criados:           {created_contacts_count}")
        logger.info(f"Novos leads criados:              {created_leads_count}")
        logger.info(f"Total de contatos para taguear:  {len(contact_ids_to_tag)}")
        logger.info(f"Total de leads para taguear:     {len(lead_ids_to_tag)}")
        
        if contact_ids_to_tag:
            logger.info("\nIniciando tagueamento dos contatos...")
            add_tag_to_entities(kommo_api, 'contacts', contact_ids_to_tag, args.tag)
            
        if lead_ids_to_tag:
            logger.info("\nIniciando tagueamento dos leads...")
            add_tag_to_entities(kommo_api, 'leads', lead_ids_to_tag, args.tag)
            
        logger.info("\n=== Operação finalizada com sucesso! ===")
        if args.dry_run:
            logger.info("⚠️  Modo DRY RUN - Nenhuma alteração real foi salva no CRM.")
        logger.info("="*60)
            
    except KeyboardInterrupt:
        logger.warning("\nExecução interrompida pelo usuário.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado durante a execução: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
