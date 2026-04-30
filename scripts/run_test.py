cd ..import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.test_extractors import run_test

if __name__ == '__main__':
    success = run_test()
    sys.exit(0 if success else 1)