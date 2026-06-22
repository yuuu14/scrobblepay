/**
 * Payment split calculator.
 * Takes scrobble data and calculates how much each artist should get.
 */

import type { ArtistSummary } from './lastfm.js';

export interface PaymentSplit {
  totalAmount: number; // in USDC cents (e.g., 500 = $5.00)
  perArtist: {
    artist: string;
    playCount: number;
    sharePercent: number;
    amountDollars: number; // in dollars (e.g., 0.48 = $0.48)
  }[];
}

export class PaymentSplitter {
  /**
   * Calculate per-artist splits based on play proportions.
   * 
   * @param artists - Aggregated artist play data
   * @param totalUsd - Total budget in USD (e.g., 5.00 = $5)
   * @param minPaymentDollars - Minimum payment in dollars to bother settling
   */
  calculate(
    artists: ArtistSummary[],
    totalUsd: number,
    minPaymentDollars = 0.001
  ): PaymentSplit {
    const totalPlays = artists.reduce((sum, a) => sum + a.playCount, 0);

    const perArtist = artists
      .map((a) => {
        const sharePercent = (a.playCount / totalPlays) * 100;
        const amountDollars = Math.round((a.playCount / totalPlays) * totalUsd * 1000) / 1000;
        return {
          artist: a.name,
          playCount: a.playCount,
          sharePercent: Math.round(sharePercent * 100) / 100,
          amountDollars,
        };
      })
      .filter((a) => a.amountDollars >= minPaymentDollars);

    return {
      totalAmount: Math.round(totalUsd * 100),
      perArtist,
    };
  }

  /**
   * Format a payment split for display / demo
   */
  formatSplit(split: PaymentSplit): string {
    const totalDisplay = (split.totalAmount / 100).toFixed(2);
    let output = `📊 Payment Split ($${totalDisplay} total)\n`;
    output += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;

    for (const artist of split.perArtist) {
      const bar = '█'.repeat(Math.round(artist.sharePercent / 2));
      output +=
        `  ${artist.artist.padEnd(28)} ` +
        `${String(artist.playCount).padStart(3)} plays ` +
        `${artist.sharePercent.toFixed(1).padStart(5)}% ` +
        `→ $${artist.amountDollars.toFixed(3).padStart(6)} ${bar}\n`;
    }

    output += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    output += `  Total artists: ${split.perArtist.length}\n`;
    return output;
  }
}
