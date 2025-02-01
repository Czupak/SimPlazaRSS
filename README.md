# SimPlazaRSS
SimPlaza.org ETL (scraper/parser) which generates RSS feed with Magnet Links.

# Install
Run `install.sh` to prepare Pipenv's Virtual Environment.

# Run Scraper
The scraper needs to run periodically. Set up cron entry to execute `run.sh` every hour.

The script will scrape the first page and prepare `index.html` for the RSS feed server.

# Run Server
Created `index.html` needs to be served using http server.

If you have one set up, you can just copy the file to the appropriate directory.

If not, you can run python http server using `http_server.sh`. It will serve the file on port 8080, which you can change.

# Configuring RSS reader
Use `http://your_http_server_ip:port`.

Example: `http://192.168.0.12:8080`.
