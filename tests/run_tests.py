# Main test runner for root tests directory
# Runs all test suites and generates reports

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

def run_tests():
    """Run all test suites."""
    print("=" * 80)
    print("Customer Success FTE - Test Suite")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Production tests
    production_tests = Path(__file__).parent.parent / "production" / "tests"
    
    if production_tests.exists():
        print("\n📋 Running Production Tests...")
        print("-" * 80)
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(production_tests), "-v", "--tb=short"],
            cwd=str(production_tests.parent.parent)
        )
        
        if result.returncode != 0:
            print(f"\n❌ Production tests failed with exit code {result.returncode}")
            return False
    else:
        print(f"\n⚠️  Production tests directory not found: {production_tests}")
    
    print("\n" + "=" * 80)
    print("✅ All tests passed!")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
