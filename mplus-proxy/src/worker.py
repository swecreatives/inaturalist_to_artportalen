import asyncio

import mistralai.workflows as workflows

from workflows.mplus_proxy import MplusApiWorkflow


async def main():
    await workflows.run_worker([MplusApiWorkflow])


if __name__ == "__main__":
    asyncio.run(main())
