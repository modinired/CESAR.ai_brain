FROM prefecthq/prefect:2.14.9-python3.11

WORKDIR /opt/prefect

# Install additional dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy flows
COPY flows/ /opt/prefect/flows/

# Set Python path
ENV PYTHONPATH=/opt:/opt/prefect

CMD ["prefect", "worker", "start", "--pool", "default-agent-pool", "--type", "process"]
