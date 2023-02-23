# -*- coding: utf-8 -*-
import asyncio
import sys

import src

if __name__ == "__main__":
    asyncio.run(src.main.main(sys.argv[1:]))
