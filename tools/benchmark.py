"""Benchmark inference speed and accuracy"""
import asyncio
import time
import sys
from pathlib import Path
from PIL import Image
import statistics
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.vision_classifier import FoodClassifier
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def benchmark_classifier():
    """Benchmark classifier performance"""
    logger.info("🏃 Running classifier benchmark...")
    
    # Load classifier
    classifier = FoodClassifier()
    await classifier.load()
    
    # Create test image
    test_image = Image.new("RGB", (512, 512), color=(100, 150, 200))
    
    # Warm-up
    logger.info("🔥 Warming up...")
    for _ in range(5):
        await classifier.predict(test_image, top_k=5)
    
    # Benchmark
    logger.info("⏱️  Benchmarking...")
    num_runs = 50
    times = []
    
    for i in range(num_runs):
        start = time.time()
        labels, scores, inference_ms = await classifier.predict(test_image, top_k=5)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        
        if (i + 1) % 10 == 0:
            logger.info(f"  Run {i+1}/{num_runs}: {elapsed:.1f}ms")
    
    # Results
    logger.info("")
    logger.info("📊 Results:")
    logger.info(f"  Runs: {num_runs}")
    logger.info(f"  Mean: {statistics.mean(times):.1f}ms")
    logger.info(f"  Median: {statistics.median(times):.1f}ms")
    logger.info(f"  Min: {min(times):.1f}ms")
    logger.info(f"  Max: {max(times):.1f}ms")
    logger.info(f"  Std Dev: {statistics.stdev(times):.1f}ms")
    logger.info(f"  Throughput: {1000 / statistics.mean(times):.1f} req/s")


if __name__ == "__main__":
    asyncio.run(benchmark_classifier())
