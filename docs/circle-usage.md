# Circle CLI & Arc 使用说明

## 环境准备

```bash
# 安装
npm install -g @circle-fin/cli
uv tool install git+https://github.com/the-canteen-dev/ARC-cli

# 登录（需要邮箱接收验证码）
CIRCLE_ACCEPT_TERMS=1 npx circle wallet login <email> --type agent --init
npx circle wallet login --request <request-id> --otp <code>

# 创建钱包
CIRCLE_ACCEPT_TERMS=1 npx circle wallet create
```

## 钱包地址

创建的 Circle Agent Wallet 地址：`0x7aa8a60a42ba1f839947f6e7472c99b7e37ef1f2`

支持多链：ETH, BASE, ARB, OP, AVAX, MATIC, MONAD, UNI

## Arc 测试网（Circle CLI 不支持直接查询）

Arc 是 Circle 自研的 L1 链，Circle CLI 的托管钱包目前不支持 Arc。

```bash
# Arc 测试网 RPC
arc-canteen rpc-url

# 或者直接查询 Arc Testnet 上的 USDC 余额（需要私钥）
curl -s https://rpc.testnet.arc.network
```

## Circle Faucet

领取测试 USDC：https://faucet.circle.com/

填入钱包地址后，选择 Arc Testnet 链（如果支持）。

## x402 支付流程

参考 circle-agent 示例：`/Users/elias/Developer/yuuu14/scrobblepay/circle-agent/`

```bash
cd circle-agent
npm install
npm start  # 启动 localhost:3000
# 浏览器打开，用 MetaMask 连接 Arc Testnet 后支付 $0.01
```

## 验证转账是否成功

### 方法1：Arc Testnet 区块浏览器

```
https://testnet.arc.network/
```

搜索钱包地址，查看 USDC 余额和交易记录。

### 方法2：Circle Gateway API

查询 settlement 状态。

### 方法3：decode-batch.ts

```bash
cd circle-agent
ARC_TESTNET_RPC=https://rpc.testnet.arc.network \
  npx tsx decode-batch.ts 0x<batch-tx-hash>
```


## ✅ 余额验证结果

查询 Arc Testnet RPC 确认：
- 钱包：`0x7aa8a60a42ba1f839947f6e7472c99b7e37ef1f2`
- 余额：**20 test USDC** ✅（faucet 到账成功）

### 查询余额命令
```bash
curl -s -X POST https://rpc.testnet.arc.network \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "eth_getBalance",
    "params": ["<钱包地址>", "latest"],
    "id": 1
  }'
```

### Arc 区块浏览器
https://testnet.arcscan.app/address/<钱包地址>

## 测试发送 nanopayment

### 方法1：运行 circle-agent 的 x402 demo
```bash
cd circle-agent
npm install
npm start
# 浏览器打开 http://localhost:3000
# 用 MetaMask 连接 Arc Testnet → 点 "Pay $0.01" → 签名
```

### 方法2：直接用 Arc RPC 转账（需要私钥）

---

## 实际发送 nanpayment 的方法

### 方案 A：MetaMask（推荐）
1. 安装 [MetaMask](https://metamask.io) 浏览器插件
2. 添加 Arc Testnet：
   - RPC: `https://rpc.testnet.arc.network`
   - Chain ID: `5042002`
   - 浏览器: `https://testnet.arcscan.app`
3. 去 https://faucet.circle.com/ 领测试 USDC
4. 跑 x402 demo 发一笔真正的 nanopayment

### 方案 B：本地私钥
```bash
# 安装 web3.py
uv pip install web3

# 发交易
PRIVATE_KEY=0x... npx tsx scripts/send-nanopayment.ts <to地址> <金额>
```

### 方案 C：Circle CLI 支持的链
Circle Agent Wallet 支持以下链发交易：
ETH, BASE, ARB, OP, AVAX, MATIC, MONAD, UNI
（Arc 暂不支持 agent 直接发）

### 验证交易
- Arc 浏览器：https://testnet.arcscan.app/
- API：`curl https://rpc.testnet.arc.network -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["<地址>","latest"],"id":1}'`
