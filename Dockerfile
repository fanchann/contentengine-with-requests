FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy AS base

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV POETRY_VIRTUALENVS_CREATE false
RUN apt-get update && apt-get install gcc dumb-init python3-dev -y
RUN pip install poetry
# RUN pip install playwright
# RUN playwright install-deps firefox && rm -rf /var/lib/apt/lists/* && \
# # Workaround for https://github.com/microsoft/playwright/issues/27313
# # While the gstreamer plugin load process can be in-process, it ended up throwing
# # an error that it can't have libsoup2 and libsoup3 in the same process because
# # libgstwebrtc is linked against libsoup2. So we just remove the plugin.
# if [ "$(uname -m)" = "aarch64" ]; then \
#     rm -rf /usr/lib/aarch64-linux-gnu/gstreamer-1.0/libgstwebrtc.so; \
# else \
#     rm -rf /usr/lib/x86_64-linux-gnu/gstreamer-1.0/libgstwebrtc.so; \
# fi
# RUN playwright install firefox --dry-run

FROM base AS deps

WORKDIR /app
COPY ./poetry.lock ./pyproject.toml /app/
RUN poetry install

FROM deps AS build

COPY . /app

ENTRYPOINT ["dumb-init", "--"]
