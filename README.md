


用這個來 build docker

docker build -t yt-clipper .  




docker run -p 5000:5000 --rm --name my-clipper \
  -v "$HOME/Library/Application Support/Google/Chrome/Default:/root/.config/google-chrome/Default:ro" \
  -v "$(pwd)/downloads:/app/downloads" \
  -e FLASK_SECRET_KEY='your_very_secret_random_key' \
  yt-clipper