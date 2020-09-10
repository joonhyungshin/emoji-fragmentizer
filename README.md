# emoji-fragmentizer
Fragmentize Slack emoji made easy

## Usage
```python emofrag.py image.png --rows 4 --cols 4 --token xoxs-123456-abcdef```

If `--token` option is omitted, the emojis will not be uploaded but instead saved to the disk.

### Obtaining user token
1. Go to your [Slack customize page](https://hpcnt.slack.com/customize).
2. Open your developer console, issue `window.prompt("your api token is: ", TS.boot_data.api_token)`.

### Supported image format
This program was tested for PNG and GIF files.
