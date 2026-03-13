FROM --platform=linux/amd64 python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

RUN curl -fL https://dl.k8s.io/release/v1.35.2/bin/linux/amd64/kubectl > /usr/local/bin/kubectl
RUN chmod +x /usr/local/bin/kubectl

COPY . /srv/kubessh
COPY helm-chart/images/kubessh/kubessh_config.py /srv/kubessh

WORKDIR /srv/kubessh

RUN pip3 install --no-cache-dir .

# Run as non-root user
RUN groupadd -r kubessh && useradd -r -g kubessh -d /home/kubessh -m kubessh
USER kubessh

ENTRYPOINT [ "/usr/local/bin/kubessh" ]
