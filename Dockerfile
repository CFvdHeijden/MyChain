FROM ubuntu:20.04

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN apt update

RUN apt install python3-pip -y

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python3" ]

CMD ["MyChain.py" ]