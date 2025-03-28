curl -o jre.tar.gz https://download.java.net/openjdk/jdk11/ri/openjdk-11+28_linux-x64_bin.tar.gz
mkdir -p /opt/java
tar -xzf jre.tar.gz -C /opt/java --strip-components=1
export JAVA_HOME=/opt/java
export PATH=$JAVA_HOME/bin:$PATH
pip install -r requirements.txt
