#!/usr/bin/env python3
"""
Script para sincronizar clientes do Evo (arquivo XLSX) com o Kommo CRM via API.

Autor: Sistema de Sincronização Evo-Kommo
Versão: 1.0.0
"""

import os
import re
import sys
import json
import time
import argparse
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


# Configurações globais
MAX_BATCH_SIZE = 50  # Kommo permite até 250, mas usamos um valor conservador
RATE_LIMIT_DELAY = 1.0  # Delay entre requests em segundos
MAX_RETRIES = 3


@dataclass
class Cliente:
    """Representa um cliente do Evo."""
    id_cliente: str
    nome: str
    data_nascimento: str
    telefone: str
    telefone_sanitizado: str
    status: str


@dataclass
class SyncStats:
    """Estatísticas da sincronização."""
    total: int = 0
    criados: int = 0
    atualizados: int = 0
    erros: int = 0
    ignorados: int = 0


class KommoAPI:
    """Cliente para interagir com a API do Kommo CRM."""
    
    def __init__(self, domain: str, client_id: str, client_secret: str, 
                 access_token: str, refresh_token: str, dry_run: bool = False):
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.dry_run = dry_run
        self.base_url = f"https://{domain}"
        self.session = requests.Session()
        
        # IDs importantes que serão descobertos durante a inicialização
        self.phone_field_id = None
        self.evo_id_field_id = None
        self.alunos_pipeline_id = None
        self.ativo_stage_id = None
        
        self.logger = logging.getLogger(__name__)
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Faz uma requisição HTTP com tratamento de erros e rate limiting."""
        url = f"{self.base_url}{endpoint}"
        
        if self.dry_run and method.upper() in ['POST', 'PATCH', 'PUT', 'DELETE']:
            self.logger.info(f"[DRY RUN] {method.upper()} {url}")
            if 'json' in kwargs:
                self.logger.info(f"[DRY RUN] Body: {json.dumps(kwargs['json'], indent=2)}")
            # Retorna uma resposta mock para dry run
            mock_response = requests.Response()
            mock_response.status_code = 200
            mock_response._content = json.dumps({"_embedded": {"contacts": []}}).encode()
            return mock_response
        
        headers = kwargs.get('headers', {})
        headers.update({
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        })
        kwargs['headers'] = headers
        
        for attempt in range(MAX_RETRIES):
            try:
                self.logger.debug(f"Fazendo request {method.upper()} para {url}")
                response = self.session.request(method, url, **kwargs)
                
                # Rate limiting
                if response.status_code == 429:
                    wait_time = RATE_LIMIT_DELAY * (2 ** attempt)
                    self.logger.warning(f"Rate limit atingido. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                # Token expirado
                if response.status_code == 401:
                    self.logger.info("Token expirado. Tentando refresh...")
                    if self.refresh_access_token():
                        headers['Authorization'] = f'Bearer {self.access_token}'
                        kwargs['headers'] = headers
                        continue
                    else:
                        raise Exception("Não foi possível renovar o token")
                
                response.raise_for_status()
                time.sleep(RATE_LIMIT_DELAY)  # Rate limiting preventivo
                return response
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Erro na tentativa {attempt + 1}: {e}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(RATE_LIMIT_DELAY * (attempt + 1))
        
        raise Exception(f"Falha após {MAX_RETRIES} tentativas")
    
    def refresh_access_token(self) -> bool:
        """Renova o access token usando o refresh token."""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            response = requests.post(
                f"{self.base_url}/oauth2/access_token",
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data['refresh_token']
            
            self.logger.info("Token renovado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao renovar token: {e}")
            return False
    
    def get_custom_fields(self) -> Dict[str, Any]:
        """Busca todos os campos customizados de contatos."""
        response = self._make_request('GET', '/api/v4/contacts/custom_fields')
        data = response.json()
        return data.get('_embedded', {}).get('custom_fields', [])
    
    def find_phone_field_id(self) -> Optional[int]:
        """Encontra o field_id do campo de telefone padrão."""
        custom_fields = self.get_custom_fields()
        
        # Procura por campos de telefone
        for field in custom_fields:
            if field.get('type') == 'multitext' and 'phone' in field.get('code', '').lower():
                return field['id']
        
        # Se não encontrou, tenta buscar campos padrão
        # No Kommo, telefone geralmente tem field_id = 0 ou campo específico
        return None
    
    def get_or_create_evo_id_field(self) -> int:
        """Busca ou cria o campo customizado 'Evo ID'."""
        custom_fields = self.get_custom_fields()
        
        # Procura campo existente
        for field in custom_fields:
            if field.get('code') == 'evo_id' or field.get('name') == 'Evo ID':
                self.logger.info(f"Campo 'Evo ID' encontrado com ID: {field['id']}")
                return field['id']
        
        # Cria campo se não existir
        self.logger.info("Campo 'Evo ID' não encontrado. Criando...")
        
        field_data = [{
            'name': 'Evo ID',
            'type': 'text',
            'code': 'evo_id'
        }]
        
        response = self._make_request('POST', '/api/v4/contacts/custom_fields', json=field_data)
        data = response.json()
        
        if '_embedded' in data and 'custom_fields' in data['_embedded']:
            field_id = data['_embedded']['custom_fields'][0]['id']
            self.logger.info(f"Campo 'Evo ID' criado com ID: {field_id}")
            return field_id
        
        raise Exception("Não foi possível criar o campo 'Evo ID'")
    
    def get_pipelines(self) -> List[Dict[str, Any]]:
        """Busca todos os pipelines de leads."""
        response = self._make_request('GET', '/api/v4/leads/pipelines')
        data = response.json()
        return data.get('_embedded', {}).get('pipelines', [])
    
    def find_alunos_pipeline_and_stage(self) -> Tuple[Optional[int], Optional[int]]:
        """Encontra o pipeline 'Alunos' e o estágio 'ATIVO'."""
        pipelines = self.get_pipelines()
        
        for pipeline in pipelines:
            if 'aluno' in pipeline.get('name', '').lower():
                pipeline_id = pipeline['id']
                
                # Busca o estágio 'ATIVO'
                if '_embedded' in pipeline and 'statuses' in pipeline['_embedded']:
                    for status in pipeline['_embedded']['statuses']:
                        if 'ativo' in status.get('name', '').lower():
                            return pipeline_id, status['id']
                
                # Se não encontrou o estágio ATIVO, usa o primeiro
                if '_embedded' in pipeline and 'statuses' in pipeline['_embedded']:
                    return pipeline_id, pipeline['_embedded']['statuses'][0]['id']
        
        return None, None
    
    def search_contact_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Busca um contato pelo telefone."""
        params = {'query': phone, 'limit': 1}
        response = self._make_request('GET', '/api/v4/contacts', params=params)
        data = response.json()
        
        contacts = data.get('_embedded', {}).get('contacts', [])
        return contacts[0] if contacts else None
    
    def create_contacts(self, contacts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cria múltiplos contatos."""
        response = self._make_request('POST', '/api/v4/contacts', json=contacts_data)
        data = response.json()
        return data.get('_embedded', {}).get('contacts', [])
    
    def update_contacts(self, contacts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Atualiza múltiplos contatos."""
        response = self._make_request('PATCH', '/api/v4/contacts', json=contacts_data)
        data = response.json()
        return data.get('_embedded', {}).get('contacts', [])
    
    def create_lead_for_contact(self, contact_id: int, contact_name: str) -> Optional[Dict[str, Any]]:
        """Cria um lead vinculado a um contato no pipeline 'Alunos'."""
        if not self.alunos_pipeline_id or not self.ativo_stage_id:
            self.logger.warning("Pipeline 'Alunos' ou estágio 'ATIVO' não encontrados")
            return None
        
        lead_data = [{
            'name': f"Lead - {contact_name}",
            'status_id': self.ativo_stage_id,
            'pipeline_id': self.alunos_pipeline_id,
            '_embedded': {
                'contacts': [{'id': contact_id}]
            }
        }]
        
        try:
            response = self._make_request('POST', '/api/v4/leads', json=lead_data)
            data = response.json()
            return data.get('_embedded', {}).get('leads', [{}])[0]
        except Exception as e:
            self.logger.error(f"Erro ao criar lead para contato {contact_id}: {e}")
            return None
    
    def initialize(self):
        """Inicializa IDs necessários para a sincronização."""
        self.logger.info("Inicializando API do Kommo...")
        
        # Busca field_id do telefone
        self.phone_field_id = self.find_phone_field_id()
        if self.phone_field_id:
            self.logger.info(f"Campo de telefone encontrado com ID: {self.phone_field_id}")
        else:
            self.logger.warning("Campo de telefone não encontrado - usando dados padrão")
        
        # Busca/cria campo Evo ID
        self.evo_id_field_id = self.get_or_create_evo_id_field()
        
        # Busca pipeline e estágio
        self.alunos_pipeline_id, self.ativo_stage_id = self.find_alunos_pipeline_and_stage()
        if self.alunos_pipeline_id and self.ativo_stage_id:
            self.logger.info(f"Pipeline 'Alunos' (ID: {self.alunos_pipeline_id}) e estágio 'ATIVO' (ID: {self.ativo_stage_id}) encontrados")
        else:
            self.logger.warning("Pipeline 'Alunos' ou estágio 'ATIVO' não encontrados")


def sanitize_phone(phone: str) -> str:
    """Remove tudo que não for dígito do telefone."""
    return re.sub(r'\D', '', str(phone))


def fetch_members_from_evo_api(api_url: str, user: str, password: str, status_filter: Optional[str] = "Active") -> List[Cliente]:
    """Busca membros da API do Evo usando paginação e retorna uma lista de Cliente."""
    logger = logging.getLogger(__name__)
    logger.info(f"Buscando membros da API do Evo: {api_url}")
    
    clientes = []
    take = 250
    skip = 0
    endpoint = f"{api_url.rstrip('/')}/api/v2/members"
    
    while True:
        try:
            logger.info(f"Carregando lote da API do Evo (skip={skip}, take={take})...")
            response = requests.get(
                endpoint,
                auth=(user, password),
                params={"take": take, "skip": skip},
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Erro ao buscar membros da API do Evo: Código {response.status_code} - {response.text}")
                raise Exception(f"Evo API error: {response.status_code}")
                
            data = response.json()
            if not data:
                break
                
            for member in data:
                try:
                    id_cliente = str(member.get("idMember") or "")
                    first_name = member.get("firstName") or ""
                    last_name = member.get("lastName") or ""
                    nome = f"{first_name} {last_name}".strip()
                    data_nascimento = member.get("birthDate") or ""
                    status = member.get("status") or ""
                    
                    # Filtra por status se definido
                    if status_filter and status_filter.lower() != "all":
                        if status.lower() != status_filter.lower():
                            continue
                            
                    # Extrai telefone celular
                    contacts = member.get("contacts") or []
                    telefone = ""
                    for contact in contacts:
                        if contact.get("contactType") == "Cellphone" or contact.get("idContactType") == 2:
                            ddi = contact.get("ddi") or ""
                            desc = contact.get("description") or ""
                            telefone = f"{ddi}{desc}"
                            if telefone:
                                break
                                
                    # Fallback para outros telefones se celular não for encontrado
                    if not telefone:
                        for contact in contacts:
                            if contact.get("contactType") in ["Phone", "Telephone"] or contact.get("idContactType") in [1, 3]:
                                ddi = contact.get("ddi") or ""
                                desc = contact.get("description") or ""
                                telefone = f"{ddi}{desc}"
                                if telefone:
                                    break
                                    
                    telefone_sanitizada = sanitize_phone(telefone)
                    
                    if not nome or not telefone_sanitizada:
                        logger.warning(f"Membro {id_cliente} ignorado: nome ou telefone ausentes/inválidos.")
                        continue
                        
                    cliente = Cliente(
                        id_cliente=id_cliente,
                        nome=nome,
                        data_nascimento=data_nascimento,
                        telefone=telefone,
                        telefone_sanitizado=telefone_sanitizada,
                        status=status
                    )
                    clientes.append(cliente)
                except Exception as member_err:
                    logger.error(f"Erro ao processar dados de membro específico: {member_err}")
                    
            if len(data) < take:
                break
                
            skip += take
            time.sleep(0.2)  # Delay preventivo para evitar sobrecarga no servidor do Evo
            
        except Exception as e:
            logger.error(f"Erro na requisição à API do Evo: {e}")
            raise
            
    logger.info(f"Total de {len(clientes)} clientes válidos carregados da API do Evo")
    return clientes


def create_contact_data(cliente: Cliente, kommo_api: KommoAPI) -> Dict[str, Any]:
    """Cria o objeto de dados para criar um contato no Kommo."""
    custom_fields_values = []
    
    # Adiciona Evo ID
    if kommo_api.evo_id_field_id:
        custom_fields_values.append({
            'field_id': kommo_api.evo_id_field_id,
            'values': [{'value': cliente.id_cliente}]
        })
    
    # Adiciona telefone
    if kommo_api.phone_field_id:
        custom_fields_values.append({
            'field_id': kommo_api.phone_field_id,
            'values': [{'value': cliente.telefone_sanitizado}]
        })
    
    contact_data = {
        'name': cliente.nome,
        'custom_fields_values': custom_fields_values
    }
    
    # Se não temos field_id do telefone, adiciona no campo padrão
    if not kommo_api.phone_field_id:
        contact_data['phone'] = cliente.telefone_sanitizado
    
    return contact_data


def create_update_contact_data(contact_id: int, cliente: Cliente, kommo_api: KommoAPI) -> Dict[str, Any]:
    """Cria o objeto de dados para atualizar um contato no Kommo."""
    contact_data = create_contact_data(cliente, kommo_api)
    contact_data['id'] = contact_id
    
    # Remove telefone da atualização (não sobrescrever)
    if 'phone' in contact_data:
        del contact_data['phone']
    
    # Remove telefone dos campos customizados também
    contact_data['custom_fields_values'] = [
        field for field in contact_data['custom_fields_values']
        if field['field_id'] != kommo_api.phone_field_id
    ]
    
    return contact_data


def process_clientes_batch(clientes: List[Cliente], kommo_api: KommoAPI, stats: SyncStats):
    """Processa um lote de clientes."""
    logger = logging.getLogger(__name__)
    
    contacts_to_create = []
    contacts_to_update = []
    
    # Processa cada cliente
    for cliente in clientes:
        try:
            # Busca contato existente
            existing_contact = kommo_api.search_contact_by_phone(cliente.telefone_sanitizado)
            
            if existing_contact:
                # Contato existe - preparar para atualização
                logger.info(f"Contato encontrado para {cliente.nome} (telefone: {cliente.telefone_sanitizado})")
                
                update_data = create_update_contact_data(
                    existing_contact['id'], cliente, kommo_api
                )
                contacts_to_update.append(update_data)
            else:
                # Contato não existe - preparar para criação
                logger.info(f"Criando novo contato para {cliente.nome} (telefone: {cliente.telefone_sanitizado})")
                
                create_data = create_contact_data(cliente, kommo_api)
                contacts_to_create.append((create_data, cliente))
        
        except Exception as e:
            logger.error(f"Erro ao processar cliente {cliente.nome}: {e}")
            stats.erros += 1
    
    # Executa criações em lote
    if contacts_to_create:
        try:
            create_data_list = [data for data, _ in contacts_to_create]
            created_contacts = kommo_api.create_contacts(create_data_list)
            
            # Cria leads para os contatos criados
            for i, created_contact in enumerate(created_contacts):
                cliente = contacts_to_create[i][1]
                logger.info(f"Contato criado: {cliente.nome} (ID: {created_contact['id']})")
                stats.criados += 1
                
                # Cria lead vinculado
                if kommo_api.alunos_pipeline_id and kommo_api.ativo_stage_id:
                    lead = kommo_api.create_lead_for_contact(
                        created_contact['id'], cliente.nome
                    )
                    if lead:
                        logger.info(f"Lead criado para {cliente.nome} (ID: {lead.get('id')})")
                
        except Exception as e:
            logger.error(f"Erro ao criar contatos: {e}")
            stats.erros += len(contacts_to_create)
    
    # Executa atualizações em lote
    if contacts_to_update:
        try:
            updated_contacts = kommo_api.update_contacts(contacts_to_update)
            for updated_contact in updated_contacts:
                logger.info(f"Contato atualizado: ID {updated_contact['id']}")
                stats.atualizados += 1
                
        except Exception as e:
            logger.error(f"Erro ao atualizar contatos: {e}")
            stats.erros += len(contacts_to_update)


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description='Sincroniza clientes do Evo com Kommo CRM')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Executa simulação sem fazer alterações')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Modo verbose (mais logs)')
    parser.add_argument('--batch-size', type=int, default=MAX_BATCH_SIZE,
                       help=f'Tamanho do lote para processamento (default: {MAX_BATCH_SIZE})')
    
    args = parser.parse_args()
    
    # Configurar logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Carregar variáveis de ambiente
        load_dotenv()
        
        required_vars = [
            'KOMMO_DOMAIN', 'KOMMO_CLIENT_ID', 'KOMMO_CLIENT_SECRET', 
            'KOMMO_ACCESS_TOKEN', 'KOMMO_REFRESH_TOKEN',
            'EVO_API_USER', 'EVO_API_PASSWORD'
        ]
        
        for var in required_vars:
            if not os.getenv(var):
                raise ValueError(f"Variável de ambiente obrigatória não encontrada: {var}")
        
        if args.dry_run:
            logger.info("=== MODO DRY RUN ATIVADO ===")
        
        # Inicializar API do Kommo
        kommo_api = KommoAPI(
            domain=os.getenv('KOMMO_DOMAIN'),
            client_id=os.getenv('KOMMO_CLIENT_ID'),
            client_secret=os.getenv('KOMMO_CLIENT_SECRET'),
            access_token=os.getenv('KOMMO_ACCESS_TOKEN'),
            refresh_token=os.getenv('KOMMO_REFRESH_TOKEN'),
            dry_run=args.dry_run
        )
        
        kommo_api.initialize()
        
        # Buscar clientes da API do Evo
        evo_url = os.getenv('EVO_API_URL', 'https://evo-integracao-api.w12app.com.br')
        evo_user = os.getenv('EVO_API_USER')
        evo_pass = os.getenv('EVO_API_PASSWORD')
        evo_status = os.getenv('EVO_MEMBER_STATUS', 'Active')
        
        clientes = fetch_members_from_evo_api(evo_url, evo_user, evo_pass, evo_status)
        
        # Estatísticas
        stats = SyncStats(total=len(clientes))
        
        logger.info(f"Iniciando sincronização de {stats.total} clientes...")
        
        # Processar em lotes
        batch_size = min(args.batch_size, MAX_BATCH_SIZE)
        for i in range(0, len(clientes), batch_size):
            batch = clientes[i:i + batch_size]
            logger.info(f"Processando lote {i//batch_size + 1} ({len(batch)} clientes)")
            
            process_clientes_batch(batch, kommo_api, stats)
            
            # Pequeno delay entre lotes
            if i + batch_size < len(clientes):
                time.sleep(RATE_LIMIT_DELAY)
        
        # Relatório final
        logger.info("=== RELATÓRIO FINAL ===")
        logger.info(f"Total de clientes processados: {stats.total}")
        logger.info(f"Contatos criados: {stats.criados}")
        logger.info(f"Contatos atualizados: {stats.atualizados}")
        logger.info(f"Erros: {stats.erros}")
        logger.info(f"Sucesso: {stats.criados + stats.atualizados}")
        
        if args.dry_run:
            logger.info("=== SIMULAÇÃO CONCLUÍDA ===")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Sincronização cancelada pelo usuário")
        return 1
        
    except Exception as e:
        logger.error(f"Erro durante a sincronização: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())