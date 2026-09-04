#!/bin/bash
BLOBS=~/.cache/huggingface/hub/models--mlx-community--Qwen3.5-9B-4bit/blobs
while find "$BLOBS" -iname '*.incomplete' 2>/dev/null | grep -q .; do
  sleep 20
done
echo "DOWNLOAD_TRULY_COMPLETE"
du -sh ~/.cache/huggingface/hub/models--mlx-community--Qwen3.5-9B-4bit
