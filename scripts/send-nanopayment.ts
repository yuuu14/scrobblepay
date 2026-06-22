/**
 * Send a nanopayment on Arc Testnet
 * 
 * Usage: 
 *   npx tsx scripts/send-nanopayment.ts <to> <amount>
 * 
 * Example:
 *   npx tsx scripts/send-nanopayment.ts 0x2164...e3e9 0.000001
 * 
 * Requires PRIVATE_KEY env var set.
 */

const ARC_RPC = 'https://rpc.testnet.arc.network';

async function main() {
  const to = process.argv[2];
  const amount = process.argv[3] || '0.000001';

  if (!to) {
    console.error('Usage: npx tsx scripts/send-nanopayment.ts <to> <amount>');
    console.error('');
    console.error('Set PRIVATE_KEY env var (the wallet must have test USDC)');
    console.error('');
    console.error('Example:');
    console.error('  PRIVATE_KEY=0x... npx tsx scripts/send-nanopayment.ts 0x2164...e3e9 0.000001');
    process.exit(1);
  }

  // Use the arc-canteen CLI to make RPC calls
  const fromAddr = process.env.FROM || '0x7aa8a60a42ba1f839947f6e7472c99b7e37ef1f2';
  
  console.log(`\n╔══════════════════════════════════════╗`);
  console.log(`║     💸 ScrobblePay Nanopayment      ║`);
  console.log(`╠══════════════════════════════════════╣`);
  console.log(`║  From:  ${fromAddr.slice(0,20)}...`);
  console.log(`║  To:    ${to.slice(0,20)}...`);
  console.log(`║  Amount: $${amount} USDC`);
  console.log(`║  Chain: Arc Testnet`);
  console.log(`║  RPC:   ${ARC_RPC}`);
  console.log(`╚══════════════════════════════════════╝\n`);

  // Check balance first
  console.log('📡 Checking balance...');
  const balanceRes = await fetch(ARC_RPC, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'eth_getBalance',
      params: [fromAddr, 'latest'],
      id: 1,
    }),
  });
  const balanceData: any = await balanceRes.json();
  const balanceWei = BigInt(balanceData.result);
  const balanceUsdc = Number(balanceWei) / 1e18;
  console.log(`   Balance: ${balanceUsdc.toFixed(4)} USDC`);
  console.log(`\n⚠️  To actually send this transaction, you need:`);
  console.log(`   1. The private key for ${fromAddr}`);
  console.log(`   2. A web3 library (ethers, viem)`);
  console.log(`\n   Currently the Circle Agent Wallet manages the key.`);
  console.log(`   To send directly, import the key into a local wallet or use MetaMask.\n`);

  // Simulate what the tx would look like
  const amountWei = BigInt(Math.floor(parseFloat(amount) * 1e18));
  console.log(`📝 Transaction would be:`);
  console.log(`   {
     from: "${fromAddr}",
     to: "${to}",
     value: "${amountWei.toString()} wei (${amount} USDC)",
     chainId: 5042002,
     gas: 21000
   }`);
  console.log(`\n✅ Simulated successfully. Ready for real execution with private key.`);
}

main().catch(console.error);
