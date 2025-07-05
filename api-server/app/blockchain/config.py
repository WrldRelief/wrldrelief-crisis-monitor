"""
🔗 Blockchain Configuration
블록체인 연동 설정
"""

import os
from typing import Optional

class BlockchainConfig:
    """블록체인 설정 클래스"""
    
    def __init__(self):
        # 환경 변수에서 설정 로드
        self.rpc_urls = [
            os.getenv("RPC_URL", "https://rpc.ankr.com/eth_sepolia"),
            "https://rpc.sepolia.org",
            "https://sepolia.drpc.org",
            "https://eth-sepolia.g.alchemy.com/v2/demo",
            "https://rpc2.sepolia.org",
            "https://sepolia.gateway.tenderly.co"
        ]
        self.rpc_url = self.rpc_urls[0]  # 기본값
        self.private_key = os.getenv("PRIVATE_KEY")
        self.contract_address = os.getenv("DISASTER_REGISTRY_ADDRESS", "0x9e3329B77915a38fae5b8375E839DeE293eAFd56")
        self.chain_id = int(os.getenv("CHAIN_ID", "11155111"))  # Sepolia
        
        # 가스 설정 (Sepolia 테스트넷 극한 최적화)
        self.gas_limit = int(os.getenv("GAS_LIMIT", "200000"))  # 더 낮춤
        self.gas_price_gwei = int(os.getenv("GAS_PRICE_GWEI", "1"))   # 최소값 (테스트넷)
        
        # 네트워크 설정
        self.network_name = os.getenv("NETWORK_NAME", "sepolia")
        self.etherscan_url = os.getenv("ETHERSCAN_URL", "https://sepolia.etherscan.io")
        
        # 검증
        self._validate_config()
    
    def _validate_config(self):
        """설정 검증"""
        if not self.private_key:
            raise ValueError("PRIVATE_KEY environment variable is required")
        
        if not self.contract_address:
            raise ValueError("DISASTER_REGISTRY_ADDRESS environment variable is required")
        
        if not self.rpc_url:
            raise ValueError("RPC_URL environment variable is required")
    
    def get_etherscan_tx_url(self, tx_hash: str) -> str:
        """Etherscan 트랜잭션 URL 생성"""
        return f"{self.etherscan_url}/tx/{tx_hash}"
    
    def get_etherscan_address_url(self, address: str) -> str:
        """Etherscan 주소 URL 생성"""
        return f"{self.etherscan_url}/address/{address}"
    
    @property
    def is_testnet(self) -> bool:
        """테스트넷 여부 확인"""
        return self.chain_id in [11155111, 5, 4, 3]  # Sepolia, Goerli, Rinkeby, Ropsten
    
    def __str__(self) -> str:
        return f"BlockchainConfig(network={self.network_name}, chain_id={self.chain_id}, contract={self.contract_address})"
