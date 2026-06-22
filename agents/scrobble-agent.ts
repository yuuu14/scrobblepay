#!/usr/bin/env tsx

/**
 * ScrobblePay Agent 🤖🎵
 * 
 * An AI agent that:
 * 1. Fetches your Last.fm scrobbles
 * 2. Calculates per-artist payment splits
 * 3. (Optionally) executes nanopayments via Circle CLI on Arc
 * 
 * Usage:
 *   npm run agent -- --user yuuu14 --budget 5.0
 *   npm run agent -- --user yuuu14 --budget 5.0 --execute
 */

import { LastFmClient } from '../src/lastfm.js';
import { PaymentSplitter } from '../src/splitter.js';
import { execSync } from 'child_process';

const LASTFM_API_KEY = process.env.LASTFM_API_KEY || '9d0b1e1c6e5f7a8b9c0d1e2f3a4b5c6d';

interface AgentConfig {
  user: string;
  budget: number;
  execute: boolean;
  lastfmApiKey: string;
}

function parseArgs(): AgentConfig {
  const args = process.argv.slice(2);
  const get = (flag: string, def?: string) => {
    const idx = args.indexOf(flag);
    return idx >= 0 ? args[idx + 1] : def;
  };

  return {
    user: get('--user', 'yuuu14')!,
    budget: parseFloat(get('--budget', '5.0')!),
    execute: args.includes('--execute'),
    lastfmApiKey: process.env.LASTFM_API_KEY || '9d0b1e1c6e5f7a8b9c0d1e2f3a4b5c6d',
  };
}

async function main() {
  const config = parseArgs();

  console.log(`
🤖 ScrobblePay Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  User:    ${config.user}
  Budget:  $${config.budget.toFixed(2)}
  Execute: ${config.execute ? '✅ ON (will send payments!)' : '❌ OFF (dry run)'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`);

  // Step 1: Fetch scrobbles
  console.log('📡 Fetching scrobbles from Last.fm...');
  const client = new LastFmClient(config.lastfmApiKey);
  const { tracks, total } = await client.getRecentTracks(config.user, 200);
  console.log(`   Found ${tracks.length} tracks (${total} total scrobbles)`);

  // Step 2: Aggregate by artist
  console.log('\n📊 Aggregating by artist...');
  const artists = client.aggregateByArtist(tracks);
  console.log(`   ${artists.length} unique artists`);

  // Step 3: Calculate payment splits
  console.log('\n💰 Calculating payment splits...');
  const splitter = new PaymentSplitter();
  const split = splitter.calculate(artists, config.budget);

  // Print the split
  if (split.perArtist.length === 0) {
    console.log('\n⚠️  No payments meet the minimum threshold.');
    return;
  }

  console.log(splitter.formatSplit(split));

  // Step 4: Execute payments (if --execute)
  if (config.execute) {
    console.log('\n💸 Executing nanopayments on Arc...');
    console.log('   (This requires a funded Arc wallet and Circle CLI configured)');
    
    for (const artist of split.perArtist.slice(0, 5)) {
      const microUSDC = artist.amountUSDC;
      if (microUSDC <= 0) continue;

      console.log(`   → Sending $${artist.amountCents.toFixed(2)} to ${artist.artist}...`);
      
      try {
        // Use Circle CLI to send payment
        const result = execSync(
          `circle wallet transfer --amount ${microUSDC} --token USDC --to "${artist.artist}" 2>&1`,
          { timeout: 30000, encoding: 'utf-8' }
        );
        console.log(`     ✅ ${result.trim()}`);
      } catch (err: any) {
        console.log(`     ⚠️  Skipped (Circle CLI not configured): ${err.message}`);
      }
    }
  } else {
    console.log('\n💡 Run with --execute to actually send payments');
    console.log('   First configure: circle wallet create');
  }

  // Summary
  console.log(`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ScrobblePay Agent complete!
   Total scrobbles:  ${total}
   Unique artists:  ${artists.length}
   Budget:          $${config.budget.toFixed(2)}
   Payouts:         ${split.perArtist.length} artists
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`);
}

main().catch((err) => {
  console.error('❌ Agent failed:', err.message);
  process.exit(1);
});
