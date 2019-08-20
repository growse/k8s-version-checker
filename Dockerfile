FROM python:3.7-alpine

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

WORKDIR /opt/k8s-version-checker
COPY version_checker version_checker
COPY tests tests
CMD ["python", "-m", "version_checker"]
