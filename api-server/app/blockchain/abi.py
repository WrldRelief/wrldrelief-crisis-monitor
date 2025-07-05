"""
🔗 Smart Contract ABI
DisasterRegistry 컨트랙트 ABI 정의
"""

DISASTER_REGISTRY_ABI = [
    {
        "inputs": [],
        "name": "initialize",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "disasterId", "type": "string"},
            {"internalType": "string", "name": "name", "type": "string"},
            {"internalType": "string", "name": "description", "type": "string"},
            {"internalType": "string", "name": "location", "type": "string"},
            {"internalType": "uint256", "name": "startDate", "type": "uint256"},
            {"internalType": "uint256", "name": "endDate", "type": "uint256"},
            {"internalType": "string", "name": "imageUrl", "type": "string"},
            {"internalType": "string", "name": "externalSource", "type": "string"}
        ],
        "name": "registerDisaster",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "disasterId", "type": "string"}
        ],
        "name": "getDisaster",
        "outputs": [
            {
                "components": [
                    {"internalType": "string", "name": "id", "type": "string"},
                    {"internalType": "string", "name": "name", "type": "string"},
                    {"internalType": "string", "name": "description", "type": "string"},
                    {"internalType": "string", "name": "location", "type": "string"},
                    {"internalType": "uint256", "name": "startDate", "type": "uint256"},
                    {"internalType": "uint256", "name": "endDate", "type": "uint256"},
                    {"internalType": "string", "name": "imageUrl", "type": "string"},
                    {"internalType": "string", "name": "externalSource", "type": "string"},
                    {"internalType": "enum DisasterRegistry.DisasterStatus", "name": "status", "type": "uint8"},
                    {"internalType": "uint256", "name": "createdAt", "type": "uint256"},
                    {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
                    {"internalType": "address", "name": "createdBy", "type": "address"}
                ],
                "internalType": "struct DisasterRegistry.Disaster",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getActiveDisasters",
        "outputs": [
            {"internalType": "string[]", "name": "", "type": "string[]"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalDisasterCount",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "role", "type": "bytes32"},
            {"internalType": "address", "name": "account", "type": "address"}
        ],
        "name": "hasRole",
        "outputs": [
            {"internalType": "bool", "name": "", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "DATA_PROVIDER_ROLE",
        "outputs": [
            {"internalType": "bytes32", "name": "", "type": "bytes32"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "string", "name": "disasterId", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "name", "type": "string"},
            {"indexed": False, "internalType": "string", "name": "location", "type": "string"},
            {"indexed": True, "internalType": "address", "name": "provider", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "DisasterRegistered",
        "type": "event"
    }
]
