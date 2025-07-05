"""
🔗 Blockchain Disaster Uploader
재해 데이터를 블록체인에 업로드하는 클래스
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
from eth_account import Account

from .config import BlockchainConfig
from .abi import DISASTER_REGISTRY_ABI
from ai_search import DisasterInfo

logger = logging.getLogger(__name__)

class DisasterUploader:
    """재해 데이터 블록체인 업로더"""
    
    def __init__(self):
        self.config = BlockchainConfig()
        
        # 계정 설정
        self.account = Account.from_key(self.config.private_key)
        
        # 여러 RPC URL 시도
        self.web3 = self._connect_to_rpc()
        
        # 컨트랙트 인스턴스
        self.contract = self.web3.eth.contract(
            address=self.config.contract_address,
            abi=DISASTER_REGISTRY_ABI
        )
        
        # 연결 확인
        self._verify_connection()
    
    def _connect_to_rpc(self) -> Web3:
        """여러 RPC URL을 시도하여 연결"""
        for i, rpc_url in enumerate(self.config.rpc_urls):
            try:
                logger.info(f"🔗 Trying RPC {i+1}/{len(self.config.rpc_urls)}: {rpc_url}")
                
                web3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # 연결 테스트
                if web3.is_connected():
                    # 추가 테스트: 체인 ID 확인
                    try:
                        chain_id = web3.eth.chain_id
                        if chain_id == self.config.chain_id:
                            logger.info(f"✅ Successfully connected to: {rpc_url}")
                            self.config.rpc_url = rpc_url  # 성공한 RPC URL 저장
                            return web3
                        else:
                            logger.warning(f"⚠️ Wrong chain ID {chain_id}, expected {self.config.chain_id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Chain ID check failed: {e}")
                else:
                    logger.warning(f"⚠️ Connection failed to: {rpc_url}")
                    
            except Exception as e:
                logger.warning(f"⚠️ RPC {rpc_url} failed: {e}")
                continue
        
        # 모든 RPC 실패
        raise ConnectionError(f"Failed to connect to any RPC. Tried {len(self.config.rpc_urls)} endpoints.")
    
    def _verify_connection(self):
        """블록체인 연결 확인"""
        try:
            logger.info(f"🔗 Attempting to connect to: {self.config.rpc_url}")
            logger.info(f"🔗 Network: {self.config.network_name} (Chain ID: {self.config.chain_id})")
            logger.info(f"🔗 Contract: {self.config.contract_address}")
            
            # 연결 테스트
            if not self.web3.is_connected():
                logger.error(f"❌ Failed to connect to RPC: {self.config.rpc_url}")
                raise ConnectionError("Failed to connect to blockchain network")
            
            # 네트워크 정보 확인
            try:
                chain_id = self.web3.eth.chain_id
                logger.info(f"✅ Connected! Chain ID: {chain_id}")
                
                if chain_id != self.config.chain_id:
                    logger.warning(f"⚠️ Chain ID mismatch: expected {self.config.chain_id}, got {chain_id}")
                
                # 최신 블록 확인
                latest_block = self.web3.eth.block_number
                logger.info(f"📦 Latest block: {latest_block}")
                
            except Exception as e:
                logger.error(f"❌ Failed to get network info: {e}")
                raise ConnectionError(f"Network info error: {e}")
            
            # 계정 잔액 확인
            try:
                balance = self.web3.eth.get_balance(self.account.address)
                logger.info(f"💰 Account: {self.account.address}")
                logger.info(f"💰 Balance: {self.web3.from_wei(balance, 'ether'):.4f} ETH")
                
                if balance == 0:
                    logger.warning("⚠️ Account balance is 0 ETH - transactions will fail")
                    
            except Exception as e:
                logger.error(f"❌ Failed to get balance: {e}")
                raise ConnectionError(f"Balance check error: {e}")
                
        except Exception as e:
            logger.error(f"❌ Blockchain connection failed: {e}")
            logger.error(f"❌ RPC URL: {self.config.rpc_url}")
            logger.error(f"❌ Network: {self.config.network_name}")
            raise
    
    async def upload_disaster(self, disaster: DisasterInfo) -> Dict[str, Any]:
        """재해 데이터를 블록체인에 업로드"""
        try:
            logger.info(f"🔗 Uploading disaster to blockchain: {disaster.id}")
            
            # 0. 권한 확인
            permissions = await self.check_permissions()
            logger.info(f"🔐 Permissions check: {permissions}")
            
            # 1. 중복 확인
            if await self._disaster_exists(disaster.id):
                return {
                    "success": False,
                    "error": f"Disaster {disaster.id} already exists on blockchain",
                    "error_type": "DUPLICATE"
                }
            
            # 2. 트랜잭션 빌드
            tx_data = self._build_transaction(disaster)
            
            # 3. 가스 추정 및 잔액 확인
            try:
                estimated_gas = self.web3.eth.estimate_gas(tx_data)
                tx_data['gas'] = min(estimated_gas + 50000, self.config.gas_limit)  # 여유분 추가
                
                # 필요한 ETH 계산
                gas_price = tx_data['gasPrice']
                total_cost = tx_data['gas'] * gas_price
                current_balance = self.web3.eth.get_balance(self.account.address)
                
                logger.info(f"⛽ Estimated gas: {estimated_gas}, using: {tx_data['gas']}")
                logger.info(f"💰 Gas cost: {self.web3.from_wei(total_cost, 'ether'):.6f} ETH")
                logger.info(f"💰 Current balance: {self.web3.from_wei(current_balance, 'ether'):.6f} ETH")
                
                if current_balance < total_cost:
                    needed_eth = self.web3.from_wei(total_cost - current_balance, 'ether')
                    return {
                        "success": False,
                        "error": f"Insufficient funds. Need {needed_eth:.6f} more ETH",
                        "error_type": "INSUFFICIENT_FUNDS",
                        "current_balance_eth": self.web3.from_wei(current_balance, 'ether'),
                        "required_eth": self.web3.from_wei(total_cost, 'ether'),
                        "needed_eth": needed_eth
                    }
                    
            except Exception as e:
                logger.warning(f"⚠️ Gas estimation failed, using default: {e}")
                tx_data['gas'] = self.config.gas_limit
            
            # 4. 트랜잭션 서명
            signed_tx = self.web3.eth.account.sign_transaction(tx_data, self.config.private_key)
            
            # 5. 트랜잭션 전송
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            logger.info(f"📤 Transaction sent: {tx_hash_hex}")
            
            # 6. 트랜잭션 대기 (비동기)
            receipt = await self._wait_for_transaction(tx_hash)
            
            if receipt.status == 1:
                # 7. 업로드 후 검증
                logger.info(f"🔍 Verifying upload...")
                await asyncio.sleep(3)  # 블록체인 상태 업데이트 대기
                
                uploaded_data = await self.get_disaster_from_blockchain(disaster.id)
                if uploaded_data:
                    logger.info(f"✅ Upload verified! Data found on blockchain:")
                    logger.info(f"   ID: {uploaded_data['id']}")
                    logger.info(f"   Name: {uploaded_data['name']}")
                    logger.info(f"   Location: {uploaded_data['location']}")
                else:
                    logger.warning(f"⚠️ Upload verification failed - data not found on blockchain")
                
                # 성공
                result = {
                    "success": True,
                    "transaction_hash": tx_hash_hex,
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "etherscan_url": self.config.get_etherscan_tx_url(tx_hash_hex),
                    "disaster_id": disaster.id,
                    "contract_address": self.config.contract_address,
                    "uploaded_at": int(datetime.now().timestamp()),
                    "verified": uploaded_data is not None,
                    "uploaded_data": uploaded_data
                }
                
                logger.info(f"✅ Disaster uploaded successfully: {disaster.id}")
                logger.info(f"🔍 View on Etherscan: {result['etherscan_url']}")
                
                return result
            else:
                # 실패
                return {
                    "success": False,
                    "error": "Transaction failed",
                    "transaction_hash": tx_hash_hex,
                    "etherscan_url": self.config.get_etherscan_tx_url(tx_hash_hex),
                    "error_type": "TRANSACTION_FAILED"
                }
                
        except ContractLogicError as e:
            logger.error(f"❌ Contract logic error: {e}")
            return {
                "success": False,
                "error": f"Contract error: {str(e)}",
                "error_type": "CONTRACT_ERROR"
            }
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "UNKNOWN_ERROR"
            }
    
    def _build_transaction(self, disaster: DisasterInfo) -> Dict[str, Any]:
        """트랜잭션 데이터 빌드"""
        
        # 재해 데이터 매핑
        disaster_data = {
            "disasterId": disaster.id,
            "name": disaster.title[:100],  # 길이 제한
            "description": disaster.description[:500] if disaster.description else "",  # 길이 제한
            "location": disaster.location[:100] if disaster.location else "",
            "startDate": disaster.timestamp,
            "endDate": 0,  # 진행중
            "imageUrl": "",  # 나중에 추가 가능
            "externalSource": disaster.source[:100] if disaster.source else "WRLD Relief Monitor"
        }
        
        # 디버깅: 실제 전송될 데이터 로깅
        logger.info(f"📋 Building transaction with data:")
        logger.info(f"   disasterId: '{disaster_data['disasterId']}'")
        logger.info(f"   name: '{disaster_data['name']}'")
        logger.info(f"   description: '{disaster_data['description']}'")
        logger.info(f"   location: '{disaster_data['location']}'")
        logger.info(f"   startDate: {disaster_data['startDate']}")
        logger.info(f"   endDate: {disaster_data['endDate']}")
        logger.info(f"   imageUrl: '{disaster_data['imageUrl']}'")
        logger.info(f"   externalSource: '{disaster_data['externalSource']}'")
        
        # 빈 문자열 검증
        if not disaster_data["disasterId"]:
            logger.error("❌ disasterId is empty!")
        if not disaster_data["name"]:
            logger.error("❌ name is empty!")
        if not disaster_data["location"]:
            logger.error("❌ location is empty!")
        
        # 컨트랙트 함수 호출 데이터
        function_call = self.contract.functions.registerDisaster(
            disaster_data["disasterId"],
            disaster_data["name"],
            disaster_data["description"],
            disaster_data["location"],
            disaster_data["startDate"],
            disaster_data["endDate"],
            disaster_data["imageUrl"],
            disaster_data["externalSource"]
        )
        
        # 강제 낮은 가스 가격 사용 (테스트넷 최적화)
        try:
            # 현재 네트워크 가스 가격 확인 (정보용)
            current_gas_price = self.web3.eth.gas_price
            
            # 테스트넷에서는 강제로 낮은 가격 사용
            forced_gas_price = self.web3.to_wei(self.config.gas_price_gwei, 'gwei')
            
            logger.info(f"⛽ Network gas price: {self.web3.from_wei(current_gas_price, 'gwei'):.2f} Gwei")
            logger.info(f"⛽ Forced gas price: {self.web3.from_wei(forced_gas_price, 'gwei'):.2f} Gwei (testnet optimization)")
            
            suggested_gas_price = forced_gas_price
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to get network gas price: {e}")
            suggested_gas_price = self.web3.to_wei(self.config.gas_price_gwei, 'gwei')
        
        # 트랜잭션 데이터
        tx_data = function_call.build_transaction({
            'from': self.account.address,
            'gas': self.config.gas_limit,
            'gasPrice': suggested_gas_price,
            'nonce': self.web3.eth.get_transaction_count(self.account.address),
            'chainId': self.config.chain_id
        })
        
        return tx_data
    
    async def _disaster_exists(self, disaster_id: str) -> bool:
        """재해가 이미 블록체인에 존재하는지 확인"""
        try:
            logger.info(f"🔍 Checking if disaster exists on blockchain: {disaster_id}")
            
            # getDisaster 함수 호출해서 확인
            disaster_data = self.contract.functions.getDisaster(disaster_id).call()
            
            # 디버깅: 반환된 데이터 로깅
            logger.info(f"📋 Blockchain query result for {disaster_id}:")
            logger.info(f"   ID field: '{disaster_data[0]}'")
            logger.info(f"   Name field: '{disaster_data[1]}'")
            logger.info(f"   Location field: '{disaster_data[3]}'")
            
            # 빈 문자열이 아니면 존재
            exists = disaster_data[0] != "" and disaster_data[0] is not None
            logger.info(f"🔍 Disaster {disaster_id} exists on blockchain: {exists}")
            
            return exists
            
        except Exception as e:
            logger.info(f"🔍 Disaster {disaster_id} does not exist on blockchain (query failed): {e}")
            # 에러가 발생하면 존재하지 않는 것으로 간주
            return False
    
    async def _wait_for_transaction(self, tx_hash) -> Any:
        """트랜잭션 완료 대기 (비동기)"""
        max_wait_time = 300  # 5분
        poll_interval = 2    # 2초마다 확인
        
        for _ in range(max_wait_time // poll_interval):
            try:
                receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                return receipt
            except TransactionNotFound:
                await asyncio.sleep(poll_interval)
                continue
        
        raise TimeoutError(f"Transaction {tx_hash.hex()} not confirmed within {max_wait_time} seconds")
    
    async def get_disaster_from_blockchain(self, disaster_id: str) -> Optional[Dict[str, Any]]:
        """블록체인에서 재해 데이터 조회"""
        try:
            disaster_data = self.contract.functions.getDisaster(disaster_id).call()
            
            if disaster_data[0] == "":  # id가 빈 문자열이면 존재하지 않음
                return None
            
            return {
                "id": disaster_data[0],
                "name": disaster_data[1],
                "description": disaster_data[2],
                "location": disaster_data[3],
                "start_date": disaster_data[4],
                "end_date": disaster_data[5],
                "image_url": disaster_data[6],
                "external_source": disaster_data[7],
                "status": disaster_data[8],
                "created_at": disaster_data[9],
                "updated_at": disaster_data[10],
                "created_by": disaster_data[11]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get disaster from blockchain: {e}")
            return None
    
    async def get_total_disasters_count(self) -> int:
        """블록체인에 등록된 총 재해 수 조회"""
        try:
            count = self.contract.functions.getTotalDisasterCount().call()
            return count
        except Exception as e:
            logger.error(f"❌ Failed to get total disasters count: {e}")
            return 0
    
    async def check_permissions(self) -> Dict[str, bool]:
        """권한 확인"""
        try:
            data_provider_role = self.contract.functions.DATA_PROVIDER_ROLE().call()
            has_permission = self.contract.functions.hasRole(data_provider_role, self.account.address).call()
            
            return {
                "has_data_provider_role": has_permission,
                "account_address": self.account.address,
                "contract_address": self.config.contract_address
            }
        except Exception as e:
            logger.error(f"❌ Failed to check permissions: {e}")
            return {
                "has_data_provider_role": False,
                "account_address": self.account.address,
                "contract_address": self.config.contract_address,
                "error": str(e)
            }
