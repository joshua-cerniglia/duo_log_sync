import os
import sys
import json
import logging

class Consumer():
    def __init__(self, log_queue, log_offset, writer, checkpoint_dir):
        self.checkpoint_dir = checkpoint_dir
        self.log_offset = log_offset
        self.log_queue = log_queue
        self.writer = writer
        self.log_type = None

    async def consume(self):
        """
        Consumer that will consume data from log_queue that a corresponding
        Producer writes to. This data is then sent over a configured transport
        protocol to respective SIEMs or server.
        """
        while True:
            logging.info("Consuming %s logs...", self.log_type)
            logs = await self.log_queue.get()

            if logs is None:
                logging.info("%s logs empty. Nothing to write...", self.log_type)
                continue

            logging.info("Consumed %s %s logs...", len(logs), self.log_type)

            try:
                for log in logs:
                    self.writer.write(json.dumps(log).encode() + b'\n')
                    await self.writer.drain()
                logging.info("Wrote data over tcp socket...")
            except Exception as e:
                logging.error("Failed to write data to transport with %s", e)
                sys.exit(1)

            # Idea is to write to log_offset file after data is sent
            # When user sets recover=True in toml, we will read from this file
            # if it exists and grab data from that offset
            # Still testing out this logic
            checkpoint_file = os.path.join(
                self.checkpoint_dir,
                f"{self.log_type}_checkpoint_data.txt")
            checkpointing_data = open(checkpoint_file, "w")
            checkpointing_data.write(json.dumps(self.log_offset))
            checkpointing_data.flush()
            checkpointing_data.close()