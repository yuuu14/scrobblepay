# ScrobblePay — Development Notes & Known Issues

## Arc Testnet — Technical Quirks

### 1. Arc 需要 EIP-1559 交易类型
- **问题**: Legacy 交易 (type 0x0) 上链后 status = 0x0，即使 value 和 gas 都正确
- **原因**: Arc 的 EVM 实现要求 type 2 (EIP-1559) 交易才能正确处理 native USDC 转账
- **修复**: `"type": "0x2"`, `maxFeePerGas`, `maxPriorityFeePerGas` 字段必需
- **参考文件**: `agents/scrobble_agent.py`

### 2. Arc native USDC 转账需要 30000 gas
- **问题**: 标准 ETH 转账 21000 gas 在 Arc 上会导致 status = 0x0，value 不到账但 gas 照扣
- **原因**: USDC 是 Arc 的 native token，每次转账需要 emit Transfer log，实际消耗 25891 gas
- **修复**: gas 设为 30000（留有安全余量）
- **验证**: `gasUsed: 25891, logs: 1 (Transfer 事件)`

### 3. 并发 nonce 冲突
- **问题**: `asyncio.gather` 同时发多笔交易时，所有 tx 拿到同一个 nonce，只有第一笔能进链
- **原因**: nonce 在 Python 里读取时还没递增，gather 并发读取拿到的值相同
- **修复**: base_nonce + i 顺序递增，单线程发交易
- **代价**: 失去了并发的速度优势，但保证了可靠性

### 4. Python 3.14 SSL 兼容性
- **问题**: `urllib.request.urlopen` 请求 Last.fm API 和 `web3.py` 请求 Arc RPC 都报 SSL EOF 错误
- **错误**: `[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol`
- **原因**: Python 3.14 的 SSL 实现与部分服务器不完全兼容（OpenSSL 3.x 的问题）
- **修复**:
  - Last.fm: 换成 `httpx` 库
  - Arc RPC: `_web3()` helper 中设置 `verify=False` 绕过

## 踩坑时间线

| # | 问题 | 发现时间 | 解决耗时 | 教训 |
|---|------|---------|---------|------|
| 1 | Circle Agent Wallet 不支持 Arc 链发交易 | ~10:30 | 30min | 先确认 CLI 能力范围再开始 |
| 2 | `.env` 路径问题 | ~11:00 | 10min | Agent 要从 `.env` 自动读 key 而不是依赖 env var |
| 3 | 并发 nonce | ~15:00 | 15min | 链上交易不能 naive 并发 |
| 4 | Arc 要 EIP-1559 | ~15:03 | 15min | 每条链的 tx 格式可能不同 |
| 5 | Arc gas 不是 21000 | ~15:06 | 5min | native token 转账的 gas 消耗不同 |
| 6 | Python 3.14 SSL | 全天反复 | 多次 | 换 httpx / 设 verify=False |

## TODO Before Submission

- [ ] 部署到公网可访问 (SCR-003)
- [ ] 录 ≤3 分钟 demo 视频
- [ ] 检查 GitHub repo 是否有敏感信息泄漏（PRIVATE_KEY）
- [ ] 提交到 Luma (https://luma.com/5xcrazms)
- [ ] Discord 分享项目链接
