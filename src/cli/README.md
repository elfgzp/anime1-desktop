# Anime1 Desktop CLI

Command line interface for Anime1 Desktop.

## Installation

```bash
# Link CLI globally
npm link

# Or use directly
npm run cli -- <command>
```

## Commands

### Quick Commands

```bash
# Show overall status
anime1 status

# Open data directory
anime1 open
```

### Auto Download Management

```bash
# Show auto download status
anime1 download status

# Start auto download service
anime1 download start

# Stop auto download service
anime1 download stop

# View download history
anime1 download history
anime1 download history -l 100
anime1 download history -s completed

# Configure auto download
anime1 download config
anime1 download config -p /path/to/downloads
anime1 download config -c 3
anime1 download config --enable

# Add manual download
anime1 download add -a "Anime Title" -e 1 -u "http://video.url"
```

### Cache Management

```bash
# Show cache information
anime1 cache info

# Clear all cache
anime1 cache clear
anime1 cache clear -f

# Clear specific cache
anime1 cache clear -c    # covers only
anime1 cache clear -p    # playlist only
anime1 cache clear -l    # anime list only

# Refresh cache
anime1 cache refresh -l  # refresh anime list
```

### Log Management

```bash
# View logs
anime1 logs view
anime1 logs view -n 100
anime1 logs view -f      # follow mode
anime1 logs view -l error

# Export logs
anime1 logs export -o /path/to/export.log

# Clear logs
anime1 logs clear
```

### Configuration

```bash
# List all settings
anime1 config list

# Get specific setting
anime1 config get theme

# Set setting
anime1 config set theme dark
anime1 config set download_path "/path/to/downloads"
```

## Options

- `-v, --version` - Show version
- `-q, --quiet` - Suppress banner output
- `-h, --help` - Show help

## Examples

```bash
# Check status and clear expired cache
anime1 status
anime1 cache clear -p

# Configure and start auto download
anime1 download config -p ~/Downloads/Anime --enable
anime1 download start

# Monitor downloads
anime1 download history -f

# View recent errors
anime1 logs view -l error -n 50
```

## Development

```bash
# Run CLI in development
npm run cli -- status

# With verbose output
DEBUG=anime1:* npm run cli -- status
```
