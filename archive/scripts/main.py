"""
Command-line interface for TJRJ Precatórios Scraper

Usage:
    # Scrape regime geral
    python main.py --regime geral

    # Scrape regime especial with custom output
    python main.py --regime especial --output meu_arquivo.csv

    # Enable debug logging and visible browser
    python main.py --regime geral --log-level DEBUG --no-headless

    # Disable caching
    python main.py --regime geral --no-cache
"""

import argparse
import sys
from pathlib import Path
from loguru import logger
import pandas as pd

from src.scraper import TJRJPrecatoriosScraper
from src.config import get_config
from src.models import ScraperConfig


def setup_logging(log_level: str):
    """Configure logging"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )


def main():
    parser = argparse.ArgumentParser(
        description='TJRJ Precatórios Web Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --regime geral
  python main.py --regime especial --output resultado.csv
  python main.py --regime geral --log-level DEBUG --no-headless
        """
    )

    parser.add_argument(
        '--regime',
        choices=['geral', 'especial'],
        default='geral',
        help='Regime to scrape (default: geral)'
    )

    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV filename (auto-generated if not specified)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable response caching'
    )

    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Load configuration
    config = get_config()

    # Override config with CLI arguments
    if args.no_cache:
        config.enable_cache = False
    if args.no_headless:
        config.headless = False

    config.regime = args.regime
    config.log_level = args.log_level

    logger.info("=" * 60)
    logger.info("🚀 TJRJ Precatórios Scraper")
    logger.info("=" * 60)
    logger.info(f"Regime: {config.regime}")
    logger.info(f"Headless: {config.headless}")
    logger.info(f"Cache: {'Enabled' if config.enable_cache else 'Disabled'}")
    logger.info("=" * 60)

    try:
        # Initialize scraper
        scraper = TJRJPrecatoriosScraper(config=config)

        # Scrape data
        df = scraper.scrape_regime(config.regime)

        if df.empty:
            logger.warning("⚠️  No data extracted!")
            logger.info("\n💡 This is expected on first run.")
            logger.info("   The scraper needs manual inspection of the site structure.")
            logger.info("   Please run with --no-headless to see the browser and inspect elements.")
            return 1

        # Save to CSV
        output_path = scraper.save_to_csv(df, filename=args.output)

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records: {len(df)}")

        if 'entidade_devedora' in df.columns:
            logger.info(f"Entities: {df['entidade_devedora'].nunique()}")

        if 'valor_atualizado' in df.columns and len(df) > 0:
            # Convert to float for sum if it's Decimal
            valores = pd.to_numeric(df['valor_atualizado'], errors='coerce')
            total_valor = valores.sum()
            logger.info(f"Total value: R$ {total_valor:,.2f}")

        logger.info(f"Output file: {output_path}")
        logger.info("=" * 60)
        logger.info("✅ SUCCESS!")

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
