# Install Java in Render
curl -fsSL https://adoptium.net/releases.html | grep -oP 'https://.*?OpenJDK.*?x64_Linux.tar.gz' | head -1 | xargs curl -O
tar -xzf OpenJDK*.tar.gz
export PATH=$PWD/jdk/bin:$PATH

pip install -r requirements.txt
