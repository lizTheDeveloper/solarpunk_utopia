"""Python version compatibility module.

Provides UTC constant for Python < 3.11 compatibility.
"""

import sys
from datetime import timezone

# UTC was added in Python 3.11
if sys.version_info >= (3, 11):
    from datetime import UTC
else:
    UTC = timezone.utc
