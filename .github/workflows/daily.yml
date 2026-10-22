name: Daily NeuroFlow Short

on:
  schedule:
    - cron: "30 12 * * *"   # 12:30 UTC = 6:00 PM IST. Change as you like.
  workflow_dispatch:

jobs:
  make-and-upload:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - name: Install tools
        run: |
          sudo apt-get update
          sudo apt-get install -y ffmpeg fonts-dejavu-core
          pip install -r requirements.txt
      - name: Make the video
        run: |
          for i in 1 2 3; do
            if python generate.py; then exit 0; fi
            echo "Attempt $i failed. Waiting 90 seconds, then trying again."
            sleep 90
          done
          exit 1
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          PIXABAY_API_KEY: ${{ secrets.PIXABAY_API_KEY }}
          PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}
      - name: Keep a copy for review
        uses: actions/upload-artifact@v4
        with:
          name: short
          path: |
            output/short.mp4
            output/meta.json
          retention-days: 7
      - name: Upload to YouTube
        run: python upload.py
        env:
          YT_CLIENT_ID: ${{ secrets.YT_CLIENT_ID }}
          YT_CLIENT_SECRET: ${{ secrets.YT_CLIENT_SECRET }}
          YT_REFRESH_TOKEN: ${{ secrets.YT_REFRESH_TOKEN }}
          PRIVACY: ${{ vars.PRIVACY }}
          AI_LABEL: ${{ vars.AI_LABEL }}
