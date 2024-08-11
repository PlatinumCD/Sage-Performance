FROM waggle/plugin-base:1.1.1-base

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/
COPY fsparser /app/fsparser

WORKDIR /app
ENTRYPOINT ["python3", "-u", "/app/app.py", "-rounds=10", "-interval=500", "-proc:stat:user", "-proc:stat:system", "-proc:stat:ctxt", "-proc:stat:intr"]
